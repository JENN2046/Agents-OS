# AGENTS OS Phase 5A M0-A Plan R2 Atomic Independent Review Package v0.1

Date: 2026-07-19  
Owner: Jenn  
Agent steward: Nobao  
Status: FIXED_FOR_FRESH_FULL_ATOMIC_INDEPENDENT_REVIEW

## 1. Review unit

```yaml
review_unit: PHASE_5A_M0A_PLAN_BUILD_PROFILE_V0_1_R2_ATOMIC_BUNDLE
atomic: true
partial_review: forbidden
R1_subjects: 4
R2_subjects: 7
total_subjects: 11
precedence:
  - R2_explicit_replacements
  - R1_all_other_clauses
```

Canonical manifest:

```text
control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r2-atomic-independent-review-package-v0.1.manifest.yaml
SHA-256: 48b5e53032e5d6bf527ff542febf20b4c9e940a6d5ab48c6960eb5bcd2bd0f26
```

## 2. R2 closure claims requiring independent proof

The reviewer must independently prove or refute:

1. the exact union of all F1–F6 accepted subjects is present and hash-bound as
   `110/110` immutable canonical bytes;
2. the closed 63-obligation inventory gives every M0-A semantic requirement an
   implementation module, reducer/boundary, persistence or explicit ephemeral
   owner, and positive, negative, replay and crash test owner;
3. the 18-table SQLite inventory is truly exhaustive and closes all canonical
   fact, assessment, snapshot, dispatch-arm, stored-first, first-apply and F6
   lineage/current-head transaction boundaries;
4. the 41-file external package inventory, tree-hash preimage, package manifest,
   exact blocked plugin manifest, direct `index.js` entrypoint and clean linked
   worktree projection are deterministic and compatible with the fixed
   VCPToolBox contract;
5. R2 does not implement or authorize Rust, JavaScript, N-API, dependency
   installation, SQLite creation, VCPToolBox changes, plugin enablement or any
   runtime/effect.

## 3. Fixed commands

Run the manifest commands from a complete offline extraction. Minimum:

```bash
python3 control-plane/registry/validate-phase5a-m0a-plan-r2-closure.py \
  control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-plan-r2-closure-witness-v0.1.json \
  --self-test

python3 control-plane/registry/build-phase5a-m0a-plan-r2-closure-witness.py \
  /tmp/phase5a-r2-review-rebuilt.json

cmp /tmp/phase5a-r2-review-rebuilt.json \
  control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-plan-r2-closure-witness-v0.1.json
```

The author result is:

```yaml
canonical_subjects: 110/110
obligations: 63
tables: 18
source_inventory: 41
fixed_mutations_rejected: 12/12
terminal_outcome: NOT_EXECUTED
```

This is not an independent conclusion.

## 4. Required independent attacks

At minimum construct coordinated, fully re-signed attempts to:

- remove or substitute one canonical accepted subject while updating package
  hashes;
- remove an F5 or F6 obligation, or preserve its label while deleting SQL,
  replay or crash ownership;
- encode assessment/snapshot objects in an undeclared hidden table or opaque
  Event payload;
- move `dispatch_arm`, stored-first accounting or first-apply state to a caller
  claim or uncommitted projection;
- change the current pointer target without fact/Event/CAS atomicity;
- add an undeclared table, view, trigger, connection or retry path;
- produce two different source trees with the same claimed materialization
  receipt through path, mode, symlink, exclusion or ordering ambiguity;
- replace `plugin-manifest.json.block` with an enabled manifest or another
  entrypoint while preserving self-declared hashes;
- modify a VCPToolBox tracked path outside the sole install overlay;
- create a second permission, identity, Task, Command or Host authority;
- turn synthetic evidence into runtime authority;
- treat author `PASS` as plan freeze or implementation authority.

Rejection must come from the target contract, not stale hashes or missing
dependent re-signing.

## 5. Allowed result

```yaml
allowed_results:
  - PASS_NO_BLOCKER
  - BLOCK
partial_acceptance: forbidden
```

`PASS_NO_BLOCKER` requires zero blocker, major, minor and unresolved ambiguity.
The author self-review is evidence only.

## 6. Governance stop

Even `PASS_NO_BLOCKER` does not accept or freeze the plan. Jenn must make the
atomic plan decision separately. Even a later plan freeze does not authorize
implementation; a second explicit Jenn implementation decision remains
mandatory.
