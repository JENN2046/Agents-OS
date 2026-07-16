# AGENTS OS F2 Actor Identity and Delegation v0.1 R22 Synthetic Derived Subject Assurance Closure Amendment

```yaml
document_type: foundation_contract_amendment
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R22_ATOMIC_BUNDLE
version: v0.1-r22
date: 2026-07-16
owner: Jenn
agent_steward: Nobao
status: proposed_final_draft
scope_locked: true
blockers_closed:
  - SYNTHETIC_DERIVED_SUBJECT_DIRECT_ASSURANCE_UNCONSTRUCTIBLE
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
F3_started: false
```

## 1. Scope, precedence, and non-expansion

R22 is permitted by `F2_FREEZE_RULE_V0_1` only because the fresh R1-R21 full
atomic review and a separate focused verification produced an exact
`M0_IMPOSSIBILITY` and `INTERNAL_CONTRADICTION` witness. R8 creates synthetic
Profile, Principal, and Binding roots as deterministic results of one manifest
`ACCEPT` Event and expressly creates no per-subject action. R16-R17 nevertheless
required a direct committed root action before those subjects could assess
`ACTIVE`.

R22 replaces only:

```text
1. the R16-R17 direct root-action assurance requirement for the exact R8
   synthetic Authenticator Profile revision-1 CREATE lineage;

2. the same requirement for the exact R8 synthetic Principal revision-1
   CREATE lineage;

3. the same requirement for the exact R8 synthetic Binding revision-1
   issuance lineage;

4. the R21 complete compromise-target traversal only where those three exact
   synthetic roots have no direct per-subject action.
```

For those three roots only, R22 applies the same closed manifest-assurance
projection pattern already used by the R18 synthetic Binding-activation
exception. It does not create an action kind, `ActionAssuranceRoleV0_1R17`
value, schema, field, fingerprint domain, writer, authority basis, permission,
state stream, Event, intent, or per-subject committed action.

Every ordinary Profile, Principal, or Binding branch remains byte-for-byte
governed by R1-R21. Every real post-root lifecycle action remains a direct R17
action with its existing role. R22 does not replace Actor, Assignment,
Delegation, activation, responsibility, permit, Prohibited Boundary, F3, F4,
production authentication, storage, Rust layout, or performance semantics.
Every older rule not expressly replaced below remains effective, and the
narrower R22 rule governs a conflict.

R1-R22 form one indivisible proposed acceptance unit. Partial acceptance is
forbidden. A derived materialization is excluded and creates no authority.

## 2. Exact synthetic-root branch selection

The exception is selected only when one immutable root satisfies every
predicate of exactly one branch below and every existing R8/R11-R14/R20
same-manifest, closed-spec, Actor-eligibility, atomicity, canonical-byte, CAS,
and replay predicate also verifies.

### 2.1 Synthetic Profile root

```text
profile_revision = 1
expected_previous_profile_revision = null
supersedes_profile_revision = null
transition_kind = CREATE
source_status = null
status = ACTIVE

lifecycle_action_ref is exact SyntheticManifestDerivedLifecycleRefV0_1
spec_kind = PROFILE
spec_id/fingerprint name this exact Profile creation spec

mutation_body_fingerprint reproduces the exact creation-spec body
mutation_intent_ref/fingerprint equal the exact manifest ACCEPT group intent
created_at_event_sequence equals the manifest ACCEPT Event
the derived ref, SyntheticM0ControllerRef, manifest, controller, and Profile
  spec all reproduce the same exact closed manifest membership
```

### 2.2 Synthetic Principal root

```text
principal_revision = 1
expected_previous_principal_revision = null
supersedes_principal_revision = null
transition_kind = CREATE
source_status = null
status = ACTIVE
principal_class = SYNTHETIC_TEST_PRINCIPAL
environment = SYNTHETIC_TEST

provisioning_source_ref and lifecycle_action_ref are byte-identical exact
  SyntheticManifestDerivedLifecycleRefV0_1 values
spec_kind = PRINCIPAL
spec_id/fingerprint name this exact Principal creation spec

mutation_body_fingerprint reproduces the exact creation-spec body
mutation_intent_ref/fingerprint equal the exact manifest ACCEPT group intent
created_at_event_sequence equals the manifest ACCEPT Event
Profile, controller, credential handles, spec, and final subject all belong
  to the same exact closed manifest
```

### 2.3 Synthetic Binding root

