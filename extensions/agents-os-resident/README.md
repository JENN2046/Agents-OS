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

The package still does not enable the plugin, start VCPToolBox, call a provider,
read private Memory, dispatch to a mock or real Host, or perform an effect.
