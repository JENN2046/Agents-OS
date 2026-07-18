# AGENTS OS F7 R2 Atomic Freeze Closeout Receipt v0.1

Date: 2026-07-19  
Mode: Yellow Work Batch  
Result: `PASS`  
Owner: Jenn  
Agent steward: Nobao

## Authority consumed

Jenn explicitly confirmed execution of Section 6 A's complete Exact decision
text in the fixed F7 R2 Atomic Freeze Decision Package v0.1.

```yaml
decision_package:
  path: control-plane/registry/reports/2026-07-19-agents-os-f7-r2-atomic-freeze-decision-package-v0.1.md
  sha256: 6efd56f523b9dc1323a213a68ab0884cb1f83f967204afd6cbd13205dc1e3ea5
manifest:
  path: control-plane/registry/reports/2026-07-19-agents-os-f7-r2-atomic-independent-review-package-v0.1.manifest.yaml
  sha256: d2fc34cd8df70d1a960e373606f6c53468e6020b8a8087b551561ebf6a032d35
independent_review:
  path: control-plane/registry/reviews/2026-07-19-yellow-agents-os-f7-r2-codex-external-independent-review.yaml
  sha256: 79d84b9231490d61a93c88574d2e6be6ef25a128f407c9c9c81a63136fb44647
  result: PASS_NO_BLOCKER
  requires_R3: false
```

## Immutable decision

```text
control-plane/registry/decisions/2026-07-19-agents-os-f7-home-domain-minimum-semantics-r2-atomic-freeze-decision-v0.1.yaml
SHA-256 f16d527fa41aa3a4036206d2efb80236936438caac0c25005f80f12d8fea922a
```

The decision atomically accepts and freezes only the eight fixed F7 subjects
under R2 then R1 precedence. Partial acceptance is forbidden. Manifest,
self-review, independent reviews, decision package, dispositions, receipts and
queues are not acceptance subjects.

## Validation

```yaml
manifest_sha256: MATCH
manifest_input_hashes: 44/44_MATCH
accepted_subject_hashes: 8/8_MATCH
independent_review_sha256_bytes_and_result: MATCH
decision_package_sha256: MATCH
decision_record_parse_and_invariants: PASS
R1_R2_fixed_validators: 2/2_PASS
R1_R2_builder_byte_reproductions: 2/2_PASS
Document_Registry: PASS
Federated_Registry: PASS
Machine_Control_Chain_Dashboard_Workbench: PASS
default_queue_equals_explicit_v4_7: PASS
git_diff_check: PASS
```

## Boundary

```yaml
F7_status: ACCEPTED_FROZEN
F7_revisions_stopped: true
requires_R3: false
F8_started: false
real_Home_or_Memory_mutation_authorized: false
sensing_or_recording_authorized: false
private_raw_Memory_access_authorized: false
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
database_change_authorized: false
service_start_authorized: false
provider_or_effect_execution_authorized: false
commit_created: false
push_PR_or_merge_performed: false
```

No `state-private/` content, secret, credential, private raw Memory, raw log,
provider response, runtime source, database, service, sensing, recording or
external delivery surface was accessed or activated.
