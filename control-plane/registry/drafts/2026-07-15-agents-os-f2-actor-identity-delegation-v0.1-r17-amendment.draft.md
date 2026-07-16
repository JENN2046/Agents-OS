# AGENTS OS F2 Actor Identity and Delegation v0.1 R17 Action-Assurance Role Vocabulary and Materialization Closure Amendment

```yaml
document_type: foundation_contract_amendment
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R17_ATOMIC_BUNDLE
project: AGENTS OS
version: v0.1-r17
date: 2026-07-15
owner: Jenn
agent_steward: Nobao
status: proposed_final_draft
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
F3_started: false
```

## 1. Scope and precedence

R17 closes only the two major findings from the fresh R1-R16 full-bundle
review:

```text
closed canonical ActionAssuranceRole vocabulary and total action mapping
duplicate-free, alias-free, fully indexed materialization v5
```

R17 has exact precedence over R16 `ActionAssuranceBindingV0_1R16.action_role`,
R16 prose role sets, and R16 materialization requirements. All other R1-R16
rules remain effective. R1-R17 form one indivisible proposed acceptance unit.
Partial acceptance is forbidden.

## 2. Closed ActionAssuranceRole vocabulary

### 2.1 Exact enum

`ActionAssuranceBindingV0_1R16.action_role` is replaced by the closed scalar:

```yaml
ActionAssuranceRoleV0_1R17:
  ACTOR_REVISION_CREATE
  ACTOR_REVISION_UPDATE
  ACTOR_TRANSITION_SUSPEND
  ACTOR_TRANSITION_RESUME
  ACTOR_TRANSITION_COMPROMISE
  ACTOR_TRANSITION_RECOVER
  ACTOR_TRANSITION_RETIRE

  PROFILE_REVISION_CREATE
  PROFILE_REVISION_UPDATE
  PROFILE_TRANSITION_SUSPEND
  PROFILE_TRANSITION_RESUME
  PROFILE_TRANSITION_RETIRE

  PRINCIPAL_REVISION_CREATE
  PRINCIPAL_REVISION_ROTATE_CREDENTIALS
  PRINCIPAL_TRANSITION_SUSPEND
  PRINCIPAL_TRANSITION_RESUME
  PRINCIPAL_TRANSITION_REVOKE
  PRINCIPAL_TRANSITION_RETIRE

  BINDING_ISSUANCE
  BINDING_TRANSITION_SUSPEND
  BINDING_TRANSITION_RESUME
  BINDING_TRANSITION_REVOKE

  BINDING_ACTIVATION
  BINDING_ACTIVATION_TRANSITION_SUSPEND
  BINDING_ACTIVATION_TRANSITION_RESUME
  BINDING_ACTIVATION_TRANSITION_REVOKE

  ASSIGNMENT_ISSUANCE
  ASSIGNMENT_TRANSITION_SUSPEND
  ASSIGNMENT_TRANSITION_RESUME
  ASSIGNMENT_TRANSITION_REVOKE

  DELEGATION_ISSUANCE
  DELEGATION_TRANSITION_SUSPEND
  DELEGATION_TRANSITION_RESUME
  DELEGATION_TRANSITION_REVOKE
  DELEGATION_TRANSITION_RENOUNCE

  DELEGATION_ACTIVATION
  DELEGATION_ACTIVATION_TRANSITION_SUSPEND
  DELEGATION_ACTIVATION_TRANSITION_RESUME
  DELEGATION_ACTIVATION_TRANSITION_REVOKE
  DELEGATION_ACTIVATION_TRANSITION_RENOUNCE

  SYNTHETIC_MANIFEST_CREATE
  SYNTHETIC_MANIFEST_ACCEPT
  SYNTHETIC_MANIFEST_REVOKE
```

The scalar is one exact NFC ASCII string from this list. Case folding,
aliases, prefixes, numeric codes, localized text, extension values, and unknown
strings reject. The enum order printed above is the canonical role order.

R17 replaces the embedded binding schema with:

```yaml
ActionAssuranceBindingV0_1R17:
  action_role: ActionAssuranceRoleV0_1R17
  action_ref:
  action_fingerprint:
  historical_action_validity_assessment_ref:
  historical_action_validity_assessment_fingerprint:
```

Embedded-object domain:

```text
agents-os.action-assurance-binding.v0.1-r17
```

