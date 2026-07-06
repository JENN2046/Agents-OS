# Phase 7 Runtime/Loader Tier B Narrow Text-Read Plan

Date: 2026-06-28

Status: plan only.

This document plans the future narrow text-read boundary for three README files
identified by Tier A metadata evidence. It does not read candidate README body
text, collect Tier B evidence, execute scripts, inspect runtime behavior, or
grant runtime/loader acceptance.

## Authorization

User request:

> 创建 Phase 7 Tier B narrow text-read plan，只规划这 3 个 README 的读取边界和红线，不实际读取正文。

Allowed in this step:

- create this Tier B narrow text-read plan
- use existing Tier A metadata and closeout receipts as inputs
- define exact future read boundaries, red lines, preflight requirements, and
  stop conditions

Not allowed in this step:

- read `runtime/README.md`
- read `extensions/README.md`
- read `execution/README.md`
- list directory contents below runtime, extensions, execution, or governance
- collect Tier B text-read evidence
- execute validators, loaders, runtime code, scripts, package managers, or sync
  commands
- modify consumers, registry, runtime, extensions, execution, or governance
- grant runtime behavior, loader behavior, or full consumer integration
  acceptance

## Inputs Rechecked Before Plan Creation

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-tier-a-metadata-evidence-review-closeout-receipt-2026-06-28.md` | `ec66555b9bce59bbec6139b0a91b75a0f96038ef5e940660e106e233f2475c48` | Confirms Tier B narrow text-read planning is admitted, but direct text-read evidence collection is not admitted yet. |
| `ops/migration/inventory/phase-7-runtime-loader-narrow-read-evidence-2026-06-28.md` | `bb7c0374b57ae2efe7a430df226b563d7fc2624586e284d604c70a4a103a68f1` | Provides Tier A metadata for the three README files. |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-narrow-read-evidence-receipt-2026-06-28.md` | `c90328ddef21c2f704b224ebaef72f7096453e3bb91832fb9f4e7cfc29c7bfb6` | Confirms Tier A metadata evidence was collected without content reads. |
| `ops/migration/plans/phase-7-runtime-loader-narrow-read-allowlist-plan-2026-06-28.md` | `fde040c04129a3af270fd2430730deced5063249b9834898689afd93c8e059f1` | Provides the original Phase 7 narrow-read candidate allowlist. |
| `ops/migration/plans/phase-7-scope-plan-2026-06-28.md` | `977c524caac711f8db669bcf2e08989947a2b6c351e3487fd38379c208dc2eda` | Confirms Phase 7 started with runtime/loader narrow-read planning only. |

Target absence confirmed before creation:

| Future target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-7-runtime-loader-tier-b-narrow-text-read-plan-2026-06-28.md` | absent |
| `ops/migration/inventory/phase-7-runtime-loader-tier-b-narrow-text-read-evidence-2026-06-28.md` | absent |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-tier-b-narrow-text-read-evidence-receipt-2026-06-28.md` | absent |

## Tier B Candidate Set

Only these three files are eligible for a future Tier B narrow text-read
preflight and evidence step:

| Candidate README | Tier A type | Tier A mode | Tier A SHA-256 |
| --- | --- | --- | --- |
| `runtime/README.md` | `regular_file` | `644` | `c12814eae1a5b10806f543ea2d6e1f894fb137472708ae11f4239212c5569016` |
| `extensions/README.md` | `regular_file` | `644` | `1b27b274275fdfa6a0721c1cbea7b15de24253d02a27c750533a9cfebf1d3da1` |
| `execution/README.md` | `regular_file` | `644` | `e46baba1fd315832b17f736be0ec5d3a55290df986476955709d89d5424c5652` |

Excluded from Tier B text-read scope:

| Excluded candidate group | Reason |
| --- | --- |
| `extensions/vcp-toolbox-jenn/`, `governance/codex-router/` | Directories require a separate directory-boundary plan before any child read. |
| `runtime/VCPToolBox/Plugin.js`, `runtime/VCPToolBox/adminServer.js`, `runtime/VCPToolBox/routes/`, `runtime/VCPToolBox/modules/`, `runtime/VCPToolBox/AdminPanel-Vue/` | Tier A recorded these planned paths as missing, so they cannot be read at current paths. |
| Any file outside the three README paths above | Out of scope for this Tier B plan. |

## Future Narrow Text-Read Boundary

A later authorized Tier B evidence step may read only the three candidate README
files above, and only after a separate preflight passes.

Allowed future read purpose:

- identify declared runtime, loader, extension, and execution responsibilities
- identify references to registry consumers, validation scripts, or integration
  surfaces
- identify whether each README is authority-like, reference-like, or stale
- record concise findings and exact path references needed for Phase 7 review

