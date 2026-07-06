# Yellow-Zone Receipt: Governance Operating Drafts v0.1

Receipt ID: `yellow-governance-operating-drafts-v0.1-2026-06-30`
Date: 2026-06-30
Executor: Nobao
Classification: `yellow_zone_draft`
Scope: `control-plane/registry/`

## Action

Added three local governance operating drafts:

- Golden Paths
- Decision Record Template
- Governance Scorecard

## Why This Is Yellow

- These drafts may shape future AGENTS OS governance workflow.
- They define repeatable paths and checks.
- They are local-only and explicitly not active authority data.
- They do not modify `WORKSPACE_REGISTRY.yaml`.

## Files Added

- `drafts/agents-os-golden-paths-v0.1-draft.md`
- `drafts/agents-os-decision-record-template-v0.1-draft.md`
- `drafts/agents-os-governance-scorecard-v0.1-draft.md`
- `receipts/2026-06-30-yellow-governance-operating-drafts-v0.1.md`
- `reviews/2026-06-30-yellow-governance-operating-drafts-v0.1.review.md`

## Files Updated

- `README.md`
- `drafts/agents-os-governance-registry-v0.1-draft.md`
- `drafts/agents-os-governance-registry.v0.1.example.yaml`

## Boundary

- Did not modify `WORKSPACE_REGISTRY.yaml`.
- Did not mark any draft as active.
- Did not write to external systems.
- Did not call runtime, provider, plugin, or paid services.
- Did not read or store secrets, private memory raw text, or provider raw
  responses.
- Did not register formal Memory.

## Validation Plan

- Confirm the new draft files exist.
- Confirm the Governance Registry YAML example still parses.
- Run task-envelope loop fixture tests.
- Run life-core policy-router fixture tests.
- Confirm no Python `__pycache__` files remain under `control-plane/`.

## Result

- New draft files exist.
- Governance Registry YAML example parsed successfully: `objects=7`.
- Registered draft candidates now include:
  - `governance-golden-paths`
  - `governance-decision-record-template`
  - `governance-scorecard`
- Task-envelope loop fixture tests passed: `cases=3 failures=0`.
- Existing life-core policy-router fixture tests passed: `cases=17 failures=0`.
- No Python `__pycache__` files were left under `control-plane/`.
- Decision Record template outer code fence was adjusted to preserve nested
  code blocks.

## Continuation

`COMPLETED`
