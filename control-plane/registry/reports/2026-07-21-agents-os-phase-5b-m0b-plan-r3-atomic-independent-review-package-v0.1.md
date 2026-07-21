# AGENTS OS Phase 5B M0-B Plan R3 Atomic Independent Review Package v0.1

## Review unit

```yaml
review_unit: PHASE_5B_M0B_PLAN_BUILD_PROFILE_V0_1_R3_ATOMIC_BUNDLE
review_mode: FRESH_FULL_ATOMIC_HASH_BOUND_INDEPENDENT_REVIEW
atomic: true
partial_review: forbidden
subjects: 12
authority_inputs: 48
author_evidence: 13
declared_inputs: 73
precedence:
  - R3_explicit_replacements
  - R2_all_other_clauses
  - R1_all_other_clauses
```

The canonical manifest is:

```text
control-plane/registry/reports/2026-07-21-agents-os-phase-5b-m0b-plan-r3-atomic-independent-review-package-v0.1.manifest.yaml
```

Its SHA-256 and the offline ZIP SHA-256 are distributed beside the fixed
package, outside the manifest digest cycle.

## Exact review purpose

R3 closes only the five fixed R2 blockers:

1. derive the exact five-method public N-API inventory from sealed `lib.rs`;
2. make candidate genesis and predecessor lineage internally valid;
3. materialize the exact sealed F3 Command, assertion, submission and request
   shapes while keeping the new command type prospective and runtime-unusable;
4. make all three composite foreign keys implementable with an exact parent
   composite unique key;
5. prove the fourteen R2 independent cases through target semantics with the
   exact-fixture seal disabled.

## Required independent work

The reviewer must fully read and hash all 73 manifest inputs, run all 12 fixed
commands from an extracted package without `.git`, and independently exercise
coordinated re-signing cases. Author self-review and validator PASS are evidence
only and cannot substitute for independent judgment.

The most important test is the separation:

```text
validate_semantics(mutated_and_fully_resigned_fixture)
  -> named target semantic rejection

validate_fixed_fixture(mutated_and_fully_resigned_fixture)
  -> byte-seal mismatch, reported separately
```

Any R2 regression rejected only by the byte seal is a blocker.

## Allowed result

```yaml
allowed_results:
  - PASS_NO_BLOCKER
  - BLOCK
```

`PASS_NO_BLOCKER` may close only the independent review gate. It does not accept
or freeze the Phase 5B plan and does not start implementation.

## Boundaries

```yaml
Phase_5B_plan_frozen: false
Phase_5B_implementation_started: false
implementation_authorized: false
Rust_JavaScript_NAPI_SQLite_or_VCPToolBox_change: false
database_or_runtime_activation: false
provider_or_production_authentication: false
private_Memory_or_sensing: false
real_effect: false
```
