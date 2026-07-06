# AGENTS OS Dashboard Route Choice Handoff v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: dashboard next-user-action handoff for route-choice stop-state

## Purpose

This report records a Dashboard change: when the Active Work Queue is stopped
at `No Active Automatic Construction Item`, the preview-only Dashboard now
emits a stable `next_user_action` object.

The object tells the machine and Jenn that the next human action is route choice
from A-E. It does not choose a route, print the full confirmation template body,
write the Active Work Queue, promote a queue item, or authorize execution.

## Output

Dashboard summary now includes:

```text
next_user_action.schema_version=agents-os.dashboard.next-user-action.v0.1
next_user_action.status=route_choice_required
next_user_action.decision_owner=Jenn
next_user_action.requires_jenn_decision=true
next_user_action.instruction=choose_one_route_id
next_user_action.accepted_route_ids=A,B,C,D,E
next_user_action.template_source_path=control-plane/registry/reports/2026-07-07-agents-os-next-route-selection-package-v0.1.md
next_user_action.exact_confirmation_templates_available=true
next_user_action.route_auto_selection_authorized=false
next_user_action.active_queue_mutation_authorized=false
next_user_action.queue_promotion_authorized=false
next_user_action.execution_authorized=false
next_user_action.write_performed=false
next_user_action.raw_content_output=false
```

## Changed Files

```text
CURRENT_STATE.md
control-plane/registry/reports/2026-07-07-agents-os-active-work-queue-v0.1.md
execution/agents-os-dashboard/dashboard.py
execution/agents-os-dashboard/test-dashboard.py
execution/agents-os-dashboard/dashboard.schemas.json
execution/agents-os-dashboard/dashboard-manifest.json
execution/agents-os-dashboard/README.md
```

## Boundary

- No route was selected.
- No route-choice confirmation text was generated or applied.
- No route was adopted into the Active Work Queue.
- No Active Work Queue mutation was performed beyond recording this closed
  governance evidence.
- No queue item was promoted from `NEXT` to `NOW`.
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
test-dashboard=PASS cases=15 failures=0
dashboard validate=PASS next_user_action.status=route_choice_required decision_owner=Jenn accepted_route_ids=A,B,C,D,E active_queue_mutation_authorized=false queue_promotion_authorized=false execution_authorized=false
dashboard summary=PASS next_user_action.exact_confirmation_templates_available=true raw_content_output=false
control_chain validate=PASS route_option_track_authorized=false route_choice_proposal_active_queue_modified=false
machine validate=PASS next_count=0 closed_count=24
validate-document-registry=PASS documents=319 pass=319 warn=0 fail=0
validate-federated-document-registry=PASS registries=3 pass=3 warn=0 fail=0
docctl status=PASS score=100 eligible_95=True hard_gates=0
docctl doctor=PASS registries=3 documents=361 scanned_files=382 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
```

## Decision

Accepted as Dashboard route-choice handoff visibility. It turns the stop-state
into a clear human decision prompt while preserving the no-selection,
no-mutation, no-promotion, and no-execution boundary.
