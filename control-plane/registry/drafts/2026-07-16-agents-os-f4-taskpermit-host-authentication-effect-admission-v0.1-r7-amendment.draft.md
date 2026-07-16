# AGENTS OS F4 TaskPermit, Host Authentication, and Effect Admission v0.1 R7 Amendment Draft

Status: author-closed review subject; not accepted or frozen  
Date: 2026-07-16  
Base R6 SHA-256: `09af4b475e6ef66c0c5faa7ec60179cf0f6a0e111f96d9d1d2ef810311af1be5`  
Blocking R6 review SHA-256: `c2a4b785f1cb49b6f503bc270a72f617a5878917b0f998d5874dcadf72cb6c12`

## 1. Scope and precedence

R7 closes only `F4-R6-FULL-ATOMIC-IR-B01` through `B04`. Effective order is
R7, R6, R5, R4, R3, R2, R1. All eighteen prior subjects remain immutable. The
effective literal is
`F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R7_ATOMIC_BUNDLE`.

## 2. Total authorization reducer

R7 replaces the R6 rejected rows with one negative-over-unavailable reducer.
After exact policy/PBL/basis mode derivation:

```text
reproducible canonical/input integrity conflict
  -> NO_REQUIREMENT_OBJECT / MODE_INPUT_INTEGRITY_CONFLICT

mode input unavailable before a mode or any negative can be proved
  -> NO_REQUIREMENT_OBJECT / MODE_INPUT_UNAVAILABLE

derived NO_SEPARATE
  -> requirement / NOT_APPLICABLE / NO_SEPARATE_REQUIRED

derived PROHIBITED
  -> requirement / REJECTED / PROHIBITED

derived EXACT_JENN:
  any proven negative -> requirement / REJECTED / first fixed negative
  else any required decision evidence unavailable -> NO_REQUIREMENT_OBJECT / MODE_INPUT_UNAVAILABLE
  else all required predicates pass -> requirement / CURRENT / JENN_DECISION_CURRENT
```

The sole exact-Jenn rejected precedence is:

```text
JENN_DECISION_REVOKED
JENN_SCOPE_MISMATCH
JENN_DECISION_EXPIRED
JENN_DECISION_MISSING
```

A proven negative dominates every concurrent unavailable predicate. Missing is
legal only when a complete canonical decision index reproducibly proves no
decision; it is mutually exclusive with every present-decision predicate.

Exact presence matrix for the seven Jenn fields
`Jenn_decision_ref`, `Jenn_decision_fingerprint`, `Jenn_actor_identity_ref`,
`issued_at_utc_ms`, `expires_at_utc_ms`, `revocation_event_sequence`, and
`exact_Jenn_scope_fingerprint`:

| Row | All seven fields |
|---|---|
| NO_SEPARATE / NOT_APPLICABLE / NO_SEPARATE_REQUIRED | null |
| PROHIBITED / REJECTED / PROHIBITED | null |
| EXACT / REJECTED / JENN_DECISION_MISSING | null |
| EXACT present current, revoked, scope-mismatched, or expired | non-null |

For a present decision, `revocation_event_sequence` is the exact current
revocation-head sequence (zero is allowed when no revocation fact precedes the
watermark), never an optional “as observed” value. Every other tuple rejects.

## 3. Total F4-only effect-trust eligibility reducer

R7 adds `CURRENT_F2_ACTOR_NOT_ACTIVE` to the R6 reason enum and freezes these
normalized observations: exact-input integrity, F2 compromise history, F4
compromise history, current F2 Actor state, F2-history availability, F4-history
availability, and current-input availability.

The total order is:

```text
1. reproducible integrity conflict
   -> INELIGIBLE / INTEGRITY_FAILURE
2. F2 compromise history present
   -> INELIGIBLE / F2_COMPROMISE_HISTORY_PRESENT
3. F4 compromise history present
   -> INELIGIBLE / F4_COMPROMISE_HISTORY_PRESENT
4. current F2 Actor reproducibly not ACTIVE
   -> INELIGIBLE / CURRENT_F2_ACTOR_NOT_ACTIVE
5. either history input unavailable, with no preceding negative
   -> INDETERMINATE / HISTORY_UNAVAILABLE
6. current F2 input unavailable, with no preceding negative
   -> INDETERMINATE / CURRENT_F2_INPUT_UNAVAILABLE
7. all inputs current, both histories reproducibly absent
   -> ELIGIBLE / NEVER_COMPROMISED_AND_ALL_CURRENT
```

