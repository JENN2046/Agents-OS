# Phase 7 Runtime Loader Narrow Read Allowlist Plan - 2026-06-28

Status: allowlist plan only; no runtime content read, loader content read,
candidate path existence check, directory listing, evidence collection,
validator execution, loader execution, YAML/JSON parsing, consumer edit,
runtime edit, maintenance/sync action, or remote action has been performed.

Notice: This plan defines candidate paths and read boundaries for a possible
future narrow runtime/loader inspection. It is not authorization to read any
candidate path. Candidate paths in this document are planning candidates only;
their existence and contents were not checked by this plan.

## Authorization

User authorization:

```text
创建 phase-7-runtime-loader-narrow-read-allowlist-plan-2026-06-28.md，仍然只规划候选路径和读边界，不读取候选内容。
```

Authorized scope:

- create this runtime/loader narrow read allowlist plan
- name future candidate paths and read boundaries
- define exclusions, stop conditions, future preflight, evidence outputs, and
  acceptance limits
- do not read candidate path contents
- do not check candidate path existence or metadata
- do not recursively list runtime-adjacent directories
- do not execute validators, loaders, scripts, tests, or runtime code
- do not parse YAML/JSON
- do not edit consumers, registry data, runtime files, prompts, governance
  files, runbooks, templates, or validator scripts

## Inputs Rechecked

| Input | SHA-256 | Mode | Use |
| --- | --- | --- | --- |
| `ops/migration/plans/phase-7-scope-plan-2026-06-28.md` | `977c524caac711f8db669bcf2e08989947a2b6c351e3487fd38379c208dc2eda` | `644` | Phase 7 scope authority. |
| `ops/migration/receipts/rules-assets-phase-6-closeout-receipt-2026-06-28.md` | `b3d7c8f47e32a32edb6d1ca9f7ff9186570e3575d09f3f6187fca13d620547a5` | `644` | Phase 7 carried-forward gates. |
| `ops/migration/plans/phase-6-closeout-readiness-plan-2026-06-28.md` | `00e40e5b3dbc9da7641f712640164243148175be4297bdf5a8d0eec368d0cef1` | `644` | Phase 6 closeout boundary source. |
| This plan target | n/a | n/a | Target was absent before creation. |
| Future narrow read evidence target | n/a | n/a | `ops/migration/inventory/phase-7-runtime-loader-narrow-read-evidence-2026-06-28.md` was absent. |
| Future narrow read receipt target | n/a | n/a | `ops/migration/receipts/rules-assets-phase-7-runtime-loader-narrow-read-evidence-receipt-2026-06-28.md` was absent. |
| Workspace Git state | n/a | n/a | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

No candidate runtime, loader, extension, project, private-state, log, cache, or
env contents were read. Candidate path existence was not checked.

## Planning Goal

Define a future narrow read boundary that can answer:

1. Which exact runtime/loader files would be safe to inspect first?
2. What is the maximum read depth for each candidate?
3. Which paths remain closed by default?
4. What evidence outputs and stop conditions are required before any read?

This plan does not prove runtime behavior, loader behavior, or consumer
integration.

## Candidate Read Tiers

| Tier | Future read depth | Purpose | Default status |
| --- | --- | --- | --- |
| Tier A | Metadata only: existence, mode, file type, hash if file exists. | Confirm whether named entrypoint candidates exist without content disclosure. | Planned only. |
| Tier B | Limited text read of exact named files only. | Inspect loader/runtime boundary declarations after metadata preflight. | Deferred; requires separate authorization. |
| Tier C | Top-level directory names only for exact named roots. | Understand candidate sub-area shape without recursive listing. | Deferred; requires separate authorization. |
| Tier D | Recursive listing or behavior execution. | Possible later runtime/loader behavior work. | Closed by default; not part of first narrow read. |

The recommended first evidence package should start with Tier A only. Tier B or
Tier C should require a separate authorization after Tier A review.

## Candidate Paths For Future Tier A Metadata-Only Check

The following candidates are based on prior Phase 6 static evidence, registry
and governance references, and migration boundary documents already used in the
rules-asset track. This plan did not verify candidate existence.

| Candidate | Category | Future maximum first read | Reason for candidacy |
| --- | --- | --- | --- |
| `runtime/README.md` | Runtime root doorplate | Tier A metadata only. | Phase 5/6 validation surfaces treated it as a required root marker. |
| `runtime/VCPToolBox/Plugin.js` | Runtime loader entrypoint candidate | Tier A metadata only. | Named in security-boundary evidence as a high-risk runtime path. |
| `runtime/VCPToolBox/adminServer.js` | Runtime admin/runtime candidate | Tier A metadata only. | Named in security-boundary evidence as a high-risk runtime path. |
| `runtime/VCPToolBox/routes/` | Runtime route tree candidate | Tier A metadata only, directory existence only. | Named in security-boundary evidence as a high-risk runtime area. |
| `runtime/VCPToolBox/modules/` | Runtime module tree candidate | Tier A metadata only, directory existence only. | Named in security-boundary evidence as a high-risk runtime area. |
| `runtime/VCPToolBox/AdminPanel-Vue/` | Runtime admin UI candidate | Tier A metadata only, directory existence only. | Named in security-boundary evidence as a high-risk runtime area. |
| `extensions/README.md` | Extension root doorplate | Tier A metadata only. | Phase 5/6 validation surfaces treated it as a required root marker. |
| `extensions/vcp-toolbox-jenn/` | Extension loader-adjacent candidate | Tier A metadata only, directory existence only. | Named in migration mapping as the WSL target for Jenn extensions. |
| `execution/README.md` | Execution root doorplate | Tier A metadata only. | Phase 5/6 validation surfaces treated it as a required root marker. |
| `governance/codex-router/` | Governance/runtime bridge candidate | Tier A metadata only, directory existence only. | Previously carried as runtime-adjacent and closed to content inspection. |

