# Phase 7 Runtime/Loader Limited Content-Read Allowlist Plan

Date: 2026-06-28

Status: plan only.

This document plans a future limited content-read gate for the five candidates
admitted by the metadata/type evidence review. It defines exact candidates,
future preflight requirements, read caps, output format, redaction rules, red
lines, and stop conditions.

It does not read file contents, parse Markdown/JSON/YAML, execute scripts, or
grant runtime/loader acceptance.

## Authorization

User request:

> 自动继续推进

Autonomous safe continuation applied to this planning-only step. The previous
closeout admitted limited content-read allowlist planning for five candidates
and kept direct content-read evidence collection not admitted.

Allowed in this step:

- create this planning-only document
- use existing metadata/type evidence and closeout receipts as inputs
- define exact admitted candidates, deferred candidates, future preflight,
  read caps, output format, redaction rules, red lines, and stop conditions

Not allowed in this step:

- read candidate file contents
- parse Markdown, JSON, YAML, lockfiles, manifests, package configs, or policies
- execute package scripts, validators, runtime, loaders, builds, tests, sync,
  deploy, network, or remote commands
- modify registry, consumers, runtime, extensions, execution, or governance
- grant runtime behavior, loader behavior, extension execution, governance router,
  or full consumer integration acceptance

## Inputs Rechecked Before Plan Creation

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-limited-file-read-allowlist-metadata-evidence-review-closeout-receipt-2026-06-28.md` | `b6b64bb5812b683b9e2a0022bbe24844ff14dbf2ba95d2ef9e9db405bf70e24e` | Admits limited content-read allowlist planning for five candidates and defers five candidates. |
| `ops/migration/inventory/phase-7-runtime-loader-limited-file-read-allowlist-metadata-evidence-2026-06-28.md` | `e987f293d26587a9dbecaf143fa49b36764944110b746404bef569ffa1aa6ef7` | Provides exact-path metadata/type evidence and file hashes. |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-limited-file-read-allowlist-metadata-evidence-receipt-2026-06-28.md` | `024c947d5f3ec4d5fd35758adcffec48cf9ff3addce2b17516166809762be235` | Confirms metadata/type evidence was collected without content output. |
| `ops/migration/plans/phase-7-runtime-loader-limited-file-read-allowlist-plan-2026-06-28.md` | `6f3c4b80e77accfda16dbc28e96724928ba6799763e1242702064ccdd48dfaa7` | Defines earlier file-read candidate classes, metadata preflight, and caps. |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-limited-file-read-allowlist-metadata-preflight-receipt-2026-06-28.md` | `8408f92fe105a65cb4b0402eefef0208f79866410a025799559526e84d669949` | Confirms metadata/type preflight. |

Target absence confirmed before creation:

| Future target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-7-runtime-loader-limited-content-read-allowlist-plan-2026-06-28.md` | absent |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-limited-content-read-allowlist-preflight-receipt-2026-06-28.md` | absent |
| `ops/migration/inventory/phase-7-runtime-loader-limited-content-read-evidence-2026-06-28.md` | absent |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-limited-content-read-evidence-receipt-2026-06-28.md` | absent |

## Admitted Content-Read Planning Candidates

The next content-read preflight may consider only these five candidates:

| Candidate path | Class | SHA-256 from metadata evidence | Size bytes | Line count | Future maximum read cap |
| --- | --- | --- | ---: | ---: | --- |
| `runtime/README.md` | Runtime Markdown | `c12814eae1a5b10806f543ea2d6e1f894fb137472708ae11f4239212c5569016` | `285` | `18` | Full file allowed only if hash stable; max `160` lines / `32 KiB`. |
| `execution/README.md` | Execution Markdown | `e46baba1fd315832b17f736be0ec5d3a55290df986476955709d89d5424c5652` | `324` | `19` | Full file allowed only if hash stable; max `160` lines / `32 KiB`. |
| `governance/codex-router/README.AGENTS_OS.md` | Governance Markdown | `21055db98edc2f5a7fea54d362f55781c12fe3b68800a7b721d783ee6f1f06a9` | `920` | `61` | Full file allowed only if hash stable; max `200` lines / `48 KiB`. |
| `governance/codex-router/package.json` | Package manifest JSON text | `1b47d214f9061cdef874a8fe6a8c3793b0192aa2f483cd34cced8cbf7ee52fa0` | `1517` | `35` | Full file text allowed only if hash stable; max `200` lines / `48 KiB`; no script execution. |
| `governance/codex-router/tsconfig.json` | TypeScript config JSON text | `45e1952e19954cd2c20f1c4d590e05984c5fdc80dd4d9e400d3b59ce85b69f33` | `475` | `21` | Full file text allowed only if hash stable; max `200` lines / `48 KiB`; no build/typecheck execution. |

No other file is admitted to the next content-read preflight.

## Deferred Candidates

These candidates remain outside the next limited content-read plan:

| Candidate path | Deferred reason | Required future gate |
| --- | --- | --- |
| `governance/codex-router/AGENTS.md` | Exceeds current `200` line governance Markdown cap. | Revised-cap or section-scoped content-read plan. |
| `governance/codex-router/PROJECT_CONTINUE_ANCHOR.md` | Exceeds current `200` line governance Markdown cap by line count. | Revised-cap or section-scoped content-read plan. |
| `governance/codex-router/README.md` | Exceeds current `200` line governance Markdown cap. | Revised-cap or section-scoped content-read plan. |
| `governance/codex-router/routing-policy.yaml` | Exceeds current line cap and requires YAML parse/semantic separation. | YAML-specific read/parse authorization plan. |
| `governance/codex-router/package-lock.json` | Lockfile content read remains deferred by prior plan. | Lockfile-specific gate only. |

