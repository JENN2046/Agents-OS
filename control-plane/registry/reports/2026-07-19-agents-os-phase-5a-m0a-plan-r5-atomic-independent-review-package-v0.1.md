# AGENTS OS Phase 5A M0-A Plan R5 Atomic Independent Review Package v0.1

Date: 2026-07-19  
Status: FIXED_FOR_FRESH_FULL_ATOMIC_INDEPENDENT_REVIEW  
Owner: Jenn  
Agent steward: Nobao

## Review unit

```yaml
review_unit: PHASE_5A_M0A_PLAN_BUILD_PROFILE_V0_1_R5_ATOMIC_BUNDLE
atomic: true
partial_review: forbidden
subjects: 33
workspace_authority_inputs: 149
author_evidence: 1
fixed_VCP_git_objects: 7
inputs: 190
precedence:
  - R5_explicit_replacements
  - R4_all_other_clauses
  - R3_all_other_clauses
  - R2_all_other_clauses
  - R1_all_other_clauses
```

Manifest:

```text
control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r5-atomic-independent-review-package-v0.1.manifest.yaml
SHA-256: e26d5e1fa35a6bb69ae26747580e066d58eed5ab9a55371ecce35a991c337fa3
```

## Required independent proof

The reviewer must independently verify every input and prove or refute:

1. F3 incarnation, epoch, `RECOVERING` fact and pointer consume the same exact
   ownership Event ID/kind/aggregate/revision/fingerprint tuple;
2. `READY` resolves the exact current `F3_WITNESS_COMMIT`, checks its subject
   and Event ordering and rechecks the exact epoch/incarnation/Event tuple;
3. reuse of any historical incarnation is impossible, including epoch 1 at epoch 3;
4. F5 stored-first Event is the exact deterministic arm Event and sequence;
5. F5 call authorization binds exact kind, intent, attempt, revision, ref and fingerprint;
6. exact replay returns the stored identities and counts while adding zero;
7. the closed JavaScript parser builds the declared AST from exact source bytes;
8. second parameters, `arguments`, aliases, closures, spreads, computed
   properties, helper calls and unsupported syntax all fail closed;
9. the proof is executable and not a string search or caller-supplied result;
10. no authority, implementation, database or runtime boundary expanded.

## Fixed commands

From the extracted package root without `.git`:

```bash
python3 workspace/control-plane/registry/validate-phase5a-m0a-plan-r4-closure.py \
  workspace/control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-plan-r4-closure-witness-v0.1.json \
  upstream/vcptoolbox/Plugin.js --self-test

python3 workspace/control-plane/registry/validate-phase5a-m0a-plan-r5-closure.py \
  workspace/control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-plan-r5-closure-witness-v0.1.json \
  workspace/control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-future-index-js-safe-wrapper-v0.1.js \
  --self-test

python3 workspace/control-plane/registry/build-phase5a-m0a-plan-r5-closure-witness.py \
  /tmp/phase5a-r5-review-rebuilt.json

cmp /tmp/phase5a-r5-review-rebuilt.json \
  workspace/control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-plan-r5-closure-witness-v0.1.json
```

Author result:

```yaml
effective_tables: 18/18
R5_replacement_tables: 4/4
semantic_owner_replacements: 2/2
SQLite_in_memory_cases: 8/8
JavaScript_AST_dataflow_cases: 13/13
fixed_cases: 21/21
fixed_mutations_rejected: 7/7
database_file_occurrence_count: 0
terminal_outcome: NOT_EXECUTED
```

This is author evidence only. The reviewer must construct coordinated,
fully-propagated persistence variants and independently inspect or replace the
closed parser/dataflow proof.

## Result and stop

Only `PASS_NO_BLOCKER` or `BLOCK` is allowed. PASS does not accept or freeze
the plan. Jenn must decide plan freeze separately; plan freeze still does not
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
