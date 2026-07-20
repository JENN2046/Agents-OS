# AGENTS OS Phase 5A M0-A Plan R6 Fresh Full Atomic Independent Review Package v0.1

Date: 2026-07-19
Owner: Jenn
Agent steward: Nobao

```yaml
review_unit: PHASE_5A_M0A_PLAN_BUILD_PROFILE_V0_1_R6_ATOMIC_BUNDLE
review_mode: fresh_full_atomic_hash_bound_independent_review
partial_review: forbidden
subjects: 42
workspace_authority_inputs: 156
author_evidence: 1
fixed_VCP_git_objects: 7
manifest_inputs: 206
manifest_sha256: 98a6f73bf96fdbd168169173c42a9a57eafe81151d27b88820534467dc4a2167
author_result: PASS_FOR_HASH_BOUND_INDEPENDENT_REVIEW
independent_result: NOT_RUN
```

## Review unit

R1–R6 form one atomic unit. Precedence is R6, R5, R4, R3, R2, R1. R1–R5
subjects and manifests must remain exact bytes. Author evidence is nonindependent
and must not be adopted as the review conclusion.

R6 is limited to the six R5 blockers:

1. full F5 authorization subject and exact replay identity binding;
2. F3 witness COMMIT byte/hash/tuple validation and READY writes;
3. inherited CommonJS export and N-API method consistency;
4. semantic rejection of authorization or runtime boundary expansion;
5. canonical fact same-revision relational immutability;
6. duplicate-key-rejecting YAML and JSON totality.

## Required reproduction

From the extracted package root without `.git`:

```text
python3 workspace/control-plane/registry/validate-phase5a-m0a-plan-r5-closure.py \
  workspace/control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-plan-r5-closure-witness-v0.1.json \
  workspace/control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-future-index-js-safe-wrapper-v0.1.js --self-test

python3 workspace/control-plane/registry/validate-phase5a-m0a-plan-r6-closure.py \
  workspace/control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-plan-r6-closure-witness-v0.1.json \
  workspace/control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-future-index-js-inherited-abi-wrapper-v0.1.js --self-test

python3 workspace/control-plane/registry/build-phase5a-m0a-plan-r6-closure-witness.py \
  /tmp/phase5a-r6-review-rebuilt.json
cmp /tmp/phase5a-r6-review-rebuilt.json \
  workspace/control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-plan-r6-closure-witness-v0.1.json
```

The independent reviewer must additionally construct coordinated, fully
recomputed synthetic cases. A rejection caused only by stale hashes or missing
reference propagation does not prove the target semantic.

## Author evidence summary, not acceptance

```yaml
effective_tables: 18/18
SQLite_cases: 13/13
JavaScript_AST_cases: 15/15
structured_input_cases: 7/7
total_fixed_cases: 35/35
self_test_mutations_rejected: 11/11
builder_byte_reproduction: PASS
database_file_occurrence_count: 0
terminal_outcome: NOT_EXECUTED
```

## Required disposition

Only `PASS_NO_BLOCKER` or `BLOCK` is allowed. `PASS_NO_BLOCKER` does not accept
or freeze the plan and does not authorize implementation. A separate Jenn
atomic plan-freeze decision is required after PASS, followed by another Jenn
implementation decision before any Rust, JavaScript, N-API or SQLite work.

