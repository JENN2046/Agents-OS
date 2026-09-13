# control-plane/registry

Navigation revision: `2026-09-13.1`. Start with [root AGENTS.md](../../AGENTS.md)
for operating rules. [WORKSPACE_MAP.md](../../WORKSPACE_MAP.md) and its inventory
own the current machine/source/deployment observations; `WORKSPACE_REGISTRY.yaml`
retains project authority declarations, not proof of installed locations.
The new orientation documents and ops inventory are outside this directory's
existing Document Registry pilot; their explicit validation is recorded in the
[orientation receipt](../../ops/reports/workspace-orientation-20260913/README.md).

Purpose:
- Hold AGENTS OS registry guidance, authority registry data, and example
  registry material.
- Keep example registry material separate from active registry state.

Contains:
- `WORKSPACE_REGISTRY.yaml`
- `GOLDEN_PATHS.md`
- `DECISION_RECORDS.md`
- `SCORECARD.md`
- `VALIDATOR_BOUNDARY_REVIEW_CHECKLIST.md`
- `decisions/`
- `drafts/`
- `examples/extensions.example.yaml`
- `examples/protected-paths.example.yaml`
- `examples/2026-06-30-golden-path-new-governance-object-scorecard-validator.md`
- `templates/`
- `templates/docs/`
- `validate-governance-registry.py`
- `test-governance-registry-validator.py`
- `validate-document-registry.py`
- `test-document-registry-validator.py`
- `validate-federated-document-registry.py`
- `test-federated-document-registry-validator.py`
- `path_boundary.py`
- `docctl.py`
- `test-docctl-doctor.py`
- `archive-notes/`
- `runbooks/`
- `receipts/`
- `reviews/`

Must not contain:
- secret values
- private credentials
- full runtime data
- unreviewed high-risk capability grants

Interfaces:
- input: workspace inventory, extension manifests, governance decisions
- output: machine-readable registry files and example material
- observed static consumer: `ops/validation/validate-workspace.sh`
- declared or future consumers: Codex prompts, extension loader, governance
  layer

Security boundary:
- Registry material may record paths, identifiers, policy names, and variable
  names.
- Registry material must not record real secret values.
- Permission expansion requires review.
- Registry data does not authorize remote actions, validation execution,
  executable-bit changes, permission expansion, or consumer integration.

Examples versus authority:
- Root-level guidance files such as `GOLDEN_PATHS.md`, `DECISION_RECORDS.md`,
  and `SCORECARD.md` are active local guidance after Jenn confirmation.
- Files under `decisions/` are accepted or superseded local decision records.
- Files under `templates/` are active local templates.
- Files under `examples/` are examples only.
- Example files must not be treated as active registry state.
- Files under `drafts/` are proposals only.
- Draft files must not be treated as active registry state.
- `WORKSPACE_REGISTRY.yaml` is the active authority registry data file.
- Authority data does not prove that every declared consumer is integrated.

Active local guidance:
- `GOLDEN_PATHS.md`
  is the active local route guide for common AGENTS OS governance work.
- `DECISION_RECORDS.md`
  is the active local guidance for recording why governance decisions changed.
- `SCORECARD.md`
  is the active local guidance for registry object health checks.
- `VALIDATOR_BOUNDARY_REVIEW_CHECKLIST.md`
  is the active local checklist for reviewing local validators and checkers.
- `templates/decision-record-template-v0.1.md`
  is the active local Decision Record template.
- `decisions/2026-06-30-governance-control-plane-layer.md`
  is the accepted local Decision Record for this governance control-plane layer.
- `runbooks/docctl-operations-runbook-v0.1.md`
  is the active local runbook for operating `docctl` document-governance
  commands.

Active guidance does not authorize external writes, runtime execution, provider
calls, formal Memory registration, secret access, or P3 bypass.

