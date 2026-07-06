# Review: Validator Boundary Baseline v0.1

Date: 2026-07-01
Status: reviewed
Scope: read-only review of three local registry validators and their fixture tests

Reviewed validators:

- `control-plane/registry/validate-document-registry.py`
- `control-plane/registry/validate-federated-document-registry.py`
- `control-plane/registry/validate-governance-registry.py`

Reviewed tests:

- `control-plane/registry/test-document-registry-validator.py`
- `control-plane/registry/test-federated-document-registry-validator.py`
- `control-plane/registry/test-governance-registry-validator.py`

## Result

No blocking bug was found in this baseline review.

The three validators now share the same boundary shape:

1. Check the CLI target before reading it.
2. Resolve paths through a safe resolver that catches symlink-loop errors.
3. Check both raw path text and resolved path destination for protected markers.
4. Return a structured invalid-target result instead of crashing or reading the target.
5. Cover the main boundary cases with local fixture tests.

No shared helper should be extracted in this pass. The duplicated pattern is now
stable enough to compare, but one more use or one small refactor proposal should
happen before replacing the repeated local functions.

## Difference Table

| Area | Document Registry | Federated Document Registry | Governance Registry | Review note |
| --- | --- | --- | --- | --- |
| target preflight | `DOC-TARGET` before `load_yaml` | `FDR-TARGET` before `load_yaml` | `SC-TARGET` before `load_yaml` | Aligned. Invalid target is rejected before file read. |
| safe resolve | `safe_resolve` catches `OSError` and `RuntimeError` | `safe_resolve` catches `OSError` and `RuntimeError` | `safe_resolve` catches `OSError` and `RuntimeError` | Aligned. Symlink loops become findings instead of crashes. |
| raw protected path | CLI target and document path references | CLI target and listed registry/tool paths | CLI target | Intentional difference: governance object paths are metadata here and are not opened. |
| resolved protected path | CLI target and document path references | CLI target and listed registry/tool paths | CLI target | Aligned for every path the validator may read. |
| symlink outside | canonical/source/related path plus CLI target fixtures | registry/tool path plus CLI target fixtures | CLI target fixtures | Aligned by read surface. |
| symlink protected | canonical/source/related path plus target fixtures | registry/tool path plus target fixtures | target fixtures | Aligned by read surface. |
| symlink loop | canonical path plus CLI target fixtures | registry path plus CLI target fixtures | CLI target fixtures | Aligned by read surface. |
| CLI fixture | protected, outside, and symlink-loop targets assert JSON failure and `target_read_performed: false` | protected, outside, and symlink-loop targets assert JSON failure and `target_read_performed: false` | protected, outside, and symlink-loop targets assert JSON failure and `target_read_performed: false` | Aligned for invalid-target main path. |
| invalid target result | `passed: false`, zero document counts, `target_read_performed: false`, no external/runtime/provider/memory action | `passed: false`, zero registry counts, `target_read_performed: false`, no external/runtime/provider/memory action | `passed: false`, zero object counts, `target_read_performed: false`, no external/runtime/provider/memory action | Aligned intent; names differ by validator domain. |

## Evidence

Fixture tests:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-document-registry-validator.py
cases=24 failures=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-federated-document-registry-validator.py
cases=21 failures=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-governance-registry-validator.py
cases=12 failures=0
```

Current example registry checks:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
Status: PASS
Summary: documents=29 pass=29 warn=0 fail=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
Status: PASS
Summary: registries=3 pass=3 warn=0 fail=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-governance-registry.py control-plane/registry/drafts/agents-os-governance-registry.v0.1.example.yaml
Status: PASS
Summary: objects=18 pass=18 warn=0 fail=0
```

## Residual Risks

- The three validators still duplicate path-boundary helper logic. This is now
  useful duplication because the behavior has just stabilized.
- The Governance Registry validator does not validate object `path` values as
  readable file paths. That is intentional because this validator treats those
  fields as metadata and does not open them.

## Baseline Decision

Keep the three validators separate for now.

Do not extract a shared helper until the duplicated behavior has one more
stable review or one more validator needs the same boundary pattern.
