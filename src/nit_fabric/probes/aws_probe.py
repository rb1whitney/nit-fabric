import hmac
import ipaddress
import json
import os
import socket
from urllib.parse import urlparse

import urllib3

http = urllib3.PoolManager()


def _is_authorized(event):
    expected = os.environ.get("PROBE_AUTH_TOKEN", "")
    if not expected:
        return True
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    auth = headers.get("authorization", "")
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


def lambda_handler(event, context):
    if not _is_authorized(event):
        return {"statusCode": 401, "body": json.dumps({"error": "unauthorized"})}

    path = event.get("rawPath", event.get("path", ""))

    if path == "/ping":
        return {
            "statusCode": 200,
            "body": json.dumps({"status": "ok", "message": "pong from AWS"}),
        }

    if path == "/check-port":
        body = json.loads(event.get("body") or "{}")
        host = body.get("host")
        port = body.get("port")
        timeout = min(max(float(body.get("timeout", 5)), 0.5), 30.0)

        if not host or port is None:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "host and port are required"}),
            }

        port_num, err = _validate_host_port(host, port)
        if err:
            return {"statusCode": 403, "body": json.dumps({"error": err})}

        try:
            with socket.create_connection((host, port_num), timeout=timeout):
                return {
                    "statusCode": 200,
                    "body": json.dumps(
                        {"status": "success", "message": f"Port {port_num} on {host} is reachable"}
                    ),
                }
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps({"status": "failure", "message": str(e)}),
            }

    if path == "/test-gcp":
        body = json.loads(event.get("body") or "{}")
        gcp_url = body.get("url")

        if not gcp_url:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "gcp url is required"}),
            }

        err = _validate_target_url(gcp_url)
        if err:
            return {"statusCode": 403, "body": json.dumps({"error": err})}

        try:
            r = http.request("GET", gcp_url, timeout=10.0)
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "success",
                    "gcp_response": json.loads(r.data.decode("utf-8")),
                }),
            }
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps({"status": "failure", "message": str(e)}),
            }

    return {
        "statusCode": 404,
        "body": json.dumps({"error": "not found"}),
    }
