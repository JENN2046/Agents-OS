# AGENTS OS F2 Effective Contract Materialization v0.1-r7

```yaml
document_type: derived_effective_contract_materialization
project: AGENTS OS
contract: F2 Actor Identity and Delegation v0.1
effective_version: v0.1-r7
date: 2026-07-14
owner: Jenn
agent_steward: Nobao
status: derived_review_surface
source_of_authority: fixed_R1_through_R7_subjects_only
is_acceptance_subject: false
creates_new_semantics: false
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
F3_started: false
```

## 1. How to use this materialization

This document is a resolved reading surface for reviewers and future
implementers. It does not replace, amend, or supersede any fixed subject. If a
sentence here conflicts with a source subject, the source subjects and their
explicit precedence control.

The authoritative acceptance unit is the indivisible R1-R7 bundle:

| Subject | SHA-256 |
|---|---|
| R1 base | `639e255417be99613cbe768c3b22edec7d5e1303d5a006e2c5dd70ceb1e83f2b` |
| R2 narrow amendment | `8df5e63b9170491c8ea0e764ee6a297035164160bee976674c073f5bf921edcd` |
| R3 final narrow amendment | `d4c7e2e59a71911e47b62dd1ecddc7f56e1292841ceb7181c4d08346f7a0a9db` |
| R4 canonicalization amendment | `a60a6a75c24b0fca68cb87e6e2f576f542f0f4a20caf12adbebb136ad9f51f59` |
| R5 scalar-encoding amendment | `cf568eac5aa06b785ad047d41e2f22e7223e625840a3d96eccfcd9a1434b57be` |
| R6 number-admission amendment | `bed38cf83a2d15da3c11383b9b1ec264a3bf390f6d9fc0931f45d2d8c0e94932` |
| R7 lifecycle/currentness/revocation/scope/scalar amendment | `343881f2292fbb3c09b0cc572b0d9a9c8f77eef1e4b5957134de31796228187c` |

Source paths:

```text
R1 control-plane/registry/drafts/2026-07-14-agents-os-actor-identity-delegation-v0.1.draft.md
R2 control-plane/registry/drafts/2026-07-14-agents-os-f2-actor-identity-delegation-v0.1-r2-amendment.draft.md
R3 control-plane/registry/drafts/2026-07-14-agents-os-f2-actor-identity-delegation-v0.1-r3-amendment.draft.md
R4 control-plane/registry/drafts/2026-07-14-agents-os-f2-actor-identity-delegation-v0.1-r4-amendment.draft.md
R5 control-plane/registry/drafts/2026-07-14-agents-os-f2-actor-identity-delegation-v0.1-r5-amendment.draft.md
R6 control-plane/registry/drafts/2026-07-14-agents-os-f2-actor-identity-delegation-v0.1-r6-amendment.draft.md
R7 control-plane/registry/drafts/2026-07-14-agents-os-f2-actor-identity-delegation-v0.1-r7-amendment.draft.md
```

## 2. Resolved source map

| Effective topic | Effective source |
|---|---|
| purpose, inherited authority, term separation | R1 Sections 1-3 |
| Actor classes and stable meanings | R1 Section 4 |
| Actor identity schema and continuity | R1 Sections 5-6 plus R2 Section 7, replaced where R7 Section 4 applies |
| Principal classes | R1 Section 7.1 |
| Principal lifecycle and currentness | R7 Sections 3, 5, and 6 replace lifecycle-opaque R1 Sections 7.2 and 8 |
| Binding subject and canonical fingerprint | R3 Section 3, R4 Sections 3-5, R5-R6 scalar rules, plus R7 Sections 2, 3, and 7 |
| Binding activation | R2 Section 5 as corrected by R3 Section 3 and narrowed by R7 Section 7 |
| Binding effective currentness | R7 Section 7 only |
| Responsibility Assignment provenance | R2 Section 3 as corrected by R7 Sections 8-12 |
| Responsibility Scope | R7 Section 10 replaces R1 Section 10.2 |
| responsibility lineage | R1 Section 11, R2 Sections 3-4, R3 Section 5, replaced where R7 Section 11 applies |
| Delegation subject and activation graph | R1 Section 11, R2 Sections 4 and 6, R3 Sections 2 and 4, R4 Sections 6-7 |
| Delegation activation projection | R7 Section 7.4 |
| Delegation effective currentness | R1 Section 12 as corrected by R7 Sections 9 and 12.2 |
| suspension, revocation, resume, renunciation | R7 Section 8 replaces the unspecified fact path in R1 Section 13 |
| historical action assurance | R7 Section 9 replaces current-session dependency wording in R1/R2 |
| action-attribution interface and F3 handoff | R2 Sections 2 and 8, R3 Section 2, R4 Section 7 |
| single Prohibited Boundary | R1 Sections 9, 13.3, and 16; unchanged by R2-R7 |
| digest and fingerprint canonicalization | R4 Sections 2-8, R5 Sections 2-5, R6 Sections 2-5, generalized by R7 Section 2 |
| recovery and tests | R1 Sections 19 and 22, R2 Sections 7-10, R3 Section 6, R4 Section 8, R5-R6 fixtures, R7 Section 13 |
| privacy and disclosure | R1 Section 20; unchanged |
| downstream dependencies | R1 Section 23, R2 Section 8, and R7 Section 15 |

