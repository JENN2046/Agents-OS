# Review: docctl doctor Backlog Classification

Date: 2026-07-01
Status: reviewed
Scope: classification of `docctl doctor` unregistered-file backlog

## Result

Current `docctl doctor` scan reports:

```text
registries=3 documents=77 scanned_files=139 unregistered=66 warn=66 fail=0
```

The backlog has no hard failure. It is a cleanup queue.

Classification:

```text
should_register: 15
should_ignore: 1
historical_archive: 50
total: 66
```

## Should Register

These should become first-class document registry entries because they are
current source files, examples, templates, or registry pilots that users or
tools may reasonably look for.

### Registry Directory

- `control-plane/registry/drafts/document-registry.v0.1.example.yaml`
- `control-plane/registry/drafts/agents-os-governance-registry-v0.1-draft.md`
- `control-plane/registry/drafts/agents-os-governance-registry.v0.1.example.yaml`
- `control-plane/registry/drafts/documentation-scorecard-v0.1-draft.md`
- `control-plane/registry/examples/extensions.example.yaml`
- `control-plane/registry/examples/protected-paths.example.yaml`
- `control-plane/registry/templates/decision-record-template-v0.1.md`
- `control-plane/registry/templates/docs/README.template.md`
- `control-plane/registry/templates/docs/archive-note.template.md`
- `control-plane/registry/templates/docs/decision-record.template.md`
- `control-plane/registry/templates/docs/how-to.template.md`
- `control-plane/registry/templates/docs/policy.template.md`
- `control-plane/registry/templates/docs/reference.template.md`
- `control-plane/registry/templates/docs/runbook.template.md`

### Task Envelope Directory

- `control-plane/task-envelope/drafts/document-registry.v0.1.example.yaml`

Recommended handling:

- register as `draft`, `example`, `template`, or `registry`
- keep authority wording explicit
- do not promote drafts to active just because they are registered

## Should Ignore

This should not be forced into the draft Document Registry by `docctl doctor`.
It belongs to active authority / governance registry handling instead.

- `control-plane/registry/WORKSPACE_REGISTRY.yaml`

Recommended handling:

- add an explicit ignore/known-external-scope policy to `docctl doctor`
- later build a separate active registry doctor if needed
- do not modify `WORKSPACE_REGISTRY.yaml` during this backlog cleanup

## Historical Archive

These should be preserved as historical evidence, but should not be promoted
one by one into current active document objects.

Recommended handling:

- create archive notes or grouped archive registry entries
- do not delete
- do not bulk-move without a separate archive plan

### Superseded Or Historical Drafts

- `control-plane/registry/drafts/2026-06-30-decision-governance-control-plane-layer.draft.md`
- `control-plane/registry/drafts/2026-06-30-governance-drafts-active-confirmation-package.md`
- `control-plane/registry/drafts/agents-os-decision-record-template-v0.1-draft.md`
- `control-plane/registry/drafts/agents-os-golden-paths-v0.1-draft.md`
- `control-plane/registry/drafts/agents-os-governance-scorecard-v0.1-draft.md`

### Registry Evidence Backlog

- `control-plane/registry/receipts/2026-06-30-a2-golden-path-example-scorecard-validator.md`
- `control-plane/registry/receipts/2026-06-30-a2-governance-registry-scorecard-validator-v0.1.md`
- `control-plane/registry/receipts/2026-06-30-a3c-governance-active-promotion.md`
- `control-plane/registry/receipts/2026-06-30-yellow-documentation-governance-draft.md`
- `control-plane/registry/receipts/2026-06-30-yellow-first-decision-record-draft.md`
- `control-plane/registry/receipts/2026-06-30-yellow-governance-active-confirmation-package.md`
- `control-plane/registry/receipts/2026-06-30-yellow-governance-operating-drafts-v0.1.md`
- `control-plane/registry/receipts/2026-06-30-yellow-governance-registry-draft-v0.1.md`
- `control-plane/registry/receipts/2026-07-01-yellow-documentation-governance-implementation-v0.1.1.md`
- `control-plane/registry/receipts/2026-07-01-yellow-documentation-governance-implementation-v0.1.md`
- `control-plane/registry/reviews/2026-06-30-a2-golden-path-example-scorecard-validator.review.md`
- `control-plane/registry/reviews/2026-06-30-a2-governance-registry-scorecard-validator-v0.1.review.md`
- `control-plane/registry/reviews/2026-06-30-a3c-governance-active-promotion.review.md`
- `control-plane/registry/reviews/2026-06-30-yellow-documentation-governance-draft.review.md`
- `control-plane/registry/reviews/2026-06-30-yellow-first-decision-record-draft.review.md`
- `control-plane/registry/reviews/2026-06-30-yellow-governance-active-confirmation-package.review.md`
- `control-plane/registry/reviews/2026-06-30-yellow-governance-operating-drafts-v0.1.review.md`
- `control-plane/registry/reviews/2026-06-30-yellow-governance-registry-draft-v0.1.review.md`
- `control-plane/registry/reviews/2026-07-01-yellow-documentation-governance-implementation-v0.1.1.review.md`
- `control-plane/registry/reviews/2026-07-01-yellow-documentation-governance-implementation-v0.1.review.md`