## Paths Closed By Default

The following remain excluded unless a later plan grants a narrower allowance:

| Path or class | Default handling |
| --- | --- |
| `state-private/` | Closed; no listing, metadata sweep, content read, or search. |
| `state-private/secrets/` | Closed; high-sensitivity credential area. |
| `state-private/MEMORY.md` | Closed; private memory/state. |
| Any `.env`, `config.env`, credential, key, token, certificate, or secret-like file | Closed; do not read or hash unless a separate security-audit plan authorizes it. |
| Logs, caches, runtime output, traces, generated data | Closed. |
| `node_modules/` or dependency/vendor trees | Closed. |
| Broad project repositories or full runtime trees | Closed. |
| Recursive listings under `runtime/`, `extensions/`, `execution/`, `domains/`, `memory/`, `archive/`, `labs/`, or `governance/codex-router/` | Closed by default. |
| Remote URLs, upstream remotes, package installs, build/test commands | Closed; not read or executed by this track. |

## Future Preflight Requirements

Before any narrow read evidence collection, a future preflight must confirm:

| Check | Required result |
| --- | --- |
| Phase 7 scope plan hash stable | Required. |
| This allowlist plan hash stable | Required. |
| Phase 6 closeout receipt hash stable | Required. |
| Future evidence target absent | `ops/migration/inventory/phase-7-runtime-loader-narrow-read-evidence-2026-06-28.md`. |
| Future evidence receipt target absent | `ops/migration/receipts/rules-assets-phase-7-runtime-loader-narrow-read-evidence-receipt-2026-06-28.md`. |
| Candidate read tier chosen | Required; default should be Tier A metadata only. |
| Candidate list unchanged or drift documented | Required. |
| Private-state and secret-like exclusions restated | Required. |
| Output policy confirmed | Required; no secret values, env values, logs, private-state contents, or runtime output. |

## Future Evidence Outputs

If separately authorized after preflight, create:

| Output | Purpose |
| --- | --- |
| `ops/migration/inventory/phase-7-runtime-loader-narrow-read-evidence-2026-06-28.md` | Record only the authorized narrow read results for the selected tier. |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-narrow-read-evidence-receipt-2026-06-28.md` | Record authorization, inputs, read boundaries, skipped actions, and remaining gates. |

Those outputs must not grant runtime behavior acceptance. They may only support a
later review deciding whether a next, narrower loader/runtime behavior plan is
safe.

## Stop Conditions For Future Evidence

Stop and do not read further if any future preflight or evidence step finds:

| Stop condition | Required response |
| --- | --- |
| Candidate path points into `state-private/`, logs, caches, active env, credentials, or secret-like files. | Stop and require a separate security/private-state authorization. |
| Candidate is a symlink or resolves outside `/home/jenn/AGENTS_OS_Workspace`. | Stop and require path-resolution review. |
| Candidate requires recursive listing to understand. | Stop unless recursive scope is separately authorized. |
| Candidate content read would be required during Tier A. | Stop; Tier A is metadata only. |
| Candidate suggests execution, install, network, remote, or build/test action. | Stop and require exact-run or remote/operational authorization. |
| Candidate hash or mode changes after preflight. | Stop and create a drift note before continuing. |

## Acceptance Limits

This plan can support only a future narrow read evidence package. It cannot
grant:

| Acceptance type | Status |
| --- | --- |
| Runtime behavior acceptance | Not authorized. |
| Loader behavior acceptance | Not authorized. |
| Full consumer integration acceptance | Not authorized. |
| Governance runtime enforcement acceptance | Not authorized. |
| Manifest/schema/content acceptance | Not authorized. |
| Full credential audit acceptance | Not authorized. |
| Maintenance/sync acceptance | Not authorized. |
| Remote/operational acceptance | Not authorized. |

## Planning Result

```text
PHASE_7_RUNTIME_LOADER_NARROW_READ_ALLOWLIST_PLAN_CREATED_NO_CANDIDATE_CONTENT_READ
```

The Phase 7 runtime/loader narrow read allowlist is planned only. Candidate
paths and read boundaries are defined for future authorization, but no candidate
path was read, listed, executed, parsed, or checked for existence by this plan.
