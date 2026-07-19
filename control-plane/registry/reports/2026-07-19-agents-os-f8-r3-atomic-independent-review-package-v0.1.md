# AGENTS OS F8 R3 Fresh Full Atomic Independent Review Package v0.1

Date: 2026-07-19
Owner: Jenn
Agent steward: Nobao
Status: `FIXED_FOR_FRESH_FULL_ATOMIC_HASH_BOUND_INDEPENDENT_REVIEW`

## 1. Review unit

```yaml
review_unit: F8_HOME_TO_ORCHESTRATOR_MINIMUM_INTERFACE_V0_1_R3_ATOMIC_BUNDLE
atomic: true
partial_review: forbidden
subjects:
  R1: 4
  R2: 4
  R3: 4
  total: 12
authority_inputs: 35
author_evidence: 2
declared_inputs: 49
manifest: control-plane/registry/reports/2026-07-19-agents-os-f8-r3-atomic-independent-review-package-v0.1.manifest.yaml
manifest_sha256: 485d62b70cd39dbe3ab62c2fadefb1c544c8b4d275b30d6d719b5d10a9c1cb1e
```

R1 and R2 subjects and manifests are immutable inputs. R3 has precedence only
for its explicit replacement clauses.

## 2. Required integrity gate

The reviewer must independently:

1. hash the exact downloadable ZIP and `MANIFEST.yaml`;
2. reject traversal, duplicate paths, symlinks or CRC failures;
3. verify `CHECKSUMS.sha256` and `ARCHIVE_MAP.yaml`;
4. verify and fully read all 49 declared inputs;
5. execute all eight manifest commands from a plain extracted directory with
   no `.git` dependency;
6. treat both author self-reviews as nonindependent evidence only.

An inaccessible ZIP, unavailable mandatory input or unexecuted command cannot
produce `PASS_NO_BLOCKER`.

## 3. Semantic review target

R3 must prove both:

```text
owner assessment
+ exact owner-issued immutable revision commitment
-> result may be consumed without F8 recomputation

acknowledgement candidate input
-> exact canonical F8 candidate-history resolution
-> exact F3 owner assessment and commitment resolution
-> low-disclosure acknowledgement
```

The reviewer must distinguish a trusted owner/candidate source commitment from
ordinary fixture inventory anchors. Fully re-signing the caller-controlled
fixture graph must not rewrite either trusted source.

The synthetic anchors are test-only. They must not become a production owner
store, permission source, identity source, Command authority or runtime input.

## 4. Required independent attacks

At minimum, independently construct complete coordinated re-signing attacks:

```text
same assessment id/revision with changed F7 result and current-head
same assessment rewrite plus owner commitment rewrite
same assessment id/revision with changed F3 outcome
same F3 outcome rewrite plus owner commitment rewrite
commitment ref/revision/fingerprint substitution
commitment bound to another owner or assessment
caller-created commitment absent from trusted owner source
candidate absent from canonical history
phantom candidate added to caller graph and all dependencies re-signed
candidate revision/fingerprint substitution
acknowledgement context changed with matching self-signed assessment
minimum watermark below, equal and higher cases
old trusted_event_sequence field substituted for the R3 field
trusted owner or candidate anchor deletion/addition/reorder/substitution
unknown/missing/wrong-type fields with ordinary fixture anchors disabled
duplicate JSON key, float, NaN and integer-as-boolean
runtime_usable, Command, Task or effect authority set true
nonzero real runtime/database/provider/private-Memory/sensing/effect occurrence
```

The reviewer must report whether rejection came from the intended owner-source,
candidate-history, schema or boundary rule—not from an unpropagated hash,
ordinary fixture anchor or exception.

## 5. Watermark rule

The fixed R3 rule is deliberately:

```text
based_on_event_sequence >= minimum_trusted_event_sequence
```

Equality and a higher owner watermark must pass. Only a lower watermark fails
closed. `F8-R2-B03` was withdrawn as a contract misread and must not be revived
as an equality requirement.

## 6. Authority boundary

The reviewer must BLOCK any path that lets F8:

```text
issue or revise owner commitments
recompute F1/F2/F3/policy/Jenn owner results
create a second permission or identity system
create Task or Command authority
promote synthetic evidence to runtime authority
start Phase 5A or authorize implementation/runtime/database/provider/auth
read private Memory, sense, record or execute a real effect
```

## 7. Allowed result

```yaml
allowed_results:
  - PASS_NO_BLOCKER
  - BLOCK
```

The output must report exact ZIP and manifest hashes, 49/49 input hashes and
full reads, 8/8 commands, independent attack counts, favorable invalid path
count, finding counts and `requires_R4`.

Even `PASS_NO_BLOCKER` does not accept or freeze F8. It only opens a future
Jenn-owned atomic freeze decision surface.
