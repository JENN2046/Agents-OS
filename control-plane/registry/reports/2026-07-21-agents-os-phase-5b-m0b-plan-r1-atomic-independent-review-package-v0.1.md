# AGENTS OS Phase 5B M0-B Plan R1 Atomic Independent Review Package v0.1

Date: 2026-07-21
Owner: Jenn
Agent steward: Nobao
Status: FIXED_FOR_FRESH_FULL_ATOMIC_HASH_BOUND_INDEPENDENT_REVIEW

## 1. Review Unit

```yaml
review_unit: PHASE_5B_M0B_PLAN_BUILD_PROFILE_V0_1_R1_ATOMIC_BUNDLE
atomic: true
partial_review: forbidden
subjects: 4
authority_inputs: 29
author_evidence: 4
declared_inputs: 37
```

The canonical manifest is:

```text
control-plane/registry/reports/2026-07-21-agents-os-phase-5b-m0b-plan-r1-atomic-independent-review-package-v0.1.manifest.yaml
SHA-256: d0fc1cb73406d5999339d20154e244a7d1bc5226b7f3b295fe53de63c1e3d3ea
```

The reviewer must review the complete manifest-bound unit. The author
self-review is evidence only and cannot substitute for independent judgment.

## 2. Review Objective

Determine whether the four subjects form a decision-complete, implementable,
privacy-preserving Phase 5B M0-B plan while preserving the already frozen F1-F8
contracts and the durable Phase 5A implementation boundary.

The plan must extend `extensions/agents-os-resident`; it must not create a
second plugin, service, writer, SQLite connection, permission system, identity
authority, Task authority, Command authority or effect authority.

## 3. Required Reproduction

The reviewer must:

1. independently hash and fully read all 37 declared inputs;
2. read all four subjects as one atomic unit;
3. execute all four commands in the manifest;
4. verify deterministic witness byte reproduction;
5. independently construct coordinated, fully re-signed adversarial cases;
6. distinguish semantic rejection from stale-hash or unpropagated-reference
   rejection;
7. report exactly `PASS_NO_BLOCKER` or `BLOCK`.

The fixed author evidence currently reports:

```yaml
decision_cases: 28
row_fingerprints_verified: 28
section_fingerprints_verified: 3
fully_resigned_mutations_rejected: 30/30
terminal_outcome: NOT_ACTIVATED
```

## 4. Highest-Risk Review Surfaces

The reviewer should attack at least these seams:

- implicit conversation, thought, relationship, trust, urgency or PBL no-match
  becoming authority;
- Session discard/remain/ephemeral paths producing canonical writes;
- candidate or handoff content changing without a new immutable revision;
- a phantom candidate outside canonical candidate history;
- Home writing Task state or authenticating/committing/replaying Command;
- F8 owner commitments being replaced, recomputed or bypassed;
- the synthetic F3 command definition becoming production usable;
- raw Session content, private Memory, provider responses, credentials or
  secret-like data entering the ledger or diagnostics;
- a sixth N-API method, second ledger writer, second SQLite connection,
  sidecar, VCPToolBox core diff or automatic retry/promotion path;
- schema-v2 transaction or crash recovery leaving an unowned window;
- fixture equality or caller-provided labels substituting for semantic
  derivation.

## 5. Acceptance Rule

`PASS_NO_BLOCKER` is allowed only if all declared bytes are available and
matched, every required command passes, the complete atomic unit is internally
consistent, and fresh coordinated attacks find neither a favorable invalid
path nor legal-input over-rejection.

Any missing input, hash mismatch, partial review, validator mismatch, internal
contradiction, implementation impossibility, authority expansion, privacy leak,
unowned crash/replay decision or automatic implementation start requires
`BLOCK`.

## 6. Governance Boundary

This review package does not authorize:

```yaml
Phase_5B_plan_acceptance_or_freeze: false
Phase_5B_implementation_start: false
Rust_or_JavaScript_or_NAPI_or_SQL_change: false
database_creation_or_migration: false
VCPToolBox_change_or_start: false
plugin_enablement: false
runtime_activation: false
production_authentication: false
private_Memory_access: false
provider_sensing_or_real_effect: false
```

A successful independent review closes only the review gate. Jenn retains the
separate atomic plan-freeze decision and any later implementation-start
decision.
