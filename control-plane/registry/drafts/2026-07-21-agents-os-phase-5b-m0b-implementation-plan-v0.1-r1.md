# AGENTS OS Phase 5B M0-B Implementation Plan v0.1 R1

```yaml
plan_id: PHASE_5B_M0_HOME_TO_ACTION_BOUNDARY_IMPLEMENTATION_PLAN_V0_1_R1
date: 2026-07-21
owner: Jenn
agent_steward: Nobao
status: FIXED_FOR_HASH_BOUND_INDEPENDENT_REVIEW
acceptance_unit: PHASE_5B_M0B_PLAN_BUILD_PROFILE_V0_1_R1_ATOMIC_BUNDLE
partial_acceptance: forbidden
implementation_authorized: false
runtime_activation_authorized: false
```

## 1. Purpose

Phase 5B M0-B will prove the minimum non-automatic path from synthetic Session
content to an F3-owned synthetic Command acknowledgement. This document freezes
how that future implementation will be built; it does not build or activate it.

The complete M0-B path is:

```text
synthetic Session observation
├── ephemeral_only / discard               -> no canonical write
├── remain_in_session                       -> no canonical write
└── explicit Life Stream candidate proposal -> F7 candidate-only revision
    ├── observe                             -> no further promotion
    ├── discard                             -> no further promotion
    ├── explicit Memory Candidate proposal  -> candidate only, no Memory write
    └── explicit Intent Candidate proposal  -> candidate only
        -> F8 nonauthoritative handoff candidate
        -> adapter constructs a synthetic F3 CommandSubmission
        -> F3 alone authenticates and commits/rejects/replays
```

No arrow is inferred from content existence, relationship, trust, role,
urgency, sentiment, history, usefulness or a Prohibited Behavior List no-match.

M0-B must prove:

```text
ordinary conversation does not create Goal or Task
ordinary thought does not create Task
Session content does not automatically form a Life Stream candidate
Memory Candidate does not become formal or long-term Memory
relationship does not expand authority
Home never writes Task state or commits a Command
raw Session content never enters the canonical Ledger
only F3 can report a synthetic Command as committed
```

## 2. Ownership and topology

The future source change is an extension of the existing Jenn-owned package:

```text
extensions/agents-os-resident/
```

M0-B does not create a second plugin, daemon, database writer, queue, Memory
service or runtime. It reuses the Phase 5A M0-A topology:

```text
synthetic Rust test harness
  -> pure Home boundary reducers
  -> existing Rust-owned ledger thread
  -> one temporary isolated SQLite connection
  -> existing F3 command-intake reducer
  -> existing five-method N-API remains unchanged
```

The VCPToolBox core diff remains zero. `plugin-manifest.json.block` remains
blocked. The installed VCPToolBox overlay and active runtime are not used during
M0-B construction or validation.

The current Phase 5A package manifest is the engineering baseline:

```text
extensions/agents-os-resident/package-manifest.json
SHA-256: 5b9d1bf3dcb51278addf9d944a77307453feafc35713e3ec9d6dac0fc815a495
```

Any future M0-B source commit must replace that manifest with a new exact file
inventory and content-tree hash. It may not rewrite the Phase 5A manifest or
claim the old content tree describes new files.

## 3. Data boundary

The Session host remains the transient authority for Session content. M0-B
receives only a synthetic observation envelope containing stable references,
revisions, commitments and an explicit branch choice. It never receives a
production conversation transcript or private raw Memory.

The canonical Ledger may contain only:

```text
source subject ref / revision / fingerprint
payload commitment
creator assessment ref / fingerprint
explicit choice enum
candidate ref / revision / fingerprint
predecessor ref / fingerprint
F8 handoff ref / fingerprint
F3 intake acknowledgement ref / fingerprint
Event ref / sequence / fingerprint
```

It may not contain:

```text
raw conversation or thought text
private Memory payload or excerpt
provider response
credential, token, cookie or key
audio, image, sensor or device payload
filesystem path supplied by a caller
formal Memory content
```

`EPHEMERAL_ONLY`, `DISCARD` and `REMAIN_IN_SESSION` return deterministic
nonpromotion results and write zero candidate, Event, pointer, Inbox or Outbox
rows. Test diagnostics stay outside the canonical Ledger.

## 4. Authority consumption

M0-B consumes, but does not recompute, exact current owner assessments from the
frozen contracts:

```text
F2 creator Actor / Principal / responsibility assessments
F3 Resident readiness and Command intake results
F7 candidate currentness and immutable candidate history
F8 owner commitments, handoff decision and acknowledgement requirements
current PBL assessment
current Jenn exact decision only when the owner requirement says it is required
```

The implementation verifies exact ref, revision, fingerprint, immutable owner
commitment, current-head marker, context and minimum Event watermark. Missing,
stale, conflicting, malformed, unknown or unavailable evidence fails closed.

