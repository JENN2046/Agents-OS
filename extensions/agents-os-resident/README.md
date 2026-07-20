# AGENTS OS Resident

This directory is the Jenn-owned external source package for the frozen Phase
5A M0-A deterministic orchestrator core.

The package is synthetic-only and runtime-unusable. Its compatibility
projection is `Plugin/AGENTSOSResident/` in a clean linked VCPToolBox worktree
at commit `555b3b538f6eb736e530c2912de678c5941f9985`. The projection must retain
`plugin-manifest.json.block`; an enabled `plugin-manifest.json` is forbidden.

WP0 establishes the deterministic package layout and WP1 establishes strict
canonical JSON/JCS/SHA-256 primitives. WP2 adds only the synthetic Resident
ownership boundary: an OS-exclusive lock, immutable identity/incarnation/epoch
descriptors, one Rust ledger thread, one SQLite connection opened only under a
test-created temporary directory, and deterministic shutdown/join behavior.

WP2 does not create the ledger v1 schema, admit a Command, enable the plugin,
start VCPToolBox, call a provider, read private Memory, or perform a real
effect.
