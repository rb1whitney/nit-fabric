package remediation

default allow = false

allow {
    count(deny) == 0
}

# Deny unrestricted public ingress
deny[msg] {
    input.resource_type == "aws_security_group_rule"
    input.cidr_blocks[_] == "0.0.0.0/0"
    msg := "Critical Breach: Unrestricted public ingress (0.0.0.0/0) is prohibited."
}

# Deny IAM Wildcard actions
deny[msg] {
    contains(input.resource_type, "iam")
    input.effect == "Allow"
    input.actions[_] == "*"
    msg := "Least Privilege Violation: Wildcard actions or roles are prohibited."
}

# Deny destruction on critical resources
deny[msg] {
    input.action_type == "destroy"
    msg := "Destruction Violation: Resource destruction of critical assets is prohibited."
}
