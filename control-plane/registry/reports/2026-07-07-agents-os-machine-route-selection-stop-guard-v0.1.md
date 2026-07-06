# AGENTS OS Machine Route Selection Stop Guard v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: harden Machine preview behavior for `No Active Automatic Construction Item`

## Purpose

This report records a Machine hardening change: when the active queue `NOW`
item is a route-selection stop-state, the Machine must not mark it actionable.

The intended behavior is:

```text
blocked=true
actionable=false
requires_jenn_decision=true
execution_authorized=false
denied_signals includes route_selection_required
```

This is a local control-plane hardening step. It is not a route selection,
runtime activation, provider plan, Memory entry point, external publication, or
deployment action.

## Boundary

- No `state-private/` content was read.
- No secrets, tokens, cookies, credentials, private raw memory, provider raw
  responses, active runtime config values, raw logs, private Notion page
  contents, or private Notion page URLs were read or output.
- No service was started.
- No executor was run.
- No provider call was performed.
- No host dispatcher route was executed.
- No VCPToolBox runtime, config, plugin, dependency, build, or service action
  was performed.
- No formal Memory write was performed.
- No external write, push, tag, release, deploy, publish, history rewrite,
  history scrub, reset, clean, bulk move, delete, rename, or overwrite was
  performed.

## Changed Files

```text
execution/agents-os-machine/machine.py
execution/agents-os-machine/test-machine.py
execution/agents-os-machine/machine-manifest.json
```

## Behavior Change

The Machine now recognizes route-selection stop-state signals from:

```text
No Active Automatic Construction Item
requires_jenn_route_choice=true
no_active_route_selected=true
do not infer a new construction route without Jenn direction
```

When one of these signals is present in a NOW item, the normalized item records:

```text
denied_signals=["route_selection_required"]
blocked=true
review_gate.requires_jenn_decision=true
review_gate.review_reason=route selection required by queue stop-state
```

The generated preview then carries the same stop-state decision:

```text
blocked=true
actionable=false
execution_authorized=false
```

## Test Coverage

`test-machine.py` now includes an explicit route-selection stop-state fixture.

Validated behavior:

```text
current queue fixture=PASS
preview authorization fixture=PASS
manifest authorization fixture=PASS
no NOW fixture=PASS
multiple NOW fixture=PASS
P3 signal fixture=PASS
negated boundary signal fixture=PASS
route selection stop-state fixture=PASS
task-envelope temporary validation fixture=PASS
cases=14 failures=0
```

## Current Preview Result

The current active queue preview now reports:

```text
source_item=No Active Automatic Construction Item
blocked=true
actionable=false
requires_jenn_decision=true
execution_authorized=false
denied_signals=route_selection_required
review_reason=route selection required by queue stop-state
```

## Decision

Accepted as a local Machine hardening. The larger AGENTS OS construction
objective remains active, but the Machine now correctly treats the current
stop-state as requiring Jenn route selection before execution.
