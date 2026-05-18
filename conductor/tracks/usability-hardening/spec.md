# Track: Usability Hardening (Phase 0)

**Owner**: @swarm-scout / @swarm-engineer
**Status**: [INITIALIZING]
**Priority**: CRITICAL (Blocker for Industrial-Grade Reliability)

## 1. Problem Statement
The `nit-fabric` project currently suffers from "Ghost Dependencies" and "Silent Discovery Failures." 
- **Ghost Dependencies**: The system relies on external binaries and environment variables that are not explicitly checked or managed, leading to runtime crashes in clean environments.
- **Silent Discovery Failures**: Cloud resource discovery fails without descriptive error messages, making it impossible for operators to distinguish between "No Resources Found" and "Access Denied" or "API Error."

## 2. Objectives
- [ ] **Dependency Characterization**: Implement a `nit-fabric doctor` command or equivalent pre-flight check.
- [ ] **Explicit Error Handling**: Refactor discovery logic to bubble up specific cloud provider errors.
- [ ] **Environment Isolation**: Ensure the tool can run in a containerized/isolated environment with minimal side effects.

## 3. Success Criteria
- `nit-fabric` fails fast with a clear error message if a required binary (e.g., `aws`, `gcloud`, `terraform`) is missing.
- Discovery logs distinguish between IAM permission errors and empty resource sets.
- 100% pass rate on "Clean Room" execution tests.

## 4. Work Tree
- `projects/nit-fabric/src/cli/doctor.py`
- `projects/nit-fabric/src/discovery/base.py`
- `projects/nit-fabric/tests/usability/`

## 5. Specialist Guidance
- **Engineer**: Lead implementation of the pre-flight checks and error bubbling.
- **Scout**: Verify the "Ghost Dependencies" are fully mapped and characterized.
