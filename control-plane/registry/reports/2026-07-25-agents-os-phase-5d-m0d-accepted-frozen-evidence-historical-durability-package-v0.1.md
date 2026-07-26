# Phase 5D M0-D Accepted/Frozen Evidence Historical Durability Package v0.1

Date: 2026-07-25
Status: CORRECTION_OVERLAY_REVIEW_NEEDED
Owner: Jenn
Agent steward: Nobao

## 1. Purpose

This package preserves three already accepted and frozen Phase 5D M0-D
governance evidence units on a branch rooted at the exact post-PR-37 mainline
state. It is a historical durability projection only.

The 58 frozen artifacts remain bound to historical anchor
`d200b31471df4c82bab86de9412086259585b893`. Two current-worktree files now
carry review-needed portability corrections. Their new bytes are not part of
the old freeze and inherit no execution authority.

It does not reactivate an old queue, replace `CURRENT_STATE.md`, change a
consumer default queue pointer, authorize execution, or reopen MEHS.

## 2. Exact Base

```yaml
base_commit: 3a5ce7ab0af075f4b12f75ca16b2f1554f399536
base_tree: d0bd0b967ead4209a828cd1133ceab2b1c9a4a54
```

## 3. Hash-Bound Manifest

```yaml
path: control-plane/registry/reports/2026-07-25-agents-os-phase-5d-m0d-accepted-frozen-evidence-historical-durability-v0.1.manifest.json
sha256: ac37d8166147fc73abd756f46afb19c4bc8c63363589573c1a14ae055d35ea11
artifact_count: 58
historical_anchor_exact_artifact_count: 58
current_worktree_correction_count: 2
materialized_from_preserved_canonical_root: 57
already_present_on_base_main: 1
declared_path_sha256_pairs_reverified: 53
declared_hash_conflicts: 0
declared_hash_mismatches: 0
```

## 4. Included Accepted/Frozen Units

| Unit | Frozen result | Decision SHA-256 | Canonical manifest SHA-256 |
|---|---|---|---|
| Host-Smoke Adapter Binding R2 | `ACCEPTED_FROZEN` | `ba24dd3a7e13d04fd23fc688f9a5a1d941d50daa352ac7cb6cbf6f26f36eb46c` | `422c97bae3c23db8c18860e3779b3c0b016bb382f1732a134f9757619caefa5f` |
| Protected Source Boundary R1 | `ACCEPTED_FROZEN` | `0ecd59f7844dbec681a32b677561a4cf133b827b5950aea2af6689a2ba47c082` | `b26584bcbc93219a382d23e4ccd1a9b09650c0fca6920604bc4b06a493ca4b45` |
| Actual Object-Only Source Run R3 | `ACCEPTED_FROZEN_OFFLINE_CLOSURE_ONLY` | `a79cbe9d089a22325165eb51c88e01e30f3007a8f7a2293ec04d5348af460922` | `f5376a4711cf9dfa533e577d7e084ab47150d676ca8ceab926ef97f166ac9df1` |

The historical `v18.7` queue bytes are included only because the R3 canonical
manifest binds them as an authority input from that review moment. They are not
the active queue and must not become a consumer default.

### 4.1 Current-worktree portability correction

The following current paths intentionally differ from their frozen
`d200b314...` bytes:

| Path | Historical SHA-256 | Current correction SHA-256 | Status |
|---|---|---|---|
| `control-plane/registry/run-phase-5d-m0d-actual-object-only-source-run-r3.py` | `3bf99381e9c4b3e4413abfa799dbad676ae864e173dbe0eeef15ce829d02e5f0` | `049475b14376183b097f8422a129bcc94af29aa3ea9a7e1f90ad1361b99c3235` | `REVIEW_NEEDED` |
| `control-plane/registry/validate-phase-5d-m0d-actual-object-only-source-run-r3.py` | `cf28f801abc3db9e133904da4d729ce40c50c4ba9f03d335b5d151841d186601` | `0c39cb4d4693641baeba54c73862032006d9b9ab1630d334530ba26e247bf9b7` | `REVIEW_NEEDED` |

The runner derives only its offline fixture root from `__file__`. Its legacy
`--actual` spelling is now a deterministic denial surface: it returns
`BLOCKED_CURRENT_JENN_EXECUTION_DECISION_REQUIRED` before reading a manifest,
running Git, creating a run root, or attempting a receipt. No caller-provided
path or digest can activate it. The frozen R3 manifest remains immutable
historical evidence, not a live trust anchor for corrected runner bytes, so the
old runner-in-manifest self-hash cycle no longer participates in execution.

The transaction-safe receipt helper remains offline fault-tested for partial
write, file-`fsync`, close, parent-`fsync`, and no-replace behavior, but no
current CLI path can call it. The validator adds copied-checkout, exact
effect-free denial, absence of a live self-hash anchor, scanner-digest, and
receipt transaction regressions. A future execution requires a separately
reviewed launcher plus an authenticated external Jenn decision; it cannot
reactivate these bytes. Neither correction updates the old R3 freeze manifest
or decision, and neither carries forward any `--actual` authority.

## 5. Explicit Exclusions

This package excludes:

- all R4 and R5 subject, manifest, runner, review, disposition, decision, and
  queue artifacts;
- the stale local `CURRENT_STATE.md` projection;
- local `v19.0` default-queue pointer changes;
- the unregistered execution-model-reset draft;
- Memory runtime data, nested Git worktrees, caches, and the empty
  `execute_command` file;
- Gate 1 authority reuse, `--actual` replay, Host or VCPToolBox Git execution;
- runtime, provider, database, private Memory, `state-private`, release,
  deploy, publish, tag, force push, or history rewrite.

## 6. Validation Contract

The candidate must fail closed unless:

1. all 58 manifest artifacts exist as exact Git blobs at historical anchor
   `d200b31471df4c82bab86de9412086259585b893`;
2. every historical-anchor artifact SHA-256 matches the durability manifest;
3. all three canonical manifests match their immutable decision bindings;
4. the two declared current-worktree corrections match their separate SHA-256
   values and remain `REVIEW_NEEDED`;
5. the selected freeze decisions still report their exact accepted/frozen
   result;
6. no R4/R5 path is present in the historical artifact set;
7. `CURRENT_STATE.md` and all consumer default queue pointers remain based on
   the post-PR-37 mainline state;
8. Document Registry and targeted offline validators pass.

## 7. Delivery Boundary

This package is local candidate evidence. It does not authorize push, PR,
merge, execution, or any subsequent construction route.
