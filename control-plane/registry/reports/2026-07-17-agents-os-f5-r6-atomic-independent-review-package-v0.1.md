# AGENTS OS F5 R6 Fresh Full Atomic Independent Review Package v0.1

Date: 2026-07-17  
Status: fixed for fresh independent review  
Owner: Jenn  
Agent steward: Nobao

## Review Unit

```yaml
review_unit: F5_OUTBOX_DELIVERY_RECOVERY_V0_1_R6_ATOMIC_BUNDLE
review_mode: fresh_full_atomic_hash_bound_independent_review
atomic: true
partial_review: forbidden
subject_count: 24
declared_input_count: 56
required_questions: 33
required_adversarial_checks: 33
fixed_commands: 7
```

```text
manifest=control-plane/registry/reports/2026-07-17-agents-os-f5-r6-atomic-independent-review-package-v0.1.manifest.yaml
manifest_sha256=24e5381a4a98629666d3de99046ed9934101b7ee98a19ec222a78396b0826f7f
```

The reviewer must review all R1-R6 subjects as one atomic unit with precedence
R6, R5, R4, R3, R2, then R1 for clauses not replaced later.

## R6 Focus

R6 restores exactly one guard:

```text
NO_EXISTING_ARM + ELIGIBLE_PROOF_PRECONDITION
→ APPLIED / ARMED_FIRST_APPLY / 1 Event / 1 call

NO_EXISTING_ARM + NOT_ELIGIBLE
→ REJECTED / FIRST_APPLY_NOT_ELIGIBLE / 0 Event / 0 call
```

The reviewer must independently reproduce the R5 counterexample by changing
only the eligible first-apply raw input to `NOT_ELIGIBLE`, preserving the
applied derived output, and recomputing the section/root fingerprints. The R6
validator must reject it. The inverse mutation must also reject.

The review must confirm that:

- receipt replay semantics remain the R5 bound-byte semantics;
- arm identity equality still occurs before lookup branching;
- eligibility does not alter exact replay, changed bytes or lookup
  indeterminate outcomes;
- the guard is not an Actor/Task permission level or new authority source;
- no delivery state, receipt type, retry model, provider path or F6 semantic
  was added.

## Independence

The R6 author self-review is hash-only evidence. The reviewer may verify its
path/hash but must not read its content or conclusion. Prior reviews are
finding lineage only and cannot substitute for fresh R1-R6 judgment. No
subject, manifest or prior review may be modified.

## Required Procedure

1. Recompute the manifest and all 56 input hashes.
2. Fully read all 24 subjects and all 11 authority inputs.
3. Run all seven fixed commands and reproduce R6 builder byte equality.
4. Answer all 33 required questions and 33 adversarial checks.
5. Independently attack first-apply eligibility plus prior receipt, arm,
   schema, precedence, graph and accounting seams.
6. Write only the manifest-declared final review YAML.

## Result Contract

`PASS_NO_BLOCKER` is allowed only with zero blocker, major, minor and
unresolved findings. A validator PASS cannot substitute for semantic review.

PASS stops F5 revision and prepares a Jenn-only atomic freeze decision surface;
it does not accept or freeze F5. BLOCK preserves all R1-R6 fixed bytes. R7 is
not preplanned and requires a new independent reproducible security
counterexample.

## Non-Authorization

This package authorizes no F5 acceptance/freeze, F6, implementation, database,
runtime, production authentication, provider/service, real handoff/dispatch/
effect, Git delivery, release, deployment, publication, formal Memory or
private raw memory access.
