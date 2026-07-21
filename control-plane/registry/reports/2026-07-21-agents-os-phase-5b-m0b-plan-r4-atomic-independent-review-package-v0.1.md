# AGENTS OS Phase 5B M0-B Plan R4 Atomic Independent Review Package v0.1

```yaml
review_unit: PHASE_5B_M0B_PLAN_BUILD_PROFILE_V0_1_R4_ATOMIC_BUNDLE
review_mode: FRESH_FULL_ATOMIC_HASH_BOUND_INDEPENDENT_REVIEW
atomic: true
partial_review: forbidden
subjects: 16
authority_inputs: 53
author_evidence: 18
declared_inputs: 87
precedence: [R4_explicit_replacements, R3_all_other_clauses, R2_all_other_clauses, R1_all_other_clauses]
```

Canonical manifest:

```text
control-plane/registry/reports/2026-07-21-agents-os-phase-5b-m0b-plan-r4-atomic-independent-review-package-v0.1.manifest.yaml
```

R4 closes only the three fixed R3 findings. The reviewer must independently
derive all six sealed F3 identity/authentication values, test candidate
PK/ref/history uniqueness without dictionary overwrite, and prove the supplied
FK list is exactly the normative ordered duplicate-free three-entry inventory.

The ten R3 favorable invalid paths must be fully re-signed and rejected by the
named R4 semantic code with the byte seal reported separately. Author validator
PASS and self-review cannot substitute for independent judgment.

```yaml
allowed_results: [PASS_NO_BLOCKER, BLOCK]
Phase_5B_plan_frozen: false
Phase_5B_implementation_started: false
implementation_authorized: false
Rust_JavaScript_NAPI_SQLite_or_VCPToolBox_change: false
runtime_database_provider_private_Memory_sensing_or_effect: false
```
