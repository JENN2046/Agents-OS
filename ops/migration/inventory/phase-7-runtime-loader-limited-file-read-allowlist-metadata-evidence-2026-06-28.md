# Phase 7 Runtime/Loader Limited File-Read Allowlist Metadata Evidence

Date: 2026-06-28

Status: collected.

This evidence records exact-path metadata/type checks for 10 limited file-read
allowlist candidates. It collects existence, path type, mode, indirect-path
marker, SHA-256, size bytes, and line count.

No file body text was printed, quoted, summarized, parsed, or recorded as
evidence. Hash and line-count commands emitted metadata only.

## Authorization

User request:

> 做 metadata/type evidence collection，只对 10 个候选做 exact-path metadata/type 检查，仍不读文件内容。

Allowed in this step:

- check the 10 exact candidate paths from the limited file-read allowlist plan
- collect existence, path type, mode, indirect-path marker, SHA-256, size bytes,
  and line count
- create this evidence file and a matching receipt

Not allowed in this step:

- print, quote, summarize, parse, or record file body text
- parse JSON, YAML, Markdown, lockfiles, manifests, or package configs
- execute validators, runtime, loaders, package managers, scripts, sync, deploy,
  network, or remote commands
- read hidden surfaces, generated artifacts, dependency directories, scripts, or
  nested paths
- grant runtime behavior, loader behavior, extension execution, governance router,
  or full consumer integration acceptance

## Input Stability

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-7-runtime-loader-limited-file-read-allowlist-plan-2026-06-28.md` | `6f3c4b80e77accfda16dbc28e96724928ba6799763e1242702064ccdd48dfaa7` | stable |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-limited-file-read-allowlist-metadata-preflight-receipt-2026-06-28.md` | `8408f92fe105a65cb4b0402eefef0208f79866410a025799559526e84d669949` | stable |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-top-level-name-allowlist-evidence-review-closeout-receipt-2026-06-28.md` | `acedac5e738504d3734bbae2063ec62284564d8ea83c3b4b6704f49ab9d0fe23` | stable |
| `ops/migration/inventory/phase-7-runtime-loader-top-level-name-allowlist-evidence-2026-06-28.md` | `6c390ae726cf85e8f081491fd8d6b53c86b7e895afbb8a8e0da6f5472049f197` | stable |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-top-level-name-allowlist-evidence-receipt-2026-06-28.md` | `7d47ad583c8a3403eaab3760cf38d1239dcb5777696c473af25211155244da45` | stable |

## Evidence Source

The complete metadata/type evidence command exited successfully after an earlier
partial timed attempt was discarded. The complete successful run is the source
for this evidence.

## Exact-Path Metadata Results

| Candidate path | Existence | Path type | Mode | Indirect path marker | SHA-256 | Size bytes | Line count | Metadata result |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| `runtime/README.md` | `yes` | `regular file` | `644` | `no` | `c12814eae1a5b10806f543ea2d6e1f894fb137472708ae11f4239212c5569016` | `285` | `18` | PASS |
| `execution/README.md` | `yes` | `regular file` | `644` | `no` | `e46baba1fd315832b17f736be0ec5d3a55290df986476955709d89d5424c5652` | `324` | `19` | PASS |
| `governance/codex-router/AGENTS.md` | `yes` | `regular file` | `644` | `no` | `80c886818565cb5cf1cff7b0fd3c89442b3a60d47c5f9d8e36d9d52cfbf4f456` | `15754` | `667` | PASS |
| `governance/codex-router/PROJECT_CONTINUE_ANCHOR.md` | `yes` | `regular file` | `644` | `no` | `c27bced1a8ff3852c23043b6446f6fef65c6c587124537b2384f65260925f87c` | `9681` | `206` | PASS |
| `governance/codex-router/README.AGENTS_OS.md` | `yes` | `regular file` | `644` | `no` | `21055db98edc2f5a7fea54d362f55781c12fe3b68800a7b721d783ee6f1f06a9` | `920` | `61` | PASS |
| `governance/codex-router/README.md` | `yes` | `regular file` | `644` | `no` | `12ecc0bff519fab4987b80fd545a3100a13ff21128a393e10ed946869302b9f5` | `12998` | `379` | PASS |
| `governance/codex-router/routing-policy.yaml` | `yes` | `regular file` | `644` | `no` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | `6318` | `254` | PASS |
| `governance/codex-router/package.json` | `yes` | `regular file` | `644` | `no` | `1b47d214f9061cdef874a8fe6a8c3793b0192aa2f483cd34cced8cbf7ee52fa0` | `1517` | `35` | PASS |
| `governance/codex-router/tsconfig.json` | `yes` | `regular file` | `644` | `no` | `45e1952e19954cd2c20f1c4d590e05984c5fdc80dd4d9e400d3b59ce85b69f33` | `475` | `21` | PASS |
| `governance/codex-router/package-lock.json` | `yes` | `regular file` | `644` | `no` | `830567045e78d2c5a46dd433035391c1c21f29a1e7dde83aace0f332ae855f23` | `18677` | `618` | PASS |

