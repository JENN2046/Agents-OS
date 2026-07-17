# AGENTS OS F5 R3 Atomic Independent Review Package v0.1

Status: fixed review instructions; not an acceptance or freeze decision  
Date: 2026-07-17  
Review unit: `F5_OUTBOX_DELIVERY_RECOVERY_V0_1_R3_ATOMIC_BUNDLE`

## 1. Review the manifest, not this presentation file

The canonical byte inventory is:

```text
control-plane/registry/reports/2026-07-17-agents-os-f5-r3-atomic-independent-review-package-v0.1.manifest.yaml
```

Recompute the manifest SHA-256 and all 32 declared input hashes. Read all 12
subjects completely. Partial review is forbidden. The R3 author self-review is
hash-only author evidence and its content or conclusion must not be read.

## 2. Required judgment

Perform a fresh judgment over the effective reading:

```text
R3 explicit replacements
-> R2 all other clauses
-> R1 all other clauses
-> bound F1/F2/F3/F4 authority inputs
```

The R1 and R2 reviews are finding lineage only. They cannot substitute for a
fresh review of all fixed subject bytes.

## 3. Seven closure gates

The review must independently decide whether R3 closes exactly:

1. recursive closed schema/JCS value validation before hashing;
2. receipt compatibility separated from application/currentness;
3. arm replay relation derived from stored/submitted state;
4. 147 pairs executed as 294 raw orderings;
5. semantically valid nonauthority scenario separated from shape examples;
6. exactly 10 × 10 = 100 transition trials;
7. six coherent graph-level identity-formula mutations.

Do not treat a builder/validator mirror, prefilled expected value, self-consistent
hash or author PASS as independent proof. Mutate fully re-signed in-memory copies
where useful; do not modify fixed subjects.

## 4. Required commands

Run every command in the manifest. The R3 validator must report at least:

```yaml
schema_profile_count: 16
schema_shape_example_count: 16
precedence_unordered_pair_count: 147
precedence_ordering_trial_count: 294
arm_state_derivation_case_count: 4
receipt_compatibility_case_count: 25
receipt_currentness_case_count: 10
transition_state_count: 10
transition_case_count: 100
schema_invalid_resigned_mutations_rejected: 8
duplicate_key_probe_rejected: true
graph_level_identity_mutations_rejected: 6
proof_mutations_rejected: 6
```

Builder reproduction must be byte-equal to the fixed R3 fixture.

## 5. Safety boundary

Review requires no web access, runtime source, service, provider, database,
credential, secret, private memory or `state-private/` access. Do not execute a
real handoff, claim, arm, provider call or physical effect.

No subject creates an Actor/Task permission level or recomputes F1/F2/F3/F4
authority. A regression in either boundary is a blocker.

## 6. Output

Write exactly one independent result to:

```text
control-plane/registry/reviews/2026-07-17-yellow-agents-os-f5-r3-full-atomic-independent-review.yaml
```

Use `PASS_NO_BLOCKER` only when blocker, major, minor and unresolved ambiguity
counts are all zero. Otherwise use `BLOCK`, identify exact counterexamples and
state the narrow required correction. Do not accept, freeze or implement F5;
Jenn owns any later atomic freeze decision.
