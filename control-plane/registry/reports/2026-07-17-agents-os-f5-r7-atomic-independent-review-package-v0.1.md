# AGENTS OS F5 R7 Fresh Full Atomic Independent Review Package v0.1

Date: 2026-07-17  
Status: fixed for fresh independent review  
Owner: Jenn  
Agent steward: Nobao

## Review Unit

```yaml
review_unit: F5_OUTBOX_DELIVERY_RECOVERY_V0_1_R7_ATOMIC_BUNDLE
review_mode: fresh_full_atomic_hash_bound_independent_review
atomic: true
partial_review: forbidden
subject_count: 28
declared_input_count: 64
required_questions: 38
required_adversarial_checks: 38
fixed_commands: 8
```

```text
manifest=control-plane/registry/reports/2026-07-17-agents-os-f5-r7-atomic-independent-review-package-v0.1.manifest.yaml
manifest_sha256=2c867bcab4810f5625caa3cb7a649209e19fc53eab34d6ba16737dcce8d14031
```

The reviewer must review all R1-R7 subjects as one atomic unit with precedence
R7, R6, R5, R4, R3, R2, then R1 for clauses not replaced later.

## R7 Focus

R7 changes exactly one validation rule:

```text
every Event/call/other count
→ exact JSON integer type
→ boolean is never an integer
→ non-negative safe range
→ only then equality, mapping, reducer or digest trust
```

The fixed R6 source fixture contains 37 count occurrences. Thirty-four have a
value of zero or one. The reviewer must independently replace every occurrence
with a JSON boolean, recompute the affected section/root fingerprints and
confirm all 37 instances reject. The reviewer must also reproduce the original
four-field R6 mutation and confirm rejection.

The review must confirm that:

- the current `AGENTS.md` bytes are bound by the R7 manifest while the R6
  manifest remains immutable historical evidence;
- R5 receipt/arm and R6 first-apply result/accounting semantics are unchanged;
- all 37 source count occurrences and 37 R7 evidence rows require exact
  integer type;
- canonical request-payload integer checks remain closed;
- no permission system, upstream authority reducer, delivery state, receipt
  type, retry model, provider path, implementation or F6 semantic was added.

## Independence

The R7 author self-review is hash-only evidence. The reviewer may verify its
path/hash but must not read its content or conclusion. Prior reviews are
finding lineage only and cannot substitute for fresh R1-R7 judgment. No
subject, manifest or prior review may be modified.

## Required Procedure

1. Recompute the manifest and all 64 input hashes.
2. Fully read all 28 subjects and all 11 authority inputs.
3. Run all eight fixed commands and reproduce R7 builder byte equality.
4. Answer all 38 required questions and 38 adversarial checks.
5. Independently test exact integer typing plus inherited receipt, arm,
   first-apply, schema, precedence, graph and accounting seams.
6. Write only the manifest-declared final review YAML.

## Result Contract

`PASS_NO_BLOCKER` is allowed only with zero blocker, major, minor and unresolved
findings. A validator PASS cannot substitute for semantic review.

PASS stops F5 revision and prepares a Jenn-only atomic freeze decision surface;
it does not accept or freeze F5. BLOCK preserves all R1-R7 fixed bytes. R8 is
not preplanned and requires a new independent reproducible security
counterexample.

## Non-Authorization

This package authorizes no F5 acceptance/freeze, F6, implementation, database,
runtime, production authentication, provider/service, real handoff/dispatch/
effect, Git delivery, release, deployment, publication, formal Memory or
private raw memory access.
