# AGENTS OS F6 R2 Fresh Full Atomic Independent Review Package v0.1

Date: 2026-07-18  
Owner: Jenn  
Review unit: `F6_VALIDATION_REQUIREMENT_CURRENT_DECISION_V0_1_R2_ATOMIC_BUNDLE`  
Canonical manifest: `control-plane/registry/reports/2026-07-17-agents-os-f6-r2-atomic-independent-review-package-v0.1.manifest.yaml`  
Manifest SHA-256: `ba0cd9b5b21b3bb6c2792aba55b4c6534e7d59bd145fc60952916bfc5ea0d7a3`

## Review boundary

This is a fresh, full, atomic, hash-bound review of eight subjects: the four
immutable R1 subjects plus the four R2 replacement subjects. R2 clauses take
precedence only where explicit; all other R1 clauses remain effective.

Partial review or partial acceptance is forbidden. The author self-review is
evidence only and cannot substitute for independent judgment.

The reviewer must independently verify all 30 manifest inputs, fully read all
eight subjects and 21 authority inputs, and execute all four fixed commands.
Any unavailable or mismatched required input produces `BLOCK`.

## Required focus

The review must prove, rather than infer from author labels, that:

- all ten normative schemas have a real closed profile and canonical instance;
- PASS requires exact current Validation authority and exact evidence;
- every current PASSED attempt and completion use the same candidate and
  dependency context;
- Task `VERIFYING` is bound by the exact F1-owned assessment;
- all assessment subject revisions are consumed;
- Requirement predecessor, provenance, Command and Event graphs are complete;
- Jenn waiver authority binds exact decision, Command, Event and current owner
  assessment;
- the cross-object Event partial order is complete;
- evidence is a sorted, unique, exact assessed set;
- carry-forward resolves directly to an original fresh PASSED attempt;
- effectful F5 `APPLIED_CURRENT` remains supporting evidence only;
- the three complete decision outputs are independently derived and
  cross-field total;
- all R1 32 fixed mutations, all R1 P01-P18 regressions and all 12 R2 negative
  cases are executed normally and rejected for the intended semantic reason;
- no synthetic object or prospective interface is runtime or production
  authority.

## Fixed reproduction target

Expected R2 validator output includes:

```yaml
result: PASS_NO_BLOCKER
normative_schema_count: 10
normative_instance_count: 40
positive_graph_count: 3
R1_fixed_mutations_rejected: 32
R1_independent_regressions_rejected: 18
R2_additional_negatives_rejected: 12
mutation_exception_count: 0
fixture_canonical_sha256: aab2fa442b8c6f83c432e43d8fb0a90132c6a1c720a0e65be65341ed34bc7412
accepted_real_task_count: 0
task_done_mutation_count: 0
runtime_activation_count: 0
external_effect_count: 0
provider_call_count: 0
raw_secret_count: 0
terminal_outcome: NOT_EXECUTED
```

Fixed validator PASS is necessary but insufficient. The reviewer must create
additional fully re-signed consistency cases, especially by changing multiple
mutually bound objects together.

## Allowed result

```yaml
allowed_results: [PASS_NO_BLOCKER, BLOCK]
requires_R3: true_or_false
partial_review: forbidden
```

If `BLOCK`, every finding must contain a reproducible counterexample and a
narrow correction. If `PASS_NO_BLOCKER`, the result only makes the eight-subject
F6 semantic bundle eligible for Jenn's later atomic freeze decision. It does
not accept or freeze F6 automatically.

## Non-authorization

This package does not authorize F6 acceptance or freeze, F7, implementation,
runtime activation, production authentication, database or service work,
provider or effect execution, real Task/Run/Validation/Event/waiver/completion
mutation, commit, push, PR, merge, tag, release, deploy or publish.
