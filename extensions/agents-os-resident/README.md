# AGENTS OS Resident

This directory is the Jenn-owned external source package for the frozen Phase
5A M0-A deterministic orchestrator core.

The package is synthetic-only and runtime-unusable. Its compatibility
projection is `Plugin/AGENTSOSResident/` in a clean linked VCPToolBox worktree
at commit `555b3b538f6eb736e530c2912de678c5941f9985`. The projection must retain
`plugin-manifest.json.block`; an enabled `plugin-manifest.json` is forbidden.

WP0 establishes only the deterministic package layout, exact toolchain and
dependency locks, inert JavaScript boundary, and hash-bound package manifest.
It does not create a database, start a runtime, call a provider, read private
Memory, or perform a real effect.
