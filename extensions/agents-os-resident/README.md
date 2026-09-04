# AGENTS OS Resident

This directory is the Jenn-owned source package for the local-owner Resident.
It contains the continuity, protected-Witness admission, Presence, Memory and
Current Work/Life paths used by the bounded local runtime, together with their
source-owned systemd projection and tests.

The package remains private and locally scoped. This source integration does
not claim M6 sustained-real-use closure, production readiness, E3/P5,
permanent cutover, or device/model/provider replacement. Its VCPToolBox
projection must retain `plugin-manifest.json.block`; an enabled
`plugin-manifest.json` is forbidden.

Authority-bearing companion exchanges authenticate the already-connected
Unix peer against the active systemd unit's exact `MainPID` before any attach
or protected request bytes are sent. Socket path ownership and mode remain
necessary profile checks, but are not treated as daemon identity. A path
replacement owned by the same UID therefore fails closed before a fabricated
Presence or provider-attempt seal can be accepted.

## Protected roots and one-shot Witness provisioning

After package installation has created the current-owner `0700` state parent,
prepare the three mutually disjoint Resident roots through the source-owned,
root-only profile:

```sh
npm run prepare:protected-roots -- \
  --root /absolute/agents-os-resident-local-owner-v1 \
  --witness-root /absolute/protected-witness \
  --memory-body-root /absolute/private-memory-bodies \
  --expected-build-id sha256:<64-lowercase-hex>
```

The command creates only absent roots as current-owner `0700` directories. An
existing exact root is accepted without changing its device/inode; a symlink,
wrong type, wrong owner, wrong mode, noncanonical path, unsafe parent or
overlapping topology fails closed without destructive repair. It does not read
an authority file, initialize Resident state or enroll a Witness.

Fresh protected-Witness state is then enrolled only through the explicit
one-shot provisioning profile. Obtain the sealed build ID and run:

```sh
npm run provision:witness -- \
  --root /absolute/agents-os-resident-local-owner-v1 \
  --witness-root /absolute/protected-witness \
  --memory-body-root /absolute/private-memory-bodies \
  --expected-build-id sha256:<64-lowercase-hex> \
  --genesis-authority-file /absolute/genesis-authority.json
```

The authority file is a current-owner, `0600`, single-link regular file at its
exact canonical path. It contains at most 4096 bytes of strict UTF-8 and one
canonical JSON object, without a trailing newline, in this exact key order:

```json
{"authorityId":"authority:<trusted-id>","protocol":"MMR0_GENESIS_PROVISIONING_V1","provisioningId":"provisioning:<trusted-id>","residentId":"resident:LOCAL_OWNER_SESSION_V1:jenn"}
```

Success prints only `RESIDENT_WITNESS_PROVISIONED` and exits after native
initialization and shutdown; no socket is started. Re-running provisioning
against an enrolled Witness is rejected and must not be treated as idempotent
success. The long-running systemd unit contains neither the authority file nor
inline genesis data and starts only after enrollment, using the protected
Witness as its continuity source. The one-shot command does not globally
consume a credential: after success, the trusted operator must remove, revoke,
or otherwise govern the authority file according to its issuing policy. It
must never be copied into the long-running unit.

WP0 establishes the deterministic package layout and WP1 establishes strict
canonical JSON/JCS/SHA-256 primitives. WP2 adds the synthetic Resident
ownership boundary: an OS-exclusive lock, immutable identity/incarnation/epoch
descriptors, one Rust ledger thread, one SQLite connection opened only under a
test-created temporary directory, and deterministic shutdown/join behavior.

WP3 adds the frozen ledger v1 storage boundary behind that same thread and
connection: the exact 18-table inventory, the two authorized immutable-history
triggers, a compiled schema seal, Event/fact/current-pointer atomic CAS, crash
rollback injection, and Inbox request-identity/replay observation. WP3 does not
admit a Command or expose any of these operations through N-API.

