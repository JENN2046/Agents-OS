# AGENTS OS F8 R1 BLOCK and R2 Atomic Review Package Receipt v0.1

Date: 2026-07-19
Mode: Yellow Work Batch
Result: `PASS`
Owner: Jenn
Agent steward: Nobao

## Preserved R1 evidence

```yaml
R1_review: control-plane/registry/reviews/2026-07-19-yellow-agents-os-f8-r1-nobao-independent-review.yaml
R1_review_sha256: 4cd577695c9753bb9d89cfcc9d7a3f36e27158b5df54b5381048d222a5e99139
R1_attack_results_sha256: d31b3a8c45bc4bfe64aebd8ca2a6eca35b37723e424559fcfa9ad1f93e66311b
R1_review_result: BLOCK
R1_findings: 4_BLOCKER_2_MAJOR
R1_disposition_sha256: 0233cb3bd71fb7d65b8c5fc1568967e49a66977d776eb6d0f657de99697b217e
R1_subjects_unchanged: 4/4
R1_manifest_sha256: 920ea2bcbc65b9af41df8eb70ea42d1e20ef7cb4a74b58e2d06d5d984e17a482
```

## Fixed R2 review surface

```yaml
review_unit: F8_HOME_TO_ORCHESTRATOR_MINIMUM_INTERFACE_V0_1_R2_ATOMIC_BUNDLE
R1_subjects: 4
R2_subjects: 4
subjects_total: 8
authority_inputs: 28
author_evidence: 1
declared_inputs: 37
manifest: control-plane/registry/reports/2026-07-19-agents-os-f8-r2-atomic-independent-review-package-v0.1.manifest.yaml
manifest_sha256: b179557dfc7c74ab60d345933d5c5e4eebb9c9418c27091a35a19611be5e2a96
review_package: control-plane/registry/reports/2026-07-19-agents-os-f8-r2-atomic-independent-review-package-v0.1.md
review_package_sha256: cf0cce1df1fac01576ed75b4887d83e798b6b575823e6c49e9c8d296b10314cf
active_work_queue: control-plane/registry/reports/2026-07-19-agents-os-active-work-queue-v5.2.md
active_work_queue_sha256: 35d2b57a93812efbbcafc5932fedf82e66cf14616329ff9a0252d6625b2b8170
```

## Author validation

```yaml
manifest_hashes: 37/37_MATCH
fixed_commands: 5/5_PASS
R1_validator: PASS
R1_builder_byte_reproduction: PASS
R2_validator: PASS
R2_builder_byte_reproduction: PASS
R2_offline_whitespace: 4/4_PASS
R2_schema_profiles: 10/10
R2_upstream_assessments: 28/28
R2_handoff_cases: 25/25
R2_candidate_revisions: 2/2
R2_acknowledgement_cases: 9/9
inherited_mutations: 41/41_REJECTED
R2_target_regressions: 17/17_PASS
parser_probes: 3/3_REJECTED
validator_exceptions: 0
```

The author self-review is nonindependent evidence only. No independent R2
result has been created.

## Boundary

```yaml
F8_started: true
F8_accepted: false
F8_frozen: false
Phase_5A_started: false
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
database_change_authorized: false
private_raw_memory_access_authorized: false
sensing_or_recording_authorized: false
provider_or_effect_execution_authorized: false
Git_delivery_authorized: false
```

The fixtures contain synthetic nonauthority bytes only. No secret, credential,
token, cookie, provider raw response, `state-private/` content or private raw
Memory was read or included.
