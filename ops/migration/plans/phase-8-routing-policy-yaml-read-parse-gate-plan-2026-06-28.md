# Phase 8 Routing Policy YAML Read/Parse Gate Plan

Date: 2026-06-28

Status: plan only.

This document plans a file-specific Phase 8 gate for
`governance/codex-router/routing-policy.yaml`. It admits bounded local text
read and YAML parse-only evidence for this exact file. It does not execute
router code, runtime, loader, package scripts, tests, builds, typechecks, sync,
deploy, network, or remote actions.

## Inputs

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/receipts/rules-assets-phase-8-parser-semantic-review-closeout-receipt-2026-06-28.md` | `475b69ed448025342dbaed9bf93748119af98671ca4be1b54a199c035d0498ab` | Confirms the first Phase 8 parser/semantic track closed with YAML deferred. |
| `ops/migration/inventory/phase-8-parser-semantic-review-evidence-2026-06-28.md` | `44f9b31361d50e8e05f35a0acb1495d37552a687c7f84b686fea95ffeffa761d` | Provides JSON parse-only context and script/config surface. |
| `ops/migration/receipts/rules-assets-phase-8-runtime-loader-behavior-validation-preflight-receipt-2026-06-28.md` | `ed60695d396ecc5b9b9d4c14e7f87dc8611fcdfc44c817f3d6424dbaeab85f99` | Confirms behavior validation remains stopped at an execution gate. |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-phase-7-closeout-receipt-2026-06-28.md` | `2a9884d9e23ca865155883d4313773682c317649789c51b45f8cdadc2d10fcfb` | Confirms Phase 7 static runtime/loader boundary evidence was closed without runtime acceptance. |
| `governance/codex-router/routing-policy.yaml` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | Exact YAML file admitted for this gate. |

## Current File Metadata

| Path | Type | Mode | Size | Lines |
| --- | --- | --- | --- | --- |
| `governance/codex-router/routing-policy.yaml` | regular file | `644` | `6318` bytes | `254` |

## Scope Decision

This gate permits one narrow exception to the earlier Phase 7 text-read cap:
`routing-policy.yaml` may be read in full because the exact file is already
identified, it is small enough for a bounded single-file review, and it is the
only YAML policy source in this gate.

Allowed upper bound:

- exact path only:
  `governance/codex-router/routing-policy.yaml`
- full file read allowed only up to `300` lines and `16 KiB`
- YAML syntax parse allowed with a local parser
- evidence may record top-level keys, nested key classes, list counts, scalar
  types, and parse status
- evidence may quote only small non-secret structural labels when needed

## Future Targets

| Future target | Intended purpose |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-8-routing-policy-yaml-read-parse-preflight-receipt-2026-06-28.md` | Confirm hashes, target absence, parser availability, and read/parse boundaries before evidence collection. |
| `ops/migration/inventory/phase-8-routing-policy-yaml-read-parse-evidence-2026-06-28.md` | Record bounded YAML read/parse evidence. |
| `ops/migration/receipts/rules-assets-phase-8-routing-policy-yaml-read-parse-evidence-receipt-2026-06-28.md` | Record evidence creation and validation limits. |
| `ops/migration/receipts/rules-assets-phase-8-routing-policy-yaml-read-parse-closeout-receipt-2026-06-28.md` | Close this YAML parse-only track without router/runtime acceptance. |

## Preflight Requirements

The next preflight must confirm:

- this plan hash
- all input hashes are stable
- all future targets are still absent
- `routing-policy.yaml` is still a regular file, mode `644`, size under
  `16 KiB`, and line count under `300`
- a local YAML parser is available
- the evidence command will not execute package scripts, router code, runtime,
  loaders, tests, builds, typechecks, sync, deploy, network, or remote actions

## Stop Conditions

Stop if:

- any input hash drifts
- any future target already exists
- `routing-policy.yaml` exceeds the admitted cap
- YAML parser availability cannot be confirmed locally
- parsing would execute code or evaluate package scripts
- evidence collection attempts to read sibling files, package lockfiles, router
  source code, hidden files, runtime files, loader files, or deferred Markdown
  files
- any result is framed as router behavior acceptance, runtime acceptance, loader
  acceptance, or full consumer integration acceptance

## Acceptance Boundary

This plan can only support YAML read/parse-only evidence. It cannot grant:

- YAML semantic acceptance
- router behavior acceptance
- runtime behavior acceptance
- loader behavior acceptance
- package script execution
- tests, builds, typechecks, validators, canaries, sync, deploy, network, or
  remote actions
- migration, rewrite, normalization, or policy changes

## Result

Routing policy YAML read/parse gate planning is complete. The next safe step is
a preflight receipt that confirms input stability, target absence, file caps,
parser availability, and no-execution boundaries.

Marker:

```text
PHASE_8_ROUTING_POLICY_YAML_READ_PARSE_GATE_PLAN_CREATED_NO_EXECUTION
```
