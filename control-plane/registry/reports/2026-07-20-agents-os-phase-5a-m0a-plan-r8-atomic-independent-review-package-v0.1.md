# AGENTS OS Phase 5A M0-A Plan R8 Fresh Full Atomic Independent Review Package v0.1

Date: 2026-07-20
Owner: Jenn
Agent steward: Nobao

```yaml
review_unit: PHASE_5A_M0A_PLAN_BUILD_PROFILE_V0_1_R8_ATOMIC_BUNDLE
review_mode: fresh_full_atomic_hash_bound_independent_review
partial_review: forbidden
subjects: 55
workspace_authority_inputs: 171
author_evidence: 1
fixed_VCP_git_objects: 7
manifest_inputs: 234
manifest_sha256: f6b00bb0a19bb464122d44839e4f8987b0a68aea0794d0a36e9e29bec1de96b3
author_result: PASS_FOR_HASH_BOUND_INDEPENDENT_REVIEW
independent_result: NOT_RUN
```

## Review unit

R1–R8 form one atomic unit. Precedence is R8 through R1. R1–R7 subjects and
manifests must remain exact bytes. Author evidence is nonindependent and must
not be adopted as the review conclusion.

R8 is limited to the two R7 blockers:

1. exact closure of every effective key through whole-source commitments and a
   complete recursive key-path inventory, without suffix heuristics;
2. exact binding of the RECOVERING revision 1 fact and current pointer to the
   inherited ownership Event sequence before READY revision 2 commits.

## Required reproduction

From the extracted package root without `.git`:

```text
python3 workspace/control-plane/registry/validate-phase5a-m0a-plan-r5-closure.py workspace/control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-plan-r5-closure-witness-v0.1.json workspace/control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-future-index-js-safe-wrapper-v0.1.js --self-test

python3 workspace/control-plane/registry/validate-phase5a-m0a-plan-r6-closure.py workspace/control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-plan-r6-closure-witness-v0.1.json workspace/control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-future-index-js-inherited-abi-wrapper-v0.1.js --self-test

python3 workspace/control-plane/registry/validate-phase5a-m0a-plan-r7-closure.py workspace/control-plane/registry/examples/2026-07-20-agents-os-phase-5a-m0a-plan-r7-closure-witness-v0.1.json --self-test

python3 workspace/control-plane/registry/validate-phase5a-m0a-plan-r8-closure.py workspace/control-plane/registry/examples/2026-07-20-agents-os-phase-5a-m0a-plan-r8-closure-witness-v0.1.json --self-test

python3 workspace/control-plane/registry/build-phase5a-m0a-plan-r6-closure-witness.py /tmp/phase5a-r6-review-rebuilt.json
cmp /tmp/phase5a-r6-review-rebuilt.json workspace/control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-plan-r6-closure-witness-v0.1.json

python3 workspace/control-plane/registry/build-phase5a-m0a-plan-r7-closure-witness.py /tmp/phase5a-r7-review-rebuilt.json
cmp /tmp/phase5a-r7-review-rebuilt.json workspace/control-plane/registry/examples/2026-07-20-agents-os-phase-5a-m0a-plan-r7-closure-witness-v0.1.json

python3 workspace/control-plane/registry/build-phase5a-m0a-plan-r8-closure-witness.py /tmp/phase5a-r8-review-rebuilt.json
cmp /tmp/phase5a-r8-review-rebuilt.json workspace/control-plane/registry/examples/2026-07-20-agents-os-phase-5a-m0a-plan-r8-closure-witness-v0.1.json
```

## Independent attack requirements

The reviewer must independently perform fully propagated cases, including:

1. add `implementation_frozen: true` to any effective source, rebuild the
   complete key inventory and witness, and require target-semantic rejection;
2. add a neutral unknown key that matches no boundary suffix;
3. remove or rename an existing key and rebuild all dependent evidence;
4. change an existing value without changing its key path;
5. modify, replace or reorder the sealed source commitments and source aliases;
6. use a RECOVERING fact and pointer both created or updated by Event sequence
   2 while ownership Event sequence remains 1;
7. independently offset only the RECOVERING fact sequence or only the pointer
   sequence;
8. start with the valid sequence-1 prestate and confirm READY is revision 2
   with the exact RECOVERING predecessor;
9. remove or stale the lifecycle pointer, substitute predecessor ref or
   fingerprint, or use noncanonical RECOVERING bytes;
10. fail after READY Event and fact creation but before pointer commit and prove
    all writes roll back;
11. mutate any R1–R7 subject or manifest and confirm immutable-lineage
    rejection.

Every coordinated mutation must propagate all editable dependent commitments.
Rejection must come from the target closed-key/source-seal semantics, exact
ownership-Event semantics or an immutable fixed input—not from a stale row,
forgotten hash, unresolved reference or probe exception.

## Required independent result

The result must be exactly one of:

```yaml
result: PASS_NO_BLOCKER | BLOCK
requires_R9: true | false
findings:
  blocker: integer
  major: integer
  minor: integer
favorable_invalid_path_count: integer
legal_input_over_rejection_count: integer
```

`PASS_NO_BLOCKER` is allowed only after all 234 inputs are fully read and
hash-matched, all nine fixed command rows are reproduced, the complete ZIP is
checked, and fresh coordinated attacks find no favorable invalid path or legal
input over-rejection.

## Boundary

`PASS_NO_BLOCKER` would close only this plan review gate. It does not accept or
freeze the plan and cannot start implementation. No Rust, JavaScript, N-API,
SQLite database file, dependency installation, VCPToolBox change/start, plugin
enablement, runtime, production authentication, provider call, private Memory,
sensing or real effect is authorized.
