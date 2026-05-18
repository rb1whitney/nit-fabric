# nit-fabric Conductor: Project Remediation Ledger

**Project Status**: [RE-ENGINEERING] | **Audit Verdict**: [VAPORWARE-REMEDIATION-ACTIVE]

---

##  Active Remediation Tracks

### Track: usability-hardening (Phase 0)
- **Owner**: @swarm-scout / @swarm-engineer
- **Goal**: Eliminate 'Ghost Dependencies' and 'Silent Discovery Failures' via pre-flight checks and explicit error bubbling.
- **Status**: [COMPLETED] | [**conductor/tracks/usability-hardening/spec.md**](file://./tracks/usability-hardening/spec.md)
- **Priority**: CRITICAL

### Track: aws-reengineering (Phase 1)
- **Owner**: @specialist-aws
- **Goal**: Implement tag-driven discovery and high-resolution topology (TGW, DX, PrivateLink).
- **Status**: [COMPLETED] | [**conductor/tracks/aws-reengineering/spec.md**](file://./tracks/aws-reengineering/spec.md)
- **Priority**: HIGH

### Track: gcp-reengineering (Phase 1)
- **Owner**: @specialist-gcp
- **Goal**: Implement Shared VPC topology and Workload Identity auditing.
- **Status**: [COMPLETED] | [**conductor/tracks/gcp-reengineering/spec.md**](file://./tracks/gcp-reengineering/spec.md)
- **Priority**: HIGH

### Track: sre-production-gate (Phase 2)
- **Owner**: @specialist-sre
- **Goal**: Implement 'Safe Remediation' framework with mandatory Terraform validation and OPA guardrails.
- **Status**: [PLANNING] | [**conductor/tracks/sre-production-gate/spec.md**](file://./tracks/sre-production-gate/spec.md)
- **Priority**: MEDIUM

### Track: formal-verification-engine (Phase 3)
- **Owner**: @security-reviewer
- **Goal**: Replace Jinja2 templates with a Z3-backed formal verification solver and type-safe generator.
- **Status**: [PLANNING] | [**conductor/tracks/formal-verification-engine/spec.md**](file://./tracks/formal-verification-engine/spec.md)
- **Priority**: STRATEGIC

---

##  Foundational Tracks (Legacy/Core)

### Track: nit-fabric-foundation
- **Status**: [STABLE] | [**conductor/tracks/nit-fabric-foundation/spec.md**](file://./tracks/nit-fabric-foundation/spec.md)

### Track: networking
- **Status**: [ACTIVE] | [**conductor/tracks/networking/spec.md**](file://./tracks/networking/spec.md)

### Track: core-logic
- **Status**: [ACTIVE] | [**conductor/tracks/core-logic/plan.md**](file://./tracks/core-logic/plan.md)

### Track: aws-hardening
- **Status**: [DEPRECATED-BY-REENGINEERING]

### Track: gcp-hardening
- **Status**: [DEPRECATED-BY-REENGINEERING]
