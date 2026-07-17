# AGENTS OS F5 R1 Atomic Independent Review Package v0.1

Date: 2026-07-17
Status: `READY_FOR_FRESH_FULL_ATOMIC_HASH_BOUND_INDEPENDENT_REVIEW`
Owner: Jenn
Agent steward: Nobao

## 1. Review instruction

Review the exact four-subject unit bound by:

```text
control-plane/registry/reports/2026-07-17-agents-os-f5-r1-atomic-independent-review-package-v0.1.manifest.yaml
```

Return only `PASS_NO_BLOCKER` or `BLOCK` under
`agents-os.hash-bound-independent-review.v0.1`. Partial review and partial
acceptance are forbidden. The author cannot act as the independent reviewer.

The reviewer must first hash all 16 declared inputs and read all four subject
files completely. The author self-review may be used only after fresh subject
judgment and cannot substitute for it.

## 2. Atomic subjects

```text
normative contract
  control-plane/registry/drafts/2026-07-17-agents-os-f5-outbox-delivery-recovery-v0.1-r1.draft.md
  sha256 96a04ae8fd83006255bf7cb5fc3902bfd07b50e22d01736bb3a36b531766e79f

deterministic fixture builder
  control-plane/registry/build-f5-r1-synthetic-delivery-recovery.py
  sha256 5b67f302b7ec40ceb6b59aa23e62340adbfdf661aea0f058c13fa3a89cd51793

fixed synthetic fixture
  control-plane/registry/examples/2026-07-17-agents-os-f5-r1-synthetic-delivery-recovery-v0.1.json
  sha256 3fcc7a8358c165224c2e5e66ed947e80939c67afbb3154150acb5e2b695a3281

independent semantic validator
  control-plane/registry/validate-f5-r1-synthetic-delivery-recovery.py
  sha256 83934d2045b68b492b12fec2f973b8d7b3e3a82492b9454336ae6dcb15d5296f
```

## 3. What F5 R1 owns

R1 defines only:

```text
durable F4-handoff-to-Outbox materialization
pre-arm claim and lease ownership with epoch/CAS fencing
one-time dispatch arm at the F4/F5 physical-effect seam
attempt, ACK, terminal receipt and late-fact accounting
dead-letter and UNKNOWN reconciliation
crash-window and startup recovery
```

F5 consumes F4 authority. It does not create or recompute Task, Actor,
Principal, Binding, responsibility, delegation, Resident, Command, permit,
Host authentication, policy, PBL, Jenn decision or effect scope.

The reviewer should treat any Actor/Task permission-level classification,
color/P0-P3 authority, second canonical writer, synthetic-to-production
conversion, PBL-derived permission or caller-selected idempotency key as a
blocker.

## 4. Current non-issuable production boundary

Frozen F4 R9 states that a real positive handoff remains non-issuable pending
accepted owner interfaces and current production receipts. F5 R1 preserves
that fact:

```yaml
accepted_real_handoff_count: 0
armed_dispatch_count: 0
runtime_consumable_count: 0
external_effect_count: 0
provider_call_count: 0
raw_secret_count: 0
terminal_outcome: NOT_EXECUTED
```

The fixture contains only synthetic schema metadata and reducer vectors. It is
not a standard F4 handoff, Outbox claim, dispatch arm, receipt or production
recovery record.

## 5. Highest-risk review questions

### Authority consumption

- Does every claim and arm bind a fresh F4-owned assessment rather than an F5
  reimplementation?
- Can a missing, stale, indeterminate or mismatching upstream input ever pass?
- Can labels, role names, trust, urgency, history, Green/Yellow/Red or P0-P3
  change a delivery result?

### One-time physical claim

- Is the arm fact committed once before any physical call?
- Does any arm, including one later proven `PRE_EFFECT_NOT_EXECUTED`, permit a
  second arm under the same F4 invocation? It must not.
- Is trusted time checked again immediately before adapter invocation, with no
  scheduling gap?

### Crash and retry

- Do all post-arm ambiguous windows become `UNKNOWN`?
- Are automatic replays limited to pre-arm enqueue/claim/lease work?
- Can endpoint idempotency capability be misused as retry authority?

### Accounting

- Is `ACKED` distinct from `SUCCEEDED`?
- Does `FAILED` avoid claiming that no partial effect occurred?
- Is dead-letter queue accounting rather than effect outcome or completion?
- Do exact duplicate receipts replay while changed bytes conflict?

### Recovery

- Can projection rebuild, query or reconciliation create a claim, arm, retry,
  compensation or external effect?
- Does startup finish its recovery barrier before ordinary claims?

## 6. Reproduction

```bash
PYTHONDONTWRITEBYTECODE=1 python3 \
  control-plane/registry/validate-f5-r1-synthetic-delivery-recovery.py

tmp="$(mktemp)"
PYTHONDONTWRITEBYTECODE=1 python3 \
  control-plane/registry/build-f5-r1-synthetic-delivery-recovery.py \
  --output "$tmp"
cmp -s "$tmp" \
  control-plane/registry/examples/2026-07-17-agents-os-f5-r1-synthetic-delivery-recovery-v0.1.json
rm -f "$tmp"
```

Expected validator surface:

```yaml
result: PASS_NO_BLOCKER
schema_profile_count: 13
decision_vector_count: 64
recovery_vector_count: 8
negative_mutations_rejected: 15
fixture_canonical_sha256: 63d7469c60ab4f27195c838bdaa93f203fc681db67fb79111408250d2b74fef9
accepted_real_handoff_count: 0
armed_dispatch_count: 0
runtime_consumable_count: 0
external_effect_count: 0
provider_call_count: 0
raw_secret_count: 0
terminal_outcome: NOT_EXECUTED
```

Validator PASS is necessary but insufficient. The reviewer must independently
read the contract, inspect builder/validator divergence, attack the state
machine and confirm that the fixture cannot become authority.

## 7. Required output

Write the fresh result to:

```text
control-plane/registry/reviews/2026-07-17-yellow-agents-os-f5-r1-full-atomic-independent-review.yaml
```

At minimum report:

```text
reviewer identity and independence basis
manifest path and SHA-256
16/16 hash result
4/4 complete subject read result
blocker/major/minor/unresolved counts
each required question and adversarial result
13 schema, 64 vector, 15 mutation and 8 recovery counts
builder byte equality and fixture canonical hash
all zero-authority/runtime/effect/provider/secret counts
requires_R2
```

Any hash mismatch, unavailable required input, partial read, synthetic
authority conversion, second physical arm, post-arm automatic retry, upstream
authority recomputation, crash ambiguity that retries, or unresolved semantic
ambiguity requires `BLOCK`.

## 8. Non-authorization

This package confirms only that F5 has started and R1 author bytes are fixed
for review. It does not accept or freeze F5, start F6, authorize implementation,
create a database, start Resident/Host/dispatcher/service/provider, enable
production authentication, consume a real F4 handoff, execute an effect, or
authorize Git delivery, release, deploy, publish or tag.
