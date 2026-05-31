# Implementation Plan: Formal Verification Engine

## 1. Executive Summary
This plan outlines the transition from heuristic Jinja2 templating to a mathematically rigorous **Formal Verification Engine**. We will use **Z3** for SMT solving to prove network security invariants and a **Pydantic-based DSL** for type-safe remediation generation.

## 2. Phase 1: TDD Foundation & Schema Definition
**Goal**: Establish the type-safe contract for all remediation actions.

- [ ] **Task 1.1: Define Remediation DSL Schemas**
  - Create `projects/nit-fabric/src/verification/models.py`.
  - Define `BaseAction`, `FirewallRuleAction`, `RoutingAction`, and `SecurityGroupAction` using Pydantic.
  - Ensure all fields are strictly typed (e.g., `IPv4Network`, `conint` for ports).
- [ ] **Task 1.2: Success Wall (Tests)**
  - Create `projects/nit-fabric/tests/verification/test_solver.py`.
  - Define test cases for:
    - CIDR containment (e.g., `10.0.0.0/24` inside `10.0.0.0/16`).
    - Rule shadowing (e.g., Rule A blocks what Rule B allows).
    - Invariant violation detection (e.g., Public -> DB).

## 3. Phase 2: Z3 Solver Implementation (`solver.py`)
**Goal**: Translate network state into SMT constraints.

- [ ] **Task 2.1: Bit-Vector IP Representation**
  - Implement `IPEncoder` to convert `IPv4Address` to Z3 `BitVec(32)`.
  - Implement CIDR-to-Constraint logic using bitwise masking.
- [ ] **Task 2.2: Logic Engine**
  - Implement `NetworkSolver` class.
  - Method `add_rule(src, dst, port, action)`: Adds logical implications to the solver.
  - Method `verify_invariant(invariant_formula)`: Checks if the negation of the invariant is satisfiable.
- [ ] **Task 2.3: Counter-Example Extraction**
  - If `solver.check()` is `sat`, extract the model and map it back to a human-readable "Violation Report" (Source IP, Dest IP, Port).

## 4. Phase 3: Type-Safe Generator (`generator.py`)
**Goal**: Replace Jinja2 with parameterized logic.

- [ ] **Task 3.1: Parameterized Generator**
  - Implement `RemediationGenerator`.
  - Use the Pydantic models from Phase 1 to construct remediation objects.
  - Implement `to_hcl()` methods for each model to produce clean, valid Terraform/OpenTofu code.
- [ ] **Task 3.2: The Verification Gate**
  - Implement a loop: `Generate -> Add to Solver -> Verify`.
  - If the generated remediation doesn't result in `unsat` for the invariant, fail the generation.

## 5. Phase 4: Integration & Formal Audit
**Goal**: Connect to the existing `nit-fabric` pipeline.

- [ ] **Task 4.1: HCL Parser Integration**
  - Create a bridge to ingest parsed HCL (from `core-logic`) into the `NetworkSolver`.
- [ ] **Task 4.2: CLI Entrypoint**
  - Add `nit verify` command to trigger the formal audit.

## 6. Expert-Only Solution Summary
The solution moves away from "string-bashing" (Jinja2) which is prone to injection and logic errors. By modeling the network as a **Bit-Vector SMT problem**, we leverage Z3's ability to perform **Exhaustive Symbolic Execution** of the firewall state. The "Type-Safe Generator" ensures that the output is not just syntactically correct, but **Semantically Proven** to resolve the identified vulnerability before a single line of HCL is written to disk.
