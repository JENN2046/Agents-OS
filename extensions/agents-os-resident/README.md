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