Drafts:
- `drafts/agents-os-documentation-governance-v0.1-draft.md`
  proposes advanced documentation governance for future large-scale AGENTS OS
  documentation.
- `drafts/agents-os-documentation-governance.v0.1.example.yaml`
  is a draft document-object metadata example.
- `drafts/document-registry.v0.1.example.yaml`
  is a draft/example machine-readable document registry for this directory
  pilot. It is not active authority data.
- `drafts/documentation-scorecard-v0.1-draft.md`
  is a draft documentation health-check rule list.
- `drafts/federated-document-registry-v0.1-draft.md`
  proposes the Step 4 registry-of-registries shape for directory-owned
  Document Registries.
- `drafts/federated-document-registry.v0.1.example.yaml`
  is a draft/example machine-readable federation over the three current
  directory Document Registry pilots.
- `drafts/2026-06-30-governance-drafts-active-confirmation-package.md`
  asks Jenn which governance drafts should be promoted toward active local use.
- `drafts/2026-06-30-decision-governance-control-plane-layer.draft.md`
  is the historical draft source for the accepted local Decision Record.
- `drafts/agents-os-governance-registry-v0.1-draft.md`
  proposes a local governance-object registry for AGENTS OS control-plane
  components.
- `drafts/agents-os-governance-registry.v0.1.example.yaml`
  is a machine-readable shape example for that proposal.
- `drafts/agents-os-golden-paths-v0.1-draft.md`
  proposes standard local routes for common governance work.
- `drafts/agents-os-decision-record-template-v0.1-draft.md`
  proposes a template for recording why governance decisions changed.
- `drafts/agents-os-governance-scorecard-v0.1-draft.md`
  proposes basic health checks for registered governance objects.
- Governance Registry drafts do not authorize permission expansion, external
  writes, runtime execution, provider calls, or formal Memory registration.

Golden Path examples:
- `examples/2026-06-30-golden-path-new-governance-object-scorecard-validator.md`
  replays `路线 1：新增治理部件` against the real Governance Registry Scorecard
  Validator object.

Validation:
- YAML syntax for example files should be checked before use.
- `validate-governance-registry.py` checks the Governance Registry draft/example
  object shape and boundary fields.
- `test-governance-registry-validator.py` runs local fixture tests for the
  scorecard validator.
- `validate-document-registry.py` checks the Document Registry draft/example
  document records, canonical paths, source-of-truth paths, status wording, and
  secret-like markers.
- `test-document-registry-validator.py` runs local fixture tests for the
  document scorecard validator.
- `validate-federated-document-registry.py` checks the draft/example Federated
  Document Registry and then validates only the explicitly listed directory
  Document Registries.
- `test-federated-document-registry-validator.py` runs local fixture tests for
  the federated validator.
- `path_boundary.py` shares only local path-boundary checks across registry
  validators.
- `docctl.py doctor` runs a read-only document governance scan over explicitly
  listed Federated Document Registry entries.
- `docctl.py intake` dry-runs a route recommendation for one local document
  path before any registry write exists.
- `docctl.py impact` gives a read-only view of which registered documents are
  affected by changed local paths.
- `docctl.py score` computes a versioned read-only document-governance score
  from `docctl doctor`.
- `docctl.py trend` gives a read-only trend view over existing local snapshots.
- `docctl.py snapshot` writes one local summary snapshot for `docctl trend`.
- `docctl.py status` gives a read-only pulse over doctor, score, trend, and
  plan-fix status.
- `docctl.py plan-fix` gives a dry-run repair proposal view without applying
  repairs.
- `docctl.py apply-fix --preview` gives a read-only preview for one `plan-fix`
  proposal. Repair execution is not implemented or authorized.
- `colameta-executor-preflight.py` runs a read-only, summary-only ColaMeta
  executor preflight gate without starting services or running executors.