Every R16 assessment field typed as
`ActionAssuranceBindingV0_1R16[]` is replaced by
`ActionAssuranceBindingV0_1R17[]`. The containing assessment domain remains
its R16 domain because R17 changes the complete known-object field type and the
R17 subject is part of its effective fingerprint contract. No R16 binding is
valid in an R17 assessment.

### 2.2 Total exclusive action-to-role mapping

The mapping uses the immutable committed subject/fact and its transition kind,
not caller labels:

| Exact action-bearing object | Exact transition/action kind | Canonical role |
|---|---|---|
| `ActorIdentityRevisionV0_1R8` | `CREATE` | `ACTOR_REVISION_CREATE` |
| same | `UPDATE` | `ACTOR_REVISION_UPDATE` |
| same | `SUSPEND` | `ACTOR_TRANSITION_SUSPEND` |
| same | `RESUME` | `ACTOR_TRANSITION_RESUME` |
| same | `COMPROMISE` | `ACTOR_TRANSITION_COMPROMISE` |
| same | `RECOVER` | `ACTOR_TRANSITION_RECOVER` |
| same | `RETIRE` | `ACTOR_TRANSITION_RETIRE` |
| `AuthenticatorProfileRevisionR9Effective` | `CREATE` | `PROFILE_REVISION_CREATE` |
| same | `UPDATE` | `PROFILE_REVISION_UPDATE` |
| same | `SUSPEND` | `PROFILE_TRANSITION_SUSPEND` |
| same | `RESUME` | `PROFILE_TRANSITION_RESUME` |
| same | `RETIRE` | `PROFILE_TRANSITION_RETIRE` |
| `PrincipalRevisionR9Effective` | `CREATE` | `PRINCIPAL_REVISION_CREATE` |
| same | `ROTATE_CREDENTIALS` | `PRINCIPAL_REVISION_ROTATE_CREDENTIALS` |
| same | `SUSPEND` | `PRINCIPAL_TRANSITION_SUSPEND` |
| same | `RESUME` | `PRINCIPAL_TRANSITION_RESUME` |
| same | `REVOKE` | `PRINCIPAL_TRANSITION_REVOKE` |
| same | `RETIRE` | `PRINCIPAL_TRANSITION_RETIRE` |
| `ActorPrincipalBindingRevisionR10Effective` | issuance action | `BINDING_ISSUANCE` |
| `GovernedStateTransitionFactV0_1R9Effective` targeting `BINDING` | `SUSPEND` | `BINDING_TRANSITION_SUSPEND` |
| same target | `RESUME` | `BINDING_TRANSITION_RESUME` |
| same target | `REVOKE` | `BINDING_TRANSITION_REVOKE` |
| `BindingActivationEvidenceR15Effective` | creation/activation action | `BINDING_ACTIVATION` |
| governed fact targeting `BINDING_ACTIVATION_EVIDENCE` | `SUSPEND` | `BINDING_ACTIVATION_TRANSITION_SUSPEND` |
| same target | `RESUME` | `BINDING_ACTIVATION_TRANSITION_RESUME` |
| same target | `REVOKE` | `BINDING_ACTIVATION_TRANSITION_REVOKE` |
| `ResponsibilityAssignmentRevisionV0_1R15` | issuance action | `ASSIGNMENT_ISSUANCE` |
| governed fact targeting `ASSIGNMENT` | `SUSPEND` | `ASSIGNMENT_TRANSITION_SUSPEND` |
| same target | `RESUME` | `ASSIGNMENT_TRANSITION_RESUME` |
| same target | `REVOKE` | `ASSIGNMENT_TRANSITION_REVOKE` |
| `DelegationGrantRevisionV0_1R15Effective` | issuance action | `DELEGATION_ISSUANCE` |
| governed fact targeting `DELEGATION` | `SUSPEND` | `DELEGATION_TRANSITION_SUSPEND` |
| same target | `RESUME` | `DELEGATION_TRANSITION_RESUME` |
| same target | `REVOKE` | `DELEGATION_TRANSITION_REVOKE` |
| same target | `RENOUNCE` | `DELEGATION_TRANSITION_RENOUNCE` |
| `DelegationActivationEvidenceR15Effective` | creation/activation action | `DELEGATION_ACTIVATION` |
| governed fact targeting `DELEGATION_ACTIVATION_EVIDENCE` | `SUSPEND` | `DELEGATION_ACTIVATION_TRANSITION_SUSPEND` |
| same target | `RESUME` | `DELEGATION_ACTIVATION_TRANSITION_RESUME` |
| same target | `REVOKE` | `DELEGATION_ACTIVATION_TRANSITION_REVOKE` |
| same target | `RENOUNCE` | `DELEGATION_ACTIVATION_TRANSITION_RENOUNCE` |
| `SyntheticM0PrincipalProvisioningManifestV0_1R8Effective` | creation action | `SYNTHETIC_MANIFEST_CREATE` |
| `SyntheticM0ManifestActivationRevisionV0_1R9` | `ACCEPT` | `SYNTHETIC_MANIFEST_ACCEPT` |
| same | `REVOKE` | `SYNTHETIC_MANIFEST_REVOKE` |

