# Implementation Plan: SRE Production Gate

## 1. Executive Summary
This plan details the implementation of the **SRE Production Gate** to enforce absolute safety for generated patches. We will build a unified Python validator class utilizing standard CLI tools (`terraform`, `opa`) to block syntactically invalid or security-violating remediations.

## 2. Phase 1: TDD Success Wall (Tests)
*   **Task 1.1: Define Validator Test Cases**
    *   Create `projects/nit-fabric/tests/test_validator.py`.
    *   Test cases:
        *   `test_terraform_validate_syntax_pass`: Asserts valid HCL passes format/validation checks.
        *   `test_terraform_validate_syntax_fail`: Asserts broken HCL is blocked with descriptive errors.
        *   `test_opa_rego_ingress_block`: Asserts that an OPA policy blocks ingress patches introducing `0.0.0.0/0`.
        *   `test_destructive_change_block`: Asserts that any patch initiating resource deletion or replacement of critical assets is blocked.

## 3. Phase 2: Structural Verification Engine
*   **Task 2.1: Terraform Sandbox Executor**
    *   Implement `TerraformValidator` class in `projects/nit-fabric/src/nit_fabric/validator.py`.
    *   Methods:
        *   `validate_syntax(hcl_content: str) -> bool`: Writes patch to a sandbox temp file, executes `terraform validate` and `terraform fmt -check`, and captures syntax errors.

## 4. Phase 3: OPA Policy Guardrails
*   **Task 3.1: Rego Policy Definition**
    *   Create OPA policies under `projects/nit-fabric/src/nit_fabric/opa_policies/`:
        *   `remediation_safety.rego`: Defines rules restricting `0.0.0.0/0` ingress and over-privileged IAM configurations.
*   **Task 3.2: OPA Policy Runner**
    *   Implement `OpaValidator` in `projects/nit-fabric/src/nit_fabric/validator.py`.
    *   Methods:
        *   `evaluate_rego(patch: str) -> List[str]`: Evaluates patch properties against OPA Rego rules using native subprocess OPA execution, returning a list of policy violations.

## 5. Phase 4: central Validation Gate Integration
*   **Task 4.1: Remediator Pipeline Hook**
    *   Integrate `ValidatorGate` inside the `PolicyRemediator` class in `remediator.py`.
    *   Ensure that no patch is output or archived to `patches.hcl` unless it successfully passes the validation gate checks.
