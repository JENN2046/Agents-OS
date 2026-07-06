# Phase 4 Package B Registry Semantic Rules Plan - 2026-06-28

Status: plan only; no registry semantic validation, YAML parsing, schema
validation, validator execution, registry edit, consumer edit, or script
execution has been performed.

Notice: This plan defines candidate semantic rules for
`control-plane/registry/WORKSPACE_REGISTRY.yaml`. It is not authorization to run
those checks, parse registry files, execute validators, source scripts, change
executable bits, edit registry data, edit consumers, inspect broader project
trees, create maintenance/sync helpers, or perform remote, branch, release,
deploy, secret, private-state, log, cache, runtime, or project-repository
actions.

## Authorization

User authorization:

```text
进入 Phase 4 Package B，做 registry semantic rules plan，只规划 registry 语义检查规则，不执行校验。
```

Authorized scope:

- create this Package B plan
- define registry semantic rule families
- decide future hard-failure, warning, and deferred rule handling
- do not validate the registry
- do not parse YAML
- do not execute validators
- do not edit registry data

## Inputs Rechecked

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-4-scope-plan-2026-06-28.md` | `14d2efce1f39ac8a05d0c81aea008e860968e5b736e7876da96bdb603f041fcc` | Rechecked as Phase 4 scope authority. |
| `ops/migration/receipts/rules-assets-phase-4-consumer-rewrite-review-closeout-receipt-2026-06-28.md` | `c040cb4a33480ec7ebb0f5583485032f7c5977ce50f5eb9bbbc1be836fcf89bd` | Rechecked as latest consumer rewrite closeout. |
| `control-plane/registry/README.md` | `2a14a146acc36f6dbd1bc3f64f80d3193b554017612924d5a404a4f32d5fe753` | Read as registry boundary guidance. |
| `control-plane/registry/WORKSPACE_REGISTRY.yaml` | `874d5098eb068de0933b9451844bb2ae412d66d9f7673d6d41a9cb9cfacb745d` | Read as planning input only; not validated. |
| This plan target | n/a | Target was absent before creation. |
| Workspace Git state | n/a | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Scope Boundary

Package B is a semantic-rules planning package. It should not be treated as a
registry validation run.

Allowed in this plan:

- name rule families
- define future severities
- define future evidence and receipt outputs
- define stop conditions

Not allowed in this plan:

- claim that the registry passes or fails any semantic rule
- parse `WORKSPACE_REGISTRY.yaml`
- compare every value against the rule list
- execute `ops/validation/validate-workspace.sh`
- edit registry, README, runbook, prompt, governance, or validator files
- create root or governance registry copies

## Planned Severity Model

| Severity | Meaning | Future handling |
| --- | --- | --- |
| `HARD_FAIL` | A rule protects authority, safety, or default-deny behavior. | Blocks future registry acceptance until separately fixed or explicitly waived. |
| `WARNING` | A rule protects clarity, completeness, or maintainability but does not by itself expand authority. | Record in evidence; does not block unless accumulated warnings are promoted by a later decision. |
| `DEFERRED` | The rule depends on runtime, external repositories, private state, loader behavior, or a later migration track. | Record as out of current Package B execution scope. |
| `INFO` | The rule records useful context without pass/fail meaning. | Record for traceability only. |

## Planned Semantic Rule Families

### 1. Authority Location And Copy Policy

| Rule | Severity | Future evidence source |
| --- | --- | --- |
| Active registry authority path must remain `control-plane/registry/WORKSPACE_REGISTRY.yaml`. | `HARD_FAIL` | Registry `workspace.authority_path`; registry README. |
| Root-level `WORKSPACE_REGISTRY.yaml` must remain absent unless separately authorized. | `HARD_FAIL` | Future path existence check. |
| `governance/WORKSPACE_REGISTRY.yaml` must remain absent unless separately authorized. | `HARD_FAIL` | Future path existence check. |
| Files under `control-plane/registry/examples/` must remain example-only and must not be treated as active registry state. | `HARD_FAIL` | Registry README; example path review. |
| Windows root path values are reference metadata, not active execution roots. | `WARNING` | Registry `workspace.windows_reference_root`; README wording. |

### 2. Required Top-Level Structure

| Rule | Severity | Future evidence source |
| --- | --- | --- |
| Registry should define `workspace`, `layers`, `repositories`, and `security`. | `HARD_FAIL` | Future YAML parse or structured read. |
| `workspace` should include name, owner, canonical root, authority path, purpose, default branch policy, remote-action authorization, and registry notes. | `WARNING` for descriptive fields; `HARD_FAIL` for authority or remote-action fields. | Future YAML parse or structured read. |
| `layers` should be a list with unique IDs and paths. | `HARD_FAIL` | Future YAML parse or structured read. |
| `repositories` should be a list with names, layers, policies, and URL metadata roles. | `WARNING` unless a missing layer reference expands authority. | Future YAML parse or structured read. |
| `security` should define default-forbidden capabilities and explicit registry authorization flags. | `HARD_FAIL` | Future YAML parse or structured read. |

### 3. Layer Semantics

| Rule | Severity | Future evidence source |
| --- | --- | --- |
| Each layer ID should be unique. | `HARD_FAIL` | Future structured read. |
| Each layer path should be relative to the workspace root and should not escape the workspace. | `HARD_FAIL` | Future structured read plus path-policy review. |
| `state_private` must remain private and must not be marked safe for public push. | `HARD_FAIL` | Layer attributes. |
| `archive` should remain read-only by default. | `HARD_FAIL` | Layer attributes. |
| `execution` should remain disabled by default unless separately authorized. | `HARD_FAIL` | Layer attributes. |
| `extensions` should continue to require manifests. | `WARNING` or `HARD_FAIL` if future extension activation depends on it. | Layer attributes. |
| Layer `must_not_contain` entries should not contradict layer purpose. | `WARNING` | Layer content policy review. |

### 4. Repository Declaration Semantics

| Rule | Severity | Future evidence source |
| --- | --- | --- |
| Every repository entry should reference an existing layer ID. | `HARD_FAIL` | Future structured read. |
| Repository URLs must remain metadata only and must not imply fetch, pull, clone, push, release, or deploy authorization. | `HARD_FAIL` | `url_role`; registry notes. |
| Repository policy should describe local handling without authorizing remote side effects. | `WARNING` or `HARD_FAIL` if remote authority is implied. | `policy`; registry notes. |
| Missing optional repository descriptions should be warnings, not blockers. | `WARNING` | Future structured read. |

### 5. Security And Permission Defaults

| Rule | Severity | Future evidence source |
| --- | --- | --- |
| `security.default_forbidden` should include push, release, deploy, secret printing, real env reads, direct main modification, and destructive delete. | `HARD_FAIL` | Future structured read. |
| `security.registry_authorizes.remote_actions` must be `false`. | `HARD_FAIL` | Future structured read. |
| `security.registry_authorizes.validation_execution` must be `false`. | `HARD_FAIL` | Future structured read. |
| `security.registry_authorizes.executable_bit_changes` must be `false`. | `HARD_FAIL` | Future structured read. |
| `security.registry_authorizes.permission_expansion` must be `false`. | `HARD_FAIL` | Future structured read. |
| Registry notes should explicitly state that URLs and paths are metadata only. | `WARNING` unless missing wording implies authority. | Registry notes and README. |

### 6. Consumer Declaration Semantics

| Rule | Severity | Future evidence source |
| --- | --- | --- |
| Registry and README wording must not claim runtime consumer integration from static data alone. | `HARD_FAIL` | Registry README; Package A evidence. |
| `ops/validation/validate-workspace.sh` may be classified as `implemented_unexecuted`, not runtime-verified. | `WARNING` if unclear; `HARD_FAIL` if claimed as executed without receipt. | Package A evidence; validator receipt chain. |
| Prompt catalogs must remain catalog/reference only unless separately authorized. | `HARD_FAIL` if active behavior authority is implied. | Package A evidence; prompt catalog docs. |
| Extension loader remains deferred unless broader loader inspection is separately authorized. | `DEFERRED` | Package A evidence. |
| Governance registry consumption remains unproven unless a later package inspects runtime enforcement. | `DEFERRED` | Package A evidence. |

### 7. Example Boundary And Secret Hygiene

| Rule | Severity | Future evidence source |
| --- | --- | --- |
| Example registry files must stay under `control-plane/registry/examples/`. | `HARD_FAIL` | Future path review. |
| Example files must not be treated as active authority. | `HARD_FAIL` | README and future evidence. |
| Registry files must not contain real secret values or credentials. | `HARD_FAIL` | Future secret-like scan with redacted reporting. |
| Registry may contain path names, identifiers, policy names, variable names, and metadata URLs. | `INFO` | Registry README. |

## Future Package B Execution Plan

If separately authorized later, Package B execution should be split into these
substeps:

1. Preflight:
   - confirm this plan hash is stable
   - confirm registry and README hashes are stable
   - confirm evidence and receipt targets do not already exist
   - confirm no validator execution is authorized by default
2. Parse-or-read decision:
   - if YAML parsing is explicitly authorized, parse only
     `control-plane/registry/WORKSPACE_REGISTRY.yaml`
   - if YAML parsing is not authorized, keep the package to text-only evidence
     and mark structured checks as deferred
3. Rule evaluation:
   - evaluate only the rule families approved for that package
   - record `HARD_FAIL`, `WARNING`, `DEFERRED`, and `INFO` counts
   - do not auto-fix registry data
4. Receipt:
   - record exact inputs, hashes, skipped checks, and remaining risk

## Planned Future Outputs

If Package B semantic-rule execution is later authorized, create:

| Output | Purpose |
| --- | --- |
| `ops/migration/inventory/phase-4-package-b-registry-semantic-rules-evidence-2026-06-28.md` | Record future semantic-rule evaluation evidence. |
| `ops/migration/receipts/rules-assets-phase-4-package-b-registry-semantic-rules-receipt-2026-06-28.md` | Record authorization, inputs, severity counts, skipped actions, and remaining risks. |

## Stop Conditions

Stop and request separate authorization before:

- parsing YAML
- running semantic checks
- editing registry data or README files
- executing or sourcing any script
- changing executable bits
- creating root or governance registry copies
- reading active env, credentials, private state, logs, caches, runtime output,
  or full project trees
- creating maintenance/sync helpers
- taking remote, branch, release, deploy, sync, commit, push, delete, move, or
  destructive actions

## Package B Planning Result

```text
PHASE_4_PACKAGE_B_REGISTRY_SEMANTIC_RULES_PLAN_CREATED_NO_VALIDATION
```

This plan defines the future registry semantic rule set. It does not claim that
the registry currently passes or fails those rules.
