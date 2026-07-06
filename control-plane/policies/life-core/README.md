# AGENTS OS Life Core Local Mirror

Status: local operational mirror / reading captured
Snapshot date: 2026-06-30
Source: Notion `AGENTS OS｜生命内核 v0.1`
Source page: [private Notion page URL redacted in Git copy]

This directory stores the local policy-facing mirror of the AGENTS OS life core.
It is meant for local `control-plane` work: governance, permissions, memory,
presence, runtime boundaries, member onboarding, and loop design.

This is not a raw Notion export. It is a full-read operational mirror and
coverage ledger based on fetched Notion page content available to Codex on
2026-06-30. The Notion pages remain the upstream source of truth.

## Files

- `agents-os-life-core-v0.1.local-mirror.md`
  Operational mirror of the life core, organized for local implementation.
- `agents-os-life-core-v0.1.reading-ledger.md`
  Batch reading ledger, source URLs, fetched status, and coverage notes.
- `policy-index.json`
  Machine-readable index for local policy module discovery.
- `policy-router.py`
  Small read-only router for action classification.
- `policy-router.rules.json`
  Transparent keyword rules used by the router.
- `policy-router.md`
  Router usage, decision meanings, and known limits.
- `policy-router.fixtures.json`
  Local regression fixtures for router behavior.
- `test-policy-router.py`
  No-dependency fixture runner for the router.
- `validate-document-registry-coverage.py`
  Local read-only coverage check between `policy-index.json` and this
  directory's Document Registry pilot.
- `drafts/`
  Documentation governance pilot material for this directory.

## Documentation Status Boundary

This directory now uses a small documentation boundary:

```text
active: README, local mirror, policy modules, policy index, policy-router docs/scripts/rules/tests, and the active fixture set.
draft: drafts/ material, including the local Document Registry pilot.
example: sample material not used as the current fixture set; examples do not grant authority.
```

The policy-router fixtures are active test inputs, not active policy authority.

In this directory's Document Registry pilot, `source_of_truth` means the local
canonical file checked by local tooling. Upstream Notion source is recorded
separately as `upstream_source` where it matters.

`drafts/document-registry.v0.1.example.yaml` is Documentation Governance
Pilot 3. It checks whether the same document registry validator can cover the
life-core policy directory. It is not active authority data and does not
authorize external writes, runtime/provider calls, secret access, private
memory access, or formal Memory registration.

## Policy Modules

The current executable policy modules are:

- `root-principles.md`
- `house-rules.md`
- `memory-rules.md`
- `members-and-rooms.md`
- `a2a-relations.md`
- `permission-levels.md`
- `standing-authorization.md`
- `activation-package.md`
- `evidence-levels.md`
- `runtime-boundaries.md`
- `cockpit-cards.md`
- `growth-rules.md`
- `presence-and-sensing.md`
- `loops-and-pilot.md`
- `progressive-workflow.md`

Each module uses the same local shape:

- policy id
- status
- source anchor
- scope
- executable rules
- gates
- hard denials
- receipt or review requirements

## A2 Control-Plane Loop

The first local A2 control-plane loop for this directory is recorded in:

- `receipts/2026-06-30-a2-life-core-module-split.md`
- `reviews/2026-06-30-a2-life-core-module-split.review.md`

The first local A2 loop for the policy router is recorded in:

- `receipts/2026-06-30-a2-policy-router.md`
- `reviews/2026-06-30-a2-policy-router.review.md`

The A2 loop for tightening the policy router and adding fixtures is recorded in:

- `receipts/2026-06-30-a2-policy-router-rule-tightening.md`
- `reviews/2026-06-30-a2-policy-router-rule-tightening.review.md`

The A2 loop for hardening external-write / provider-response guards is recorded
in:

- `receipts/2026-06-30-a2-policy-router-guard-hardening.md`
- `reviews/2026-06-30-a2-policy-router-guard-hardening.review.md`

The A2 loop for the progressive workflow first version is recorded in:

- `receipts/2026-06-30-a2-progressive-workflow.md`
- `reviews/2026-06-30-a2-progressive-workflow.review.md`

The A2 loop for progressive workflow stage classification is recorded in:

- `receipts/2026-06-30-a2-progressive-workflow-stage-classification.md`
- `reviews/2026-06-30-a2-progressive-workflow-stage-classification.review.md`

## Policy Router

The local router is a read-only helper. It does not execute actions and does
not authorize actions by itself.

Example shape:

```text
python3 control-plane/policies/life-core/policy-router.py --action "split local life-core policy docs"
```

Fixture tests:

```text
python3 control-plane/policies/life-core/test-policy-router.py
```

Router decisions:

- `allowed`: action appears allowed at the routed permission level, with stated
  evidence.
- `blocked`: action is not authorized by current life-core policy.
- `needs_activation`: action needs a higher gate, explicit authorization, or a
  full Activation path before execution.
- `proposal_only`: action is A4/P3b-style; only a proposal or preflight may be
  produced.
- `needs_classification`: router did not find enough signal; use manual Review.

## Authority Boundary

- Notion is the upstream knowledge source.
- This directory is the local control-plane mirror.
- The root workspace `AGENTS.md` and higher-priority runtime instructions still
  govern local execution.
- This mirror does not authorize secret access, external writes, provider calls,
  production actions, browser login-state actions, deletion, or permission
  escalation.

## Current Local Interpretation

AGENTS OS has two foundations:

- Life foundation: common life, long-term relationship, trust, memory,
  boundaries, responsibility, and Agent-to-Agent relation.
- Engineering foundation: VCPToolBox / VCPChat / local runtime as body,
  interface, tool nervous system, and execution substrate.

The local implementation should therefore start from life-core policies and
only then wire runtime capabilities through permission, activation, evidence,
review, and memory gates.
