# Phase 4 Package D Registry Semantic Evaluation Authorization Plan - 2026-06-28

Status: authorization plan only; no registry semantic evaluation, YAML parsing,
validator execution, schema validation, registry edit, consumer edit, script
execution, or dependency installation has been performed.

Notice: This plan decides the safe authorization shape for a possible future
semantic evaluation of Package B registry rules after the Package C parse-only
result. It is not authorization to evaluate rules now, parse YAML again, execute
validators, source scripts, change executable bits, edit registry data, edit
consumers, install dependencies, create maintenance/sync helpers, or perform
remote, branch, release, deploy, secret, private-state, log, cache, runtime, or
project-repository actions.

## Authorization

User authorization:

```text
进入 Package D，做 registry semantic evaluation authorization plan，规划是否允许基于已解析结果执行 Package B 的语义规则评估。
```

Authorized scope:

- create this Package D authorization plan
- decide whether future semantic evaluation may use Package B rules and Package
  C parse evidence
- classify which rule families are eligible, partial, or deferred
- define future preflight, allowed outputs, and stop conditions
- do not run semantic evaluation in this step
- do not parse YAML in this step
- do not execute validators
- do not edit registry data

## Naming Note

The earlier Phase 4 scope plan named a Package D candidate around validator
execution authorization. This Package D plan follows the current user
instruction and is limited to registry semantic evaluation authorization.
Validator execution remains a separate future gate.