```text
binding_revision = 1
expected_previous_binding_revision = null
supersedes_binding_revision = null
activation_mode = SYNTHETIC_M0_FIXTURE
status = ACTIVE

issuance_input_snapshot is the exact SyntheticBindingPrecommitInputV0_1R11
binding_issuance_source_ref is exact SyntheticManifestDerivedLifecycleRefV0_1
spec_kind = BINDING
spec_id/fingerprint name this exact Binding creation spec

mutation_body_fingerprint reproduces the exact Binding body/spec
mutation_intent_ref/fingerprint equal the exact manifest ACCEPT group intent
created_at_event_sequence equals the manifest ACCEPT Event
the pre-existing Actor is exact R13-R14 ELIGIBLE at ACCEPT
Actor, Profile, Principal, controller, precommit input, Binding spec, and final
  Binding all reproduce the same exact closed manifest membership
```

Seeing only `SYNTHETIC_TEST`, `SYNTHETIC_FIXTURE`, a derived ref, an absent
ordinary action, or a matching stable ID never selects this exception. A near,
partial, mixed, wrong-kind, wrong-spec, cross-manifest, stale, substituted, or
fingerprint-mismatched shape rejects at admission or yields `INDETERMINATE` at
assessment. It never falls back from one branch to another or to an ordinary
branch.

## 3. Current manifest-assurance projection

### 3.1 Immutable origin anchor and current assessment

The `manifest_assessment_ref/fingerprint` embedded in each
`SyntheticManifestDerivedLifecycleRefV0_1` is the immutable `ACTIVE` assessment
anchor verified at the manifest `ACCEPT` Event. It proves origin and derivation;
it is not current-validity evidence at a later watermark.

At containing assessment watermark `W`, Rust starts from the exact immutable
`manifest_ref/fingerprint` in the derived ref and the closed manifest ledger
indexes through `W`. It must derive exactly one current
`SyntheticM0ManifestAssessmentV0_1R16` whose:

```text
manifest identity and creation fingerprint are exact
activation stream is unique, contiguous, and fork-free through W
based_on_event_sequence = W
canonical fingerprint verifies
action_assurance_bindings are the complete R17 set at W
```

The current manifest assessment contains exactly one
`SYNTHETIC_MANIFEST_CREATE` binding, exactly one
`SYNTHETIC_MANIFEST_ACCEPT` binding, and exactly one
`SYNTHETIC_MANIFEST_REVOKE` binding if and only if the current contiguous
activation chain contains the later terminal revoke. Every binding preserves
its original exact action ref, action fingerprint, historical-assessment ref,
historical-assessment fingerprint, and R17 role.

The ACCEPT-time anchor fingerprint need not equal the later current assessment
fingerprint. Treating the old anchor as the current assessment, requiring the
two fingerprints to remain equal, or deriving currentness without the closed
indexes through `W` yields `INDETERMINATE` and denies new use.

### 3.2 Conditional complete assurance sets

For the exact synthetic Profile-root lineage:

```text
PROFILE_REVISION_CREATE direct binding is absent and forbidden
project the exact SYNTHETIC_MANIFEST_CREATE and SYNTHETIC_MANIFEST_ACCEPT
  bindings from the current manifest assessment byte-identically
include every accepted ordinary Profile action after the synthetic root with
  its unchanged direct R17 role and binding
```

For the exact synthetic Principal-root lineage:

```text
PRINCIPAL_REVISION_CREATE direct binding is absent and forbidden
project the same exact manifest CREATE and ACCEPT enabling bindings
include every accepted ordinary Principal action after the synthetic root with
  its unchanged direct R17 role and binding
```

For the exact synthetic Binding-root lineage:

```text
BINDING_ISSUANCE direct binding is absent and forbidden
project the same exact manifest CREATE and ACCEPT enabling bindings
include every accepted ordinary Binding transition after issuance with its
  unchanged direct R17 role and binding
consume R18 activation assurance only through the exact fingerprinted
  BindingActivationAssessmentV0_1R16; do not duplicate activation assurance
```

The manifest CREATE and ACCEPT bindings projected into the synthetic Binding
issuance assessment and the R18 synthetic activation assessment must be
byte-identical at `W`.
Disagreement in manifest identity, role, ref, fingerprint, historical
assessment, impact coverage, order, or watermark is `INDETERMINATE`.

The current manifest assessment's optional `SYNTHETIC_MANIFEST_REVOKE` binding
is not copied into these downstream arrays. Its current assessment fingerprint
and `REVOKED` result are a transitive currentness dependency under R8/R16. This
keeps the existing R18 activation complete set unchanged while ensuring that a
later revoke still makes every derived subject non-active at the same `W`.

`SyntheticManifestDerivedLifecycleRefV0_1`, its canonical fingerprint,
derivation replay identity, spec ref, evidence ref, controller ref, or
assessment ref is never an assurance action and never receives an R17 role.
It cannot appear as an `ActionAssuranceBinding.action_ref`,
`HistoricalActionValidityAssessment.action_ref`, LifecycleActionRef substitute,
or `CompleteCompromiseTargetActionMember`.

