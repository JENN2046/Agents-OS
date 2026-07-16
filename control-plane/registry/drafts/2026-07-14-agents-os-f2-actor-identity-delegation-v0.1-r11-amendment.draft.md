# AGENTS OS F2 Actor Identity and Delegation v0.1 R11 Synthetic Precommit Snapshot and Final Materialization Closure Amendment

```yaml
document_type: foundation_contract_amendment
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R11_ATOMIC_BUNDLE
version: v0.1-r11
date: 2026-07-14
owner: Jenn
agent_steward: Nobao
status: proposed_final_draft
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
F3_started: false
```

## 1. Scope and precedence

R11 closes only `F2-R10-IR-B01` and `F2-R10-IR-M01`. It has exact precedence
over R10 Sections 3.3, 4, 5, and 6 for synthetic Binding snapshot and
materialization rules. All other R1-R10 semantics remain unchanged. R1-R11 are
one indivisible proposed acceptance unit; the materialization is excluded.

## 2. Acyclic synthetic precommit input

R11 replaces `SyntheticBindingIssuanceInputSnapshotV0_1R10` with:

```yaml
SyntheticBindingPrecommitInputV0_1R11:
  precommit_input_id:
  workspace_fixture_id:
  controller_spec_ref:
  controller_spec_fingerprint:
  actor_creation_spec_ref:
  actor_creation_spec_fingerprint:
  principal_creation_spec_ref:
  principal_creation_spec_fingerprint:
  authenticator_profile_creation_spec_ref:
  authenticator_profile_creation_spec_fingerprint:
  binding_scope_fingerprint:
  not_before_utc_ms:
  expires_at_utc_ms: utc_milliseconds | null
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:
`agents-os.synthetic-binding-precommit-input.v0.1-r11`.

This object contains only values computable before the manifest body. It
forbids manifest ref/fingerprint, manifest activation ref/fingerprint, its own
Binding creation-spec ref/fingerprint, Event sequence, action, intent, replay,
current assessment, and control proof.

The Binding creation spec includes this precommit input and its fingerprint.
Its `BINDING_REVISION` mutation-body fingerprint is then computable; the
manifest can include that fixed spec fingerprint; the manifest fingerprint and
activation can then be computed in order.

## 3. Post-activation provenance

The final synthetic Binding uses the unchanged R9
`binding_issuance_source_ref: SyntheticManifestDerivedLifecycleRefV0_1` for:

```text
manifest ref/fingerprint
manifest activation ref/fingerprint
Binding creation-spec ref/fingerprint
group intent/action/replay identity
materialization Event
```

Those derived provenance values remain outside the precommitted mutation body,
as R9 Section 3.3 already requires. They are included in the final subject
fingerprint through the exact issuance-source object. The source ref must prove
that the precommit input's controller/Actor/Principal/Profile specs and the
Binding creation spec are exact members of the same ACTIVE manifest and that
all subjects materialized atomically at the named Event.

R10 `ActorPrincipalBindingRevisionR10Additions` is narrowed for synthetic mode:

```yaml
issuance_input_snapshot: SyntheticBindingPrecommitInputV0_1R11
issuance_input_snapshot_fingerprint: exact precommit-input fingerprint
```

Non-synthetic mode continues to use `BindingIssuanceInputSnapshotV0_1R10`
unchanged. Principal control proof remains later activation-only for both.

## 4. Exact creation order

```text
controller + Actor + Profile + Principal creation specs fixed
-> SyntheticBindingPrecommitInput fixed
-> Binding creation spec/body fingerprint fixed
-> manifest body and fingerprint fixed
-> manifest creation intent and Jenn decision fixed
-> activation body/intent and Jenn decision fixed
-> one atomic materialization Event
-> final derived issuance refs and final subject fingerprints
```

No step references its own digest or a later step.

## 5. Materialization correction requirements

The R11 materialization must exactly restore the R8/R9 tables:

```text
Assignment transitions -> JENN_ROOT_ACTION only
no evidence-steward role or wording
all ten TransitionAuthorityBasis kinds -> full required/forbidden field matrix
all R10 complete reducers remain printed
synthetic precommit and post-activation provenance shown separately
```

## 6. Required future fixtures

```text
synthetic precommit contains manifest fingerprint -> reject
synthetic precommit contains own Binding spec fingerprint -> reject
synthetic precommit contains activation or Event -> reject
derived issuance source names different manifest member -> reject
Assignment transition by DIRECT_DELEGATOR_ACTION -> reject
unknown evidence steward input -> reject
valid ordered synthetic graph -> deterministic materialization
```

## 7. Finding disposition and non-authorization

| Finding | R11 disposition |
|---|---|
| `F2-R10-IR-B01` | resolved by precommit/post-activation separation |
| `F2-R10-IR-M01` | resolved only by corrected R11 materialization |

```yaml
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R11_ATOMIC_BUNDLE
partial_acceptance: forbidden
acceptance_authority: Jenn
independent_review_required: true
implementation_authority_by_acceptance: false
runtime_activation_authority_by_acceptance: false
production_authentication_authority_by_acceptance: false
F3_start_by_acceptance: false
```

R11 creates no runtime object, database, service, credential, Binding, proof,
provider call, permit, or effect. It does not accept F2 or start F3.
