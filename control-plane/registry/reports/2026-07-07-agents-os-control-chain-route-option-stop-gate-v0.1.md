# AGENTS OS Control Chain Route Option Stop Gate v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: explicit Control Chain stop gate for route-option candidates

## Purpose

This report records a Control Chain hardening change: route-option candidates
from the Task Producer are now an explicit Jenn-decision stop gate.

The relevant upstream producer command is:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/producer.py from-route-option --option A --json
```

The Control Chain may inspect this candidate, but it must not select the route,
promote the queue, authorize execution, or route it to a runnable track.

## Behavior

Route-option candidates are recognized by either:

```text
source.kind=route_selection_option
source_facts.route_option_id present
```

The Commander decision must return:

```text
decision=stop_needs_jenn_decision
recommended_track=stop
execution_authorization_scope=blocked_requires_jenn
requires_jenn_decision=true
execution_authorized=false
blocked_capabilities includes route_selection_required
blocked_capabilities includes route_auto_selection
```

The Track Selector must return:

```text
selected_track=stop
track_authorized=false
```

## Changed Files

```text
execution/agents-os-control-chain/control_chain.py
execution/agents-os-control-chain/test-control-chain.py
execution/agents-os-control-chain/control-chain-manifest.json
execution/agents-os-control-chain/README.md
```

## Boundary

- No route was selected.
- No route option was promoted.
- No Active Work Queue mutation was performed.
- No service was started.
- No executor was run.
- No provider call was performed.
- No runtime or plugin was activated.
- No formal Memory write was performed.
- No external write, push, tag, release, deploy, publish, history rewrite,
  reset, clean, bulk move, delete, rename, overwrite, or destructive operation
  was performed.
- No `state-private/` content was read.
- No secrets, tokens, cookies, credentials, private raw memory, provider raw
  responses, active runtime config values, raw logs, private Notion page
  contents, or private Notion page URLs were read or output.

## Validation

```text
test-control-chain=PASS cases=22 failures=0
control_chain validate=PASS route_option_decision=stop_needs_jenn_decision route_option_track_authorized=false
producer from-route-option A=PASS blocked=true requires_jenn_decision=true route_selected=false route_auto_selection_authorized=false
machine validate=PASS
validate-document-registry=PASS documents=301 pass=301 warn=0 fail=0
validate-federated-document-registry=PASS registries=3 pass=3 warn=0 fail=0
docctl status=PASS score=100 eligible_95=True hard_gates=0
docctl doctor=PASS registries=3 documents=343 scanned_files=364 unregistered=0 warn=0 fail=0
```

## Decision

Accepted as an explicit route-option stop gate. Task Producer can propose a
candidate route, but Control Chain cannot select, promote, or execute it without
Jenn choosing the route.
