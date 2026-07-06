# Phase 4 Package C Registry YAML Parse Authorization Plan - 2026-06-28

Status: authorization plan only; no YAML parsing, semantic validation, schema
validation, validator execution, registry edit, consumer edit, script execution,
or dependency installation has been performed.

Notice: This plan decides the safe authorization shape for a possible future
parse-only check of `control-plane/registry/WORKSPACE_REGISTRY.yaml`. It is not
authorization to parse YAML now, parse additional files, run semantic rule
evaluation, execute validators, source scripts, change executable bits, edit
registry data, edit consumers, install dependencies, create maintenance/sync
helpers, or perform remote, branch, release, deploy, secret, private-state, log,
cache, runtime, or project-repository actions.

## Authorization

User authorization:

```text
进入 Package C，做 YAML parse authorization plan，先规划是否允许只解析 control-plane/registry/WORKSPACE_REGISTRY.yaml。
```

Authorized scope:

- create this Package C authorization plan
- decide whether a future parse-only package may target exactly
  `control-plane/registry/WORKSPACE_REGISTRY.yaml`
- define future preflight, allowed outputs, and stop conditions
- do not parse YAML in this step
- do not run semantic checks
- do not execute validators
- do not edit registry data

## Naming Note

The earlier Phase 4 scope plan named a Package C candidate around JSON Schema
semantic validation. This Package C plan follows the current user instruction
and is limited to registry YAML parse authorization. It does not authorize or
replace a future JSON Schema validation package.

## Inputs Rechecked

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-4-scope-plan-2026-06-28.md` | `14d2efce1f39ac8a05d0c81aea008e860968e5b736e7876da96bdb603f041fcc` | Rechecked as Phase 4 scope authority. |
| `ops/migration/receipts/rules-assets-phase-4-package-b-registry-semantic-rules-review-closeout-receipt-2026-06-28.md` | `7d095bc46910c37eb2f6bcdab2b02da51761154be866f87e831395024b9b2001` | Rechecked as Package B closeout authority. |
| `ops/migration/plans/phase-4-package-b-registry-semantic-rules-plan-2026-06-28.md` | `d14e95efd4fe69042aaa5fb186c3229cfe4f1695961c67f9d50734ae7f2c9ab7` | Rechecked as semantic-rule context. |
| `control-plane/registry/WORKSPACE_REGISTRY.yaml` | `874d5098eb068de0933b9451844bb2ae412d66d9f7673d6d41a9cb9cfacb745d` | Candidate parse target; not parsed. |
| This plan target | n/a | Target was absent before creation. |
| Workspace Git state | n/a | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Authorization Decision

| Question | Decision | Reason |
| --- | --- | --- |
| May a future package parse `control-plane/registry/WORKSPACE_REGISTRY.yaml`? | `ADMIT_PARSE_ONLY_WITH_GATES` | Package B text evidence left structured checks deferred; parse-only is the next narrowest step. |
| May the future package parse registry example files? | `NOT_ADMITTED` | Examples are example-only and should stay outside the first authority-registry parse gate. |
| May the future package parse every YAML file under `control-plane/` or `ops/`? | `NOT_ADMITTED` | Broad parsing would expand scope beyond the named registry authority file. |
| May the future package perform semantic pass/fail evaluation after parsing? | `NOT_ADMITTED_BY_THIS_PLAN` | Semantic rule evaluation needs separate authorization after parse evidence exists. |
| May the future package execute `ops/validation/validate-workspace.sh`? | `NOT_ADMITTED` | Validator execution remains a separate exact-run gate. |
| May the future package edit registry data based on parse findings? | `NOT_ADMITTED` | Parse evidence must not auto-fix or rewrite the registry. |

Plain-language decision:

```text
Future YAML parsing may be planned for exactly control-plane/registry/WORKSPACE_REGISTRY.yaml,
but only as parse-only evidence. It must not become semantic validation, validator
execution, or registry editing without separate authorization.
```

## Future Parse-Only Scope

If separately authorized, the future parse-only package may:

- read exactly `control-plane/registry/WORKSPACE_REGISTRY.yaml`
- parse it with a local safe YAML loader
- report whether parsing succeeded or failed
- report top-level key names and coarse value types
- record parser/tool identity and command environment at a high level
- create a parse evidence file and receipt

The future parse-only package must not:

- parse `control-plane/registry/examples/*.yaml`
- parse templates, runbooks, prompts, governance files, or project trees
- run Package B semantic `HARD_FAIL` or `WARNING` checks
- run validators or shell scripts
- install dependencies
- fetch schemas or external resources
- print secret values, env values, private-state content, logs, or caches
- edit any file based on parse results

## Future Preflight Required

| Check | Required result |
| --- | --- |
| This plan hash is stable | Required before parse authorization. |
| Package B closeout hash is stable | Required before parse authorization. |
| Registry target hash is stable | Required before parse authorization. |
| Registry target path is exact | Must be exactly `control-plane/registry/WORKSPACE_REGISTRY.yaml`. |
| Parse evidence target is absent | Avoid overwriting previous parse evidence. |
| Parse receipt target is absent | Avoid overwriting previous parse receipt. |
| Parser availability is local | No dependency install, network fetch, or external service. |
| Output redaction policy is set | Do not print secret values or full private-state content. |

## Future Parser Policy

| Policy | Requirement |
| --- | --- |
| Loader type | Use a safe/non-executing YAML loader only. |
| Dependency policy | Use only already available local tooling; do not install packages. |
| Network policy | No network or external schema fetch. |
| Scope policy | One file only: `control-plane/registry/WORKSPACE_REGISTRY.yaml`. |
| Output policy | Prefer parse status, top-level keys, coarse types, and counts over full content dumps. |
| Failure policy | Parse failure should be recorded as evidence, not auto-fixed. |

## Planned Future Outputs

If the future parse-only package is separately authorized, create:

| Output | Purpose |
| --- | --- |
| `ops/migration/inventory/phase-4-package-c-registry-yaml-parse-evidence-2026-06-28.md` | Record parse-only evidence for the authority registry file. |
| `ops/migration/receipts/rules-assets-phase-4-package-c-registry-yaml-parse-receipt-2026-06-28.md` | Record authorization, input hashes, parser boundary, parse result, skipped actions, and remaining risks. |

## Relationship To Package B

Package B remains the semantic-rules planning and text-evidence package. A
future Package C parse-only result can unblock later structured checks, but it
does not by itself prove:

- registry business-rule acceptance
- repository layer cross-reference correctness
- layer uniqueness
- path normalization or escape safety
- consumer runtime integration
- validator runtime behavior
- JSON Schema validity

## Stop Conditions

Stop and request separate authorization before:

- parsing YAML
- evaluating semantic pass/fail rules
- parsing any file other than `control-plane/registry/WORKSPACE_REGISTRY.yaml`
- installing dependencies
- fetching external schemas or resources
- executing or sourcing any script
- changing executable bits
- editing registry data, README files, consumers, prompts, governance files, or
  validator files
- reading active env, credentials, private state, logs, caches, runtime output,
  or full project trees
- creating maintenance/sync helpers
- taking remote, branch, release, deploy, sync, commit, push, delete, move, or
  destructive actions

## Package C Planning Result

```text
PHASE_4_PACKAGE_C_REGISTRY_YAML_PARSE_AUTHORIZATION_PLAN_CREATED_NO_PARSE
```

This plan admits a future parse-only preflight and authorization path for the
single authority registry YAML file. It does not authorize parsing yet.
