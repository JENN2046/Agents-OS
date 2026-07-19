# AGENTS OS F8 R4 Fresh Full Atomic Independent Review Package v0.1

Date: 2026-07-19
Owner: Jenn
Agent steward: Nobao
Status: `FIXED_FOR_FRESH_FULL_ATOMIC_HASH_BOUND_INDEPENDENT_REVIEW`

## 1. Review unit

```yaml
review_unit: F8_HOME_TO_ORCHESTRATOR_MINIMUM_INTERFACE_V0_1_R4_ATOMIC_BUNDLE
atomic: true
partial_review: forbidden
subjects:
  R1: 4
  R2: 4
  R3: 4
  R4: 4
  total: 16
authority_inputs: 42
author_evidence: 3
declared_inputs: 61
manifest: control-plane/registry/reports/2026-07-19-agents-os-f8-r4-atomic-independent-review-package-v0.1.manifest.yaml
manifest_sha256: bae62380982fdfa57b81c5349897bee6edde6161c357c869018cc77e6247effb
```

R1-R3 subjects and manifests are immutable. R4 has precedence only for its
consumer nullability and all-null resolution replacements.

## 2. Required integrity gate

The reviewer must independently:

1. hash the exact downloadable ZIP and `MANIFEST.yaml`;
2. reject traversal, duplicate paths, symlinks or CRC failures;
3. verify `CHECKSUMS.sha256` and `ARCHIVE_MAP.yaml`;
4. verify and fully read all 61 declared inputs;
5. execute all eleven manifest commands from a plain extracted directory with
   no `.git` dependency; and
6. treat all three author self-reviews as nonindependent evidence only.

Any unavailable mandatory input or unexecuted command requires `BLOCK`.

## 3. Semantic target

R4 must prove the closed sum type:

```text
ALL_NULL
or
ALL_NON_NULL with exact primitive profiles
```

There are 62 other null masks. Every one must be rejected. The reviewer should
fully re-sign mutations rather than relying on stale hashes or fixture anchors.

For `ALL_NULL`, resolution must occur before owner lookup:

```text
owner-store lookup count = 0
assessment result interpreted = false
authority created = false
resolution = ASSESSMENT_CONSUMER_UNAVAILABLE
```

Required formation and acknowledgement consumers then fail closed using their
existing indeterminate outcomes.

## 4. R2 H01 compatibility

The reviewer must resolve the exact immutable R2 H01 row and prove:

```text
R4 upgraded consumer first-three-field down-projection
== exact R2 H01 assessment consumer inventory

jenn_exact_decision R4 consumer == all six null
jenn_requirement == no exact decision required
result remains CANDIDATE_FORMED
```

Also attack the opposite case: when upstream says an exact Jenn decision is
required, an all-null decision consumer must still fail closed under inherited
R2/R3 semantics.

## 5. Required independent attacks

At minimum test:

```text
all-null consumer in every allowed location
all-non-null consumer in every allowed location
all 62 mixed-null masks
one null among five non-null and one non-null among five null
unknown/missing/reordered consumer fields
wrong ref/revision/fingerprint primitive types
boolean as revision and integer as boolean
duplicate JSON key, float and NaN
all-null consumer that attempts owner lookup
all-null consumer that reuses a prior or default assessment
formation all-null changed to favorable result with all dependencies re-signed
acknowledgement all-null changed to committed with all dependencies re-signed
R2 H01 source substitution or consumer inventory substitution
R2 H01 optional Jenn consumer changed to a mixed-null tuple
R2 H01 down-projection changed while all R4 hashes are re-signed
exact-decision-required case with all-null decision consumer
unknown fields in R4 formation, acknowledgement or compatibility rows
R3 owner commitment, candidate history and watermark regression attacks
runtime, permission, Task, Command, provider, private Memory or effect flags
```

The report must distinguish target semantic rejection from stale-hash,
unpropagated-reference or exception rejection.

## 6. Boundary

R4 must not:

```text
issue or recompute upstream assessments or commitments
weaken R3 immutable owner-source or candidate-history resolution
change the minimum watermark greater-than-or-equal rule
create a permission, identity, Task or Command authority
promote synthetic evidence to runtime authority
start Phase 5A or implementation/runtime/database/provider/auth work
read private Memory, sense, record or execute a real effect
```

## 7. Allowed result

```yaml
allowed_results:
  - PASS_NO_BLOCKER
  - BLOCK
```

The output must report ZIP and manifest hashes, 61/61 input verification,
11/11 commands, independent attack counts, favorable invalid path count,
finding counts and `requires_R5`.

Even `PASS_NO_BLOCKER` does not accept or freeze F8. It only opens a future
Jenn-owned atomic freeze decision surface.

