# AGENTS OS Runtime Reality Maps Salvage Package v0.1

Date: 2026-07-25
Status: LOCAL_CANDIDATE
Owner: Jenn
Agent steward: Nobao

## 1. Purpose

This package preserves three independent `FINDINGS_ONLY` runtime reality
reports from the canonical workspace without changing their bytes. The reports
remain historical source-audit snapshots dated 2026-07-12.

They are not current runtime readiness evidence, activation evidence, provider
evidence, or authorization to read configuration or private data.

## 2. Exact Salvage Base

```yaml
base_commit: 3a5ce7ab0af075f4b12f75ca16b2f1554f399536
base_tree: d0bd0b967ead4209a828cd1133ceab2b1c9a4a54
source: preserved canonical-root report bytes
source_git_provenance_claimed: false
report_bytes_modified: false
```

## 3. Hash-Bound Report Set

| Report | SHA-256 |
|---|---|
| `ops/reports/vcpchat-runtime-reality-map-2026-07-12.md` | `2d6e931ae7eca2f36eb7f3469518c56411666bb24aa36b8167a6aa5074668172` |
| `ops/reports/vcpmobile-runtime-reality-map-2026-07-12.md` | `cc6259534c7d46242b8bb3493bb8f74c7e8891efd61e66aad34b0086414aac21` |
| `ops/reports/vcptoolbox-runtime-reality-map-2026-07-12.md` | `cd1052d8d6edf5c141238984809de29790bdaf71910b19b04587bcdd97f8bc0e` |

## 4. Interpretation Boundary

- `VCPChat` records a read-only source audit against the report's declared
  `main` snapshot at `cfa5883b8373`.
- `VCPMobile` records a read-only source audit against the report's declared
  `main` snapshot at
  `b386d06a231985777de6038b78350a6801de4498`.
- `VCPToolBox` records the bounded local source/worktree reality observed by
  the report; this package does not add a commit provenance claim.
- Absolute `/home/jenn/...` paths inside the reports are preserved historical
  scope labels. They do not authorize access to those paths or assert that the
  same runtime state still exists.
- Findings and proposed integration phases remain analysis, not an active
  construction route or accepted implementation plan.

## 5. Retained Prohibitions

This package does not authorize runtime activation, Host or VCPToolBox Git,
provider execution, active configuration reads, private data or private Memory
reads, `state-private` access, database writes, release, deploy, publish, tag,
force push, history rewrite, push, PR, or merge.

## 6. Validation Contract

The package is valid only while:

1. all three reports exist as regular files;
2. every report SHA-256 matches Section 3;
3. each report still declares `status: FINDINGS_ONLY`;
4. the reports continue to state that runtime/provider/private-data or
   private-memory/config access was not performed;
5. the three report bytes remain exact copies of the preserved canonical-root
   source files at salvage time.
