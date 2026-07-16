# AGENTS OS F2 Actor Identity and Delegation v0.1 R14 Closed Reference Eligibility Closure Amendment

```yaml
document_type: foundation_contract_amendment
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R14_ATOMIC_BUNDLE
version: v0.1-r14
date: 2026-07-14
owner: Jenn
agent_steward: Nobao
status: proposed_final_draft
implementation_authorized: false
runtime_activation_authorized: false
F3_started: false
```

## 1. Exact closure

R14 closes only `F2-R13-IR-B01` and `F2-R13-IR-m01`. It removes the R13
eligibility phrase:

```text
no production Actor Binding or active Jenn credential is referenced
```

That phrase is forbidden as an eligibility predicate because it requires an
undefined open-world inventory and could confuse missing coverage with absence.

## 2. Closed reference universe

`SyntheticM0ActorEligibilityAssessmentV0_1R13` evaluates only its complete
positive input set:

```text
the exact Actor current head and ACTIVE assessment at ACCEPT
the complete contiguous Actor revision chain to revision 1
the exact revision-1 CREATE authority basis
the exact root Jenn governance authority ref
actor_class
the ACCEPT Event watermark
```

Its `ELIGIBLE` predicate is exactly:

```text
all listed inputs present, verified, fingerprint-matching, and complete
current Actor assessment = ACTIVE at ACCEPT
revision 1 transition = CREATE
revision 1 basis_kind = JENN_GOVERNANCE_DECISION_BASIS
root governance authority environment = SYNTHETIC_TEST
permitted_basis_uses contains IDENTITY_BOOTSTRAP
actor_class in RESIDENT_COORDINATOR | DOMAIN_AGENT | TEMPORARY_WORKER | SYSTEM_SERVICE
```

`JENN_HUMAN_ROOT` and `EXECUTION_HOST` are excluded by the closed class
allowlist. The assessment does not read, enumerate, or make claims about any
Binding or credential inventory.

The synthetic Binding transaction separately verifies its own closed reference
universe:

```text
Actor ref/fingerprint = the ELIGIBLE assessment Actor
Profile spec = exact same-manifest synthetic Profile spec
Principal spec = exact same-manifest SYNTHETIC_TEST Principal spec
every credential handle = exact member of manifest deterministic_credential_handle_refs
Binding spec contains no external Binding, credential, Jenn identity, or host identity ref
```

These checks cover every reference the new Binding can actually use. They do
not infer anything from a global absence query.

## 3. Materialization wording

Every materialized summary replaces “ACTIVE Actor” with
`SyntheticM0ActorEligibilityAssessment = ELIGIBLE` and prints the two closed
input sets above. No earlier ACTIVE-only sentence remains effective.

## 4. Non-authorization

R1-R14 form one indivisible proposed acceptance unit. Partial acceptance is
forbidden. Only Jenn may accept it. Acceptance grants no implementation,
runtime activation, production authentication, or F3 authority.