Allowed future read method:

- read the three README files as text only
- do not execute anything referenced by the README files
- do not follow links, imports, scripts, or path references into other files
- do not recursively list directories
- do not normalize, rewrite, or migrate content during evidence collection
- summarize findings; do not dump full README content into evidence

Per-file content limit for a future evidence step:

| README | Future read cap |
| --- | --- |
| `runtime/README.md` | At most first `120` lines and at most `24 KiB`, whichever limit is reached first. |
| `extensions/README.md` | At most first `120` lines and at most `24 KiB`, whichever limit is reached first. |
| `execution/README.md` | At most first `120` lines and at most `24 KiB`, whichever limit is reached first. |

If a file exceeds either cap, the future evidence step must stop for that file
and record `READ_LIMIT_EXCEEDED` without reading beyond the boundary.

## Red Lines

The future Tier B text-read evidence step must stop or redact when these
conditions appear:

| Red line | Required handling |
| --- | --- |
| Candidate hash or mode differs from Tier A metadata | Stop before reading that candidate and record `CANDIDATE_DRIFT`. |
| Candidate is no longer a regular file | Stop before reading that candidate and record `NOT_REGULAR_FILE`. |
| Candidate is a symlink, junction, mount, or indirect path | Stop before reading that candidate and record `INDIRECT_PATH`. |
| Read would require directory traversal, child listing, or following links | Stop that expansion and record `OUT_OF_SCOPE_EXPANSION`. |
| Secret-like assignment, token, key, credential, private URL, or raw env value appears | Do not copy the value; record only redacted hit count and pattern class. |
| README instructs remote sync, network calls, install, deploy, push, credential setup, or external service writes | Record the instruction as a risk summary only; do not execute or expand it. |
| README references code files, configs, manifests, or scripts outside the three README files | Record the reference path only if visible inside the allowed read cap; do not open the referenced file. |
| README content is binary, unreadable, or unexpectedly encoded | Stop that file and record `UNREADABLE_TEXT`. |
| User-owned work or unrelated drift is detected in planned target evidence files | Stop before writing evidence and ask for direction. |

## Future Preflight Required Before Any Text Read

A later authorized Tier B preflight must confirm:

| Check | Required result |
| --- | --- |
| This plan hash | Stable from plan creation. |
| Tier A metadata evidence hash | Stable at `bb7c0374b57ae2efe7a430df226b563d7fc2624586e284d604c70a4a103a68f1`. |
| Tier A review closeout hash | Stable at `ec66555b9bce59bbec6139b0a91b75a0f96038ef5e940660e106e233f2475c48`. |
| Future evidence target | Absent before evidence creation. |
| Future receipt target | Absent before receipt creation. |
| Candidate file identity | Each candidate remains a regular file with the same mode and SHA-256 recorded in Tier A metadata. |
| Candidate path class | No candidate is a symlink or indirect path. |
| Read cap feasibility | The evidence command must enforce the `120` line and `24 KiB` per-file caps. |
| Redaction method | Secret-like values must be redacted before evidence text is written. |

If any required result fails, Tier B text-read evidence collection is not
admitted.

## Future Evidence Outputs

If separately authorized after preflight, Tier B may create:

| Output | Purpose |
| --- | --- |
| `ops/migration/inventory/phase-7-runtime-loader-tier-b-narrow-text-read-evidence-2026-06-28.md` | Concise, redacted findings from the three README files within the read caps. |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-tier-b-narrow-text-read-evidence-receipt-2026-06-28.md` | Receipt recording preflight result, files read, limits enforced, redactions, and unverified items. |

This plan does not authorize either output by itself.

## Acceptance Boundary

Tier B narrow text-read evidence, even if later collected successfully, can only
support a static documentation readiness review.

It cannot grant:

- runtime behavior acceptance
- loader behavior acceptance
- extension execution acceptance
- registry semantic acceptance beyond previously granted L1 static registry
  acceptance
- full consumer integration acceptance
- permission to execute validators or runtime scripts
- permission to migrate, rewrite, or normalize runtime/extension content

## Stop Conditions For The Next Step

Stop before Tier B evidence collection if:

- this plan changes unexpectedly
- Tier A inputs drift
- any candidate README drifts from Tier A metadata
- a candidate path becomes indirect
- future evidence or receipt targets already exist
- evidence collection cannot enforce line, byte, and redaction limits
- the requested next action expands from README text evidence into runtime,
  loader, extension, directory, or script inspection

## Result

Tier B narrow text-read planning is complete for the three README candidates.
No candidate README body text was read in this planning step.

Marker:

```text
PHASE_7_RUNTIME_LOADER_TIER_B_NARROW_TEXT_READ_PLAN_CREATED_NO_TEXT_READ
```
