# AGENTS OS Resident

This directory is the Jenn-owned external source package for the frozen Phase
5A M0-A deterministic orchestrator core.

The package is synthetic-only and runtime-unusable. Its compatibility
projection is `Plugin/AGENTSOSResident/` in a clean linked VCPToolBox worktree
at commit `555b3b538f6eb736e530c2912de678c5941f9985`. The projection must retain
`plugin-manifest.json.block`; an enabled `plugin-manifest.json` is forbidden.

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
