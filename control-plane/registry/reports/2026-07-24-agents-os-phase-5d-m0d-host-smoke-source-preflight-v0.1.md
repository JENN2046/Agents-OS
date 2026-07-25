# Phase 5D M0-D Host Smoke Source Preflight v0.1

Date: 2026-07-24

```yaml
status: PASS_SOURCE_INTEGRITY_AND_STATIC_API_SHAPE
terminal_outcome: NOT_EXECUTED
actual_Host_smoke: NOT_AUTHORIZED_BY_THIS_PREFLIGHT
next_gate: JENN_EXPLICIT_PHASE_5D_M0D_HOST_SMOKE_EXECUTION_DECISION
```

## Scope and isolation

Jenn authorized a read-only preflight of the canonical VCPToolBox root at:

```text
/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox
```

The preflight created a fresh detached worktree at the sealed commit, read only
the seven frozen source objects and their static API shape, then removed that
temporary worktree. The original VCPToolBox worktree was not modified. Existing
local changes in that original worktree were neither read as source inputs nor
changed.

No plugin was delivered, enabled, discovered, loaded, initialized, shut down,
or invoked. No N-API, runtime, database, provider, authentication, private
Memory, sensing, or effect path was used.

## Sealed source verification

```yaml
sealed_commit: 555b3b538f6eb736e530c2912de678c5941f9985
sealed_tree: fd82d403e79f36f749eb7f555b4736eae3eacdff
detached_worktree_head: 555b3b538f6eb736e530c2912de678c5941f9985
detached_worktree_status: CLEAN
temporary_worktree_removed: true
node_static_syntax_check_for_Plugin_js: PASS
```

| Path | Git blob OID | SHA-256 | Result |
|---|---|---|---|
| `AGENTS.md` | `28f22b4de495a63f14ede8fe72698278c877cb8d` | `24b2a4c3e45a98107a726c8dfd80b577846052d49068bb1c13479f872bf0374b` | MATCH |
| `Plugin/AGENTS.md` | `c2d23c041033b1f7d46b9dc3bdb2ba738566c872` | `b060ad148827faa37877deb8b170399a0f00f46bc194797949005c9bb62572d4` | MATCH |
| `docs/PLUGIN_ECOSYSTEM.md` | `81dc779453ccf2fb56c1f57d1ecde8ff3ffda506` | `f806b90c4f7d46bd2113f8b5af9f773adce49b454d615e7b6aa8445663490a65` | MATCH |
| `rust-vexus-lite/AGENTS.md` | `0fad4dba9bcbaa2452a362910b01e6275e5c352e` | `e5e68ad817c4fc7da657ce0d9c131db666eff97888b772ac31b9661210c93494` | MATCH |
| `rust-vexus-lite/Cargo.toml` | `3682f96f45c095f85e0f3c93bc2d6c1f21c98dde` | `01f6f29f824418c58dc1c0a5243df514bd6b2bd5cd6a68de850c13e465e6eea9` | MATCH |
| `rust-vexus-lite/package.json` | `232a95ef206e6ffab0cdff959826faaa10f6fedb` | `c996185f59cc84208077f854077f2f5451368ea9cd05c775ba0b06028fed7f7c` | MATCH |
| `Plugin.js` | `5fd77cea37c30ef432f23d9627d05aba862b9744` | `be15f76324b73400fe70052e6f07a0254b2a9c26393009ad1f026793fb36f5a2` | MATCH |

## Static lifecycle finding

The sealed Host source has a `PluginManager` lifecycle, but its available
methods are not inert probes:

```text
PluginManager.loadPlugins()
  -> discovery + module loading + module.initialize(...)

PluginManager.shutdownAllPlugins()
  -> VectorDB shutdown + plugin/service shutdown + scheduled-job cancellation

PluginManager.processToolCall(...)
  -> execution boundary
```

The ecosystem document describes the lifecycle as discovery, loading,
initialization, execution, and shutdown. Static inspection found no independent
core method named `quarantine_cleanup`; cleanup must therefore be provided by
the separately governed quarantine harness and receipt path, not inferred as a
safe core Host call.

## Consequence for the next decision

This preflight proves that the frozen source target is present and unchanged. It
does **not** authorize a direct call to `loadPlugins()` or
`shutdownAllPlugins()` against the existing Host worktree: either call can touch
the ordinary plugin population and runtime dependencies.

An actual Host-smoke execution decision must first bind all of the following:

1. a new disposable quarantine Host worktree rooted at the sealed commit;
2. an allowlisted, inert plugin payload and preserved disabled-manifest state;
3. the exact selector, arguments, expected observations, and stop conditions;
4. a cleanup finalizer that proves no residual Host/plugin state remains; and
5. a fail-closed outcome for every unavailable, unexpected, or non-inert Host
   condition.

Until that separate Jenn decision exists, the correct state remains
`NOT_EXECUTED`.
