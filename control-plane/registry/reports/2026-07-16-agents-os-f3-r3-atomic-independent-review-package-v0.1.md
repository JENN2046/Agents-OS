# AGENTS OS F3 R3 Atomic Independent Review Package v0.1

Date: 2026-07-16  
Status: `READY_FOR_FRESH_HASH_BOUND_INDEPENDENT_REVIEW`  
Owner: Jenn  
Agent steward: Nobao  
Scope: fixed F3 R1+R2+R3 atomic contract bundle

## 1. Review unit

```yaml
review_unit_id: F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R3_ATOMIC_BUNDLE
subject_count: 3
precedence:
  - R3_explicit_replacements
  - R2_other_explicit_replacements
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

R3
path: control-plane/registry/drafts/2026-07-16-agents-os-f3-resident-singleton-napi-identity-continuity-v0.1-r3-amendment.draft.md
sha256: 8a25b247a0618ab06ef6186464405b9d137bf68967a9952647986562cb93244c
lines: 814
```

R1 and R2 remain fixed. R3 is a narrow amendment and must never be reviewed
alone.

## 2. Canonical manifest

```text
path: control-plane/registry/reports/2026-07-16-agents-os-f3-r3-atomic-independent-review-package-v0.1.manifest.yaml
sha256: ddaaf1fe8a2fae333b17971e9404e68202ce210d6ddc1d0e7c7823a3af228269
```

The manifest is the canonical review authority. It binds 23 complete regular
files: three subjects, ten governing inputs, and ten review/amendment-lineage
records. This presentation is excluded from the manifest to avoid a digest
cycle and may not substitute for the fixed bytes.

## 3. Why R3 exists

The fresh R1+R2 review returned:

```yaml
result: BLOCK
blocker_count: 0
major_count: 3
minor_count: 0
requires_R3: true
```

R3 accepts all three findings for correction:

| Finding | Required closure | R3 surface |
|---|---|---|
| M01 | disjoint no-intake readiness response and persisted terminal semantics | Sections 2.1-2.4 |
| M02 | unique global authority epoch across older-ledger restore lineages | Sections 3.1-3.5 |
| M03 | full issuance registry values and exact synthetic subject vocabulary | Sections 4.1-5.4 |

The author self-review is bound only by digest. A fresh reviewer must not read
or rely upon its content or conclusion.

## 4. Fresh-review rule

The reviewer must:

```text
start from the canonical manifest
recompute the manifest and all 23 input digests over entire-file bytes
read R1, R2, and R3 completely
apply only the explicit precedence rules
form fresh judgment before using old reviews as finding lineage
recompute both descriptor digests and the CommandTypeDefinition fingerprint
verify all 57 synthetic kinds, schema mappings, and predecessor edges
return BLOCK on mismatch, unavailable input, partial review, or unresolved ambiguity
```

## 5. Required semantic surfaces

### Pre-intake versus canonical intake

Verify the exact boundary:

```text
decode and derive Command bytes
-> public READY observation
-> one ledger-thread transaction and current recheck
-> successful READY + CONTINUOUS + witness barrier
-> replay lookup and gate result
-> canonical intake
```

Any readiness, continuity, witness, or integrity failure before the successful
barrier must write nothing and reserve no command ID. An identical request
after READY must be a first intake eligibility attempt. A genuinely persisted
`REJECTED` or gate-derived `INDETERMINATE` disposition must remain replayable.

### Authority epoch and older restore

Construct both branches:

```text
normal: ledger head = witness global H -> commit H+1
older restore: ledger head R < retained global H
  -> CAS ledger R
  -> CAS witness H
  -> commit global H+1 under one new lineage
  -> bind explicit gap R+1..H
```

Test duplicate epochs, crash windows, stale restore decisions, lineage reuse,
witness change during decision use, and later normal restart. No two retained
COMMITTED witness entries may share an epoch.

### Issuance registry closure

Recompute from the exact printed JCS bytes:

```text
payload schema SHA-256
045f1f13910b04589ca0c65e4536b3a8b253e70c37ff59d92caca6ccb51ef2c1

reducer SHA-256
4c4bac289945131cd556dd855398761cc940b150d2930b4f4453d103c1296e70

CommandTypeDefinition canonical fingerprint
549553a694a1d95f58932db1831b817f3cf4f744f4e33a73dbfc9ba233a5a07f
```

Check the owner, target kind, sorted gate refs, registry revision, failure
semantics, and F2 frozen seam. A digest match alone is insufficient if the
descriptor meaning creates authority expansion or contradicts the effective
bundle.

### Constructive synthetic M0

Verify exact cardinality and topology from all 57 manifest entries. The trace
must construct complete genesis, issuance, pending Delegation, activation,
identical replay, altered conflict, epoch-2 restart, READY continuity, and
concurrent-start denial evidence. No bare label may stand in for a schema-bound
leaf or predecessor.

### Inherited safety and downstream boundaries

Freshly recheck identity spoofing, dual writer, proof cycles, exact F2
`AUTHENTICATED`, all frozen Actor continuity inputs, revocation/currentness,
one thread/connection, and reserved methods. F4 still owns TaskPermit, host,
and fence admission; F5 owns Outbox behavior; F6 owns Validation decisions.

## 6. Required coverage

The manifest requires:

```yaml
required_questions: 20
required_adversarial_checks: 33
synthetic_enum_entries: 57
synthetic_schema_and_predecessor_mappings: 57
```

Every item needs an explicit result and evidence. Each finding needs an ID,
severity, exact section evidence, concrete counterexample, impact, and required
correction.

## 7. Required result

Write exactly:

```text
control-plane/registry/reviews/
2026-07-16-yellow-agents-os-f3-r3-full-atomic-independent-review.yaml
```

The result must conform to
`agents-os.hash-bound-independent-review.v0.1` and report:

```yaml
result: PASS_NO_BLOCKER | BLOCK
summary:
  blocker_count:
  major_count:
  minor_count:
  requires_R4: true | false

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

`PASS_NO_BLOCKER` is valid only when all hashes and derived digests match,
20/20 questions and 33/33 adversarial checks are answered, the 57/57 mapping
is complete, and no blocker, major, or unresolved contract ambiguity remains.

## 8. Post-review routing

```text
BLOCK
  -> preserve R1/R2/R3 and review bytes
  -> disposition findings
  -> R4 only if required
  -> new complete fresh hash-bound atomic review

PASS_NO_BLOCKER
  -> register the fixed result
  -> prepare a Jenn-only atomic accept/freeze decision surface
```

Neither route automatically accepts or freezes F3, starts F4, or authorizes
implementation, runtime, database, authentication, provider, service, commit,
push, PR, or merge work.

## 9. Reproduction

Parse the manifest and recompute every listed path over entire regular-file
bytes with no canonicalization. The manifest self-digest is external. Any
mismatch invalidates the package until a new package is deliberately created.