## Read-Cap Feasibility Notes

These notes do not authorize content reads. They compare metadata against the
future caps planned earlier.

| Candidate path | Planned class | Cap feasibility note |
| --- | --- | --- |
| `runtime/README.md` | Runtime Markdown | Under planned `160` line / `32 KiB` cap. |
| `execution/README.md` | Execution Markdown | Under planned `160` line / `32 KiB` cap. |
| `governance/codex-router/AGENTS.md` | Governance Markdown | Exceeds planned `200` line cap; content read should remain deferred or require a revised cap plan. |
| `governance/codex-router/PROJECT_CONTINUE_ANCHOR.md` | Governance Markdown | Exceeds planned `200` line cap by line count; content read should remain deferred or require a revised cap plan. |
| `governance/codex-router/README.AGENTS_OS.md` | Governance Markdown | Under planned `200` line / `48 KiB` cap. |
| `governance/codex-router/README.md` | Governance Markdown | Exceeds planned `200` line cap; content read should remain deferred or require a revised cap plan. |
| `governance/codex-router/routing-policy.yaml` | Governance policy YAML | Exceeds planned `200` line cap; content read and parse review should remain separate. |
| `governance/codex-router/package.json` | Small JSON config | Under planned `200` line / `48 KiB` cap; script execution remains forbidden. |
| `governance/codex-router/tsconfig.json` | Small JSON config | Under planned `200` line / `48 KiB` cap; build/typecheck execution remains forbidden. |
| `governance/codex-router/package-lock.json` | Lockfile JSON | Metadata only in this track; content read requires a lockfile-specific plan. |

## Boundary Compliance

| Boundary | Result |
| --- | --- |
| Exact candidate paths only | PASS |
| Candidate count remained `10` | PASS |
| Existence/type/mode/indirect marker collected | PASS |
| SHA-256, size, and line count collected | PASS |
| No file body text printed, quoted, summarized, parsed, or recorded | PASS |
| No JSON/YAML/Markdown/lockfile parsing | PASS |
| No nested path listing | PASS |
| No hidden-surface inspection | PASS |
| No validator/script/runtime/loader execution | PASS |
| No remote/sync/deploy/network command | PASS |

## Not Verified

- File contents were not semantically inspected.
- JSON, YAML, Markdown, lockfiles, manifests, package configs, scripts, and
  policies were not parsed.
- Package scripts were not read as executable intent or executed.
- Routing policy semantics were not evaluated.
- Hidden surfaces were not inspected.
- Runtime, loader, extension, execution, governance-router, and consumer behavior
  were not executed or accepted.
- Full consumer integration was not verified.

## Result

Metadata/type evidence was collected for all 10 exact candidates. All 10 exist
as regular, non-indirect files with mode `644`. This evidence does not authorize
content reads, parsing, execution, or runtime/loader acceptance.

Marker:

```text
PHASE_7_RUNTIME_LOADER_LIMITED_FILE_READ_ALLOWLIST_METADATA_EVIDENCE_COLLECTED_EXACT_PATH_ONLY_NO_CONTENT_OUTPUT
```
