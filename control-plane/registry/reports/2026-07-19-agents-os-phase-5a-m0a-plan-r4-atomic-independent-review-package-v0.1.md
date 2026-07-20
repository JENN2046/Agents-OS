# AGENTS OS Phase 5A M0-A Plan R4 Atomic Independent Review Package v0.1

Date: 2026-07-19  
Status: FIXED_FOR_FRESH_FULL_ATOMIC_INDEPENDENT_REVIEW  
Owner: Jenn  
Agent steward: Nobao

## Review unit

```yaml
review_unit: PHASE_5A_M0A_PLAN_BUILD_PROFILE_V0_1_R4_ATOMIC_BUNDLE
atomic: true
partial_review: forbidden
subjects: 25
inputs: 176
precedence:
  - R4_explicit_replacements
  - R3_all_other_clauses
  - R2_all_other_clauses
  - R1_all_other_clauses
```

Manifest:

```text
control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r4-atomic-independent-review-package-v0.1.manifest.yaml
SHA-256: 0803bd3e90a0652f1e0cc97b9a4168185df37cd9c76506746796e6096d3dbe58
```

## Required independent proof

The reviewer must independently verify every input and prove or refute:

1. F3 epoch genesis and restart are exact, while gap, fork, wrong prior
   incarnation and missing ownership Event cannot commit;
2. incarnation, epoch, `RECOVERING` lifecycle fact, pointer and Event have one
   exact all-or-zero transaction owner, and `READY` requires the later exact
   witness COMMIT observation;
3. F5 claim lease facts bind `OUTBOX_CLAIM_LEASE` and the exact intent;
4. arm request ID, fingerprint and canonical bytes equal the selected attempt;
5. receipt attempt/intent/claim and first-apply guard form one exact tuple;
6. stored-first Event and call-authorization counts are each exactly one,
   while exact replay additions are zero;
7. fixed `Plugin.js` bytes prove the actual
   `processToolCall(pluginSpecificArgs, directContext)` call;
8. a coordinated AST/dataflow attack cannot make `directContext`,
   `requestIp`, `sourceNode`, `signal` or auth context affect N-API, reducers,
   fingerprints, logs, receipts, errors or output;
9. no authority, implementation or runtime boundary expanded.

## Fixed commands

From the extracted package root without `.git`:

```bash
python3 workspace/control-plane/registry/validate-phase5a-m0a-plan-r4-closure.py \
  workspace/control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-plan-r4-closure-witness-v0.1.json \
  upstream/vcptoolbox/Plugin.js --self-test

python3 workspace/control-plane/registry/build-phase5a-m0a-plan-r4-closure-witness.py \
  /tmp/phase5a-r4-review-rebuilt.json

cmp /tmp/phase5a-r4-review-rebuilt.json \
  workspace/control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-plan-r4-closure-witness-v0.1.json
```

Author result:

```yaml
effective_tables: 18/18
R4_replacement_tables: 7/7
semantic_owner_replacements: 6/6
SQLite_in_memory_cases: 10/10
fixed_mutations_rejected: 11/11
fixed_Plugin_js_sha256: be15f76324b73400fe70052e6f07a0254b2a9c26393009ad1f026793fb36f5a2
database_file_occurrence_count: 0
terminal_outcome: NOT_EXECUTED
```

This is author evidence only. The reviewer must construct coordinated
fully-propagated SQL graphs and an independent JavaScript AST/dataflow probe.

## Result and stop

Only `PASS_NO_BLOCKER` or `BLOCK` is allowed. PASS does not accept or freeze
the plan. Jenn must decide plan freeze separately; even plan freeze does not
authorize implementation.

```yaml
implementation_authorized: false
dependency_installation_authorized: false
database_file_creation_authorized: false
VCPToolBox_change_or_start_authorized: false
plugin_enablement_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
provider_private_memory_sensing_or_real_effect_authorized: false
commit_push_merge_authorized: false
```
