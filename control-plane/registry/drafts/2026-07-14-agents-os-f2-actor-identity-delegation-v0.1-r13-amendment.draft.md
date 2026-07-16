# AGENTS OS F2 Actor Identity and Delegation v0.1 R13 M0 Actor Eligibility Closure Amendment

```yaml
document_type: foundation_contract_amendment
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R13_ATOMIC_BUNDLE
version: v0.1-r13
date: 2026-07-14
owner: Jenn
agent_steward: Nobao
status: proposed_final_draft
implementation_authorized: false
runtime_activation_authorized: false
F3_started: false
```

## 1. Scope

R13 closes only `F2-R12-IR-B01` and `F2-R12-IR-M01`. It defines a derived M0
Actor eligibility assessment without changing Actor schema or creation routes,
and replaces the synthetic Binding row in the materialization.

## 2. Deterministic eligibility assessment

```yaml
SyntheticM0ActorEligibilityAssessmentV0_1R13:
  actor_identity_ref:
  actor_identity_fingerprint:
  actor_identity_assessment_ref:
  actor_identity_assessment_fingerprint:
  root_create_revision_ref:
  root_create_revision_fingerprint:
  root_create_authority_basis_ref:
  root_create_authority_basis_fingerprint:
  root_Jenn_governance_authority_ref:
  root_Jenn_governance_authority_fingerprint:
  assessment: ELIGIBLE | INELIGIBLE | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:
`agents-os.synthetic-m0-actor-eligibility-assessment.v0.1-r13`.

`ELIGIBLE` requires all of:

```text
exact Actor current assessment = ACTIVE at manifest ACCEPT Event
complete contiguous revision chain to revision 1 CREATE
revision 1 basis_kind = JENN_GOVERNANCE_DECISION_BASIS
root JennRootGovernanceAuthorityRef environment = SYNTHETIC_TEST
root permitted_basis_uses contains IDENTITY_BOOTSTRAP
actor_class in RESIDENT_COORDINATOR | DOMAIN_AGENT | TEMPORARY_WORKER | SYSTEM_SERVICE
actor_class is not JENN_HUMAN_ROOT or EXECUTION_HOST
no production Actor Binding or active Jenn credential is referenced
all lineage fingerprints and authority refs verify
```

Any explicit class/environment/provenance violation is `INELIGIBLE`; missing,
forked, stale, incomplete, or conflicting evidence is `INDETERMINATE`. Only
`ELIGIBLE` may support a synthetic Binding. The assessment is derived at the
ACCEPT Event, has no writer-owned head, and creates no authority.

## 3. Binding integration

The Binding precommit body continues to contain only the exact existing Actor
ref/fingerprint. At ACCEPT, the atomic transaction derives the eligibility
assessment above and requires `ELIGIBLE`. The assessment ref/fingerprint is
validation evidence for the materialization transaction and final effective
Binding assessment; it is not inserted into the precommit body, manifest, or
final Binding subject fingerprint.

The R12 wording “Actor ACTIVE assessment” is replaced by “exact
`SyntheticM0ActorEligibilityAssessmentV0_1R13 = ELIGIBLE`”, which includes the
ACTIVE assessment and synthetic bootstrap provenance.

## 4. Exact synthetic materialization row

```text
SYNTHETIC_M0_FIXTURE required at ACCEPT Event:
  exact ACTIVE manifest assessment
  exact controller spec/currentness
  exact Profile, Principal, Binding creation-spec membership
  exact Binding precommit Actor ref/fingerprint
  exact SyntheticM0ActorEligibilityAssessment = ELIGIBLE
  exact scope and time window

forbidden in precommit body:
  every current assessment including Actor eligibility
  control proof
  manifest/activation/own-spec/Event provenance

required as transaction validation evidence, outside body:
  Actor eligibility assessment at ACCEPT Event
```

This Event-time validation is the sole declared exception to the earlier
“no pre-existing current assessment in synthetic precommit” wording; it does
not alter the body fingerprint.

## 5. Non-authorization

R1-R13 form one indivisible proposed acceptance unit. Partial acceptance is
forbidden. Only Jenn may accept it. Acceptance grants no implementation,
runtime activation, production authentication, or F3 authority.

