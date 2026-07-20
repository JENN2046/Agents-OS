# AGENTS OS Phase 5A M0-A Plan v0.1 R2 Narrow Closure Amendment

Status: fixed for fresh full atomic independent review
Runtime usable: no
Implementation authorized: no

## 1. Atomic relationship

This amendment closes only `PHASE5A-M0A-PLAN-IR-B01` through `B03` from the
R1 independent review. The four R1 subjects and the R1 manifest remain
immutable. Precedence is:

```text
R2 explicit replacements
→ R1 all other clauses
```

R1 and R2 are one non-partial plan-acceptance unit. R2 does not accept or
freeze Phase 5A, authorize implementation, or activate any runtime.

## 2. Closed F1–F6 implementation-obligation inventory

The R2 contract-obligation inventory is exhaustive for M0-A. Its
`canonical_subjects` must equal, by path and SHA-256, the union of every
`accepted_subjects` entry in the accepted F1 decision and frozen F2–F6
decisions: exactly 110 immutable files.

Every obligation has all of the following closed owners:

```text
source Phase and canonical subject set
M0-A disposition
Rust module owner
reducer or boundary owner
persistence row-class owner or explicit NONE_DERIVED_EPHEMERAL
positive test
negative test
replay test
crash test or explicit NOT_APPLICABLE_NO_TRANSACTION
```

An accepted subject without membership in the phase source set, an obligation
without an owner, or an implementation behavior not represented by an
obligation is `M0A_INCOMPLETE`. Frozen upstream reducers are consumed; Phase
5A must not create a second implementation of F1–F6 authority semantics.

## 3. Exhaustive persistence boundary

The R2 persistence profile replaces the R1 15-table list. Its table inventory
is exhaustive: implementation may create exactly the declared 18 tables and
no hidden table, view, trigger, virtual table, attached database, read pool, or
second connection.

All canonical immutable objects not assigned a dedicated table use
`canonical_fact`; their closed row-class-to-`fact_kind` mapping is normative.
`current_fact_pointer` may target only a committed `canonical_fact` tuple and
is updated by compare-and-set in the same `BEGIN IMMEDIATE` transaction that
inserts the new fact and Event.

F5 delivery attempts, dispatch arms, stored-first accounting, first-apply
eligibility, claims and receipts have dedicated exact rows. F6 Requirement,
Validation Set, attempt context, waiver, carry-forward, contextual assessment,
current decision and completion guard objects use exact `canonical_fact`
`fact_kind` values; their predecessor and current-head rules are preserved by
immutable rows plus the same-transaction current pointer CAS.

The profile's columns, keys, foreign keys, mutability rules and transaction
owners are the complete schema contract for M0-A. Any schema expansion after
plan freeze requires a new atomic review and Jenn decision.

## 4. Exact external materialization

The R2 external-materialization profile replaces R1's three self-declared
hash names with a reproducible protocol:

1. A closed planned source-file inventory is fixed before implementation.
2. Only regular files are allowed; symlinks, devices, sockets and hardlink
   ambiguity are forbidden.
3. Relative paths are NFC UTF-8 POSIX paths, sorted by UTF-8 byte order.
4. File modes normalize to `100644` or `100755`.
5. Every leaf commits path, mode, byte length and file SHA-256 using the exact
   length-prefixed record defined in the profile.
6. The content-tree SHA-256 commits the ordered leaf records.
7. The canonical package manifest commits source commit, inventory,
   content-tree digest, blocked-plugin-manifest digest and direct-entrypoint
   digest using exact canonical JSON bytes.
8. `plugin-manifest.json.block` has the exact payload fixed in the profile.
9. `index.js` is the single direct entrypoint and has the fixed export surface.
10. Materialization validation uses a clean linked worktree at the fixed
    VCPToolBox commit; only `Plugin/AGENTSOSResident/**` may differ, while all
    tracked VCPToolBox paths must remain byte-identical to the base commit.

The copied install tree is a projection, never the source of truth. The
blocked filename is mandatory; `plugin-manifest.json` is forbidden.

## 5. Verification

The deterministic R2 builder derives one closure witness from the R2 profiles,
the six acceptance decisions and all 110 canonical accepted subjects. The
offline validator independently re-derives:

- the exact 110-subject union and every file hash;
- the closed obligation IDs and their complete owner fields;
- exhaustive persistence table and row-class ownership;
- exact materialization inventory, tree-record algorithm, blocked manifest and
  entrypoint contract;
- R1 subject and manifest immutability;
- all nonimplementation and nonruntime boundaries.

Fixture equality is constructive evidence only. A fresh independent reviewer
must still read all fixed inputs and construct coordinated counterexamples.

## 6. Stop rule

R2 may enter Jenn's plan-freeze decision surface only after a fresh full atomic
hash-bound independent review returns `PASS_NO_BLOCKER`. Even plan freeze does
not start implementation. Rust, JavaScript, N-API, dependency installation,
SQLite creation and plugin materialization require Jenn's separate second
implementation decision.