Thus integrity and proven compromise history dominate unavailable evidence;
F2 history precedes F4 history when both exist. This reducer never changes the
F2 Actor lifecycle or its RECOVER result.

## 4. Disposition fingerprint correction

For `HostWorkStartDispositionFactV0_1R6`, the list after the domain separator
contains exactly 28 values. Value 1 is the literal
`agents-os.host-work-start-disposition-fact.v0.1-r6`; value 2 is
`observation_id`; values 3-28 follow the R6 printed schema through
`host_observation_attestation_fingerprint`. `fact_fingerprint` is excluded.
Any fixture or implementation with 27 values rejects. The R7 validator prints
and asserts `disposition_preceding_field_count = 28` and the exact ordered field
name list before accepting its fingerprint.

## 5. Canonical complete-effective reconstruction and output

R7 replaces R6 Section 6. The full fixture begins with one base-integrity node
containing the immutable R1 fixture file digest, canonical digest, ordered 14
base-node digests, and R1 validator result. It does not embed or emit any R1
effective object. Every later node has the base-integrity node as a direct
dependency in addition to its semantic predecessors.

The reconstruction algorithm is closed:

1. Parse and verify the exact immutable R1 witness only as source evidence.
2. For each effective object below, select only fields in its effective R7
   field list; copy an unchanged R1 value only when that exact field survives.
3. Insert every R5-R7 replacement field; no implicit merge or unknown field is
   allowed.
4. Recompute nested and outer identities/fingerprints from the resulting full
   object in printed field order.
5. Emit the complete object, not a base hash plus delta.
6. Recursively reject these removed fields anywhere outside the base-integrity
   node: `Jenn_authorization_binding`,
   `Jenn_authorization_binding_fingerprint`, `Jenn_authorization_current`,
   `side_effect_class`, `source_authority_refs`, `source_scope_refs`,
   `ACCEPTANCE_MISSING`, and the R1 Host-identity-only field set.

The validator emits complete objects for all of:

```text
EffectAuthorizationRequirementResolutionV0_1R7
EffectAuthorizationRequirementV0_1R7
F2ExecutionHostPrincipalBindingExtensionV0_1R7
F4HostEffectTrustEligibilityAssessmentV0_1R7
F4HostTrustRevisionV0_1R7
HostAuthenticationAssessmentV0_1R7
CapabilityGrantV0_1R7
ResourceGrantV0_1R7
EffectIntentBindingV0_1R7
TaskPermitV0_1R7 plus TaskPermitIssuanceFact
TaskPermitCurrentnessAssessmentV0_1R7
HostLocalAdmissionRequest and HostLocalAdmissionDecision
FinalHandoffAuthorityAssessmentV0_1R7
HostWorkAcceptanceFact plus activation transition
HostWorkStartDispositionFactV0_1R6 effective under R7
F4AcceptedEffectHandoffV0_1R7
F5BoundaryZeroEffectStubV0_1R7
```

The exact effective `TaskPermitV0_1R7` is the R1 field order with these
explicit replacements: contract literal R7; `host_identity_ref/fingerprint`
become `host_trust_ref/fingerprint`; capability/resource arrays use R7 grants;
the effect intent uses `side_effect_audit_label`; `Jenn_authorization_binding`
becomes `effect_authorization_requirement`; and `max_invocations` is literal
1. Every other R1 permit field survives in its prior relative order.

The exact effective currentness object replaces `host_identity_current` with
`host_trust_current` and `Jenn_authorization_current` with
`effect_authorization_requirement_current`; every other R2 effective check
survives. Admission uses the same renamed requirement check.

The exact effective handoff is the full R1 list with the R6 replacement after
human-presence: `effect_authorization_requirement_fingerprint`, then
`final_handoff_authority_assessment_fingerprint`; the old Jenn field is absent.
Every other handoff field survives in prior relative order.

The fixture must contain at least one complete permit, currentness assessment,
admission, acceptance, final authority assessment, disposition, handoff, and
zero-effect terminal stub. All object fingerprints, outer node fingerprints,
dependency edges, complete field-name sets, removed-field absence, and zero
effect/provider/raw-secret counts are machine checked.

## 6. Gate and non-authorization

The R7 amendment, full-effective fixture, and validator are three new subjects;
the next fresh full atomic review covers all twenty-one R1-R7 subjects. Only
Jenn may accept or freeze F4. Nothing starts F5/F6 or authorizes implementation,
runtime, database, service, Host, provider, production authentication,
credentials, keys, physical effects, commit, push, merge, release, or deploy.
