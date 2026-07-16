# AGENTS OS F4 TaskPermit, Host Authentication, and Effect Admission v0.1 R5 Amendment Draft

Status: author-closed review subject; not accepted or frozen  
Date: 2026-07-16  
Base R1 SHA-256: `3378396108f090469984facb8ddcb238ae122be9cab71afe2f8c3bd1cd577db3`  
Base R2 SHA-256: `30cdbf0acb348d4c0c933f95bdcf51c7f3a6326ad678d8fca1f19faf4c85f705`  
Base R3 SHA-256: `4a65021d5c15640531aa59c3641f1ef1ab6dae86421a4ebfc4f6a3af25dd9939`  
Base R4 SHA-256: `7c6034e037cfe2ff5d31b4c5f47bd2e584536cf9b8c8dbdda5b706512a03e79b`

## 1. Scope and precedence

R5 closes `F4-R1-IR-B01`, `B02`, `B03`, the open part of `B04`, `B06`, and
`M02`. `B05` remains closed by R2/R3, `M03` remains closed by R4, and `M01`
remains a witness-evidence limitation rather than an authority rule.

Effective reading order is R5 explicit replacements, R4, R3, R2, then R1.
All twelve R1-R4 subject bytes and every prior review remain immutable. The
effective acceptance literal is
`F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R5_ATOMIC_BUNDLE`.

## 2. One prohibited boundary; no color-driven permission model

This section replaces every R1 rule where `GREEN`, `YELLOW`, `RED`, `P3a`, or
`P3b` decides issuance, admission, currentness, or handoff. Those labels may
remain only as non-authoritative audit metadata and MUST NOT appear in any
authority predicate.

```yaml
EffectAuthorizationRequirementV0_1R5:
  interface_version: agents-os.effect-authorization-requirement.v0.1-r5
  mode: NO_SEPARATE_JENN_AUTHORIZATION_REQUIRED | EXACT_CURRENT_JENN_AUTHORIZATION_REQUIRED | PROHIBITED_NON_ISSUABLE
  requirement_basis_ref: stable_ref
  requirement_basis_fingerprint: lowercase_sha256
  policy_bundle_revision: positive_safe_integer
  policy_bundle_fingerprint: lowercase_sha256
  prohibited_behavior_list_revision: positive_safe_integer
  prohibited_behavior_list_fingerprint: lowercase_sha256
  exact_effect_scope_fingerprint: lowercase_sha256
  Jenn_decision_ref: stable_ref | null
  Jenn_decision_fingerprint: lowercase_sha256 | null
  Jenn_actor_identity_ref: stable_ref | null
  issued_at_utc_ms: non_negative_safe_integer | null
  expires_at_utc_ms: positive_safe_integer | null
  revocation_event_sequence: non_negative_safe_integer | null
  currentness_result: NOT_APPLICABLE | CURRENT | REJECTED | INDETERMINATE
  canonical_fingerprint: lowercase_sha256
```

The canonical policy evaluator derives `mode` from the exact current policy,
the one current Prohibited Behavior List, and the exact effect scope. Callers,
prompts, colors, risk lanes, and implementation labels cannot select it.

- `NO_SEPARATE_JENN_AUTHORIZATION_REQUIRED` requires all Jenn fields null and
  currentness `NOT_APPLICABLE`.
- `EXACT_CURRENT_JENN_AUTHORIZATION_REQUIRED` requires every Jenn field,
  exact scope equality, trusted time before expiry, no later revocation, and
  currentness `CURRENT`.
- `PROHIBITED_NON_ISSUABLE` requires Jenn fields null and can never enter a
  permit, even if a purported Jenn decision exists.
- Missing or unreproducible policy/PBL/basis evidence is `INDETERMINATE` and
  issues no permit.

