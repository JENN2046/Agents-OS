# AGENTS OS Task Producer Route Choice Preview v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: preview-only intake for explicit Jenn route-choice confirmation text

## Purpose

This report records a Task Producer change: it can now parse an explicit Jenn
route-choice confirmation text and emit a local preview of the selected route
option.

The command is:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/producer.py route-choice-preview --confirmation-text "确认选择 AGENTS OS 下一路线：Formal Memory Loop。" --json
```

This is not route adoption. It is not queue mutation. It does not authorize
execution.

## Behavior

`route-choice-preview` reads the local route-selection package:

```text
control-plane/registry/reports/2026-07-07-agents-os-next-route-selection-package-v0.1.md
```

It requires the input text to include:

```text
确认选择 AGENTS OS 下一路线：
```

It then matches one known route title:

```text
VCPToolBox Runtime Recovery Or Controlled First-Use
Formal Memory Loop
External Git Publication Exact Gate
Provider Execution Design Gate
New AGENTS OS Construction Route
```

For `New AGENTS OS Construction Route`, placeholder goals fail; a concrete
route goal is required.

Successful output keeps:

```text
preview_only=true
confirmation_text_included=false
route_choice_detected=true
route_selection_confirmed_by_input=true
workspace_route_state_modified=false
active_queue_modified=false
queue_write_authorized=false
queue_promotion_authorized=false
route_auto_selection_authorized=false
execution_authorized=false
```

## Changed Files

```text
execution/agents-os-task-producer/producer.py
execution/agents-os-task-producer/test-producer.py
execution/agents-os-task-producer/producer-manifest.json
execution/agents-os-task-producer/README.md
control-plane/registry/reports/2026-07-07-agents-os-next-route-selection-package-v0.1.md
```

## Boundary

- No route was adopted into workspace state.
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
test-producer=PASS cases=18 failures=0
producer route-choice-preview=PASS selected_option=B workspace_route_state_modified=false active_queue_modified=false execution_authorized=false
producer validate=PASS route_choice_preview.present=true selected_option_id=B workspace_route_state_modified=false active_queue_modified=false
control_chain validate=PASS route_option_decision=stop_needs_jenn_decision route_option_track_authorized=false
machine validate=PASS
validate-document-registry=PASS documents=304 pass=304 warn=0 fail=0
validate-federated-document-registry=PASS registries=3 pass=3 warn=0 fail=0
docctl status=PASS score=100 eligible_95=True hard_gates=0
docctl doctor=PASS registries=3 documents=346 scanned_files=367 unregistered=0 warn=0 fail=0
```

## Decision

Accepted as a preview-only route-choice intake gate. It gives the system a
verifiable way to parse Jenn's future route choice without turning that parse
into queue mutation or execution.