Home may not derive Actor lifecycle, Principal binding, responsibility,
delegation, F3 readiness, PBL currentness or Jenn authorization. A favorable F7
or F8 result is candidate evidence, not permission or Command authority.

## 5. Work packages

Implementation after a separate Jenn implementation-start decision proceeds in
this exact order:

| Work package | Result | Advancement condition |
|---|---|---|
| WP0 M0-B extension skeleton | fixed module/test layout, inherited locks, schema v2 migration stub, unchanged N-API exports | Phase 5A tests pass byte-for-byte and no new dependency or N-API method appears |
| WP1 Session nonpromotion boundary | strict synthetic observation decoder and `EPHEMERAL_ONLY` / `DISCARD` / `REMAIN_IN_SESSION` reducers | all three paths make zero canonical writes and raw-content probes reject |
| WP2 F7 candidate revisions | immutable low-disclosure `LIFE_STREAM_CANDIDATE`, `MEMORY_CANDIDATE`, `INTENT_CANDIDATE` revisions | exact predecessor/current-head and same-revision rewrite tests pass |
| WP3 Explicit promotion gates | observe, discard, Memory Candidate and Intent Candidate transitions | every missing or implicit choice fails closed; no Memory, Goal or Task writer exists |
| WP4 F8 handoff composition | consume frozen R1-R5 owner commitments and canonical history to form a nonauthority handoff candidate | phantom history, owner rewrite, stale watermark and direct-write tests pass |
| WP5 F3 synthetic intake seam | implementation-only synthetic command definition and adapter through existing `execute_command` | F3 alone authenticates, commits, rejects and replays; Home owns no Command row |
| WP6 Ledger privacy and recovery | schema v2 candidate/link rows, atomic Event/pointer updates and low-disclosure recovery | crash matrix, quick/foreign-key checks and no-raw-content scans pass |
| WP7 Integrated M0-B witness | complete synthetic branch tree plus committed/rejected/indeterminate F3 outcomes | two clean runs and one restart run are deterministic with zero real occurrences |

No package may skip its predecessor. A failure is repaired within the frozen
scope; it cannot add a service, new permission model or runtime activation.

## 6. Implementation-only synthetic seam

The only new command type permitted in M0-B is:

```text
M0_SYNTHETIC_SUBMIT_HOME_INTENT
```

It is a test-only entry in the existing `SYNTHETIC_TEST` command-definition
registry. It is not the production F3 type requested prospectively by F8, does
not satisfy that future compatibility gate and cannot load outside the
production-incompatible synthetic domain.

The adapter constructs an existing frozen `CommandSubmission` candidate using
only the exact F8 handoff tuple and synthetic principal material. It calls the
existing `execute_command` path. It may not write `inbox_command`,
`command_envelope`, `replay_index` or Event rows itself.

No sixth N-API method, lifecycle method, filesystem path, SQL, callback,
provider handle or executable JavaScript object is introduced.

## 7. Persistence and atomicity

M0-B advances a new temporary-test schema version:

```text
v1 -> v2
```

The v2 migration is allowed only for a fresh or copied synthetic test database.
Production or existing databases remain forbidden.

New canonical row classes are limited to:

```text
home_candidate_revision   immutable low-disclosure candidate revision
home_candidate_head       compare-and-set current pointer
home_handoff_link         immutable F7 candidate to F8 handoff tuple
```

Candidate formation atomically commits the immutable candidate, its Event and
the candidate-head CAS. Handoff link formation atomically commits the exact
link and Event after rechecking candidate currentness. F3 intake remains a
separate F3-owned transaction and is observed only through its immutable
assessment/acknowledgement.

There is deliberately no `session_content`, `memory_content`, relationship,
Task, permission, provider or sensing table in M0-B.

## 8. Replay and recovery

Every mutating synthetic request binds canonical request bytes and an
idempotency key. Exact replay returns the first committed accounting. Same ID
with different canonical bytes is a protocol conflict. Same-revision candidate
or handoff rewriting is rejected against immutable history.

After restart:

```text
candidate/Event/head committed together or not at all
handoff link/Event committed together or not at all
F3 committed outcome is replayed by F3
missing or ambiguous F3 outcome remains INDETERMINATE
no candidate, handoff or Command is automatically retried or promoted
```

M0-B creates no Outbox effect and cannot turn an F3 acknowledgement into F4
admission or F5 delivery.

## 9. Stop and acceptance rules

This plan package must receive a Fresh Full Atomic Hash-Bound Independent
Review. Author validation and author self-review are evidence only.

An independent `PASS_NO_BLOCKER` does not freeze this plan. Jenn must atomically
accept and freeze the complete R1 unit. Even that freeze does not start
implementation. Governance must stop at:

```text
AWAITING_JENN_PHASE_5B_M0B_IMPLEMENTATION_START_DECISION
```

Only a later exact Jenn decision may authorize WP0. Runtime activation,
production authentication, real Session content, private Memory, providers,
sensing, VCPToolBox startup and real effects remain separate future gates.
