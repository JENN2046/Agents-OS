# AGENTS OS Task Producer Route Option Intake v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: candidate-only route option intake for Task Producer

## Purpose

This report records a Task Producer change: it can now create candidate task
JSON from a Jenn-selectable route option in the local route-selection package.

The command is:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/producer.py from-route-option --option A --json
```

This is not route selection. It is not queue promotion. It does not authorize
execution.

## Behavior

`from-route-option` reads:

```text
control-plane/registry/reports/2026-07-07-agents-os-next-route-selection-package-v0.1.md
```

It accepts option IDs:

```text
A B C D E
```

It emits candidate JSON with:

```text
source.kind=route_selection_option
source.raw_content_included=false
source_facts.route_selected=false
authorization.route_auto_selection_authorized=false
authorization.queue_write_authorized=false
queue_effect.active_queue_modified=false
execution_effect.execution_authorized=false
risk_signals includes route_selection_required
blocked=true
actionable_after_review=false
review_gate.requires_jenn_decision=true
```

Invalid route option IDs fail before candidate generation.

## Candidate Routes

The Producer can generate blocked candidate previews for:

```text
A: AGENTS OS VCPToolBox controlled recovery restart v0.1
B: AGENTS OS formal Memory candidate gate v0.1
C: AGENTS OS external Git publication target gate v0.1
D: AGENTS OS provider execution design gate v0.1
E: AGENTS OS new construction route intake v0.1
```

Every route option candidate remains blocked until Jenn chooses a route.

## Changed Files

```text
execution/agents-os-task-producer/producer.py
execution/agents-os-task-producer/test-producer.py
execution/agents-os-task-producer/candidate-task.schema.json
execution/agents-os-task-producer/producer-manifest.json
execution/agents-os-task-producer/README.md
```

## Boundary

- No route was selected.
- No queue item was promoted.
- No Active Work Queue write was performed.
- No service was started.
- No executor was run.
- No provider call was performed.
- No host dispatcher route was executed.
- No VCPToolBox runtime, config, plugin, dependency, build, or service action
  was performed.
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
test-producer=PASS cases=16 failures=0
producer from-route-option A=PASS blocked=true requires_jenn_decision=true route_selected=false route_auto_selection_authorized=false queue_write_authorized=false execution_authorized=false
producer validate=PASS route_option_candidates=5 all_blocked=true all_requires_jenn_decision=true all_route_selected=false
machine validate=PASS preview.blocked=true preview.actionable=false
dashboard validate=PASS route_selection.status=awaiting_jenn_selection option_count=5
validate-document-registry=PASS documents=298 pass=298 warn=0 fail=0
validate-federated-document-registry=PASS registries=3 pass=3 warn=0 fail=0
docctl status=PASS score=100 eligible_95=True hard_gates=0
docctl doctor=PASS registries=3 documents=340 scanned_files=361 unregistered=0 warn=0 fail=0
```

## Decision

Accepted as candidate-only route option intake. This closes one gap between the
route-selection package and future queue proposal work while preserving Jenn's
route-selection authority.