R5 replaces `JennAuthorizationBindingV0_1` in the permit with the exact
`EffectAuthorizationRequirementV0_1R5`. It replaces currentness/admission
checks named `Jenn_authorization*` with
`effect_authorization_requirement_current`. Any retained
`side_effect_audit_label` is excluded from authorization derivation and cannot
change a result.

## 3. F4 Host trust extends the F2 Host identity; it does not create one

R5 replaces R1 `HostIdentityRevisionV0_1` with this effect-trust extension:

```yaml
F4HostTrustRevisionV0_1R5:
  interface_version: agents-os.f4-host-trust-revision.v0.1-r5
  host_id: stable_ref
  host_trust_revision: positive_safe_integer
  expected_previous_host_trust_revision: positive_safe_integer | null
  previous_host_trust_ref: stable_ref | null
  previous_host_trust_fingerprint: lowercase_sha256 | null

  host_actor_id: stable_ref
  host_actor_identity_revision: positive_safe_integer
  host_actor_identity_ref: stable_ref
  host_actor_identity_fingerprint: lowercase_sha256
  host_actor_identity_assessment_ref: stable_ref
  host_actor_identity_assessment_fingerprint: lowercase_sha256

  host_process_principal_id: stable_ref
  host_process_principal_revision: positive_safe_integer
  host_process_principal_ref: stable_ref
  host_process_principal_fingerprint: lowercase_sha256
  host_process_principal_assessment_ref: stable_ref
  host_process_principal_assessment_fingerprint: lowercase_sha256

  host_process_binding_ref: stable_ref
  host_process_binding_revision: positive_safe_integer
  host_process_binding_fingerprint: lowercase_sha256
  host_process_binding_assessment_ref: stable_ref
  host_process_binding_assessment_fingerprint: lowercase_sha256

  provisioning_action_ref: stable_ref
  provisioning_action_fingerprint: lowercase_sha256
  provisioning_basis_ref: stable_ref
  provisioning_basis_fingerprint: lowercase_sha256
  transition_kind: CREATE | UPDATE | SUSPEND | RESUME | REVOKE | COMPROMISE | RETIRE
  transition_action_ref: stable_ref
  transition_action_fingerprint: lowercase_sha256
  transition_authority_basis_ref: stable_ref
  transition_authority_basis_fingerprint: lowercase_sha256

  authenticator_profile_ref: stable_ref
  authenticator_profile_revision: positive_safe_integer
  authenticator_profile_fingerprint: lowercase_sha256
  credential_binding_ref: low_disclosure_ref
  credential_binding_fingerprint: lowercase_sha256
  lifecycle_state: PRESTART | ACTIVE | SUSPENDED | REVOKED | COMPROMISED | RETIRED
  validity_start_utc_ms: non_negative_safe_integer
  validity_end_utc_ms: positive_safe_integer | null
  issued_event_sequence: non_negative_safe_integer
  canonical_fingerprint: lowercase_sha256
```

`host_id` MUST equal `host_actor_id`; the exact current F2 Actor class MUST be
`EXECUTION_HOST`, the exact Principal class MUST be `HOST_PROCESS`, and the
current F2 Binding MUST bind that Principal revision to that Actor revision.
All three assessments MUST be current and active at provisioning,
authentication, issuance, acceptance, and final handoff.

CREATE requires the accepted F2 provisioning path and absence of a Host-trust
head. Every later transition uses previous-plus-one CAS and an authenticated
transition action whose authority basis is valid for the exact target and
transition. A Host trust revision cannot attest, provision, or resume itself.
F2 suspension, revocation, compromise, retirement, expiry, principal loss, or
binding loss dominates F4 state and blocks authentication. F2 or F4 compromise
is terminal for that Actor lineage; recovery requires a new F2 EXECUTION_HOST
Actor identity and new Host trust lineage.

R5 extends `HostAuthenticationAssessmentV0_1` with the exact Actor, Principal,
Binding, and their current assessment refs/fingerprints. `AUTHENTICATED/MATCH`
requires all of them current in the same watermark as the F4 Host trust and
credential/profile checks.

