# Implementation Plan: AWS Re-engineering (TDD-First)

## Phase 1: Test Infrastructure (TDD)
- [ ] **Task 1.1**: Create `tests/test_aws_discovery.py`.
- [ ] **Task 1.2**: Define mock AWS responses for TGW, DX, and Route Tables.
- [ ] **Task 1.3**: Write failing tests for:
    - `test_discover_transit_gateways`: Verify TGW attachments and routes are captured.
    - `test_discover_direct_connect`: Verify DX Gateway associations.
    - `test_tag_based_filtering`: Verify only resources with `nit-fabric:managed=true` are processed.

## Phase 2: Core Discovery Implementation
- [ ] **Task 2.1**: Implement `AWSDiscoverer.get_transit_gateways()`.
- [ ] **Task 2.2**: Implement `AWSDiscoverer.get_direct_connect_gateways()`.
- [ ] **Task 2.3**: Implement `AWSDiscoverer.get_route_tables_detailed()`.
- [ ] **Task 2.4**: Implement `AWSDiscoverer.get_vpc_endpoints_detailed()`.

## Phase 3: Integration & Refactoring
- [ ] **Task 3.1**: Refactor `bin/discover.py` to use the new `AWSDiscoverer` class.
- [ ] **Task 3.2**: Update the `CloudDiscoverer` to orchestrate the new AWS logic.
- [ ] **Task 3.3**: Replace the 'slop' (naming-based logic) with the tag-driven protocol.

## Phase 4: Verification
- [ ] **Task 4.1**: Run `pytest tests/test_aws_discovery.py` and ensure all tests pass.
- [ ] **Task 4.2**: Execute `python3 bin/discover.py --mode mock` to verify the updated mock output.
- [ ] **Task 4.3**: (Optional) Run in `--mode cli` against a sandbox environment.

## Expert-Level Patterns
- **Pagination**: Use Boto3 paginators for all `describe_*` calls to handle large-scale environments.
- **Error Handling**: Implement exponential backoff for AWS API throttling.
- **Graph Representation**: Store connectivity as an adjacency list to facilitate path analysis (e.g., "Can Subnet A reach the DX Gateway?").
