# Phase 3 Validation Scope Plan - 2026-06-28

Status: scope plan only; no Phase 3 validation executed.

Notice: This plan defines the possible Phase 3 validation scope for the rules
asset migration track. It is not authorization to run validation commands, not
authorization to parse shell scripts, not authorization to execute validators,
not authorization to create maintenance/sync helpers, not authorization to
change executable bits, and not authorization for remote, branch, release,
deploy, secret, private-state, log, cache, runtime, or project-repository
actions.

## Goal

Define a narrow, local Phase 3 validation scope that can be authorized in small
packages after Phase 2 closeout.

The Phase 3 validation plan must answer:

1. Which files are in scope?
2. Which checks are static text/file checks?
3. Which checks require parser or syntax-only validation?
4. Which checks are explicitly forbidden without separate authorization?
5. What output is safe to report?

## Evidence Used

| Evidence | Path | Observed fact |
| --- | --- | --- |
| Original migration plan | `ops/migration/plans/rules-assets-migration-plan-2026-06-27.md` | Phase 3 should remain local and narrow. |
| Phase 2 remaining-scope plan | `ops/migration/plans/phase-2-remaining-scope-and-closeout-plan-2026-06-28.md` | Requires separate Phase 3 plan before validation begins. |
| Phase 2 closeout evidence | `ops/migration/inventory/phase-2-closeout-readiness-evidence-2026-06-28.md` | Phase 2 is ready to stop at the Phase 3 gate; validation has not passed. |
| Phase 2 closeout receipt | `ops/migration/receipts/rules-assets-phase-2-closeout-receipt-2026-06-28.md` | Records `STOPPED_AT_PHASE_3_VALIDATION_GATE`. |
| File scope probe | Local read-only `find` and `stat` checks | Identified migrated rules assets and confirmed validation scripts are `644`. |

## In-Scope Files For Phase 3

Phase 3 should validate only the rules-asset migration surface, not the full
workspace.

### Control Plane Assets

| Area | Files |
| --- | --- |
| Contracts | `control-plane/contracts/README.md`, `control-plane/contracts/jenn-extension.manifest.schema.json` |
| Registry | `control-plane/registry/README.md`, `control-plane/registry/WORKSPACE_REGISTRY.yaml`, `control-plane/registry/examples/extensions.example.yaml`, `control-plane/registry/examples/protected-paths.example.yaml` |
| Runbooks | `control-plane/runbooks/README.md`, `control-plane/runbooks/add-new-extension.md`, `control-plane/runbooks/onboard-new-agent.md`, `control-plane/runbooks/run-codex-task.md` |
| Templates | `control-plane/templates/README.md`, `control-plane/templates/common/README.template.md`, `control-plane/templates/env/config.env.example.template`, `control-plane/templates/extensions/jenn-extension.manifest.example.json`, `control-plane/templates/security/SECURITY.template.md`, `control-plane/templates/validation/validation-execution-authorization.template.md` |
| Prompts | `control-plane/prompts/README.md`, `control-plane/prompts/agents/README.md`, `control-plane/prompts/codex/README.md`, `control-plane/prompts/reference/legacy-listed-prompts.md` |

### Governance And Ops Assets

| Area | Files |
| --- | --- |
| Security authority | `governance/SECURITY_BOUNDARIES.md` only |
| Validation docs/scripts | `ops/validation/README.md`, `ops/validation/validate-extension-manifests.sh`, `ops/validation/validate-no-secrets.sh`, `ops/validation/validate-workspace.sh` |
| Migration evidence | `ops/migration/inventory/*.md`, `ops/migration/plans/*.md`, `ops/migration/receipts/*.md`, `ops/migration/decisions/*.md`, `ops/migration/candidates/*.md`, `ops/migration/README.md` |

### Reference-Only Roots

| File | Use |
| --- | --- |
| `_ROOT_POLICY.md` | Reference current root authority only. |
| `_DIRECTORY_PRINCIPLES.md` | Reference target-layer meaning only. |
| `_MIGRATION_MAP.md` | Reference source/target mapping only. |

These root files may be read as context, but Phase 3 should not rewrite them.

## Explicitly Out Of Scope

| Excluded area | Reason |
| --- | --- |
| `governance/codex-router/` | This is a full project tree, not part of the Phase 2 rules-asset migration surface. It also contains project docs, tests, packages, and `node_modules`. |
| `runtime/` | Runtime repositories and artifacts require their own migration strategy. |
| `domains/` | Domain systems are outside rules-asset closeout. |
| `memory/` | Memory systems require separate sensitive-data handling. |
| `state-private/` | Private state is excluded. |
| `archive/` | Archive review is not needed for rules-asset validation. |
| `ops/maintenance/` | Maintenance/sync helpers are deferred and no sync helper exists in the WSL target. |
| `node_modules/`, `.venv/`, `dist/`, `build/`, `tmp/`, caches, logs | Generated/runtime dependency or output areas are excluded. |
| Active `.env`, active config, tokens, credentials, private auth files | Secret-bearing surfaces are excluded and must not be read. |

