# AGENTS OS Active Work Queue v0.4

Date: 2026-07-16
Status: active
Owner: Jenn
Agent steward: Nobao
Supersedes: `control-plane/registry/reports/2026-07-16-agents-os-active-work-queue-v0.3.md`

## Purpose

This is the current machine-readable construction queue after F3 R1 author
closeout and independent-review package preparation. Queues v0.1-v0.3 remain
unchanged as historical evidence.

The active unit remains F3 contract closure. This queue does not accept or
freeze F3 and creates no implementation, runtime, database,
production-authentication, service, provider, credential, F4, release, deploy,
publication, or formal Memory authority.

## Current Facts

```text
F2_status=ACCEPTED_FROZEN
F3_started=true
F3_status=CONTRACT_CLOSURE_ACTIVE
F3_R1_subject_sha256=e439b3178984ac28ae584a961e2e0dc2248002592f0fb571e5e0db05d117a70e
F3_R1_author_review=PASS_FOR_HASH_BOUND_INDEPENDENT_REVIEW
F3_R1_review_manifest=control-plane/registry/reports/2026-07-16-agents-os-f3-r1-independent-review-package-v0.1.manifest.yaml
F3_R1_review_manifest_sha256=40b07f20be1bd3d25dee62cf2a54dd6a0d8d9246b6d7774f98632ed27c35a2a6
F3_R1_independent_review_package_ready=true
F3_R1_independent_review_result=NOT_CREATED
F3_acceptance_mode=ATOMIC_BUNDLE
F3_partial_acceptance=forbidden
F3_accepted=false
F3_frozen=false
F4_started=false
implementation_authorized=false
runtime_activation_authorized=false
production_authentication_authorized=false
database_change_authorized=false
service_start_authorized=false
provider_execution_authorized=false
credential_change_authorized=false
```

## NOW

### NOW-001: F3 R1 Fresh Hash-Bound Independent Review

An independent reviewer must start from the canonical manifest, recompute every
listed SHA-256, review the complete fixed R1 bytes, and return either
`PASS_NO_BLOCKER` or `BLOCK` under the package output contract. The author
self-review is lineage only and cannot substitute for independent judgment.

```text
requires_jenn_decision=false
reviewer_independence_required=true
author_may_self_attest_independence=false
partial_review=forbidden
execution_authorized=false
```

## NEXT

### NEXT-001: F3 Independent Review Finding Disposition

If the result is `BLOCK`, dispose every exact finding and create R2 only when
the fixed evidence requires it. A correction restarts the complete independent
review from zero.

### NEXT-002: F3 Jenn Atomic Freeze Decision Surface

If a valid fixed hash-bound result is `PASS_NO_BLOCKER`, prepare the exact
Jenn-only atomic accept/freeze surface. No automatic acceptance is permitted.

## LATER

```text
F4=TaskPermit_identity_bound_host_and_fence_effect_admission_after_F3_acceptance_and_separate_Jenn_start
implementation_profile=separate_Jenn_decision_after_required_foundation_contracts
```

## BLOCKED

```text
author_independence_claim=forbidden
F3_acceptance_or_freeze=blocked_until_valid_independent_review_and_Jenn_decision
F4_start=blocked_until_F3_gate_and_separate_Jenn_decision
Rust_or_JavaScript_implementation=not_authorized
database_creation_migration_or_live_access=not_authorized
Resident_runtime_or_service_start=not_authorized
production_authentication_crypto_keys_or_credentials=not_authorized
provider_executor_plugin_or_external_effect=not_authorized
public_API_or_MCP_expansion=not_authorized
commit_push_merge_release_deploy_publish_or_tag=not_authorized_by_review_package
formal_Memory_or_private_raw_memory_access=not_authorized
```

## CLOSED

```text
F1_goal_spec_success_criteria_plan_membership=accepted
F2_actor_identity_delegation_R1_through_R22=accepted_frozen
F3_explicit_start_gate=satisfied
F3_R1_author_surface=fixed
F3_R1_author_self_review=passed_for_independent_review
F3_R1_independent_review_package=fixed
active_work_queue_v0_1=superseded_historical_bytes_preserved
active_work_queue_v0_2=superseded_historical_bytes_preserved
active_work_queue_v0_3=superseded_historical_bytes_preserved
```
