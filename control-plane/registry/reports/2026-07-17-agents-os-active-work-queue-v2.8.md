# AGENTS OS Active Work Queue v2.8

Date: 2026-07-17
Status: superseded after Jenn-owned narrow R2 start decision
Owner: Jenn
Agent steward: Nobao
Supersedes: `control-plane/registry/reports/2026-07-17-agents-os-active-work-queue-v2.7.md`

## Purpose

Historical machine-readable queue after the fixed F6 R1 atomic review returned
`BLOCK` and before the narrow R2 start decision. Queues v0.1-v2.7 remain
byte-preserved historical evidence.

This queue records only the evidence-bound R1 disposition and the Jenn-owned
R2 start gate. It does not authorize R2 author construction by itself, F6
acceptance or freeze, F7, implementation, runtime, database, provider, service,
authentication, real Task/Run/Validation mutation, effect or Git delivery.

## Current Facts

```text
F6_started=true
F6_status=R1_BLOCK_NEEDS_NARROW_R2_START_DECISION
F6_R1_manifest_sha256=65b73b15dd0ad98c3263a8aa4932dbb13468ae6468de8213c44f3473e77f5e11
F6_R1_independent_review_sha256=a623f99adabc78ff5e2a43598e26107ad6c231964e82cba0f8ff66b138a7bae6
F6_R1_independent_review_result=BLOCK
F6_R1_findings=7_BLOCKER_2_MAJOR_1_MINOR
F6_R1_disposition_sha256=4932da948be632c5d8b4737aad6a11b007e63ce77bcb1db50c378aae987959a0
requires_R2=true
R2_truly_required=true
F6_acceptance_ready=false
F6_accepted=false
F6_frozen=false
F7_started=false
implementation_authorized=false
runtime_activation_authorized=false
production_authentication_authorized=false
database_change_authorized=false
service_start_authorized=false
provider_execution_authorized=false
real_Task_Run_Validation_Event_waiver_completion_mutation_authorized=false
Git_delivery_authorized=false
```

## NOW

### NOW-001: Jenn-Owned Narrow F6 R2 Start Decision

```text
decision_owner=Jenn
required_scope=five_proof_surfaces_mapping_all_ten_R1_findings
R1_subjects_and_manifest=immutable
partial_acceptance=forbidden
automatic_R2_start=false
```

## NEXT

```text
if_Jenn_starts_R2=create_new_R2_amendment_builder_fixture_validator
R2_review_unit=R1_four_subjects_plus_R2_four_subjects
fresh_full_atomic_hash_bound_independent_review=required
```

## BLOCKED

```text
edit_R1_subjects_manifest_or_self_review=forbidden
partial_F6_acceptance_or_freeze=forbidden
new_Validation_Task_or_waiver_semantics=forbidden
F1_F3_F5_frozen_subject_change=forbidden
F7_implementation_runtime_database_provider_service_effect=forbidden
real_Task_Run_Validation_Event_waiver_completion_mutation=forbidden
commit_push_PR_merge_release_deploy_publish_tag=not_authorized
```

## CLOSED

```text
F6_R1_independent_review=BLOCK_COMPLETE
F6_R1_literal_fixed_commands=PASS_2_OF_2
F6_R1_fixed_mutations=PASS_32_OF_32_REJECTED
F6_R1_additional_defect_probes=18_OF_18_INCORRECTLY_ACCEPTED
F6_R1_finding_disposition=10_OF_10_MAPPED_TO_FIVE_R2_PROOF_SURFACES
```