## Validation Packages

Phase 3 should be authorized package-by-package.

### Package A - Scope And Receipt Completeness

Risk: low.

Checks:

- confirm expected Batch 1 through Batch 12 receipts exist
- confirm Phase 2 closeout evidence and closeout receipt exist
- confirm no root `WORKSPACE_REGISTRY.yaml`
- confirm no `governance/WORKSPACE_REGISTRY.yaml`
- confirm no `ops/maintenance/sync-upstream-vcp.sh`
- confirm validation scripts remain non-executable

No parser, validator, or script execution is included.

### Package B - Static File And Path Scan

Risk: low to medium because path output may reveal workspace structure.

Checks:

- scan only the in-scope files listed above
- report file paths and counts, not full file contents
- check for forbidden path/name signals:
  `.env`, `secret`, `token`, `credential`, `cache`, `logs`, `node_modules`,
  `.venv`, `dist`, `build`, `tmp`
- separate example/template names from active secret/config names
- stop if a real active secret-like file path is found inside the scoped
  migration surface

No secret values should be printed.

### Package C - Static Content Boundary Scan

Risk: medium because content scanning can surface sensitive-looking strings.

Checks:

- scan in-scope rules-asset files for live-secret-like patterns
- scan for copy-ready remote, branch, destructive, sync, and validator-execution
  commands
- distinguish prohibition text from actionable command examples
- confirm README and template files retain non-authorization language
- confirm prompt catalogs are catalog/reference only, not active prompts

Output should summarize findings by file and line category. Do not print secret
values if a live-secret-like pattern is found.

### Package D - JSON/YAML Parse Validation

Risk: low to medium.

Candidate files:

| Format | Files |
| --- | --- |
| JSON | `control-plane/contracts/jenn-extension.manifest.schema.json`, `control-plane/templates/extensions/jenn-extension.manifest.example.json` |
| YAML | `control-plane/registry/WORKSPACE_REGISTRY.yaml`, `control-plane/registry/examples/extensions.example.yaml`, `control-plane/registry/examples/protected-paths.example.yaml` |

Checks:

- parse JSON files with a local parser
- parse YAML files with a local parser if available
- do not validate against external schemas or remote resources
- do not fetch dependencies
- do not modify parsed files

### Package E - Shell Syntax-Only Validation

Risk: medium.

Candidate files:

```text
ops/validation/validate-extension-manifests.sh
ops/validation/validate-no-secrets.sh
ops/validation/validate-workspace.sh
```

Checks:

- perform syntax-only shell parsing
- do not execute scripts
- do not source scripts
- do not change executable bits
- confirm scripts remain mode `644`

This package requires explicit authorization because it is a validation action,
even though syntax-only parsing is not functional execution.

## Explicitly Forbidden In Phase 3 Unless Separately Authorized

- Do not execute any validator script.
- Do not run `ops/validation/validate-workspace.sh` as a functional check.
- Do not create or run maintenance/sync helpers.
- Do not change executable bits.
- Do not read active `.env`, credential, token, private-state, cache, log, or
  runtime output files.
- Do not scan full project repositories such as `governance/codex-router/`.
- Do not inspect `node_modules`.
- Do not run remote, branch, release, deploy, push, pull, merge, checkout,
  destructive, copy, move, or sync actions.

## Suggested Phase 3 Order

| Order | Package | Reason |
| ---: | --- | --- |
| 1 | Package A - Scope and receipt completeness | Lowest risk and confirms closeout state. |
| 2 | Package B - Static file and path scan | Finds obvious forbidden path/name issues without parsing. |
| 3 | Package C - Static content boundary scan | Checks safety wording and secret/command patterns. |
| 4 | Package D - JSON/YAML parse validation | Confirms structured assets parse locally. |
| 5 | Package E - Shell syntax-only validation | Last because it touches script validation, even without execution. |

## Planned Phase 3 Outputs

If later authorized, Phase 3 should create:

| Output | Purpose |
| --- | --- |
| `ops/migration/inventory/phase-3-validation-evidence-2026-06-28.md` | Records package-by-package validation evidence. |
| `ops/migration/receipts/rules-assets-phase-3-validation-receipt-2026-06-28.md` | Records validation authorization, checks run, checks skipped, and remaining risks. |

## Authorization Boundary

Before any Phase 3 validation is run, request explicit authorization for one of:

```text
Authorize Phase 3 Package A only.
Authorize Phase 3 Packages A-B only.
Authorize Phase 3 Packages A-C only.
Authorize Phase 3 Packages A-D only.
Authorize Phase 3 Packages A-E, including shell syntax-only parsing, but no script execution.
```

Any authorization must still exclude functional script execution, remote actions,
maintenance/sync helpers, executable-bit changes, private-state reads, and
project-repository migration unless the user explicitly authorizes those items
in a separate request.
