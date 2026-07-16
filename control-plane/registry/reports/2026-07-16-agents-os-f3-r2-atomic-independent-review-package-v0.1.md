# AGENTS OS F3 R2 Atomic Independent Review Package v0.1

Date: 2026-07-16
Status: `READY_FOR_FRESH_HASH_BOUND_INDEPENDENT_REVIEW`
Owner: Jenn
Agent steward: Nobao
Scope: fixed F3 R1+R2 atomic contract bundle

## 1. Review unit

```yaml
review_unit_id: F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R2_ATOMIC_BUNDLE
subject_count: 2
precedence:
  - R2_explicit_replacements
  - R1_all_other_clauses
partial_review: forbidden
review_mode: fresh_full_atomic_hash_bound_independent_review
author_self_review_is_independent: false
F3_accepted: false
F3_frozen: false
F4_started: false
implementation_authorized: false
runtime_activation_authorized: false
```

The exact subjects are:

```text
R1
path: control-plane/registry/drafts/2026-07-16-agents-os-f3-resident-singleton-napi-identity-continuity-v0.1-r1.draft.md
sha256: e439b3178984ac28ae584a961e2e0dc2248002592f0fb571e5e0db05d117a70e
lines: 1050

R2
path: control-plane/registry/drafts/2026-07-16-agents-os-f3-resident-singleton-napi-identity-continuity-v0.1-r2-amendment.draft.md
sha256: 4cd066dacf0f73d21566640a25c5cf5e90ca800ed4a793827c5088936703b236
lines: 1172
```

R1 remains fixed. R2 is a narrow amendment and must never be reviewed alone.

## 2. Canonical manifest

```text
path: control-plane/registry/reports/2026-07-16-agents-os-f3-r2-atomic-independent-review-package-v0.1.manifest.yaml
sha256: f8aabb05463f95ae72727330515822765b35586a8a9f35fbbca7346289330fee
```

The manifest is the canonical hash-bound pointer bundle. It binds 17 files:
both subjects, ten governing inputs, and five review/amendment-lineage records.
The presentation report is excluded from the manifest to avoid a digest cycle.

## 3. Why R2 exists

The fresh R1 review returned:

```yaml
result: BLOCK
blocker_count: 0
major_count: 6
minor_count: 0
requires_R2: true
```

R2 accepts all six findings for correction:

| Finding | Required closure | R2 surface |
|---|---|---|
| M01 | persist rejected Command disposition and replay it after gate changes | Sections 2.1-2.7 |
| M02 | use exact frozen F2 `AUTHENTICATED` value | Section 3 |
| M03 | total continuity reducer over all frozen Actor results | Section 4 |
| M04 | ledger-external monotonic witness and explicit restore lineage | Sections 5.1-5.5 |
| M05 | closed acyclic intake and replay schemas | Sections 2.2-2.7 |
| M06 | construct pending Delegation before activation | Sections 6.1-6.6 |

The author self-review is bound only as lineage. Its conclusion is not printed
in the canonical manifest and must not be read or relied upon by the reviewer.

## 4. Fresh-review rule

The reviewer must:

```text
start from the canonical manifest
recompute all 17 listed file digests over complete regular-file bytes
read both R1 and R2 completely
apply R2 precedence only to its explicit replacements
use the old R1 review as finding lineage, not as substitute judgment
derive the new result independently
return BLOCK on a hash mismatch, missing input, partial review, or unresolved ambiguity
```

The reviewer must not read or rely upon the author self-review conclusion. Its
digest is lineage evidence only.

## 5. Required semantic surfaces

### Intake and replay

Verify the complete graph and computation order:

```text
CanonicalCommand fingerprint
-> independent global intake/replay refs
-> gate result
-> committed context when admitted
-> envelope containing only the independent intake ref
-> action/activation ref
-> terminal intake fingerprint
-> replay-entry fingerprint
```

Verify that the global `command_id` specialization is stricter than, and does
not violate, the accepted `(source, command_id)` minimum. Verify first
`COMMITTED`, `REJECTED`, and gate-derived `INDETERMINATE` dispositions, changed
bytes/source, lost response, deterministic reducer rejection, and integrity
failure are mutually exclusive and total.

### Frozen F2 seam and continuity

Verify that ordinary authentication uses only
`AuthenticationAssessmentV0_1R15.assessment = AUTHENTICATED`; `VERIFIED` remains
limited to principal-control proof assessment. Verify all eight exact frozen
Actor assessment values and an unknown value have one fail-closed continuity
result. A Jenn decision must not override non-`ACTIVE` F2 currentness.

### Singleton and anti-rollback

Verify the three linked layers:

```text
OS-enforced exclusive process lock
one current canonical authority epoch owned by the incarnation
one durable ledger-external committed witness generation bound to that epoch
```

Review the full reservation/commit/abandon crash reducer, coherent old-ledger
restore, witness/ledger mismatch, new-incarnation behavior after finalizing an
old crash window, and exact Jenn restore decision binding. The witness is a
contract primitive, not implementation authorization.

### Constructive synthetic M0

Verify the declared genesis can produce:

```text
synthetic Jenn root Actor/Binding/root direction
synthetic coordinator Actor/Binding
AUTHENTICATED synthetic assessments
READY Resident identity + lock/epoch/witness
LEDGER_ONLY DELEGATION_ISSUANCE Command
exact pending frozen F2 Delegation
separate DELEGATION_ACTIVATION_ACK
identical replay, altered replay conflict, restart, and concurrent-start denial
```

No bare fixture label may replace a complete F2 proof graph. No real credential,
provider, host, service, runtime, database, private Memory, TaskPermit, or
external effect may enter the witness.

### Downstream and non-authorization boundary

Verify F4 still owns TaskPermit, host identity, and effect fencing; F5 still
owns Outbox delivery/retry/reconciliation; F6 still owns Validation current
decisions. R2 must not authorize Rust/JavaScript implementation, database work,
runtime/service activation, production authentication, provider execution,
public API/MCP expansion, commit, push, or merge.

## 6. Required adversarial checks

At minimum, attempt all 22 manifest checks:

```text
two live writers satisfying different authority halves
coherent old ledger restore after a newer committed witness
crash after witness reservation before epoch commit
crash after epoch commit before witness finalize
duplicate, forked, or reused witness generation
restore decision bound to another backup or witness state
model/session continuity without canonical identity evidence
all frozen Actor values plus an unknown value
JavaScript/direct SQL/read pool as second authority path
unknown N-API method/schema/field reaching a reducer
caller-supplied context/envelope/intake/Event/action/generation
AuthenticationAssertion and Command fingerprint cycle
content-addressed intake-ref cycle
rejected Command retry after gate change
same command_id with changed source or payload
lost response causing a second mutation
revocation and Command using different watermarks
activation before constructive issuance
pending Delegation self-authorizing activation
synthetic fixture importing real authority or effect
F3 envelope/issuance treated as F4 admission
reserved Outbox/reconcile method performing work
```

## 7. Required result

Write exactly:

```text
control-plane/registry/reviews/
2026-07-16-yellow-agents-os-f3-r2-full-atomic-independent-review.yaml
```

The result must conform to
`agents-os.hash-bound-independent-review.v0.1` and include:

```yaml
manifest:
  path: control-plane/registry/reports/2026-07-16-agents-os-f3-r2-atomic-independent-review-package-v0.1.manifest.yaml
  sha256: f8aabb05463f95ae72727330515822765b35586a8a9f35fbbca7346289330fee
  all_input_hashes_verified: true | false

subjects:
  R1:
    sha256: e439b3178984ac28ae584a961e2e0dc2248002592f0fb571e5e0db05d117a70e
    bytes_reviewed_unchanged: true | false
  R2:
    sha256: 4cd066dacf0f73d21566640a25c5cf5e90ca800ed4a793827c5088936703b236
    bytes_reviewed_unchanged: true | false

result: PASS_NO_BLOCKER | BLOCK
summary:
  blocker_count:
  major_count:
  minor_count:
  requires_R3: true | false

mandatory_counts:
  identity_spoofing:
  dual_writer:
  circular_proof:
  authority_expansion:
  fail_open_currentness:
  replay_ambiguity:
  downstream_boundary_leak:
  M0_impossibility:
  internal_contradiction:
```

Each finding must include exact section evidence, a concrete counterexample,
impact, and required correction. `PASS_NO_BLOCKER` is valid only with 18/18
required questions and 22/22 adversarial checks answered and no remaining
blocker, major, or unresolved contract ambiguity.

## 8. Post-review routing

```text
BLOCK
  -> preserve R1/R2 bytes and review lineage
  -> author finding disposition
  -> R3 only when required
  -> new complete hash-bound fresh review

PASS_NO_BLOCKER
  -> register fixed review result
  -> prepare Jenn-only atomic accept/freeze decision surface
```

Neither route automatically accepts or freezes F3, starts F4, or authorizes
implementation/runtime/database/authentication/provider/service work.

## 9. Reproduction

Parse the manifest and recompute each listed `path` digest over the entire
regular file with no canonicalization. The manifest's own SHA-256 is external.
Any mismatch invalidates this package until a new manifest is created.
