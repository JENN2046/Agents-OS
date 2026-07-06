# AGENTS OS VCPToolBox Private Runtime Cold Audit v0.1

Date: 2026-07-06

Owner: Jenn

Agent steward: Nobao

Status: accepted local review report

## Scope

This report records a code-only, no-run audit of
`runtime/VCPToolBox` as the private local runtime body for AGENTS OS.

The review covered:

- `server.js` and `adminServer.js` startup/auth/network posture.
- `routes/specialModelRouter.js` model proxy routing.
- `routes/admin/` config, plugin, file-management, and plugin-store surfaces.
- `Plugin.js` plugin loading and execution path.
- `modules/toolApprovalManager.js`, `modules/toolResultPrivacyGuard.js`, and
  `modules/vcpLoop/toolExecutor.js`.
- Plugin manifest inventory and package metadata.
- Git checkout status and ignore coverage summary.

## Explicit Non-Actions

- No VCPToolBox service was started.
- No `adminServer.js`, `server.js`, `Plugin.js`, plugin, provider, executor,
  build, or test command was run.
- No provider call was made.
- No active `config.env`, `.env`, token, cookie, credential, private memory,
  provider raw response, or log raw content was read or output.
- No `state-private/` content was read.
- No VCPToolBox source, config, plugin manifest, runtime state, or auth file was
  modified.

## Private-Project Context

AGENTS OS is Jenn's personal private project. That changes the product standard:
VCPToolBox does not need to satisfy public SaaS, enterprise, multi-user, or
internet-facing platform requirements before it is useful.

The correct standard is Jenn-local:

- local usefulness first
- private data does not leak
- high-risk actions do not happen by surprise
- failures are observable and recoverable
- Nobao and local agents can advance work inside clear red lines

Under that standard, VCPToolBox is not disqualified by being powerful. Its
power is the point. The required work is to keep that power inside a local,
explicitly bounded runtime posture.

## Core Finding

VCPToolBox is a real runtime body for AGENTS OS, not a small dependency. It is a
Node.js AI middle layer with a plugin supervisor, admin panel, provider proxy,
RAG/search/memory surfaces, file operations, browser bridge, shell execution,
media generation, task/agent communication, and multiple language runtimes.

Its value and its risk are the same fact: it exposes many capabilities through a
model-driven tool protocol and an admin control plane.

## High-Risk Surfaces

### Special Model Router Auth Ordering

`server.js` mounts `routes/specialModelRouter.js` before the general Bearer
token middleware. If image or embedding model whitelists are non-empty and the
service is reachable, matching model requests can be routed to the upstream API
before the normal `serverKey` check.

Risk: an unintended caller on a reachable interface may trigger upstream
provider calls through whitelisted models.

Required posture: localhost-only binding plus explicit review before enabling
special model whitelists.

### Network Posture

Both main and admin servers use broad CORS and large request bodies. The main
server listens with `app.listen(port)` and does not itself prove localhost-only
binding in the inspected code.

Risk: acceptable for a trusted local private runtime; not acceptable as a
network-exposed service.

Required posture: bind or firewall to localhost before first real use.

### Admin Plane Is A Secret And Runtime Control Plane

Admin routes can read/write main `config.env`, plugin `config.env`, tool
approval config, plugin descriptions, plugin enablement, and plugin configs.
This is coherent for a local owner-admin console, but it means admin access is
equivalent to runtime control and sensitive configuration access.

Risk: admin panel exposure or weak admin credentials becomes full local runtime
control.

Required posture: admin panel must remain local-only and treated as a high-trust
owner console.

### Plugin Execution Surface

Plugin execution is manifest-driven and can spawn processes. Enabled plugin
inventory includes shell, PowerShell, file operations, browser bridge, URL fetch,
search, image/video generation, task/agent communication, and bridge services.

Risk: model-produced tool calls can have real filesystem, process, provider, or
browser side effects when the relevant plugin is enabled and configured.

Required posture: high-risk plugins should require explicit local gating before
first live use.

### Tool Approval And Privacy Guard Defaults

The code contains Tool Approval and tool-result privacy guard modules, but their
defaults are disabled. Presence of these modules is not the same as active
protection.

Risk: a powerful tool chain can run without human approval if configuration does
not enable approval rules.

Required posture: enable approval or equivalent local guard for shell, file,
provider, browser, external fetch, and bridge tools before unsupervised use.

### File Operation Default Semantics

`FileOperator` supports broad file read/write/move/delete/download/diff
operations. Its code default allows all paths when `ALLOWED_DIRECTORIES` is
empty. Actual active config values were not read.

Risk: if left empty, file operations may apply outside the intended workspace.

Required posture: set an explicit Jenn-local allowed directory policy before
using FileOperator in live model loops.

## Engineering Maturity Findings

- Root `package.json` has an intentionally failing placeholder `npm test`.
- Only a small number of root tests were found relative to the runtime surface.
- Lockfiles exist for the root Node package, admin panel, and Rust subproject.
- The runtime has many dependencies and native/browser/network packages.
- Current VCPToolBox checkout has dirty/untracked local runtime/build/config
  adjacent artifacts.
- `.gitignore` coverage does not cover every observed local runtime/build
  artifact.

## Positive Findings

- Admin auth exists and blocks admin panel when credentials are absent.
- Tool approval, result privacy guard, plugin enable/disable, and plugin store
  safety checks exist.
- Plugin store includes SSRF and archive traversal defenses.
- Several file-management routes implement root-boundary checks.
- High-risk shell plugins have admin/auth concepts in their manifests and code.
- The project already documents itself as a personal AI middle layer with a
  plugin ecosystem.

## Required First-Use Posture

For AGENTS OS, VCPToolBox should be treated as a private local runtime body with
these minimum gates:

1. localhost-only service binding or firewall confirmation.
2. no provider calls until explicitly enabled for a session or task.
3. high-risk plugin allowlist before first autonomous loop.
4. explicit `FileOperator` allowed directories.
5. tool approval or equivalent guard for shell/file/browser/provider/bridge.
6. active config values stay outside Git and outside reports.
7. VCPToolBox dirty checkout is classified before any Git baseline.

## Conclusion

VCPToolBox is suitable as AGENTS OS's private runtime body, but not as an
unbounded always-on execution substrate. It should be integrated under
Jenn-local rules: high autonomy inside local red lines, no public exposure, no
surprise provider calls, no surprise secret/config reads, and no surprise
filesystem writes outside explicitly allowed local scope.

