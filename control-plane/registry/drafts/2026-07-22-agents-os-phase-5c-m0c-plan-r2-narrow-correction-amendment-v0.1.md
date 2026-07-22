# AGENTS OS Phase 5C M0-C Plan R2 Narrow Correction Amendment v0.1

```yaml
amendment_id: PHASE_5C_M0C_PLAN_R2_NARROW_CORRECTION_AMENDMENT_V0_1
date: 2026-07-22
owner: Jenn
agent_steward: Nobao
status: FIXED_FOR_FRESH_FULL_ATOMIC_INDEPENDENT_REVIEW
review_unit: PHASE_5C_M0C_PLAN_BUILD_PROFILE_V0_1_R2_ATOMIC_BUNDLE
predecessor_review:
  path: control-plane/registry/reviews/2026-07-22-yellow-agents-os-phase-5c-m0c-plan-r1-full-atomic-independent-review.yaml
  sha256: c95974a58dcda60742a8ef3cfb8ab1abaea12f5d1bd2ff8d53b27c65e1200cd7
  result: BLOCK
replaces_only:
  - PHASE5C_M0C_PLAN_R1_IR_B01
  - PHASE5C_M0C_PLAN_R1_IR_B02
R1_all_other_clauses: remain_in_force_and_immutable
partial_acceptance: forbidden
```

## 1. Exact correction boundary

R2 closes precisely two R1 review findings. It adds no packaging capability,
plugin loader, service, identity, permission, Task, Command, effect, database,
or runtime authority.

1. The future archive is one exact, uncompressed POSIX ustar byte sequence with
   a closed member mapping, normalized headers, a defined SHA-256 preimage, and
   an exact success/failure delivery-and-cleanup state machine.
2. The synthetic witness carries structural records rather than favorable
   booleans. The validator derives sealing, member mapping, archive bytes,
   entrypoint lazy loading, N-API inventory, delivery, and cleanup from those
   records and fails closed.

The new source inventory profile is an immutable *future-build input seal*. It
does not read a VCPToolBox worktree, install or enable anything, or make the
synthetic fixture a production package.

## 2. Archive and delivery contract

The exact R2 archive/output contract is in
`2026-07-22-agents-os-phase-5c-m0c-exact-archive-output-lifecycle-profile-v0.1-r2.yaml`.
It is normative over R1's broad deterministic wording for this one topic.

```text
future sealed source inventory
-> UTF-8 bytewise ordered regular-file member mapping
-> uncompressed POSIX ustar encoding with normalized headers
-> SHA-256 of complete raw archive bytes
-> in-memory return only after owned temporary-root cleanup
```

No caller-controlled output path, persistent output location, filesystem
handoff, enabled manifest, native host loading, or VCPToolBox write is allowed.
On any error, no archive bytes are returned and the owned temporary root must
already be removed before the failure result is returned.

## 3. Structural proof contract

The R2 witness is `SYNTHETIC_TEST` only. It contains:

* a sealed source-inventory record set and its independently fixed digest;
* exact VCPToolBox commit/path/blob/SHA commitments consumed from R1's sealed
  host profile;
* a closed archive member mapping plus an actual small synthetic ustar byte
  exercise;
* actual entrypoint source bytes, derived CommonJS exports and lazy native-load
  placement;
* a closed N-API method inventory; and
* an exact output lifecycle event sequence with an empty residue inventory.

The synthetic archive exercise validates the encoder and lifecycle mechanics;
it is never an installable package, a Host input, or a substitute for a future
implementation's complete sealed-source hash checks.

## 4. Required negative proof

The validator must reject fully re-signed structural substitutions for every
previously unrepresentable R1 class: sealed host substitution, member
addition/removal/duplication/reordering/replacement, unsafe member kinds or
paths, eager native loading, output residue, and archive-format/metadata/
checksum-preimage drift. A rejection caused only by a stale fixture fingerprint
does not count.

## 5. Non-authorizations and stop rule

R2 changes only control-plane planning evidence. It does not authorize Rust,
JavaScript, N-API, SQLite, dependency installation, VCPToolBox changes,
plugin enablement, runtime activation, database access, production
authentication, private Memory, provider, sensing, effect, release, deploy,
publish, commit, push, or merge.

After the author package is fixed, the only next gate is:

```text
PHASE_5C_M0C_PLAN_R2_FRESH_FULL_ATOMIC_HASH_BOUND_INDEPENDENT_REVIEW
```

`PASS_NO_BLOCKER` from that review still requires a separate Jenn atomic plan
freeze decision. It never starts implementation.
