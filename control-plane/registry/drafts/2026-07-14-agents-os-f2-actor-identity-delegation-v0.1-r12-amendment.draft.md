# AGENTS OS F2 Actor Identity and Delegation v0.1 R12 Existing Actor Synthetic Binding Closure Amendment

```yaml
document_type: foundation_contract_amendment
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R12_ATOMIC_BUNDLE
version: v0.1-r12
date: 2026-07-14
owner: Jenn
agent_steward: Nobao
status: proposed_final_draft
implementation_authorized: false
runtime_activation_authorized: false
F3_started: false
```

## 1. Scope and precedence

R12 closes only `F2-R11-IR-B01` and `F2-R11-IR-M01`. It replaces the Actor
fields and membership predicate in R11 Sections 2-4 and corrects the R11
materialization Profile-controller row. All other R1-R11 rules remain effective.

## 2. Existing Actor boundary

The synthetic manifest does not create Actors. R12 replaces:

```yaml
actor_creation_spec_ref:
actor_creation_spec_fingerprint:
```

in `SyntheticBindingPrecommitInputV0_1R11` with:

```yaml
existing_actor_identity_ref:
existing_actor_identity_fingerprint:
```

The exact Actor revision must exist before manifest construction. It must use
an M0-allowed non-production Actor fixture established through the ordinary
Actor lifecycle contract, not through this manifest. Its ref/fingerprint are
fixed in the Binding creation spec and equal the Binding subject Actor fields.

At the atomic manifest `ACCEPT` Event, Rust separately derives the exact
`ActorIdentityAssessment` at that Event. The assessment must be `ACTIVE`, and
its ref/fingerprint is validation evidence, not a creation-spec/body field.
Missing, stale, suspended, compromised, retired, expired, or mismatched Actor
assessment rejects the whole atomic materialization. No Actor is created,
updated, or activated by the manifest.

The final `SyntheticManifestDerivedLifecycleRefV0_1` proves membership only for
Profile, Principal, and Binding specs, exactly as its existing `spec_kind` enum
declares. For Actor it proves only that the Binding spec names the exact
pre-existing Actor ref/fingerprint; it must not claim Actor spec membership.

## 3. Correct synthetic order

```text
pre-existing Actor revision fixed
controller + Profile + Principal creation specs fixed
-> synthetic Binding precommit input fixed
-> Binding creation spec/body fingerprint fixed
-> manifest body/fingerprint
-> manifest creation and activation decisions
-> at ACCEPT Event verify pre-existing Actor ACTIVE
-> atomically create Profile, Principal, Binding
-> final derived issuance refs and subject fingerprints
```

## 4. Profile target/controller correction

The materialized `PROFILE_CONTROLLER_ACTION` row must distinguish:

```text
target Profile assessment:
  CREATE -> absent
  UPDATE or SUSPEND -> ACTIVE
  RESUME -> SUSPENDED
  RETIRE -> ACTIVE or SUSPENDED

controller_currentness_assessment:
  always operational/ACTIVE for an allowed controller route
```

The target Profile is never reused as proof that its controller is current.

## 5. Findings and non-authorization

| Finding | R12 disposition |
|---|---|
| `F2-R11-IR-B01` | resolved by exact pre-existing Actor ref plus Event-time ACTIVE assessment |
| `F2-R11-IR-M01` | resolved only by corrected R12 materialization |

R1-R12 form one indivisible proposed acceptance unit. Partial acceptance is
forbidden. Only Jenn may accept it. Acceptance does not authorize
implementation, runtime activation, production authentication, or F3.

