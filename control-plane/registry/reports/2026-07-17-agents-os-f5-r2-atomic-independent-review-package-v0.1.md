# AGENTS OS F5 R2 Atomic Independent Review Package v0.1

Date: 2026-07-17  
Status: `READY_FOR_FRESH_FULL_ATOMIC_HASH_BOUND_INDEPENDENT_REVIEW`  
Owner: Jenn  
Agent steward: Nobao

## 1. Review unit

Review the exact R1+R2 eight-subject unit bound by:

```text
control-plane/registry/reports/2026-07-17-agents-os-f5-r2-atomic-independent-review-package-v0.1.manifest.yaml
SHA-256 0a7c56a03adfa28fd50974766e5bff01d016dd9d18bed5c6b43abd25c40b7c7d
```

The precedence is `R2 explicit replacements`, then every non-conflicting R1
clause. Partial review and partial acceptance are forbidden. The reviewer must
read all eight subjects and recompute all 24 declared hashes.

The author self-review must not be opened or used as judgment. Its bytes may be
hashed only.

## 2. R2 correction surface

R2 closes the four R1 findings without changing R1 bytes:

```text
arm request identity plus four-state replay relation
exact duplicate = replay first accounting, zero Event, zero call
changed bytes under one request identity = integrity conflict

explicit claim, lease and first-arm failure precedence
147 pairwise failure combinations

total receipt kind/status matrix
canonical receipt disposition and currentness precedence

16 canonical effective-schema instances
six effective derived identities
100 state-transition pairs
28 structured adversarial inputs
29 fully re-signed semantic mutations
```

## 3. Highest-risk questions

The reviewer must independently determine:

- whether arm request identity stays invariant across retries and cannot be
  caller-selected;
- whether exact replay and changed-byte conflict are derived from canonical
  writer state rather than caller booleans;
- whether exact replay can ever produce a second Event or call;
- whether every simultaneous claim, lease or arm failure has one normative
  primary reason and the complete sorted reason set;
- whether `TRANSPORT_ACK + SUCCEEDED` and every other forbidden receipt pair
  deterministically reject;
- whether old epochs, stale fences or invalid transitions can advance current
  projection or Task;
- whether builder and validator really recompute object fingerprints, all six
  identities, transitions, attacks and mutations independently;
- whether F5 has recreated any F1/F2/F3/F4 authority, permission ladder,
  identity source, policy evaluator or effect authority.

## 4. Reproduction

```bash
PYTHONDONTWRITEBYTECODE=1 python3 \
  control-plane/registry/validate-f5-r1-synthetic-delivery-recovery.py

PYTHONDONTWRITEBYTECODE=1 python3 \
  control-plane/registry/validate-f5-r2-full-effective-delivery-recovery.py

tmp="$(mktemp)"
PYTHONDONTWRITEBYTECODE=1 python3 \
  control-plane/registry/build-f5-r2-full-effective-delivery-recovery.py \
  --output "$tmp"
cmp -s "$tmp" \
  control-plane/registry/examples/2026-07-17-agents-os-f5-r2-full-effective-delivery-recovery-v0.1.json
rm -f "$tmp"
```

Expected R2 validator surface:

```yaml
result: PASS_NO_BLOCKER
schema_profile_count: 16
canonical_instance_count: 16
derived_identity_count: 6
pairwise_precedence_case_count: 147
arm_replay_case_count: 4
receipt_compatibility_case_count: 25
transition_case_count: 100
adversarial_case_count: 28
negative_mutations_rejected: 29
fixture_canonical_sha256: 9fafe36c7f8c186b86f669db2ee6547bafb95d4130308089691ffe9185f0b07a
accepted_real_handoff_count: 0
armed_dispatch_count: 0
runtime_consumable_count: 0
external_effect_count: 0
provider_call_count: 0
raw_secret_count: 0
terminal_outcome: NOT_EXECUTED
```

Validator PASS is necessary but insufficient. The reviewer must inspect the
effective R1+R2 semantics and may return only `PASS_NO_BLOCKER` or `BLOCK`.

## 5. Required output

```text
control-plane/registry/reviews/2026-07-17-yellow-agents-os-f5-r2-full-atomic-independent-review.yaml
```

The result must follow the manifest output contract. Any hash mismatch,
partial read, unresolved ambiguity, replay second-call path, invalid receipt
pair acceptance, non-total precedence, validator overclaim, upstream-authority
recomputation or synthetic authority conversion requires `BLOCK` and
`requires_R3=true`.

## 6. Non-authorization

This package does not accept or freeze F5, start F6, authorize implementation,
create a database, start Resident/dispatcher/Host/service/provider, enable
production authentication, consume a real F4 handoff, execute an effect, write
formal Memory, or authorize Git delivery, release, deploy, publish or tag.
