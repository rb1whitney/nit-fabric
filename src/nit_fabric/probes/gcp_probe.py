import hmac
import ipaddress
import os
import socket
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)


def _is_authorized():
    expected = os.environ.get("PROBE_AUTH_TOKEN", "")
    if not expected:
        return True
    auth = request.headers.get("Authorization", "")
    token = auth[7:] if auth.lower().startswith("bearer ") else ""
    return hmac.compare_digest(token, expected)


def _validate_target_url(target_url):
    parsed = urlparse(target_url)
    if parsed.scheme != "https" or not parsed.hostname:
        return "Only https URLs with a valid hostname are allowed"
    allowed_hosts = [h.strip().lower() for h in os.environ.get("ALLOWED_PROBE_HOSTS", "").split(",") if h.strip()]
    host = parsed.hostname.lower()
    if allowed_hosts and host not in allowed_hosts:
        return f"Host {host} is not in ALLOWED_PROBE_HOSTS"
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_link_local or ip.is_loopback or ip.is_multicast or ip.is_unspecified or (
            ip.is_private and host not in allowed_hosts
        ):
            return f"Target IP {host} is blocked by SSRF policy"
    except ValueError:
        if host in ("localhost", "metadata.google.internal"):
            return f"Target host {host} is blocked by SSRF policy"
    return None


def _validate_host_port(host, port):
    try:
        port_num = int(port)
    except (TypeError, ValueError):
        return None, "port must be an integer"
    if not (1 <= port_num <= 65535):
        return None, "port must be between 1 and 65535"
    allowed_hosts = [h.strip().lower() for h in os.environ.get("ALLOWED_PROBE_HOSTS", "").split(",") if h.strip()]
    host_l = str(host).strip().lower()
    if allowed_hosts and host_l not in allowed_hosts:
        return None, f"Host {host_l} is not in ALLOWED_PROBE_HOSTS"
    try:
        ip = ipaddress.ip_address(host_l)
        if ip.is_link_local or ip.is_loopback or ip.is_unspecified:
            return None, f"Target IP {host_l} is blocked"
    except ValueError:
        if host_l in ("localhost", "metadata.google.internal"):
            return None, f"Target host {host_l} is blocked"
    return port_num, None


@app.route("/ping", methods=["GET"])
def ping():
    if not _is_authorized():
        return jsonify({"error": "unauthorized"}), 401
    return jsonify({"status": "ok", "message": "pong from GCP"})


@app.route("/check-port", methods=["POST"])
def check_port():
    if not _is_authorized():
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json() or {}
    host = data.get("host")
    port = data.get("port")
    timeout = min(max(float(data.get("timeout", 5)), 0.5), 30.0)

    if not host or port is None:
        return jsonify({"error": "host and port are required"}), 400

    port_num, err = _validate_host_port(host, port)
    if err:
        return jsonify({"error": err}), 403

    try:
        with socket.create_connection((host, port_num), timeout=timeout):
            return jsonify({"status": "success", "message": f"Port {port_num} on {host} is reachable"})
    except Exception as e:
        return jsonify({"status": "failure", "message": str(e)}), 500


@app.route("/test-aws", methods=["POST"])
def test_aws():
    if not _is_authorized():
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json() or {}
    aws_url = data.get("url")

    if not aws_url:
        return jsonify({"error": "aws url is required"}), 400

    err = _validate_target_url(aws_url)
    if err:
        return jsonify({"error": err}), 403

    try:
        response = requests.get(aws_url, timeout=10)
        return jsonify({
            "status": "success",
            "aws_response": (
                response.json()
                if response.headers.get("Content-Type", "").startswith("application/json")
                else response.text
            ),
        })
    except Exception as e:
        return jsonify({"status": "failure", "message": str(e)}), 500


# Production containers should run via WSGI: gunicorn -w 4 -b 0.0.0.0:8080 nit_fabric.probes.gcp_probe:app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=False)