- `test-docctl-doctor.py` runs local fixture tests for `docctl doctor`.
- `test-docctl-intake.py` runs local fixture tests for dry-run `docctl intake`.
- `test-docctl-impact.py` runs local fixture tests for read-only `docctl impact`.
- `test-docctl-score.py` runs local fixture tests for read-only `docctl score`.
- `test-docctl-trend.py` runs local fixture tests for read-only `docctl trend`.
- `test-docctl-snapshot.py` runs local fixture tests for local `docctl
  snapshot`.
- `test-docctl-status.py` runs local fixture tests for read-only `docctl
  status`.
- `test-docctl-plan-fix.py` runs local fixture tests for dry-run `docctl
  plan-fix`.
- `test-docctl-apply-fix-preview.py` runs local fixture tests for read-only
  `docctl apply-fix --preview`.
- `test-colameta-executor-preflight.py` runs local fixture tests for the
  read-only ColaMeta executor preflight gate.
- `validate-workspace.sh` exists as a local validator file, but execution still
  requires separate authorization.
- Registry validation references in this README are documentation, not runnable
  commands.

Local scorecard check:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-governance-registry.py
```

Local scorecard fixture tests:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-governance-registry-validator.py
```

Local document registry check:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py
```

Local document registry fixture tests:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-document-registry-validator.py
```

Local federated document registry check:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py
```

Local federated document registry fixture tests:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-federated-document-registry-validator.py
```

Local docctl doctor:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
```

Local docctl doctor fixture tests:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-docctl-doctor.py
```

Local docctl intake dry-run:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py intake <path>
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py intake <path> --json
```

Local docctl intake fixture tests:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-docctl-intake.py
```

Local docctl impact view:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py impact <path> [<path> ...]
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py impact <path> --json
```

Local docctl impact fixture tests:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-docctl-impact.py
```

Local docctl score:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py score
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py score --json
```

Local docctl score fixture tests:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-docctl-score.py
```

Local docctl trend:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py trend
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py trend --json
```

Local docctl trend fixture tests:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-docctl-trend.py
```

Local docctl snapshot writer:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py snapshot
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py snapshot --json
```

Local docctl snapshot fixture tests:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-docctl-snapshot.py
```

Local docctl status pulse:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status --json
```

Local docctl status fixture tests:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-docctl-status.py
```

Local docctl plan-fix dry-run:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py plan-fix
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py plan-fix --json
```

Local docctl plan-fix fixture tests:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-docctl-plan-fix.py
```

Local docctl apply-fix preview-only:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py apply-fix --preview PF-0001
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py apply-fix --preview PF-0001 --json
```

Local docctl apply-fix preview fixture tests:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-docctl-apply-fix-preview.py
```

Local ColaMeta executor preflight gate:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/colameta-executor-preflight.py
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/colameta-executor-preflight.py --json
```

Local ColaMeta executor preflight fixture tests:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-colameta-executor-preflight.py
```

Local docctl operations runbook:

```text
control-plane/registry/runbooks/docctl-operations-runbook-v0.1.md
```

Document Governance Baseline v0.1:
- Current baseline review:
  `control-plane/registry/reviews/2026-07-01-yellow-document-governance-baseline-v0.1.review.md`
- Baseline `docctl doctor` result:
  `registries=3 documents=102 scanned_files=149 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0`
- Any document-governance change should finish by running:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
```

Document intake routing:
- Current effective document -> register it in the directory-owned Document
  Registry.
- Draft, template, or example -> register it and make clear it is not active
  authority unless Jenn has confirmed active status.
- File governed by another active local system -> list it as
  `known_external_scope` in the Federated Document Registry.
- Historical material -> cover it with an archive note; do not bulk move or
  delete it without a separate archive plan.

The scorecard validators are read-only. They do not execute registry objects,
scan the full workspace, create databases/indexes, write external systems, or
grant authority.

Owner:
- Human owner: Jenn
- Agent owner: Project Agent
- Review required: yes for new repo, new extension, and permission changes
