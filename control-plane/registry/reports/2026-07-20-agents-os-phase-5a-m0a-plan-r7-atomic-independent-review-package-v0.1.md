# AGENTS OS Phase 5A M0-A Plan R7 Fresh Full Atomic Independent Review Package v0.1

Date: 2026-07-20
Owner: Jenn
Agent steward: Nobao

```yaml
review_unit: PHASE_5A_M0A_PLAN_BUILD_PROFILE_V0_1_R7_ATOMIC_BUNDLE
review_mode: fresh_full_atomic_hash_bound_independent_review
partial_review: forbidden
subjects: 49
workspace_authority_inputs: 163
author_evidence: 1
fixed_VCP_git_objects: 7
manifest_inputs: 220
manifest_sha256: d929a86317ecd2d9140645f1c1c8dd267cb982acfda3aa2a7830415a5917e299
author_result: PASS_FOR_HASH_BOUND_INDEPENDENT_REVIEW
independent_result: NOT_RUN
```

## Review unit

R1–R7 form one atomic unit. Precedence is R7 through R1. R1–R6 subjects and
manifests must remain exact bytes. Author evidence is nonindependent and must
not be adopted as the review conclusion.

R7 is limited to the two R6 blockers:

1. complete, recursively derived semantic enforcement of every effective
   plan-only boundary field;
2. a real immutable `RECOVERING revision 1` to `READY revision 2` transaction
   with exact predecessor, pointer CAS and all-or-zero rollback evidence.

## Required reproduction

From the extracted package root without `.git`:

```text
python3 workspace/control-plane/registry/validate-phase5a-m0a-plan-r5-closure.py workspace/control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-plan-r5-closure-witness-v0.1.json workspace/control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-future-index-js-safe-wrapper-v0.1.js --self-test

python3 workspace/control-plane/registry/validate-phase5a-m0a-plan-r6-closure.py workspace/control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-plan-r6-closure-witness-v0.1.json workspace/control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-future-index-js-inherited-abi-wrapper-v0.1.js --self-test

python3 workspace/control-plane/registry/validate-phase5a-m0a-plan-r7-closure.py workspace/control-plane/registry/examples/2026-07-20-agents-os-phase-5a-m0a-plan-r7-closure-witness-v0.1.json --self-test

python3 workspace/control-plane/registry/build-phase5a-m0a-plan-r6-closure-witness.py /tmp/phase5a-r6-rebuilt.json
cmp /tmp/phase5a-r6-rebuilt.json workspace/control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-plan-r6-closure-witness-v0.1.json

python3 workspace/control-plane/registry/build-phase5a-m0a-plan-r7-closure-witness.py /tmp/phase5a-r7-rebuilt.json
cmp /tmp/phase5a-r7-rebuilt.json workspace/control-plane/registry/examples/2026-07-20-agents-os-phase-5a-m0a-plan-r7-closure-witness-v0.1.json
```

## Independent attack requirements

The reviewer must independently perform fully propagated cases, including:

1. change each discovered boundary value while rebuilding profile and witness
   hashes;
2. remove, add, rename or change the type of a boundary field;
3. change `materialization_ABI.governance.implementation_authorized` to true
   and rebuild every dependent commitment;
4. start with a valid RECOVERING revision 1 fact and pointer, then verify READY
   is revision 2 rather than revision 1;
5. substitute the RECOVERING predecessor ref or fingerprint;
6. remove or stale the lifecycle pointer;
7. fail after Event and fact creation but before pointer commit and prove all
   three writes roll back;
8. attempt direct READY revision 1 from empty lifecycle history;
9. mutate R1–R6 bytes or manifests and confirm immutable-lineage rejection.

Rejections must come from the target semantic or immutable fixed input, not
from an unpropagated hash, stale dependent reference or probe exception.

## Boundary

`PASS_NO_BLOCKER` would close only this plan review gate. It does not accept or
freeze the plan and cannot start implementation. No Rust, JavaScript, N-API,
SQLite database file, dependency installation, VCPToolBox change/start, plugin
enablement, runtime, production authentication, provider call, private Memory,
sensing or real effect is authorized.