## Future Content-Read Preflight

Before any content-read evidence is collected, a later preflight must confirm:

| Check | Required result |
| --- | --- |
| This plan hash | Stable from plan creation. |
| Metadata evidence review closeout hash | Stable at `b6b64bb5812b683b9e2a0022bbe24844ff14dbf2ba95d2ef9e9db405bf70e24e`. |
| Metadata evidence hash | Stable at `e987f293d26587a9dbecaf143fa49b36764944110b746404bef569ffa1aa6ef7`. |
| Metadata evidence receipt hash | Stable at `024c947d5f3ec4d5fd35758adcffec48cf9ff3addce2b17516166809762be235`. |
| Future content evidence target | Absent before creation. |
| Future content receipt target | Absent before creation. |
| Admitted candidate set | Exactly the five candidates in this plan; no additions. |
| Candidate file hashes | Match the hashes recorded in this plan. |
| Candidate file modes/types | Still regular, non-indirect files with mode `644`. |
| Read command boundary | Enforces per-file line/byte caps before evidence is written. |
| Redaction method | Secret-like, token-like, credential-like, private URL, raw env value, and key-like content must be redacted before evidence is written. |

If any required result fails, content-read evidence collection is not admitted.

## Future Evidence Output Format

A future content-read evidence step, if separately authorized, must use bounded
summaries and redacted snippets only. It must not dump full file bodies unless
the file is under the cap and the evidence explicitly records that a full-file
bounded read was authorized for that file.

Allowed output fields:

| Field | Meaning |
| --- | --- |
| Candidate path | Exact admitted path. |
| File class | Class from this plan. |
| Hash verified | Whether the hash matched this plan before reading. |
| Lines read | Bounded line count actually read. |
| Bytes read | Bounded byte count actually read. |
| Redaction count | Count and class of redactions, without raw secret values. |
| Static findings | Short bullets derived from visible text only. |
| Authority-risk label | `runtime-doc`, `execution-doc`, `governance-doc`, `package-manifest-text`, or `tsconfig-text`. |
| Not granted | Explicit statement that behavior, parsing, execution, and acceptance remain deferred. |

Forbidden output:

- raw secret values
- complete raw command output dumps
- package script execution
- parsed dependency trees
- parsed compiler options
- semantic acceptance of package or tsconfig behavior
- runtime/router/loader acceptance
- content from deferred candidates
- content from files referenced by admitted candidates

## Red Lines

The future preflight or content-read evidence step must stop when:

| Red line | Required handling |
| --- | --- |
| Any input hash drifts | Stop before reading content. |
| Any admitted candidate hash drifts | Stop for that candidate and record `CANDIDATE_DRIFT`. |
| Candidate set changes | Stop before reading content. |
| Candidate becomes missing, non-regular, or indirect | Stop for that candidate. |
| File exceeds planned line or byte cap | Stop for that candidate and record `READ_LIMIT_EXCEEDED`. |
| Redaction cannot be applied before writing evidence | Stop before writing evidence. |
| Content contains secret-like, token-like, credential-like, raw env, or private URL values | Redact values and record counts only. |
| `package.json` contains scripts | Record as static text only if visible in authorized read; do not execute or treat as authorization. |
| `tsconfig.json` contains compiler options | Record as static text only if visible in authorized read; do not run build or typecheck. |
| Markdown text appears authoritative | Label authority risk; do not grant runtime, execution, governance, router, or consumer acceptance. |
| Content references other files | Record reference only if visible; do not open referenced files. |
| Any request asks to parse, execute, install, build, test, sync, deploy, network, or remote-write | Stop and require a separate plan/authorization. |

## Stop Conditions

Stop before future content-read evidence collection if:

- this plan hash drifts
- required input hashes drift
- future evidence or receipt targets already exist
- admitted candidate set differs from this plan
- candidate hash/mode/type/indirect state differs from metadata evidence
- the read command cannot enforce caps
- redaction cannot be guaranteed before evidence write
- the action would read deferred candidates
- the action would read referenced files
- the action would parse JSON/YAML/Markdown or execute scripts
- the action would imply runtime/loader/router/consumer acceptance

## Future Outputs

If separately authorized after preflight, the next content-read gate may create:

| Output | Purpose |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-limited-content-read-allowlist-preflight-receipt-2026-06-28.md` | Receipt confirming plan/input/candidate stability, caps, redaction method, and target absence before content read. |
| `ops/migration/inventory/phase-7-runtime-loader-limited-content-read-evidence-2026-06-28.md` | Redacted bounded content evidence for the admitted five candidates only. |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-limited-content-read-evidence-receipt-2026-06-28.md` | Receipt recording files read, caps enforced, redactions, deferred items, and unverified items. |

This plan does not authorize these outputs by itself.

## Acceptance Boundary

This plan can only support a future bounded content-read preflight and evidence
gate.

It cannot grant:

- content-read evidence collection without separate preflight/authorization
- parsing or semantic review authorization
- package script execution
- build/typecheck/test execution
- runtime behavior acceptance
- loader behavior acceptance
- extension execution acceptance
- governance router acceptance
- full consumer integration acceptance
- migration, rewrite, or normalization authorization

## Result

Limited content-read allowlist planning is complete for five admitted candidates.
Five candidates remain deferred. The next safe step is a formal content-read
preflight that confirms plan/input/candidate stability and redaction/cap
boundaries before any content is read.

Marker:

```text
PHASE_7_RUNTIME_LOADER_LIMITED_CONTENT_READ_ALLOWLIST_PLAN_CREATED_NO_CONTENT_READ
```
