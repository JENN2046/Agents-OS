# Phase 5D M0-D Accepted/Frozen Evidence Historical Durability Package v0.1

Date: 2026-07-25
Status: LOCAL_CANDIDATE
Owner: Jenn
Agent steward: Nobao

## 1. Purpose

This package preserves three already accepted and frozen Phase 5D M0-D
governance evidence units on a branch rooted at the exact post-PR-37 mainline
state. It is a historical durability projection only.

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
sha256: ebe4baa01deb8c1016051505c672a2a535d488a6cd6986bcc5d0192fd0c338b4
artifact_count: 58
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

1. all 58 manifest artifacts exist as regular files;
2. every artifact SHA-256 matches the durability manifest;
3. all three canonical manifests match their immutable decision bindings;
4. the selected freeze decisions still report their exact accepted/frozen
   result;
5. no R4/R5 path is present in the durability manifest;
6. `CURRENT_STATE.md` and all consumer default queue pointers remain based on
   the post-PR-37 mainline state;
7. Document Registry and targeted offline validators pass.

## 7. Delivery Boundary

This package is local candidate evidence. It does not authorize push, PR,
merge, execution, or any subsequent construction route.