## 3. Effective purpose and boundaries

F2 determines:

```text
which stable Actor identity exists
which concrete Principal may represent an Actor now
which Authenticator Profile and credential-status facts support that Principal
which durable responsibility belongs to an Actor
which bounded Delegation chain transfers responsibility
which committed action historically established a fact
which one Prohibited Behavior List revision is checked
```

F2 does not determine:

```text
ordinary-action permission levels
risk tiers or trust scores
Goal, Task, Run, or Validation state
TaskPermit or effect admission
host authentication or fencing
provider execution
production credential design
the final contents of the canonical Prohibited Behavior List
```

Identity, responsibility, delegation, relationship, authentication, and
execution admission remain different concepts.

## 4. Effective Actor model

The closed Actor classes remain:

```text
JENN_HUMAN_ROOT
RESIDENT_COORDINATOR
DOMAIN_AGENT
TEMPORARY_WORKER
SYSTEM_SERVICE
EXECUTION_HOST
```

An Actor is a stable accountable identity, not a model, prompt, process,
session, Principal, credential, database row, or display name.

The effective Actor revision contains the R1 identity fields plus the R2/R7
lifecycle provenance and CAS fields:

```text
stable actor_id and actor_class
contiguous actor_identity_revision
one current head
canonical name and charter refs
immutable identity-stewardship lineage
CREATE / UPDATE / SUSPEND / RESUME / COMPROMISE / RECOVER / RETIRE
source and target status
exact LifecycleActionRef
Temporary Worker validity window and assignment binding
recovery evidence where required
Event sequence and canonical fingerprint
```

Effective transitions are:

```text
CREATE: none -> ACTIVE
UPDATE: ACTIVE -> ACTIVE or SUSPENDED -> SUSPENDED
SUSPEND: ACTIVE -> SUSPENDED
RESUME: SUSPENDED -> ACTIVE
COMPROMISE: ACTIVE/SUSPENDED -> COMPROMISED
RECOVER: COMPROMISED -> ACTIVE
RETIRE: ACTIVE/SUSPENDED/COMPROMISED -> RETIRED
```

An Actor may self-suspend through an authenticated action but may not
self-resume, self-recover, self-retire, change class, approve its own root
identity, or create itself. `RETIRED` is terminal. Temporary Worker expiry is
derived from its exact validity window and assignment binding.

Identity stewardship remains:

```text
Jenn root -> Jenn-attributable governance route
Nobao -> Jenn
Domain Agent -> Jenn or Nobao
Temporary Worker -> Jenn, Nobao, or responsible Domain Agent
System Service / Execution Host -> accepted provisioning route
```

Nobao continuity depends on stable identity, Jenn-governed revisions, current
representation, accountable Events, and selected identity narrative. It does
not depend on one model, prompt, session, process, device, or VCPToolBox body.

## 5. Effective Profile and Principal model

An Authenticator Profile now has:

```text
contiguous profile revision and one current head
CREATE / UPDATE / SUSPEND / RESUME / RETIRE lifecycle
immutable proof kind, controller lineage, and steward lineage
exact supported Principal classes and environments
exact verifier, controller, credential-status provider, clock, replay, and trust-anchor refs
exact LifecycleActionRef and canonical fingerprint
```

Only an `ACTIVE` exact current Profile may provision a Principal, verify a new
assertion, or support a currently effective Binding. A superseded Profile
revision cannot verify new work. F2 accepts no production Profile or key.

A Principal now has:

```text
contiguous principal revision and one current head
immutable principal_id, class, environment, and lifecycle-controller lineage
CREATE / ROTATE_CREDENTIALS / SUSPEND / RESUME / REVOKE / RETIRE lifecycle
exact Profile revision
opaque credential handles only
exact provisioning and transition actions
deterministic PrincipalAssessment
```

`REVOKED` permits only retirement; `RETIRED` is terminal. A Principal cannot
create or attest itself. Only credential rotation may replace handles or move
to a newer revision of the same Profile ID.

Every credential handle has a low-disclosure current assessment:

```text
ACTIVE
REVOKED
INDETERMINATE
```

Secret bytes, keys, tokens, cookies, biometric material, and raw proofs never
enter the Ledger or model context.

## 6. Effective M0 synthetic provisioning

M0 uses one deterministic synthetic manifest containing creation specs, not
completed subjects. This avoids a fingerprint cycle.

```text
manifest creation specs do not reference the manifest or later acceptance
Jenn separately accepts the exact manifest fingerprint
synthetic Profiles and Principals reference that accepted manifest
Rust creates only the exact listed subjects
```

The manifest cannot contain production state, real credentials, active Jenn
credentials, active host identity, real secrets, or promotion to another
environment.

## 7. Effective Binding model

A Binding subject states that one exact Principal revision may represent one
exact Actor identity revision in one exact representation-context set. It does
not grant responsibility, permission, capability, trust, or effect admission.

The effective creation order is acyclic:

```text
Binding subject
-> binding subject fingerprint
-> BindingActivationEvidence
-> BindingActivationAssessment
-> binding_activation_projection
-> ActorPrincipalBindingAssessment
-> binding_effective_current_projection
```

Binding issuance uses exactly one route:

```text
Jenn interactive bootstrap/registration
Resident-attested Agent session
accepted Service provisioning
Worker assignment handshake
accepted synthetic M0 manifest
```

The issuance route uses a `LifecycleActionRef`; bootstrap and provisioning do
not invent an Actor issuer. Binding revisions use contiguous CAS. Actor and
Principal IDs cannot change inside one Binding stream.

`BindingActivationAssessment` proves only activation evidence. It does not
prove current effectiveness.

`ActorPrincipalBindingAssessment` is the sole answer to whether the Binding may
support a new Command. It combines:

```text
current Binding head and transitions
current ACTIVE Actor identity
current ACTIVE Principal
current ACTIVE exact Authenticator Profile
all ACTIVE credential-handle assessments
ACTIVATED evidence
trusted time inside the Binding window
matching fingerprints and Event sequence
```

Only effective `ACTIVE` may represent the Actor for a new Command. Suspension,
revocation, expiry, supersession, or indeterminate evidence fails closed.

## 8. Effective responsibility model

Responsibility records accountable work ownership; it is not permission.

Every v0.1 durable Assignment is issued directly from a Jenn root direction.
`PARENT_ASSIGNMENT` is rejected. Nobao and other responsible Actors pass work
down only through Delegation.

The effective scope is:

```yaml
scope_contract_version: agents-os.responsibility-scope.v0.1-r7
workspace_id:
scope_mode: EXACT_SET
resource_refs: nonempty_sorted_exact_set
```

`DECLARED_SUBTREE`, wildcard, glob, regex, natural language, future resource,
and ambient workspace scope are rejected. Subset comparison is literal set
inclusion and cannot change with a later domain containment rule.

Assignment currentness depends on:

```text
one current Assignment head
current ACTIVE recipient identity revision
historically valid and currently CONFIRMED issuance action
no closing transition fact
current time window
exact scope and lineage fingerprints
```

It does not depend on the old issuing session, Principal, Binding, or Profile
remaining active.

## 9. Effective Delegation model

Every Delegation has one root:

```text
Jenn root direction
or one current root Responsibility Assignment
```

Every edge:

```text
names a different ACTIVE delegator and delegate Actor revision
names the exact immediate parent
retains the exact root source
narrows the exact scope and time window
decrements remaining depth exactly once
requires explicit activation
cannot weaken the Prohibited Boundary
```

At most three Delegation edges are permitted. Actor IDs may not repeat anywhere
in the chain. Parallel chains are evaluated separately and cannot be unioned.

The activation graph remains acyclic:

```text
Delegation subject
-> subject fingerprint
-> delegate acknowledgement
-> activation evidence
-> DelegationActivationAssessment
-> delegation_activation_projection
-> R1 DelegationAssessment
-> delegation_effective_current_projection
```

Activation assessment proves only activation. R1 `DelegationAssessment`, with
R7 corrections, is the only effective reducer.

Historical acknowledging or issuing session Bindings need not remain current.
Current operational dependencies are the exact Actor identities, root source,
parent Delegations, activation result, transition facts, scope/lineage, policy,
time, and fingerprints.

## 10. Effective transition model

Actor, Principal, and Authenticator Profile lifecycle changes use their own
contiguous subject revisions and transition matrices.

Binding, Assignment, Delegation, and activation-evidence administrative changes
use `GovernedStateTransitionFactV0_1`:

```text
exact target kind/ref/fingerprint
SUSPEND / RESUME / REVOKE / RENOUNCE
exact requesting action and authority basis
exact target-head and last-transition CAS
prospective effective Event sequence
reason codes and canonical fingerprint
```

The fact never edits the original subject and never impersonates its issuer.
`REVOKE` and `RENOUNCE` are terminal for the exact target revision. `RESUME`
works only after suspension. There is no restore-from-revocation operation.

Jenn may revoke any covered target. Target-specific rules additionally allow
the proper steward, lifecycle controller, issuer/delegator, bound Actor, or
delegate to perform only the transitions assigned to that role. A mechanical
incident route can only move toward suspension or revocation.

Parent closure affects descendants through the effective reducer; it does not
fabricate child Events.

## 11. Effective historical-action model

The validity of a committed issuance action is evaluated at its commit Event.
Normal later lifecycle changes do not retroactively invalidate it:

```text
session end
Binding expiry
routine Principal or Binding replacement
credential rotation
issuer identity update
```

Historical assurance is:

```text
CONFIRMED
CHALLENGED
INVALIDATED
INDETERMINATE
```

Only a revisioned, CAS-protected `CompromiseImpactFactV0_1` may challenge or
invalidate an explicit complete set of action refs. An incident mechanism may
challenge; Jenn or the same-or-higher identity steward may invalidate or clear
a challenge. Invalidated impact is terminal. No historical Event is deleted or
rewritten, and compensation remains the owning domain's responsibility.

## 12. Effective authentication and Command handoff

F2 owns the identity/responsibility side of action attribution. F3 owns Command
payload schemas, canonical intake, inbox/replay, atomic commit, and crash
outcome.

An `AuthenticatedActorActionRef` is accepted only when F3 proves one immutable
Command envelope and one atomically committed intake fact. Pending, rejected,
or outcome-indeterminate intake cannot establish stewardship, issuance, or
activation evidence.

For a new Command, the runtime must reconstruct rather than trust caller claims:

```text
current Actor identity
current effective Principal Binding
AuthenticationAssertion and assessment
current responsibility source and Delegation lineage
one current Prohibited Behavior List revision
```

Authentication proves who submitted exact bytes. It does not grant permission,
responsibility, TaskPermit, or effect admission.

## 13. Effective single Prohibited Boundary

F2 defines exactly one project-level Prohibited Behavior List and no permission
ladder, allowlist, risk matrix, trust score, or per-Actor variant.

```text
no prohibition matches -> F2 raises no permission stop; owning domain continues
prohibition matches -> stop and record the matched identifier
required facts remain unresolved -> stop and report the boundary
```

Only Jenn may revise the project-level list through an explicit governance
revision, below applicable higher constraints. Delegation, relationship,
urgency, old approval, or prior success cannot change it.

The canonical list itself is still a separate implementation-readiness
dependency and is not created by F2 acceptance.

