# Specification: SRE Production Gate (Safe Remediation)

## 1. Objective
Establish a zero-trust, deterministic **Safe Remediation** validation gate for `nit-fabric`. Every generated HCL patch or Shell script must pass through mandatory syntactic, structural, and security policy checks using **Terraform/OpenTofu validation** and **Open Policy Agent (OPA)** constraints before it can be presented to operators or applied.

## 2. Core Components

### 2.1 Syntactic and Structural Validation Gate (`TerraformValidator`)
*   **Syntax Audits**: Run `terraform validate` and `terraform fmt -check` on generated patches to guarantee structural soundness.
*   **Sandbox Directory Execution**: Patches must be merged into a local sandbox workspace alongside target modules to perform dry-runs without contaminating the live codebase.

### 2.2 Security Policy Guardrails (`OpaValidator`)
*   **Rego Engine Integration**: Integrate OPA policy evaluations using Rego scripts to verify that proposed remediations do not violate organizational safety baselines.
*   **Mandatory Checks**:
    *   **Anti-Breach Rule**: Block any patch attempting to expose open ingress (`0.0.0.0/0`) or open egress paths.
    *   **Least Privilege Rule**: Block IAM additions that grant over-privileged wildcard actions (`*`) or roles (`roles/owner`, `roles/editor`).

### 2.3 Destructive Action Prevention
*   **Plan Mutation Guard**: Intercept Terraform execution plans to detect `destroy` or `replace` actions on protected resources (VPC, Transit Gateway, Direct Connect Gateway, GKE Workload Identity pools).
*   **Prevention Gate**: Throw immediate validation errors if destructive changes are detected without explicit interactive bypasses.

## 3. Success Criteria
*   Immediate rejection of syntactically invalid HCL patches.
*   OPA Rego policy blocks open security group ingress or over-privileged service account policies.
*   Accidental resource deletions are blocked via pre-apply plan auditing.
