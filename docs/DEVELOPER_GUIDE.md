# nit-fabric | Developer Guide & Code Tour
*A Guide to Codebase Structure, Formal Verification, and Infrastructure Design*

---

## 1. Directory Overview & Codebase Architecture

`nit-fabric` separates discovery, evaluation, formal verification, and remediation into distinct layers. This guide explains how to navigate, modify, and run the code.

```
nit-fabric/
├── bin/            # CLI controllers and nexus synchronization script
├── docs/           # Specifications, runbooks, and developer documentation
├── src/            # Core application package (nit_fabric)
├── terraform/      # Hub/Spoke connectivity and security infrastructure
└── tests/          # Pytest validation test suites
```

---

## 2. Execution Layer (`bin/`)

### 2.1 Nexus Synchronization (`bin/nexus.py`)
`bin/nexus.py` enforces the **Agentic Standard**. Since agent configurations are centralized inside the `.agent/` master vault, the `nexus.py` script synchronizes IDE configurations (`.claude/`, `.gemini/`, `.vscode/`, `.github/`) by symlinking vendor-specific paths to the central vault. This prevents configuration duplication.

### 2.2 CLI Controller (`bin/nit-fabric`)
The primary interface for the tool. It implements the three-stage lifecycle:
1. **`scan`**: Triggers active discovery across Cloud APIs to output `context.json`.
2. **`remediate --explain`**: Parses violations, running policy evaluation to generate `violations.json`.
3. **`remediate --provider cli`**: Renders structural HCL patches (`patches.hcl`) and CLI scripts (`fix.sh`).

---

## 3. Core Engine (`src/nit_fabric/`)

### 3.1 Syntax & Policy Gate (`src/nit_fabric/validator.py`)
The [validator.py](file://./src/nit_fabric/validator.py) implements the production safety gates:
* **HCL Syntax Checking**: Validates generated patches using `terraform validate` if installed. It strips environment dependencies (like missing provider schemas) to focus strictly on syntactic validity, with a built-in pure Python fallback parser.
* **OPA Rego Evaluation**: Uses Open Policy Agent (OPA) with policies defined at `remediation_safety.rego` to block unsafe actions (such as `0.0.0.0/0` public ingress, wildcard IAM policy bindings, or critical resource destructions).

### 3.2 Formal Verification (`src/nit_fabric/verification/`)
For safety-critical configurations, pure validation is not enough. The `verification` sub-package uses formal mathematical modeling.

#### 3.2.1 SMT Theorem Proving (`src/nit_fabric/verification/solver.py`)
The [solver.py](file://./src/nit_fabric/verification/solver.py) uses the **Z3 SMT Solver** to prove network invariants.
* **Bit-Vector Modeling**: IPv4 addresses are converted to 32-bit bit-vectors ($BitVec(32)$).
* **CIDR Expressions**: A CIDR range (e.g. `10.0.0.0/16`) is represented as a bitwise mask equality constraint:
  $$(IP \ \& \ Mask) == NetworkAddress$$
* **Invariant Proofs**:
  * **Containment**: Proof that a child network is completely within a parent network by checking that $Child \land \neg Parent$ is unsatisfiable (`unsat`).
  * **Overlap**: Proof that two subnets are disjoint by checking that $A \land B$ is `unsat`.
  * **Ingress Security Pathing**: Models firewall routing paths to mathematically prove whether any public IP can reach a protected backend. If Z3 returns satisfiable (`sat`), it outputs the exact source IP counter-example that bypasses the firewall rules.

#### 3.2.2 Models and Generator (`src/nit_fabric/verification/models.py` & `generator.py`)
Provides intermediate representation structures mapping discovered cloud objects (Subnets, Security Groups, Instances) into mathematical models that can be ingested by the solver.

---

## 4. Infrastructure Baseline (`terraform/`)

The infrastructure baseline sets up the multi-cloud transit connection.
* **`modules/aws_hub/`**: Sets up the Transit Gateway, VPC endpoints, and the primary hub VPC.
* **`modules/gcp_spoke/`**: Provisions the GCP Cloud Router, HA VPN Gateways, and primary subnets.
* **`boundary_rules.tf`**: Sets up the default-deny Tier-0 transit boundaries.
* **`main.tf`**: Orchestrates modules and defines transit subnets using algebraic IPAM variables.

---

## 5. Test Verification Suites (`tests/`)

The test suite validates logic correctness before any pull request is merged:
* **`test_engine.py`**: Asserts policy rules-engine behavior (CIDR overlaps, public ingress, bucket versioning).
* **`test_determinism.py`**: Validates the trie-based algebraic IPAM solver to ensure subnet allocations are 100% deterministic.
* **`test_sovereignty.py`**: Characterizes zero-trust boundary rule audits and topology graph validations.
* **`test_validator.py`**: Verifies syntax gates and evaluation logic (OPA Rego emulation fallbacks).
* **`verification/test_solver.py`**: Asserts the mathematical correctness of Z3 SMT containment, overlap, and reachability proofs.
