# AGENTS OS Phase 5A M0-A Plan R3 Atomic Independent Review Package v0.1

Date: 2026-07-19
Status: FIXED_FOR_FRESH_FULL_ATOMIC_INDEPENDENT_REVIEW
Owner: Jenn
Agent steward: Nobao

## Review unit

```yaml
review_unit: PHASE_5A_M0A_PLAN_BUILD_PROFILE_V0_1_R3_ATOMIC_BUNDLE
atomic: true
partial_review: forbidden
subjects: 18
precedence:
  - R3_explicit_replacements
  - R2_all_other_clauses
  - R1_all_other_clauses
```

Manifest:

```text
control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r3-atomic-independent-review-package-v0.1.manifest.yaml
SHA-256: d9af2c8b8f8e469edf64d6897f16e1730d32897a7f9ea1333f1a3b2efb194c49
```

## Required independent proof

The reviewer must independently verify all 164 inputs and prove or refute:

1. all 11 R3 owner replacements correspond to existing R2 obligations and
   provide semantically complete F3/F5/F6 transaction and persistence owners;
2. admitted F3 Commands commit Inbox, Envelope, facts, Current State, Event,
   replay and optional ledger-only intent in one all-or-zero transaction;
3. the effective 18-table schema is executable and rejects cross-kind,
   cross-logical identity, wrong fingerprint, wrong attempt/intent, cross-Task,
   branch, revision-gap and predecessor-substitution graphs;
4. Resident lifecycle uses exactly the frozen six states;
5. F5 first-apply guard is committed before call/receipt and stored-first
   accounting contains exact Event and call-authorization identities/counts;
6. every state transaction shares the inherited pointer-CAS-before-Event crash
   order with deferred foreign keys and rollback-all failure;
7. source and installed tree digests use byte-identical preimages while the
   package manifest is verified separately;
8. the VCP direct module ABI exports `processToolCall(args)`, not the outer
   manager's three-argument method;
9. no implementation, database, plugin or runtime authority was introduced.

## Fixed commands

```bash
python3 control-plane/registry/validate-phase5a-m0a-plan-r3-closure.py \
  control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-plan-r3-closure-witness-v0.1.json \
  --self-test

python3 control-plane/registry/build-phase5a-m0a-plan-r3-closure-witness.py \
  /tmp/phase5a-r3-review-rebuilt.json

cmp /tmp/phase5a-r3-review-rebuilt.json \
  control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-plan-r3-closure-witness-v0.1.json
```

Author result:

```yaml
semantic_owner_replacements: 11/11
effective_tables: 18/18
persistence_negatives: 12/12
materialization_negatives: 8/8
fixed_mutations_rejected: 16/16
database_occurrence_count: 0
terminal_outcome: NOT_EXECUTED
```

This is author evidence only. The independent reviewer should execute the
effective DDL in an isolated in-memory test and construct coordinated
cross-table cases rather than relying on structural inspection alone.

## Result and stop

Only `PASS_NO_BLOCKER` or `BLOCK` is allowed. Partial acceptance is forbidden.
A PASS does not freeze the plan. Jenn must decide plan freeze separately, and
plan freeze still does not authorize implementation.