### Task Envelope Evidence Backlog

- `control-plane/task-envelope/receipts/2026-06-30-a2-example-task-envelope-loop.md`
- `control-plane/task-envelope/receipts/2026-06-30-a2-task-envelope-loop-runner-v0.1.md`
- `control-plane/task-envelope/receipts/2026-06-30-a2-task-envelope-v0.1.md`
- `control-plane/task-envelope/receipts/2026-06-30-a2-task-envelope-validator-v0.1.md`
- `control-plane/task-envelope/receipts/2026-06-30-task-envelope-loop-2026-06-30-example-local-task-envelope-loop.md`
- `control-plane/task-envelope/reviews/2026-06-30-a2-example-task-envelope-loop.review.md`
- `control-plane/task-envelope/reviews/2026-06-30-a2-task-envelope-loop-runner-v0.1.review.md`
- `control-plane/task-envelope/reviews/2026-06-30-a2-task-envelope-v0.1.review.md`
- `control-plane/task-envelope/reviews/2026-06-30-a2-task-envelope-validator-v0.1.review.md`

### Life Core Evidence Backlog

- `control-plane/policies/life-core/receipts/2026-06-30-a2-life-core-module-split.md`
- `control-plane/policies/life-core/receipts/2026-06-30-a2-policy-router-external-write-guard.md`
- `control-plane/policies/life-core/receipts/2026-06-30-a2-policy-router-guard-hardening.md`
- `control-plane/policies/life-core/receipts/2026-06-30-a2-policy-router-rule-tightening.md`
- `control-plane/policies/life-core/receipts/2026-06-30-a2-policy-router.md`
- `control-plane/policies/life-core/receipts/2026-06-30-a2-progressive-workflow-stage-classification.md`
- `control-plane/policies/life-core/receipts/2026-06-30-a2-progressive-workflow.md`
- `control-plane/policies/life-core/receipts/2026-07-01-yellow-documentation-governance-pilot-3-life-core-fix.md`
- `control-plane/policies/life-core/reviews/2026-06-30-a2-life-core-module-split.review.md`
- `control-plane/policies/life-core/reviews/2026-06-30-a2-policy-router-external-write-guard.review.md`
- `control-plane/policies/life-core/reviews/2026-06-30-a2-policy-router-guard-hardening.review.md`
- `control-plane/policies/life-core/reviews/2026-06-30-a2-policy-router-rule-tightening.review.md`
- `control-plane/policies/life-core/reviews/2026-06-30-a2-policy-router.review.md`
- `control-plane/policies/life-core/reviews/2026-06-30-a2-progressive-workflow-stage-classification.review.md`
- `control-plane/policies/life-core/reviews/2026-06-30-a2-progressive-workflow.review.md`
- `control-plane/policies/life-core/reviews/2026-07-01-yellow-documentation-governance-pilot-3-life-core-fix.review.md`

## Recommended Order

1. Register the 15 `should_register` files first.
2. Add one explicit `docctl doctor` ignore rule for `WORKSPACE_REGISTRY.yaml`.
3. Create grouped archive notes for the 50 historical files.
4. Only after that, decide whether `docctl doctor` should support an ignore
   policy file or an archive registry.

## Boundary

This classification does not authorize:

- modifying `WORKSPACE_REGISTRY.yaml`
- bulk moving or deleting archive files
- automatic registry repair
- external writes
- runtime/provider calls
- formal Memory registration
