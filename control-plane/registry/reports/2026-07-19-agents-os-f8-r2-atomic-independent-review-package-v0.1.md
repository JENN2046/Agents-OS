# AGENTS OS F8 R2 Atomic Independent Review Package v0.1

Date: 2026-07-19
Owner: Jenn
Review unit: `F8_HOME_TO_ORCHESTRATOR_MINIMUM_INTERFACE_V0_1_R2_ATOMIC_BUNDLE`
Status: `FIXED_FOR_FRESH_FULL_ATOMIC_HASH_BOUND_INDEPENDENT_REVIEW`

## Canonical manifest

```text
control-plane/registry/reports/2026-07-19-agents-os-f8-r2-atomic-independent-review-package-v0.1.manifest.yaml
SHA-256: b179557dfc7c74ab60d345933d5c5e4eebb9c9418c27091a35a19611be5e2a96
```

```yaml
R1_subjects_immutable: 4
R2_subjects_new: 4
subjects_total: 8
authority_inputs: 28
author_evidence: 1
declared_total: 37
partial_review: forbidden
```

## Review request

Perform a fresh full atomic hash-bound independent review from the exact fixed
bytes. Do not use either author self-review as a conclusion. Verify all 37
hashes, fully read all eight subjects and 28 authority inputs, and run all five
manifest commands in both the workspace or the offline archive form selected
by each command.

The central question is:

> After R2, can any fully re-signed graph reuse, rewrite, substitute or
> mis-contextualize owner evidence and still obtain a favorable F8 handoff or
> acknowledgement, or pass a schema-invalid object by relying on fixture
> anchors rather than target-schema validation?

## Required independent attacks

At minimum independently reproduce and extend:

1. Change an assessment result and current-head marker at the same revision,
   recompute its row fingerprint, retain the old consumer fingerprint, and try
   to obtain `CANDIDATE_FORMED`.
2. Change the same assessment and synchronously change the consumer fingerprint
   but leave the candidate assessment-set commitment stale.
3. Change consumer, assessment and candidate assessment-set together and
   confirm F8 still resolves the row from the owner assessment source rather
   than accepting a caller result label.
4. Change an F3 outcome subject revision, context or Event watermark, update
   its row fingerprint and acknowledgement commitment, and retain a favorable
   committed claim.
5. Change `created_event_ref` or any other stable ref to an integer, boolean,
   empty string or null, fully re-sign all dependents, disable fixture anchors,
   and require a target-schema error.
6. Mutate unknown fields, enums, nullable tuples, safe integers, reason/result
   combinations, predecessor fields and occurrence counts with anchors
   disabled.
7. Reorder `required_intake_results` to the historical R1 builder order and
   fully re-sign the section and root.
8. Remove either accepted architecture input from the manifest.
9. Execute the five fixed commands from a plain extracted ZIP with no `.git`
   directory.

Every coordinated probe must propagate the dependent fingerprints it is meant
to preserve. Report whether rejection came from the intended exact-fingerprint,
currentness, acknowledgement or schema rule rather than a stale hash, canonical
fixture anchor or exception.

## Fixed author results

```yaml
R1_validator: PASS
R1_builder_byte_reproduction: PASS
R2_validator: PASS
R2_builder_byte_reproduction: PASS
R2_offline_whitespace_check: 4/4_PASS
R2_schema_profiles: 10/10
R2_upstream_assessments: 28/28
R2_handoff_cases: 25/25
R2_candidate_revisions: 2/2
R2_acknowledgement_cases: 9/9
R1_inherited_mutations: 41/41_REJECTED
R2_target_regressions: 17/17_PASS
parser_probes: 3/3_REJECTED
validator_exceptions: 0
real_command_count: 0
provider_call_count: 0
external_effect_count: 0
terminal_outcome: NOT_EXECUTED
```

These are author claims only.

## Six-finding closure claim

```yaml
F8-R1-B01: canonical_order_fixed
F8-R1-B02: exact_assessment_fingerprint_and_set_binding_added
F8-R1-B03: exact_F3_ack_subject_revision_context_and_watermark_added
F8-R1-B04: schema_totality_independent_of_fixture_anchors_added
F8-R1-M01: two_architecture_inputs_added
F8-R1-M02: Git_independent_offline_whitespace_command_added
```

## Critical boundary

F8 still forms only a synthetic, nonauthoritative and runtime-unusable handoff
candidate. No R2 object is permission, authentication, a Task, a committed F3
Command or effect authority. F3 remains the sole Command authentication,
intake, commit, rejection and replay authority.

## Allowed result and governance

Allowed results are exactly `PASS_NO_BLOCKER` or `BLOCK`. Neither result by
itself accepts or freezes F8.

```yaml
F8_started: true
F8_accepted: false
F8_frozen: false
Phase_5A_started: false
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
private_raw_memory_access_authorized: false
sensing_or_recording_authorized: false
provider_or_effect_execution_authorized: false
```