The R17 43-entry enum and action-to-role mapping remain unchanged. Manifest
actions retain only their original manifest roles. No manifest action is
relabelled `PROFILE_REVISION_CREATE`, `PRINCIPAL_REVISION_CREATE`, or
`BINDING_ISSUANCE`.

### 3.3 Order, uniqueness, and branch exclusivity

Each containing `action_assurance_bindings` array retains the R17 canonical
order:

```text
ActionAssuranceRoleV0_1R17 enum ordinal
then action_ref NFC UTF-8 bytes
then action_fingerprint lowercase digest bytes
```

Repeated roles require different exact action refs. A duplicate
`(action_role, action_ref)` pair, one ref with two roles or fingerprints, an
invented direct synthetic-root role, an omitted or extra manifest binding, an
ordinary root action mixed with the synthetic projection, or a caller-supplied
order rejects or yields `INDETERMINATE` under the owning boundary.

An ordinary Profile/Principal CREATE or Binding issuance still requires its
exact direct action and original role. Manifest assurance cannot repair an
ordinary missing action. Conversely, an exact synthetic root has an empty
direct-root-action set and may not also carry the ordinary direct role. Later
real actions are not excluded by the root exception.

R22 changes only the branch-selected contents of existing assessment arrays.
`ActionAssuranceBindingV0_1R17`,
`HistoricalActionValidityAssessmentV0_1R16`, every containing assessment
schema/domain, and every canonical ordering rule remain unchanged.

## 4. Reducer, proof DAG, and fail-closed behavior

### 4.1 Reducer order

The affected Profile, Principal, and effective Binding reducers use this exact
prelude before their existing object-specific currentness rules:

```text
1. select exactly one ordinary or Section 2 synthetic-root branch;
2. verify the branch-selected complete direct and transitive assurance set;
3. require containing assessment, current manifest assessment, every projected
   historical assessment, and every impact input set to cover exact W;
4. apply R15 CompromiseImpact current_assurance mapping;
5. preserve proven safer and terminal effects and prohibit automatic restore;
6. permit ACTIVE only when the current manifest is ACTIVE, both manifest
   enabling assurances are CONFIRMED, every later required direct assurance is
   CONFIRMED, and every pre-existing object-specific dependency passes.
```

Missing, extra, duplicated, stale, forked, cross-manifest, wrong-spec,
wrong-kind, role-mismatched, fingerprint-mismatched, or watermark-mismatched
coverage produces `INDETERMINATE` and denies new use. R22 does not turn
historical origin proof into current validity.

### 4.2 Safe state and revoke

If either manifest CREATE/ACCEPT assurance is `CHALLENGED` or `INDETERMINATE`,
or the current manifest assessment is `INDETERMINATE`, every otherwise-usable
derived Profile, Principal, Binding, controller, and synthetic activation is
non-active or `INDETERMINATE` under its existing reducer. No new proof,
representation, Command attribution, permit, or effect admission is allowed.

If an enabling manifest action is `INVALIDATED`, R15's existing synthetic
manifest rule makes the manifest prospectively `REVOKED` and all derived
subjects non-active. A valid later manifest `REVOKE` has the same no-new-use
boundary. Each downstream reducer uses its existing applicable safer state;
where no exact terminal fact or enum state exists it returns `INDETERMINATE`.
R22 invents no status value or transition fact.

A proven manifest `REVOKE` remains effective even if its own assurance is later
challenged or invalidated. It never restores a Profile, Principal, Binding,
controller, or activation. Manifest revoke remains terminal; R22 adds no resume
or compensation path.

### 4.3 Acyclic dependency order

The effective proof order is:

```text
manifest creation/activation actions + impact indexes through W
-> current SyntheticM0ManifestAssessment(W)
-> synthetic Profile assessment
-> synthetic Principal assessment
-> synthetic Binding issuance and R18 activation assessments
-> effective Binding assessment
```

Manifest assessment never reads a derived Profile, Principal, Binding,
activation assessment, or their assurance arrays. The immutable derived ref is
fixed before downstream assessment and the current manifest assessment is
recomputed from manifest indexes only. No proof edge points back to manifest
acceptance, so R22 creates no fixed point.

## 5. Complete CompromiseImpact projection

R21 `CompleteCompromiseTargetActionMemberV0_1R21`, its R17 canonical order, and
the `agents-os.compromise-complete-target-action-set.v0.1-r21` fingerprint
formula remain byte-for-byte unchanged.

When an already-eligible R15/R21 target selection traverses one of the three
R22 assurance edges, the exact contribution is the existing manifest action
member with role `SYNTHETIC_MANIFEST_CREATE` or
`SYNTHETIC_MANIFEST_ACCEPT`. It never invents a Profile CREATE, Principal
CREATE, or Binding issuance member. A current `SYNTHETIC_MANIFEST_REVOKE`
remains selectable through the existing manifest action-assurance index and
`SAFETY_TRANSITION` mapping; R22 does not duplicate it through the downstream
enabling projection. R15 target-membership and impact authority predicates
remain unchanged; dependency alone does not create a new eligible compromised
target.

