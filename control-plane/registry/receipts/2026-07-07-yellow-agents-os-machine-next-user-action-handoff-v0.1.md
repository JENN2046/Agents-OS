# Receipt: AGENTS OS Machine Next User Action Handoff v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: local receipt for Machine route-choice next-user-action handoff

## Completed

- Added `parse_route_option_ids()` to Machine.
- Added `next_user_action_for_item()` to Machine preview output.
- Surfaced Jenn as the route decision owner when `route_selection_required` is
  detected.
- Surfaced accepted route ids A-E and the route-selection template source path.
- Kept route-choice template body output disabled through
  `raw_content_output=false`.
- Added preview validation for next-user-action denied authority flags.
- Added fixture tests for current stop-state, route-selection fixture, P3-only
  non-route blocker, and denied queue promotion.
- Updated Machine README and manifest.
- Updated current state, active queue evidence, and document registry entries.

## Result Summary

```text
machine_next_user_action_visible=true
status=route_choice_required
decision_owner=Jenn
accepted_route_ids=A,B,C,D,E
exact_confirmation_templates_available=true
route_auto_selection_authorized=false
active_queue_mutation_authorized=false
queue_promotion_authorized=false
execution_authorized=false
write_performed=false
raw_content_output=false
```

## Not Performed

- No route was selected.
- No route-choice confirmation text was applied.
- No Active Work Queue route adoption was performed.
- No queue item was promoted.
- No `state-private/` read.
- No secrets, tokens, cookies, credentials, private raw memory, provider raw
  response, raw log, active runtime config values, private Notion page contents,
  or private Notion page URLs were read or output.
- No service start, executor run, provider call, runtime/plugin activation,
  formal Memory write, external write, push, tag, release, deploy, publish,
  history rewrite, reset, clean, bulk move, delete, rename, overwrite, or
  destructive operation.

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

## Result

Accepted as local Machine route-choice handoff evidence. The real queue remains
in stop-state.
