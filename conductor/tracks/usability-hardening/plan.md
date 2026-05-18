# Implementation Plan: Usability Hardening (Phase 0)

## 🔍 Analysis & Context
*   **Objective**: Eliminate 'Ghost Dependencies' and 'Silent Discovery Failures' by refactoring path resolution, implementing pre-flight checks, and enforcing strict error propagation.
*   **Affected Files**:
    - `projects/nit-fabric/bin/nit-fabric` (Entry point)
    - `projects/nit-fabric/bin/discover.py` (Discovery logic)
    - `projects/nit-fabric/pyproject.toml` (New)
    - `projects/nit-fabric/src/nit_fabric/preflight.py` (New)
*   **Key Dependencies**: `subprocess`, `argparse`, `pkg_resources` (or `importlib.metadata`), `pytest`.
*   **Risks/Edge Cases**: 
    - Breaking existing workflows that rely on relative paths.
    - `gcloud`/`aws` CLI version mismatches.
    - Permission issues when creating the `out/` directory.

## 📋 Micro-Step Checklist
- [ ] Phase 1: Characterization & Infrastructure
  - [ ] Step 1.1: Define `pyproject.toml` and move to `src/` layout.
  - [ ] Step 1.2: Create TDD harness for `PreFlightChecker`.
- [ ] Phase 2: Implementation
  - [ ] Step 2.1: Implement `PreFlightChecker` for AWS/GCP auth.
  - [ ] Step 2.2: Refactor `nit-fabric` entry point for dynamic discovery.
  - [ ] Step 2.3: Refactor `discover.py` for strict error propagation and `out/` artifacts.
- [ ] Phase 3: Verification
  - [ ] Step 3.1: Verify `pip install -e .` works.
  - [ ] Step 3.2: Verify `nit-fabric scan` fails loudly without auth.
  - [ ] Step 3.3: Verify artifacts are written to `out/`.

## 📝 Step-by-Step Implementation Details

### Phase 1: Characterization & Infrastructure
1. **Step 1.1 (Packaging)**: Establish the modern Python project structure.
    *   **Action**: Create `projects/nit-fabric/pyproject.toml`.
    *   **Content**:
        ```toml
        [build-system]
        requires = ["setuptools>=61.0"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "nit-fabric"
        version = "0.1.0"
        dependencies = [
            "jinja2",
            "pyyaml",
        ]

        [project.scripts]
        nit-fabric = "nit_fabric.main:main"

        [tool.setuptools.packages.find]
        where = ["src"]
        ```
    *   **Action**: Move `projects/nit-fabric/bin/*.py` to `projects/nit-fabric/src/nit_fabric/`.
    *   **Action**: Update `nit-fabric` wrapper to use `import nit_fabric`.

2. **Step 1.2 (TDD Harness)**: Define success for pre-flight checks.
    *   **Target File**: `projects/nit-fabric/tests/test_preflight.py`
    *   **Test Cases**: 
        - `test_aws_auth_fail`: Mock `aws sts get-caller-identity` failure.
        - `test_gcp_auth_fail`: Mock `gcloud auth print-access-token` failure.
        - `test_path_resolution`: Verify `out/` directory is correctly resolved relative to package root.

### Phase 2: Implementation
1. **Step 2.1 (PreFlightChecker)**:
    *   **Target File**: `projects/nit-fabric/src/nit_fabric/preflight.py`
    *   **Logic**: 
        - `check_aws()`: Runs `aws sts get-caller-identity --query Account --output text`.
        - `check_gcp()`: Runs `gcloud config get-value project`.
        - Raise `AuthenticationError` with specific remediation steps if they fail.

2. **Step 2.2 (Dynamic Entry Point)**:
    *   **Target File**: `projects/nit-fabric/src/nit_fabric/main.py` (formerly `bin/nit-fabric`)
    *   **Change**: Replace `subprocess.run("python3 projects/nit-fabric/bin/...")` with direct function calls or `sys.executable -m nit_fabric.discover`.

3. **Step 2.3 (Robust Discovery)**:
    *   **Target File**: `projects/nit-fabric/src/nit_fabric/discover.py`
    *   **Change**: Update `_run_cli` to remove `try-except` swallowing. Use `check=True` and let `CalledProcessError` bubble up or wrap in a custom `DiscoveryError`.
    *   **Change**: Default output path to `projects/nit-fabric/out/context.json`.

### Phase 3: Verification
1. **Step 3.1 (Installation)**:
    *   **Action**: `pip install -e projects/nit-fabric/`
    *   **Success**: `nit-fabric --help` works from any directory.

2. **Step 3.2 (Failure Mode)**:
    *   **Action**: Unset `AWS_PROFILE` and run `nit-fabric scan --mode cli`.
    *   **Success**: Tool exits with non-zero code and "AWS Authentication Failed" message.

## ✅ Success Criteria
1. No hardcoded `projects/nit-fabric/bin/` paths in the codebase.
2. `PreFlightChecker` successfully detects missing cloud credentials.
3. All discovery errors include the stderr from the underlying CLI tool.
4. Artifacts consistently land in `projects/nit-fabric/out/`.