The final target set is a set-union by exact action identity. When Profile,
Principal, Binding issuance, and R18 Binding activation traverse the same
manifest action, that action appears exactly once with its one original role,
ref, and fingerprint. The reducer merges identical dependency paths before
encoding. An encoded duplicate, the same ref with another role or fingerprint,
a derived-ref member, a pseudo root member, an omitted eligible manifest
member, or an extra ineligible member rejects.

Existing R15 classification remains unchanged:

```text
manifest CREATE or ACCEPT -> SYNTHETIC_MANIFEST_CREATE_OR_ACCEPT
manifest REVOKE -> SAFETY_TRANSITION
```

`CHALLENGE` and `INVALIDATE` propagate through the verified current manifest
assessment and Section 4 safe-state rules. Shared manifest derivation retains
its existing shared fate; R22 creates no per-subject isolation that R8 did not
provide.

## 6. Constructive witness and conformance negatives

One required positive witness is:

```text
exact R21 DOMAIN_AGENT revision-1 synthetic Actor bootstrap -> ACTIVE
-> R13-R14 Actor eligibility -> ELIGIBLE
-> one exact manifest CREATE action and revision-1 ACCEPT action
-> one atomic ACCEPT Event materializes same-manifest Profile, Principal,
   Binding, controller, derived refs, and final fingerprints
-> current manifest assessment at W = ACTIVE with exact CONFIRMED CREATE/ACCEPT
-> Profile array projects manifest bindings and no PROFILE_REVISION_CREATE
-> Profile assessment = ACTIVE
-> Principal array projects the same bindings and no PRINCIPAL_REVISION_CREATE
-> Principal assessment = ACTIVE
-> Binding issuance array projects the same bindings and no BINDING_ISSUANCE
-> R18 activation assessment uses byte-identical manifest assurance and no
   BINDING_ACTIVATION action
-> effective Binding assessment = ACTIVE
```

The conformance set must reject or fail closed for at least:

```text
invented PROFILE_REVISION_CREATE, PRINCIPAL_REVISION_CREATE, or BINDING_ISSUANCE
ordinary root using manifest projection instead of its direct action
synthetic revision greater than 1 omitting its real direct action
derived ref used as an action or compromise member
manifest ACCEPT assigned more than its one manifest role
missing CREATE or ACCEPT assurance
extra, duplicated, substituted, or misordered assurance binding
wrong spec_kind, spec fingerprint, stable ID, controller, Actor, or manifest
partial materialization or mixed ordinary/synthetic provenance
ACCEPT-time anchor reused as current assessment at later W
any mismatch among containing, manifest, historical, impact, or index watermark
manifest fork, CAS gap, coverage gap, or fingerprint conflict
valid REVOKE ignored because earlier enabling assurances remain CONFIRMED
REVOKE assurance challenge or invalidation used to auto-restore
same manifest action encoded multiple times through different dependency paths
pseudo subject action included while the real manifest action is omitted
ordinary canonical bytes changed by the R22 implementation
```

Mandatory invariants remain:

```text
ActionAssuranceRole count = 43
new schemas = 0
new fingerprint domains = 0
new action or authority kinds = 0
new writers or state streams = 0
R21 compromise member schema and formula unchanged
ordinary branch canonical bytes unchanged
```

## 7. Corrected complete materialization requirements

The next complete materialization must be a new immutable version after v17.
It must:

```text
apply Sections 2-5 without changing any ordinary branch
print the three exact synthetic-root branch discriminators
print immutable ACCEPT anchor versus current manifest assessment at W
print conditional Profile, Principal, and Binding assurance complete sets
print the no-derived-ref-as-action and no-direct-plus-transitive invariants
print exact watermark, order, uniqueness, compromise set-union, and revoke rules
update Profile, Principal, Binding, startup/recovery, assurance, compromise,
  synthetic graph, reducer, and source-index reading surfaces
retain all v17 source-exact materialization corrections
update exact subject hashes, source refs, counts, and precedence
create no new semantic field, enum, schema, domain, writer, or authority
```

The materialization is non-authoritative. It may not repair R1-R22 by
interpretation.

## 8. Review gate and non-authorization

The corrected R1-R22 unit and its complete materialization require a targeted
consistency review followed by a fresh full atomic review under
`F2_FREEZE_RULE_V0_1`. `PASS_NO_BLOCKER` makes the unit eligible only for
Jenn's atomic freeze decision.

R22 does not accept, freeze, implement, activate, commit, push, deploy, or
start F3. It authorizes no runtime, provider, credential, production
authentication, database, service, host effect, external write, or permission
expansion.