## 14. Effective canonicalization

All F2 fingerprints use SHA-256, RFC 8785 JCS, Unicode 15.1 NFC, schema-known
fields only, explicit array order, duplicate rejection, and domain separation.

Fields named `*_fingerprint` use the R4 FingerprintEnvelope rules. SHA-derived
stable replay/evidence scalar IDs use the R5 64-character lowercase-hex string
rules. Parent formulas insert the exact declared digest string, not raw bytes or
an alternate envelope.

All F2 JSON numbers use the R7 canonical scalar profile after parsing to
ECMAScript Number / IEEE 754 binary64:

```text
safe uint 0..2^53-1
positive revision 1..2^53-1
Event sequence 0..2^53-1
UTC milliseconds 0..2^53-1
positive duration 1..2^53-1
delegation maximum edges exactly 3
remaining depth 0..2
assignment redelegation depth 0..3
-0, parsed non-integer, overflow, non-finite, and wrong type rejected
```

Original numeric token spelling is not retained. Parsed-equal tokens insert the
same JCS number.

## 15. Effective current-state authority map

| Fact or question | Sole authority |
|---|---|
| Actor revision head | Actor identity current-head pointer under Rust CAS |
| Actor effective status | `ActorIdentityAssessment` |
| Profile revision head | Authenticator Profile current-head pointer under Rust CAS |
| Profile effective status | `AuthenticatorProfileAssessmentR7` |
| Principal revision head | Principal current-head pointer under Rust CAS |
| Principal effective status | `PrincipalAssessmentR7` |
| Binding activation | `binding_activation_projection` |
| Binding usable for new Command | `binding_effective_current_projection` from `ActorPrincipalBindingAssessmentR7` |
| Assignment effective state | R1/R2 Assignment assessment with R7 corrections |
| Delegation activation | `delegation_activation_projection` |
| Delegation effective state | R1 `DelegationAssessment` with R7 corrections |
| historical action assurance | `HistoricalActionValidityAssessmentR7` |
| administrative transition | current `GovernedStateTransitionFactV0_1` projection |
| prohibited-line result | one current list revision checked during F3 intake |

No activation assessment is an effective-currentness authority. No UI,
materialization, caller, model, or Memory becomes a canonical writer.

## 16. Superseded readings that must not be implemented

The following readings are explicitly non-effective:

```text
BindingActivationAssessment alone means a Binding is currently usable
DelegationActivationAssessment alone means a Delegation is currently effective
R3 binding_current_projection is an independent current-state authority
R3 delegation_current_projection is an independent current-state authority
an issuing session Binding must remain active forever
routine session expiry retroactively invalidates committed Assignment/Delegation
a revoker must impersonate the original issuer in a new subject revision
an unspecified revocation fact may change current state
PARENT_ASSIGNMENT is permitted in v0.1
DECLARED_SUBTREE is permitted in v0.1
only BindingScope context_revision needs a numeric range
synthetic M0 subjects may self-provision or reference a circular manifest
F2 acceptance creates a production Authenticator or canonical prohibited list
```

## 17. Recovery and required validation

Recovery must reproduce every current head, lifecycle transition, transition
fact, activation projection, effective projection, historical assurance,
scope/lineage fingerprint, scalar admission, and Event sequence from immutable
facts. A fork, missing Event, ambiguous authority, unknown schema, mismatched
fingerprint, or unavailable required controller/time source produces
`INDETERMINATE` and stops affected intake.

Required future tests include lifecycle CAS races, activation/effective-state
separation, ordinary session expiry, compromise impact, cross-issuer revocation,
delegate renunciation, exact-set scope, single lineage depth/cycle, every
numeric boundary, synthetic manifest acyclicity, cross-writer JCS bytes, and
crash-recovery projection equality.

## 18. Remaining external dependencies

Even if Jenn later accepts the R1-R7 bundle, these remain separate:

```text
canonical Prohibited Behavior List convergence
F3 Command intake and Rust single-writer contract
F4 TaskPermit, host authentication, and effect fencing
production Authenticator and key-provisioning review
Jenn implementation authorization
Jenn runtime-activation authorization
```

This materialization grants none of them.
