# AGENTS OS Machine Next User Action Handoff v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: machine preview next-user-action handoff for route-selection stop-state

## Purpose

This report records a Machine change: when the single `NOW` item is
`No Active Automatic Construction Item`, `machine.py preview-now --json` now
emits a stable `next_user_action` object.

The object carries the same human-decision boundary as the Dashboard handoff:
Jenn is the decision owner, the accepted route ids are A-E, and the route
selection package is the template source. It does not choose a route, print the
full confirmation template body, write the Active Work Queue, promote a queue
item, or authorize execution.

## Output

Machine preview now includes:

```text
next_user_action.schema_version=agents-os.machine.next-user-action.v0.1
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

Machine validation now also summarizes:

```text
preview.next_user_action_status=route_choice_required
preview.next_user_action_owner=Jenn
```

## Changed Files

```text
CURRENT_STATE.md
control-plane/registry/reports/2026-07-07-agents-os-active-work-queue-v0.1.md
execution/agents-os-machine/machine.py
execution/agents-os-machine/test-machine.py
execution/agents-os-machine/README.md
execution/agents-os-machine/machine-manifest.json
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
test-machine=PASS cases=15 failures=0
machine preview-now=PASS next_user_action.status=route_choice_required decision_owner=Jenn accepted_route_ids=A,B,C,D,E active_queue_mutation_authorized=false queue_promotion_authorized=false execution_authorized=false
machine validate=PASS blocked=true actionable=false next_user_action_status=route_choice_required next_user_action_owner=Jenn
dashboard validate=PASS next_user_action.status=route_choice_required route_adoption_gate.status=waiting_for_jenn_route_choice
validate-document-registry=PASS documents=322 pass=322 warn=0 fail=0
validate-federated-document-registry=PASS registries=3 pass=3 warn=0 fail=0
docctl status=PASS score=100 eligible_95=True hard_gates=0
docctl doctor=PASS registries=3 documents=364 scanned_files=385 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
```

## Decision

Accepted as Machine route-choice handoff visibility. Machine preview now gives
the same human-decision handoff as Dashboard while preserving the no-selection,
no-mutation, no-promotion, and no-execution boundary.
