# AGENTS OS Phase 5B M0-B Plan R2 Atomic Independent Review Package v0.1

Date: 2026-07-21
Owner: Jenn
Agent steward: Nobao
Status: FIXED_FOR_FRESH_FULL_ATOMIC_HASH_BOUND_INDEPENDENT_REVIEW

## 1. Review Unit

```yaml
review_unit: PHASE_5B_M0B_PLAN_BUILD_PROFILE_V0_1_R2_ATOMIC_BUNDLE
atomic: true
partial_review: forbidden
subjects:
  R1_immutable: 4
  R2_new: 4
  total: 8
authority_inputs: 43
author_evidence: 8
declared_inputs: 59
```

The canonical manifest is:

```text
control-plane/registry/reports/2026-07-21-agents-os-phase-5b-m0b-plan-r2-atomic-independent-review-package-v0.1.manifest.yaml
SHA-256: 32020e90e2d7b52cd3c46893af57674c8f90c0bee516b829299e95e7cc524380
```

R2 has precedence only for its explicit replacements. All other R1 clauses
remain in force. Partial review or acceptance is forbidden.

## 2. Narrow Closure Objective

The reviewer must decide whether R2 closes exactly the four preserved R1
findings:

1. the exact implementable source inventory and single-writer routes;
2. the exact F8 handoff to F3 payload, Command ID, request and replay seam;
3. a constructive candidate/history/owner/writer/transaction/crash graph;
4. total schema-v2 columns, keys, constraints, indexes, triggers, migration,
   CAS and failpoints.

R2 must not create a second permission, identity, Task, Command, Validation or
effect authority and must not expand the public five-method N-API surface.

## 3. Required Reproduction

The reviewer must:

1. independently hash and fully read all 59 declared inputs;
2. confirm the four R1 subjects, R1 manifest, independent review and fixed
   lineage remain byte-identical;
3. read all eight subjects as one atomic unit;
4. execute all eight manifest commands in an extracted directory without
   `.git`;
5. reproduce both R1 and R2 fixtures byte-for-byte;
6. independently construct coordinated, fully re-signed attacks;
7. distinguish semantic rejection from stale-hash or unpropagated-reference
   rejection;
8. report exactly `PASS_NO_BLOCKER` or `BLOCK`.

The fixed author evidence reports:

```yaml
R1_decision_cases: 28/28
R1_fully_resigned_mutations: 30/30_REJECTED
R2_graph_nodes: 31/31
R2_graph_edges: 29/29
R2_graph_sections: 9/9
R2_fully_resigned_mutations: 32/32_REJECTED
R2_parser_probes: 5/5_REJECTED
terminal_outcome: NOT_ACTIVATED
```

## 4. Highest-Risk Review Surfaces

The independent reviewer should attack at least:

- omissions or invented files in the 21-file exact source inventory;
- an internal N-API frame change leaking into a sixth public method;
- a second writer, connection, plugin, service or sidecar;
- owner commitment or candidate-history same-revision rewrites;
- a phantom candidate or altered handoff tuple entering F3;
- two distinct handoffs sharing a Command ID;
- changed canonical request bytes replaying as an exact duplicate;
- incomplete schema columns, FKs, checks, indexes or immutability triggers;
- metadata publication before DDL completion;
- partially visible precommit crash states or automatic post-handoff retry;
- caller claims or fixture anchors substituting for semantic derivation;
- synthetic evidence becoming runtime usable.

## 5. Acceptance Rule

`PASS_NO_BLOCKER` is allowed only if all 59 bytes match, all eight commands
pass, the eight subjects form one internally consistent and implementable plan,
and fresh coordinated attacks find neither a favorable invalid path nor legal
input over-rejection.

Any missing input, hash mismatch, partial review, implementation impossibility,
authority expansion, unowned write/replay/recovery decision, schema or crash
gap, privacy leak or automatic implementation start requires `BLOCK`.

## 6. Governance Boundary

```yaml
Phase_5B_plan_acceptance_or_freeze: false
Phase_5B_implementation_start: false
Rust_JavaScript_NAPI_or_SQL_change: false
database_creation_or_migration: false
VCPToolBox_change_or_start: false
plugin_enablement: false
runtime_activation: false
production_authentication: false
private_Memory_access: false
provider_sensing_or_real_effect: false
commit_or_push_by_review_package: false
```

A successful review closes only the R2 independent-review gate. Jenn retains
the separate plan-freeze and implementation-start decisions.