WP4 added the closed five-method Node-API boundary, strict canonical F3 request
and response frames, the four-definition synthetic-only Command registry,
deterministic synthetic principal verification, read-only ledger counts, and
atomic terminal replay for Commands whose domain reducer is not active yet.
The inherited CommonJS wrapper remains byte-identical to the frozen safe
projection. WP4 did not claim a successful domain mutation.

WP5 activates the three delivery method contracts only inside the isolated
`SYNTHETIC_TEST` boundary. `M0_SYNTHETIC_ENQUEUE_MOCK_EFFECT` atomically records
an Inbox row, Command envelope, Event, nonauthority Outbox intent and exact
replay tuple. Crash injection proves all-or-zero rollback; response-loss replay
returns the stored first response with zero additions. The Outbox intent binds
fixed production-incompatible F4 evidence and has `authority_eligible=false`.
Consequently `claim_outbox` deterministically returns
`SYNTHETIC_INPUT_NOT_EXECUTABLE`, receipt acknowledgement has no applicable
claim, and reconciliation observes a pre-arm non-effect state. Claim, lease,
receipt, UNKNOWN and precedence reducers are implemented and tested without
creating a claim, arm, call authorization, receipt, Host call or effect.

WP6 activates only the two frozen synthetic validation/completion Commands.
`M0_SYNTHETIC_RECORD_VALIDATION` consumes an exact owner-result tuple without
recomputing any upstream reducer and atomically records the immutable
`VALIDATION_CURRENT_DECISION` plus `COMPLETION_GUARD_ASSESSMENT` at one Event
barrier. `M0_SYNTHETIC_COMPLETE_TASK` re-reads those exact facts and pointers,
checks the same synthetic Task identity, the current validation-set result,
the F5 blocker and all five quiescence counts, then atomically records one
`TASK_COMPLETION` fact, current pointer, Event, completion row and replay tuple.
Disagreement, unavailable evidence, cross-Task bindings, unresolved synthetic
Outbox state, stale CAS, changed replay bytes and injected pre-Event crashes
all fail closed with zero partial completion rows.

WP7 activates the remaining frozen synthetic Goal/Task Command and closes the
integrated witness without adding an interface, table, authority, or runtime
path. One immutable Goal projection binds exactly three fixed synthetic Task
identities. The four closed Command types then produce a deterministic
five-Event chain, one completed validation Task, and one non-executable mock
effect intent. A read-only ledger projection hashes every immutable identity
tuple and canonical byte digest into one root. Two independent clean databases
produce the fixed root
`fd153ca175aee104b59af73d3cd31acfa74416567831dba00c42de2f88eb7650`;
shutdown/restart replay returns the original four response byte strings with
zero added rows. The mock-effect count denotes the synthetic nonauthority
intent only: external call, Host dispatch, provider, network, real Task,
real Command, real effect, private Memory, sensing and runtime activation
counts remain zero.

The inert CommonJS compatibility entry point loads the fixed Linux x64 N-API
binary lazily inside `processToolCall` before dispatching its closed three-field
frame. Loading the source module alone therefore remains inert, while an actual
tool call cannot reach an undeclared native binding. The wrapper still exports
only `initialize`, `processToolCall`, and `shutdown`.

The package still does not enable the plugin, start VCPToolBox, call a provider,
read private Memory, dispatch to a mock or real Host, or perform an effect.

Phase 5B M0-B WP0 adds only the fixed `src/home/` module layout, the
`tests/synthetic_m0b.rs` layout check and an inert schema v2 migration
declaration. Schema v1 remains active, the five-method N-API surface is
unchanged, and no candidate transition, handoff composition, new Command type,
database migration or runtime path is active yet.

Phase 5B M0-B WP1 adds the strict commitment-only synthetic Session observation
decoder and the `EPHEMERAL_ONLY`, `DISCARD` and `REMAIN_IN_SESSION` reducers.
Each returns a deterministic `NO_PROMOTION` decision with zero candidate,
Event, pointer, Inbox, Outbox, Goal or Task writes and no authority. Unknown,
implicit, raw-content-shaped, noncanonical or production-shaped input fails
closed before reduction. The module has no ledger dependency, so these paths
cannot perform a canonical write.

