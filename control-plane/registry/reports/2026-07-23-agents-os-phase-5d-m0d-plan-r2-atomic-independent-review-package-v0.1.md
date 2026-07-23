# AGENTS OS Phase 5D M0-D Plan R2 Atomic Independent Review Package v0.1

Status: fixed for Fresh Full Atomic Hash-Bound Independent Review  
Date: 2026-07-23

## Review unit

```yaml
review_unit: PHASE_5D_M0D_PLAN_BUILD_PROFILE_V0_1_R2_ATOMIC_BUNDLE
atomic: true
partial_review: forbidden
subjects: 6
authority_inputs: 20
author_evidence: 3
declared_inputs: 29
manifest_sha256: f8c4dc55df8c7110462d1ec117856df275edaf654ab057f083ce1817f7bbb061
```

R1 is immutable historical evidence. R2 replaces only the clauses needed to
close R1's three independent-review blockers: exact immutable source/Host/
extension commitments, Plan-to-outcome semantic binding, and duplicate-key /
profile-identity totality.

## Required reviewer procedure

1. Treat the manifest as the atomic unit; recompute all 29 input hashes and
   fully read all six subjects, all twenty authority inputs and all three author
   evidence files.
2. Verify the ZIP has no duplicate, unsafe or symlink member; verify CRC,
   `CHECKSUMS.sha256`, `ARCHIVE_MAP.json`, and byte equality between archive and
   declared workspace payloads.
3. Run all six fixed commands in the workspace and again from an isolated ZIP
   extraction without `.git`.
4. Do not use the author self-review as a decision substitute.
5. Independently fully re-sign attacks after editing only isolated package
   copies. Recompute dependent fixture, manifest, archive map and checksums.

## Required attacks

The review must establish target-semantic rejection, not merely a stale outer
hash mismatch, for at least these cases:

```text
source payload commit substitution
sealed Host commit/tree substitution
each seven-path Host row substitution
extension manifest / blocked manifest / entrypoint hash substitution
absolute or alternate source root
Plan text claiming current Host/plugin/runtime execution
Plan text claiming processToolCall/native execution
duplicate YAML profile key
noncanonical schema_version, profile_id or status
coordinated Plan + profile + fixture resigning
runtime_usable, real occurrence or Host-executed outcome forgery
```

R2 is valid only if each attack is rejected by the immutable source anchor,
exact Plan semantic binding, strict duplicate-key parser or closed profile /
witness semantics. A pre-existing outer archive hash alone is insufficient.

## Boundary

No review step may read or create a VCPToolBox worktree, deliver/install an
archive, enable/discover/load a plugin, invoke lifecycle methods,
`processToolCall`, native N-API, runtime/service, database, provider,
authentication, private Memory, sensing or effect. The fixture is synthetic;
the only allowed favorable result is the non-executing planning outcome
`QUARANTINED_HOST_SMOKE_PREFLIGHT_READY` with `runtime_usable=false` and
`real_occurrence_count=0`.

## Allowed outcomes

```yaml
allowed_results:
  - PASS_NO_BLOCKER
  - BLOCK

PASS_NO_BLOCKER:
  means: independent review gate only
  does_not_mean:
    - plan acceptance or freeze
    - implementation authorization
    - VCPToolBox access
    - archive delivery or plugin enablement
    - Host/native/runtime/database/provider/private-Memory/effect execution

BLOCK:
  requires: preserve R1_R2 bytes, record finding disposition, and await a new Jenn narrow revision decision
```
