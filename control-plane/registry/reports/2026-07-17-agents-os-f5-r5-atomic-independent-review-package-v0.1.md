# AGENTS OS F5 R5 Fresh Full Atomic Independent Review Package v0.1

Date: 2026-07-17  
Status: fixed for fresh independent review  
Owner: Jenn  
Agent steward: Nobao

## 1. Review Unit

```yaml
review_unit: F5_OUTBOX_DELIVERY_RECOVERY_V0_1_R5_ATOMIC_BUNDLE
review_mode: fresh_full_atomic_hash_bound_independent_review
atomic: true
partial_review: forbidden
subject_count: 20
declared_input_count: 48
required_questions: 36
required_adversarial_checks: 46
fixed_commands: 6
```

Canonical manifest:

```text
path=control-plane/registry/reports/2026-07-17-agents-os-f5-r5-atomic-independent-review-package-v0.1.manifest.yaml
sha256=54e401c18d30c1462b2a6be90a4c72f2ddd3afa44167f634532b126a24715f38
```

The reviewer must review all R1-R5 subjects as one unit. Effective precedence
is R5, then R4, R3, R2 and R1 for clauses not replaced later.

## 2. R5 Scope

R5 exists only because the fixed R4 review produced two new independently
reproducible, fully re-signed counterexamples:

1. detached receipt `kind/status` could change while the replay fingerprint
   stayed unchanged;
2. arm `LOOKUP_INDETERMINATE` could bypass stored/submitted request-ID
   equality.

R5 must prove:

```text
complete receipt payload
→ exact canonical UTF-8 bytes
→ SHA-256 fingerprint
→ independently parsed stored/submitted records
→ exact replay only on equal key + equal fingerprint + equal bytes
```

and:

```text
parse/bind submitted request
→ parse/bind stored request when present
→ require equal request identity
→ only then select lookup branch
```

The review must verify that R5 does not add delivery states, receipt types,
retry models, provider protocols, permission levels or upstream authority
reducers.

## 3. Independence Rule

The current author self-review is a hash-only input. The fresh reviewer:

- may verify its path and SHA-256;
- must not read its content or conclusion;
- must not use any prior review as a substitute for fresh R1-R5 judgment;
- may use prior reviews only to preserve finding lineage;
- must not modify any subject, manifest or earlier review.

Use a reviewer that did not author the R5 subjects.

## 4. Required Procedure

1. Recompute the manifest SHA-256.
2. Recompute all 48 declared input hashes.
3. Fully read all 20 subjects and all 11 authority inputs.
4. Read R1-R4 reviews only for finding lineage.
5. Do not read the R5 author self-review content.
6. Run all six fixed commands from the manifest.
7. Independently reproduce the R5 builder byte-equality check.
8. Independently attack both R4 counterexamples with every mutated section and
   root fingerprint recomputed.
9. Answer all 36 required questions and all 46 adversarial checks.
10. Write the result only to the manifest-declared target review path.

## 5. Required Attack Focus

The reviewer must especially test:

- adding detached `receipt_kind/effect_status` fields to an exact replay;
- changing bound submitted receipt kind/status and recomputing its bytes/hash;
- changing stored receipt bytes and recomputing its bytes/hash;
- noncanonical receipt bytes with a recomputed SHA-256;
- outer receipt keys that disagree with bound payload keys;
- different valid canonical arm request identities under lookup indeterminate;
- identity equality occurring after rather than before lookup branching;
- missing/unknown root, section, row, nested raw or payload fields;
- any regression in R1-R4 schema, reducer, precedence, graph or accounting
  proofs;
- any nonzero real handoff, claim, arm, runtime, effect, provider or secret
  count.

## 6. Allowed Results

```yaml
allowed_results:
  - PASS_NO_BLOCKER
  - BLOCK

PASS_NO_BLOCKER_requires:
  blocker: 0
  major: 0
  minor: 0
  unresolved: 0
```

A validator PASS is evidence, not a substitute for semantic review. Any
reproducible counterexample must be reported with the fixed bytes, derivation
path and exact required correction.

## 7. Governance Boundary

This package does not authorize:

```text
F5 acceptance or freeze
F6 start or semantics
implementation
database creation or write
runtime activation
production authentication
provider, service, host or physical effect
commit, push, PR, merge, release, deploy, publish or tag
formal Memory or private raw memory access
```

If the result is `PASS_NO_BLOCKER`, stop F5 revision and prepare a Jenn-only
atomic freeze decision surface. Do not freeze automatically.

If the result is `BLOCK`, preserve all fixed R1-R5 bytes. R6 is not preplanned
and may be considered only for a new independent reproducible security
counterexample.