Phase 5B M0-B WP2 derives immutable, low-disclosure F7 candidate revisions for
the three closed classes. It validates exact canonical proposal bytes, complete
immutable history, distinct candidate identities, exact current predecessors
and same-revision replay versus rewrite. Candidate canonical bytes contain only
refs, revisions, fingerprints, commitments, class and a future Event sequence;
all action, Task, Command, Memory-write, effect and runtime authority remains
false. WP2 is deliberately storage-free. Schema v2 and atomic candidate/Event/
head persistence remain owned by the later frozen WP6 package.

Phase 5B M0-B WP3 implements the explicit promotion gates from a current Life
Stream candidate. `OBSERVE_WITHOUT_PROMOTION` and `DISCARD` terminate with zero
writes. `PROPOSE_MEMORY_CANDIDATE` and `PROPOSE_INTENT_CANDIDATE` derive only a
new commitment-only candidate revision through the WP2 reducer. Missing,
unknown, implicit, stale, non-Life-Stream, raw-content-shaped and
production-shaped inputs fail closed. No branch creates formal Memory, Goal,
Task, Command or effect authority, and persistence remains deferred to WP6.

Phase 5B M0-B WP4 composes a synthetic, nonauthoritative F8 handoff candidate
only after resolving the exact frozen R5 owner-source anchor and the canonical
current Intent Candidate history. Owner-source rewriting, phantom or reordered
history, stale Intent tuples, behind-watermark evidence, same-revision handoff
rewriting and direct-write-shaped inputs fail closed. The favorable result is
still candidate evidence only: F3 must recheck it, and no Command, Task or
effect authority or ledger write is produced before the later packages.

Phase 5B M0-B WP5 adds exactly one production-incompatible command definition,
`M0_SYNTHETIC_SUBMIT_HOME_INTENT`, with the frozen closed payload. The Home
adapter derives its Command ID, authentication-bound submission, existing
six-field `execute_command` request and replay identity from the exact WP4
candidate; it does not write the ledger. F3 validates the synthetic principal
and payload, then alone commits the Inbox, CommandEnvelope, Event and replay
rows in one transaction. Invalid input writes nothing, exact replay returns the
stored first response with zero additions, and the public five-method N-API
inventory remains unchanged. No production F3 type or runtime authority is
created.

Phase 5B M0-B WP6 activates the explicit synthetic-test-only schema v1→v2
migration and the three frozen low-disclosure tables. Candidate formation now
commits one immutable candidate revision, its Event and the exact candidate
head CAS in one Rust-ledger-thread transaction. Handoff formation re-resolves
the immutable owner set and canonical candidate history, rechecks the exact
current Intent Candidate, then commits one immutable link and Event. Every
pre-commit failpoint rolls back all rows; post-commit response loss resolves as
an exact replay without automatic promotion or F3 submission. F3 Home Intent
intake additionally resolves the persisted handoff and current candidate tuple
before it may commit. Quick/FK checks, immutable triggers and stored-byte scans
cover the disposable synthetic SQLite database; existing, production and
private databases remain outside this implementation boundary.

Phase 5B M0-B WP7 closes the integrated synthetic witness. Four fixed Session
observations cover `EPHEMERAL_ONLY`, `DISCARD`, `REMAIN_IN_SESSION` and the
explicit Life Stream proposal branch. Exactly one Life Stream, Memory and
Intent candidate, one F8 handoff, one F3-committed Home Intent and one
zero-Event indeterminate F3 control are recovered from the immutable v2
ledger; the rejected F3 control proves zero writes. The read-only projection
binds all canonical row digests and the sparse Event chain into fixed root
`81bb0e8a7bc3e389b8220efef5def05a2d891e44b3fe2a1515ffbc0e56324a80`.
Two clean disposable databases and one restart produce identical bytes with no
automatic candidate, handoff or Command addition. Real Session, Goal, Task,
Command, Memory, provider, sensing, external effect and runtime activation
counts remain zero.