## 4. Final handoff rechecks every permit-bound authority

R5 chooses complete final recheck, not reliance on asynchronous fence
propagation. It adds this input to `HostWorkStartDispositionFactV0_1`:

```yaml
FinalHandoffAuthorityAssessmentV0_1R5:
  interface_version: agents-os.final-handoff-authority-assessment.v0.1-r5
  permit_ref: stable_ref
  permit_fingerprint: lowercase_sha256
  task_authority_currentness_ref: stable_ref
  task_authority_currentness_fingerprint: lowercase_sha256
  actor_principal_binding_currentness_ref: stable_ref
  actor_principal_binding_currentness_fingerprint: lowercase_sha256
  responsibility_delegation_currentness_ref: stable_ref
  responsibility_delegation_currentness_fingerprint: lowercase_sha256
  resident_command_continuity_ref: stable_ref
  resident_command_continuity_fingerprint: lowercase_sha256
  Host_F2_trust_currentness_ref: stable_ref
  Host_F2_trust_currentness_fingerprint: lowercase_sha256
  policy_bundle_revision: positive_safe_integer
  policy_bundle_fingerprint: lowercase_sha256
  prohibited_behavior_list_revision: positive_safe_integer
  prohibited_behavior_list_fingerprint: lowercase_sha256
  effect_authorization_requirement_ref: stable_ref
  effect_authorization_requirement_fingerprint: lowercase_sha256
  trusted_time_utc_ms: non_negative_safe_integer
  watermark_event_sequence: non_negative_safe_integer
  result: CURRENT | REJECTED | INDETERMINATE
  reason: ALL_AUTHORITY_CURRENT | AUTHORITY_STALE | AUTHORITY_UNAVAILABLE | INTEGRITY_FAILURE
  assessment_fingerprint: lowercase_sha256
```

The Rust canonical writer re-reads every exact bound F1 Task, F2 Actor,
Principal, Binding, responsibility and delegation, F3 Resident/Command,
policy, PBL, effect-authorization requirement, F2/F4 Host trust, time, and all
three fences at one serializable watermark immediately before committing the
disposition/handoff. A committed source revocation is therefore observed even
when a propagation projection has not yet advanced a fence.

R5 adds `final_handoff_authority_current` to the R4 eleven normalized start
rechecks. `REJECTED` maps to `NOT_STARTED / AUTHORITY_STALE`;
`INDETERMINATE` maps to `INDETERMINATE / OBSERVATION_UNAVAILABLE` when no
negative exists. The rejected precedence is:

```text
INTEGRITY_FAILURE
AUTHORITY_STALE
HOST_UNAUTHENTICATED
FENCED
EPOCH_STALE
EXPIRED
SECRET_HANDLE_STALE
ATTESTATION_STALE
HUMAN_PRESENCE_STALE
```

This replaces only R4's start reason enum and precedence. Its no-fact
acceptance-resolution boundary remains unchanged.

## 5. Non-bypassable F4/F5 physical-effect seam

F4 freezes these requirements on every future F5 contract and implementation
without starting F5:

```text
immediately before the first physical file/process/network/device/provider/UI effect
  -> atomically claim the exact handoff once by invocation identity
  -> require trusted time before start_authority_expires_at_utc_ms
  -> re-read the complete Section 4 authority set at one current watermark
  -> require current Task/Host/effect fences and no domain quarantine
  -> require exact Host, execution epoch, secret handles, attestation, and presence
  -> only then cross the physical boundary
```

Claim replay with identical terminal accounting returns that accounting; a
second physical claim, changed bytes, stale/expired/revoked evidence,
quarantine, unknown currentness, or an unprovable claim outcome is
`NOT_EXECUTABLE` and MUST NOT call a provider, process, filesystem, network,
device, or UI actuator. `NOT_EXECUTABLE` is a pre-effect gate result, not proof
of `NOT_EXECUTED`; only future positive terminal accounting may prove the
latter. This seam grants F5 no new authority and cannot widen the handoff.