Rows are ordered for readability only; matching is by the exact tuple. Exactly
one row must match. Zero or multiple matches reject. CompromiseImpact actions,
historical assessments, authentication assertions, derived assessments,
CREATE target specs, and authority-basis records are not direct assurance
actions and cannot receive a role.

### 2.3 Complete-set derivation and repeated roles

At one assessment watermark Rust derives bindings from closed ledger indexes:

```text
Actor/Profile/Principal:
  every committed action on the complete contiguous root-to-current revision chain

Binding/Assignment/Delegation:
  exact issuance action plus every accepted target transition fact through watermark

Binding/Delegation activation:
  exact activation-evidence creation action plus every accepted evidence transition fact

Synthetic manifest:
  exact manifest creation action plus current contiguous activation revisions through watermark
```

An action included by the closed index is mapped through Section 2.2. A role
may repeat when multiple actions share the same tuple, for example repeated
suspend/resume cycles. Repetition is distinguished only by exact action ref and
fingerprint; duplicate `(action_role, action_ref)` pairs reject.

Canonical array order is:

```text
ActionAssuranceRoleV0_1R17 enum ordinal
then action_ref NFC UTF-8 bytes
then action_fingerprint lowercase digest bytes
```

Caller-supplied ordering or role labels are ignored and recomputed. Missing
index coverage, revision/fact fork, action without exactly one role, missing
binding, extra binding, or mismatched historical assessment produces
`INDETERMINATE` and denies new use. Safety-transition and enabling-transition
semantics remain exactly R16: no automatic restore and no automatic
reactivation.

## 3. Materialization v5 requirements

The author must create:

```text
F2 Effective Contract Materialization v0.1-r17-v5
```

It is derived-only and not an acceptance subject. It must:

```text
print every effective schema exactly once
print every reducer exactly once
replace all R16 assurance binding types with ActionAssuranceBindingV0_1R17
print the complete enum, mapping, complete-set derivation, and ordering
use TransitionAuthorityBasisV0_1R9 in the effective governed transition fact
print one complete CompromiseImpactFactV0_1R9Effective schema
contain no superseded or undefined schema alias
provide one exhaustive object/reducer index whose every row names:
  exact printed object or reducer
  kind
  fingerprint domain or NOT_STANDALONE
  authoritative source subject and section
  materialization section
```

The schema index row set must equal every top-level schema block in v5. The
reducer index row set must equal every explicitly named reducer definition in
v5.
Duplicate object names, missing rows, extra rows, conflicting schemas, broad
source-only prose, and unresolved aliases fail materialization validation.

## 4. Required future fixtures

```text
unknown action_role string -> reject
known role attached to wrong action tuple -> reject
same action maps to zero or two roles -> reject
repeated suspend actions -> same role, deterministic action-ref order
caller changes role label or order -> recompute and reject mismatch
closed ledger index contains action missing from binding set -> INDETERMINATE
v5 duplicate schema name -> validation failure
v5 stale TransitionAuthorityBasisV0_1R8 alias -> validation failure
v5 index row set differs from schema/reducer set -> validation failure
```

## 5. Finding disposition

| Finding | R17 disposition |
|---|---|
| `F2-R16-FULL-IR-M01` | Sections 2.1-2.3 freeze the enum, total tuple mapping, repeated-role semantics, complete-set derivation, and canonical order |
| `F2-R16-FULL-IR-M02` | Section 3 requires duplicate removal, R9 authority basis, one impact schema, no stale aliases, and an exhaustive exact index |

## 6. Non-authorization

R17 does not accept F2, authorize implementation, start F3, activate runtime,
authorize production authentication, create a permission taxonomy, modify the
single Prohibited Boundary, or modify R1-R16/prior review bytes.

The next gate is a fresh hash-bound independent full review of R1-R17 and
materialization v5. Jenn acceptance may occur only after a clean review.