Phase 5C M0-C WP0 adds a sealed-host and sealed-source baseline checker. It
consumes only the frozen seven VCPToolBox path/blob/SHA commitments and the
frozen 46-file source-inventory profile; it does not read a VCPToolBox
worktree. The checker permits only the four reviewed Phase 5C source paths and
verifies the immutable existing source bytes, blocked manifest state and inert
entrypoint boundary. At WP0 it reports `WP0_BASELINE_VERIFIED`, not package
compatibility, installation, activation or execution authority. The package is
still not built, delivered, enabled or loaded through a Host.

Phase 5C M0-C WP1 adds an offline staging builder. It accepts no caller path,
creates a new owned temporary root, derives the closed current source subset
from the sealed contract, rehashes every source before and after copying, and
cleans that root before it returns. It reports staging metadata only; it does
not emit a persistent archive, install anything, enable a manifest or invoke a
native Host.

Phase 5C M0-C WP2 verifies the disabled manifest and inert CommonJS entrypoint
without importing it through a Host. It parses only the blocked manifest and
evaluates the fixed entrypoint in an isolated VM with a throwing `require`;
the successful result proves no eager require occurs. It does not call
`processToolCall`, load the addon or enable the plugin.

Phase 5C M0-C WP3 combines the sealed extension facts with the frozen
VCPToolBox commit, tree and seven path/blob/SHA commitments. Its only positive
result is `PACKAGE_COMPATIBLE_PREVIEW`: a static compatibility statement for
that exact tuple. It neither reads a VCPToolBox worktree nor grants plugin
enablement, Host loading, runtime or effect authority.

Phase 5C M0-C WP4 constructs only raw, uncompressed POSIX USTAR bytes from the
closed source inventory in a newly created owned temporary root. Every member
uses the frozen `agents-os-resident/` prefix, bytewise source order, normalized
metadata, exact header bytes, zero padding and two terminal zero blocks. The
temporary `archive.tar` is re-read only into memory and the owned root is
removed before return; no archive is delivered, installed, enabled or written
to the workspace. The offline tamper suite checks headers, content, padding,
terminal blocks, paths, duplicate members, ordering and NFC path handling.

Phase 5C M0-C WP5 exercises the cleanup contract only against newly created,
disposable owned temporary roots. Its fault probe writes the synthetic archive,
attempts a direct non-recursive root removal while `archive.tar` remains,
observes the real `ENOTEMPTY` residue before finalization, returns the required
fail-closed synthetic code, and then removes the root. A separate deliberately
truncated in-memory return is detected before use, and the no-archive failure
path is also finalized. None of these probes retains an archive or touches a
Host, VCPToolBox, runtime, database, provider, private Memory, sensing or
effect boundary.

Phase 5C M0-C WP6 combines the sealed-source baseline, blocked-manifest and
inert-entrypoint checks, exact seven-object Host compatibility preview,
byte-identical raw USTAR builds, semantic archive tamper matrix and cleanup
observations into `OFFLINE_COMPATIBILITY_WITNESS_PASSED`. The witness is local
evidence only. Its positive result does not authorize archive delivery, plugin
enablement, Host loading, runtime activation, database work, private Memory,
provider use, sensing or any effect.

Phase 5D M0-D adds a separate, offline-only quarantined Host-smoke preflight
harness. It revalidates the frozen Phase 5C source baseline and seven sealed
Host commitments without opening a VCPToolBox worktree; creates only fresh,
harness-owned temporary quarantine roots; preserves the blocked manifest;
models the inert `initialize` and `shutdown` results in memory; traps
`processToolCall` and native loading before use; and removes every synthetic
temporary artifact. Its terminal result is
`QUARANTINED_HOST_SMOKE_PREFLIGHT_READY`, not archive delivery, plugin
enablement, Host discovery, lifecycle invocation, runtime activation, database
access, provider use, private-Memory access, sensing, recording, or a real
effect.