## 6. Capability and resource authority source closure

R5 replaces the supporting grant schemas with:

```yaml
CapabilityGrantV0_1R5:
  capability_definition_ref: stable_ref
  capability_definition_fingerprint: lowercase_sha256
  capability_revision: positive_safe_integer
  operation_registry_revision: positive_safe_integer
  operation_registry_fingerprint: lowercase_sha256
  operation_set: sorted_unique_closed_strings
  constraint_fingerprint: lowercase_sha256
  source_authority_refs: sorted_unique_stable_refs
  source_authority_set_fingerprint: lowercase_sha256
  derived_subset_proof_ref: stable_ref
  derived_subset_proof_fingerprint: lowercase_sha256
  canonical_fingerprint: lowercase_sha256

ResourceGrantV0_1R5:
  resource_definition_ref: stable_ref
  resource_definition_fingerprint: lowercase_sha256
  resource_kind: closed_R1_resource_kind
  resource_ref: low_disclosure_ref
  resource_subject_fingerprint: lowercase_sha256
  operation_registry_revision: positive_safe_integer
  operation_registry_fingerprint: lowercase_sha256
  operation_set: sorted_unique_closed_strings
  selector_constraint_fingerprint: lowercase_sha256
  source_scope_refs: sorted_unique_stable_refs
  source_scope_set_fingerprint: lowercase_sha256
  containment_assessment_ref: stable_ref
  containment_assessment_fingerprint: lowercase_sha256
  canonical_fingerprint: lowercase_sha256
```

Definitions and the operation registry MUST be current accepted owner-domain
subjects. Every operation is an exact member of that definition's vocabulary.
Source authority is the exact intersection of current F1 Task scope, F2
responsibility/delegation containment, F3 Command definition, policy/PBL, and
exact Jenn decision when applicable. Missing, stale, wildcard, ambient,
unregistered, or unprovable containment issues no permit.

## 7. One invocation in v0.1

R5 replaces `TaskPermitV0_1.max_invocations` with `literal:1` and requires
`PermitInvocationIdentityV0_1.invocation_ordinal = 1`. The exact external
idempotency identity is the immutable permit/effect-intent `idempotency_key`
bound into that sole invocation and handoff. Multi-invocation permits are not
representable in v0.1 and require a future separately reviewed version.

## 8. Evidence, invariants, and next gate

R5 adds these independently countable invariants:

1. Colors and P0-P3 labels never select an authorization result.
2. One current policy/PBL-derived requirement has exactly one legal mode.
3. F4 Host trust has exactly one current F2 EXECUTION_HOST/HOST_PROCESS/Binding lineage.
4. No Host lifecycle transition is self-issued or bypasses CAS/typed authority.
5. Final handoff rechecks every permit-bound authority at one watermark.
6. A committed authority loss blocks handoff without waiting for fence propagation.
7. Physical start requires a one-time claim and a fresh complete currentness check.
8. Stale, unknown, quarantined, or conflicting physical-boundary evidence calls no effect.
9. Every capability/resource operation has a current definition and exact source containment proof.
10. Every v0.1 permit and invocation is single-use.

The focused R5 fixture and validator are synthetic, offline, and zero-effect.
They are constructive evidence only and do not replace fresh semantic review.
The indivisible review unit is all fifteen R1-R5 subjects. The corrected
offline review package MUST include every manifest-bound input, including all
thirteen authority inputs. Partial acceptance is forbidden; only Jenn may
later accept and freeze the complete bundle.

Nothing here authorizes F5/F6, implementation, Rust, N-API, database, runtime,
Resident/Host/service startup, production authentication, credentials, keys,
provider calls, physical effects, commit, push, merge, release, or deploy.