## Inputs Rechecked

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-4-scope-plan-2026-06-28.md` | `14d2efce1f39ac8a05d0c81aea008e860968e5b736e7876da96bdb603f041fcc` | Rechecked as Phase 4 scope authority. |
| `ops/migration/plans/phase-4-package-b-registry-semantic-rules-plan-2026-06-28.md` | `d14e95efd4fe69042aaa5fb186c3229cfe4f1695961c67f9d50734ae7f2c9ab7` | Rechecked as Package B rule authority. |
| `ops/migration/receipts/rules-assets-phase-4-package-b-registry-semantic-rules-review-closeout-receipt-2026-06-28.md` | `7d095bc46910c37eb2f6bcdab2b02da51761154be866f87e831395024b9b2001` | Rechecked as Package B closeout authority. |
| `ops/migration/receipts/rules-assets-phase-4-package-c-registry-yaml-parse-review-closeout-receipt-2026-06-28.md` | `a2e8c7af0a2d77ebfd8e206801b39f43539c95eb28a89aa7bbc6b203219b75de` | Rechecked as Package C closeout authority. |
| `ops/migration/inventory/phase-4-package-c-registry-yaml-parse-evidence-2026-06-28.md` | `8530a4645b0aeeca3eed7bde7d706e7383df8c634b875f904dd5ebea6393c6e7` | Rechecked as parse-only evidence. |
| `control-plane/registry/WORKSPACE_REGISTRY.yaml` | `874d5098eb068de0933b9451844bb2ae412d66d9f7673d6d41a9cb9cfacb745d` | Candidate future semantic-evaluation target; not evaluated. |
| This plan target | n/a | Target was absent before creation. |
| Workspace Git state | n/a | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Authorization Decision

| Question | Decision | Reason |
| --- | --- | --- |
| May a future package execute Package B semantic rule evaluation? | `ADMIT_EVALUATION_WITH_GATES` | Package B defined the rule set and Package C proved the authority registry parses successfully. |
| May the future package claim registry acceptance based only on Package C coarse parse evidence? | `NOT_ADMITTED` | Package C evidence recorded only top-level keys and coarse types, not full structured values. |
| May the future package evaluate only top-level shape from existing parse evidence without reparsing? | `ADMIT_LIMITED_EVIDENCE_REUSE` | Existing parse evidence is enough for top-level type/key-count/key-name observations only. |
| May the future package evaluate full Package B rules against structured registry data? | `ADMIT_WITH_EXACT_STRUCTURED_READ_GATE` | Full evaluation needs structured values; it must be separately authorized and limited to the same authority registry file. |
| May the future package parse registry examples or other YAML files? | `NOT_ADMITTED` | Examples and broad YAML scans remain outside the registry authority evaluation scope. |
| May the future package execute validators? | `NOT_ADMITTED` | Validator execution remains a separate exact-run authorization gate. |
| May the future package auto-fix registry data after evaluation? | `NOT_ADMITTED` | Evaluation evidence must not mutate registry data. |

Plain-language decision:

```text
Future Package B semantic evaluation is allowed to be planned, but only behind a
separate evaluation authorization. Existing Package C parse evidence can support
top-level shape checks; full semantic evaluation requires an exact structured
read gate for the same registry file and still cannot edit anything.
```

## Future Evaluation Scope

If separately authorized, the future semantic evaluation package may:

- use Package B rule families as the evaluation checklist
- use Package C parse evidence as proof that the target YAML parsed successfully
- evaluate top-level shape against the existing parse evidence
- perform an exact structured read of
  `control-plane/registry/WORKSPACE_REGISTRY.yaml` only if separately included
  in the future evaluation authorization
- record `PASS`, `FAIL`, `WARNING`, `DEFERRED`, and `NOT_EVALUATED` results
- create semantic evaluation evidence and receipt

The future semantic evaluation package must not:

- edit registry data
- parse registry example files
- parse broad YAML trees
- execute validators
- run shell scripts
- install dependencies
- fetch schemas or external resources
- inspect private state, logs, caches, active env files, or project trees
- treat warnings as approval to auto-fix
- treat a passing subset as whole-registry acceptance

## Planned Evaluation Result Labels

| Label | Meaning |
| --- | --- |
| `PASS` | The rule was evaluated within scope and the observed structured value matched the rule. |
| `FAIL` | The rule was evaluated within scope and the observed structured value violated the rule. |
| `WARNING` | The rule was evaluated or partially evaluated and found a clarity/completeness concern that does not by itself expand authority. |
| `DEFERRED` | The rule requires runtime, loader, governance enforcement, private state, external repository, or broader migration evidence. |
| `NOT_EVALUATED` | The rule was intentionally left out of the authorized evaluation package. |

## Planned Rule Family Eligibility

| Package B rule family | Future evaluation eligibility | Notes |
| --- | --- | --- |
| Authority location and copy policy | `ELIGIBLE_WITH_GATES` | Authority path and forbidden root/governance copies can be checked with exact paths and structured registry values. |
| Required top-level structure | `ELIGIBLE_WITH_GATES` | Existing parse evidence covers top-level keys; full field checks need structured read. |
| Layer semantics | `ELIGIBLE_WITH_GATES` | Layer IDs, relative paths, safety flags, and required manifests need structured read; path escape checks should remain local and non-mutating. |
| Repository declaration semantics | `ELIGIBLE_WITH_GATES` | Repository-to-layer cross-reference and URL metadata rules need structured read. |
| Security and permission defaults | `ELIGIBLE_WITH_GATES` | Default-forbidden and `registry_authorizes` false flags are strong candidates for hard-fail checks. |
| Consumer declaration semantics | `PARTIAL_OR_DEFERRED` | Static-consumer wording can be reviewed; runtime consumer integration remains deferred. |
| Example boundary and secret hygiene | `PARTIAL_OR_DEFERRED` | Example paths and secret-like scans can be checked separately; exhaustive credential assurance remains unclaimed. |

## Future Preflight Required

| Check | Required result |
| --- | --- |
| This plan hash is stable | Required before semantic evaluation authorization. |
| Package B plan and closeout hashes are stable | Required before semantic evaluation authorization. |
| Package C parse evidence and closeout hashes are stable | Required before semantic evaluation authorization. |
| Registry target hash is stable | Required before semantic evaluation authorization. |
| Evaluation evidence target is absent | Avoid overwriting previous evaluation evidence. |
| Evaluation receipt target is absent | Avoid overwriting previous evaluation receipt. |
| Evaluation scope is exact | Must name the specific rule families and whether structured read is allowed. |
| Output policy is set | Report counts and rule IDs; avoid full content dumps and secret values. |
| Mutation boundary is set | No registry edits, chmod changes, validator execution, or auto-fix behavior. |

## Planned Future Outputs

If the future semantic evaluation package is separately authorized, create:

| Output | Purpose |
| --- | --- |
| `ops/migration/inventory/phase-4-package-d-registry-semantic-evaluation-evidence-2026-06-28.md` | Record semantic evaluation evidence and rule results. |
| `ops/migration/receipts/rules-assets-phase-4-package-d-registry-semantic-evaluation-receipt-2026-06-28.md` | Record authorization, inputs, rule result counts, skipped actions, and remaining risks. |

## Registry Acceptance Boundary

Even if a future Package D evaluation reports no `FAIL` items, it should not by
itself authorize:

- registry edits
- consumer activation
- validator execution
- remote actions
- extension activation
- permission expansion
- runtime enforcement claims

Registry acceptance, if desired, should be a separate closeout decision after
evaluation evidence is reviewed.

## Stop Conditions

Stop and request separate authorization before:

- evaluating semantic rules
- reparsing or structured-reading registry YAML
- parsing files other than `control-plane/registry/WORKSPACE_REGISTRY.yaml`
- editing registry data, README files, consumers, prompts, governance files, or
  validator files
- executing or sourcing any script
- changing executable bits
- installing dependencies
- fetching external schemas or resources
- reading active env, credentials, private state, logs, caches, runtime output,
  or full project trees
- creating maintenance/sync helpers
- taking remote, branch, release, deploy, sync, commit, push, delete, move, or
  destructive actions

## Package D Planning Result

```text
PHASE_4_PACKAGE_D_REGISTRY_SEMANTIC_EVALUATION_AUTHORIZATION_PLAN_CREATED_NO_EVALUATION
```

This plan admits a future semantic evaluation authorization path. It does not
authorize evaluation yet and does not claim registry acceptance.
