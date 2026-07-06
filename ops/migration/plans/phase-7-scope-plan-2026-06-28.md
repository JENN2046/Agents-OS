# Phase 7 Scope Plan - 2026-06-28

Status: scope plan only; no runtime content read, loader content read, directory
listing, evidence collection, validator execution, loader execution,
YAML/JSON parsing, consumer edit, runtime edit, maintenance/sync action, or
remote action has been performed.

Notice: This plan opens Phase 7 after Phase 6 closed only the limited
static/local readiness track. It plans the first safe Phase 7 gate:
runtime/loader narrow read allowlist planning. It is not authorization to read
runtime or loader contents.

## Authorization

User authorization:

```text
开 Phase 7 scope plan，优先从 runtime/loader narrow read allowlist 规划开始，仍然只规划不读内容。
```

Authorized scope:

- create this Phase 7 scope plan
- identify runtime/loader narrow read allowlist planning as the first Phase 7
  gate
- define the shape of the future allowlist plan
- do not create the future allowlist plan in this step
- do not read runtime, loader, extension, private-state, log, cache, env, or
  project-tree contents
- do not recursively list runtime-adjacent directories
- do not execute validators, loaders, scripts, tests, or runtime code
- do not parse YAML/JSON
- do not edit consumers, registry data, runtime files, prompts, governance
  files, runbooks, templates, or validator scripts

## Inputs Rechecked

| Input | SHA-256 | Mode | Use |
| --- | --- | --- | --- |
| `ops/migration/receipts/rules-assets-phase-6-closeout-receipt-2026-06-28.md` | `b3d7c8f47e32a32edb6d1ca9f7ff9186570e3575d09f3f6187fca13d620547a5` | `644` | Phase 7 gate source. |
| `ops/migration/plans/phase-6-closeout-readiness-plan-2026-06-28.md` | `00e40e5b3dbc9da7641f712640164243148175be4297bdf5a8d0eec368d0cef1` | `644` | Phase 6 closeout boundary source. |
| This plan target | n/a | n/a | Target was absent before creation. |
| Future runtime/loader allowlist plan target | n/a | n/a | `ops/migration/plans/phase-7-runtime-loader-narrow-read-allowlist-plan-2026-06-28.md` was absent. |
| Workspace Git state | n/a | n/a | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

No runtime, loader, extension, project, private-state, log, cache, or env
contents were read for this plan.

## Phase 7 Opening Boundary

Phase 7 starts where Phase 6 stopped:

- Phase 6 proved limited static/local readiness.
- Phase 6 did not prove runtime behavior.
- Phase 6 did not inspect loader internals.
- Phase 6 did not prove full consumer integration.
- Phase 6 left Tier 2 runtime-adjacent content closed.

Therefore Phase 7 should not start by reading runtime or loader files. It should
start by planning a narrow read allowlist.

## First Phase 7 Gate

| Question | Phase 7 opening decision | Reason |
| --- | --- | --- |
| What starts Phase 7? | Runtime/loader narrow read allowlist planning. | Phase 6 carried runtime behavior and loader inspection forward without granting content reads. |
| Should this scope plan read runtime or loader contents? | No. | The user requested planning only and no content reads. |
| Should this scope plan list runtime or loader directories recursively? | No. | Directory listings can disclose implementation or private-state shape. |
| Should this scope plan execute anything? | No. | Execution gates require separate exact-run plans. |
| Should this scope plan grant runtime acceptance? | No. | No runtime behavior evidence exists. |
| What is the next safe artifact? | A runtime/loader narrow read allowlist plan. | It can name exact candidate read surfaces and stop conditions before any read happens. |

## Planned Next Artifact

If separately authorized, create:

| Output | Purpose |
| --- | --- |
| `ops/migration/plans/phase-7-runtime-loader-narrow-read-allowlist-plan-2026-06-28.md` | Plan exact candidate read paths, permitted read depth, exclusions, evidence outputs, and stop conditions for a later narrow runtime/loader inspection. |

That future plan should still be plan-only. It should not read the candidate
files or directories by itself.

## Future Allowlist Plan Requirements

A future runtime/loader narrow read allowlist plan must decide, before any
content read:

| Required decision | Required handling |
| --- | --- |
| Exact target category | Distinguish runtime behavior, loader behavior, extension loader references, or consumer linkage. |
| Exact path candidates | Name each future path candidate explicitly; no globs, recursive roots, or broad project trees by default. |
| Read depth | Define whether the later evidence step may read file content, file metadata only, or top-level presence only. |
| Exclusion rules | Exclude private-state, logs, caches, active env files, credentials, generated output, node_modules, and broad project trees by default. |
| Output policy | Record hashes, modes, and summarized evidence; do not print secrets, env values, logs, or private-state contents. |
| Stop conditions | Stop on unexpected symlink, secret-like path, executable behavior, remote reference, dependency install need, or path drift. |
| Evidence targets | Name future evidence and receipt paths before any read. |

## Candidate Gate Sequence

| Order | Gate | Status after this plan |
| --- | --- | --- |
| 1 | Runtime/loader narrow read allowlist plan. | Planned next; not created by this scope plan. |
| 2 | Runtime/loader narrow read allowlist preflight. | Deferred; should confirm stable hashes, exact path candidates, and target absence. |
| 3 | Narrow read evidence collection. | Deferred; requires separate authorization and must obey the allowlist. |
| 4 | Narrow read evidence review. | Deferred; may classify what was observed but must not grant runtime behavior acceptance. |
| 5 | Runtime/loader behavior or exact-run planning. | Deferred high-risk; requires command, working directory, output policy, failure policy, and receipt target. |

## Gates Still Carried Forward

| Gate | Status |
| --- | --- |
| Runtime behavior acceptance | Deferred. |
| Runtime code execution or exact-run behavior testing | Deferred; requires exact authorization. |
| Extension loader behavior or acceptance | Deferred. |
| Extension loader inspection | Deferred until a narrow read allowlist is planned and authorized. |
| Full consumer integration acceptance | Deferred. |
| Consumer rewrite patch | Deferred; requires patch plan, preflight, and receipt. |
| Governance runtime enforcement acceptance | Deferred. |
| Manifest/schema/content validation | Deferred. |
| Registry YAML parsing or semantic re-evaluation | Deferred if needed. |
| Full credential audit or file-content scanning | Deferred. |
| Private-state, logs, caches, active env, and credential reads | Closed by default. |
| Maintenance/sync helper planning or execution | Deferred. |
| Runtime/domain/memory/project migration | Deferred or separate track. |
| Remote/operational actions | Forbidden without explicit remote intent and high-risk preflight. |

## Stop Conditions

Stop and request separate authorization before:

- creating the runtime/loader narrow read allowlist plan
- reading runtime, loader, extension, project, private-state, log, cache, env,
  credential, or generated contents
- recursively listing runtime-adjacent directories
- executing validators, loaders, scripts, tests, or runtime code
- parsing YAML/JSON
- editing consumers, registry data, runtime files, prompts, governance files,
  runbooks, templates, or validator scripts
- changing executable bits
- creating maintenance/sync helpers
- committing, pushing, syncing, releasing, deploying, branching, copying,
  moving, deleting, or taking remote/external action

## Planning Result

```text
PHASE_7_SCOPE_PLAN_CREATED_RUNTIME_LOADER_NARROW_READ_ALLOWLIST_PLANNING_FIRST_NO_CONTENT_READ
```

Phase 7 is opened as a planning track only. The next safe action is a separate
runtime/loader narrow read allowlist plan that names exact future read
candidates before any content is read.
