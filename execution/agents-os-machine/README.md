# AGENTS OS Machine Skeleton v0.1

This directory contains the first local AGENTS OS machine skeleton.

It is a preview-only control machine. It reads the Active Work Queue, confirms
the single `NOW` item, emits a normalized queue model, and derives a temporary
task-envelope preview for validation.

It is not an executor, service, provider adapter, Memory writer, VCPToolBox
starter, ColaMeta runner, or task producer.

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-machine/machine.py inspect-queue --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-machine/machine.py preview-now --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-machine/machine.py validate
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-machine/test-machine.py
```

## Review Rule

All machine outputs are preview/draft until reviewed.

```text
machine_generated=true
status=preview_or_draft
requires_nobao_review=true
review_status=pending
execution_authorized=false
```

Machine self-check is necessary but never sufficient for execution. Nobao may
accept low-risk local work. Jenn must decide P3, provider, runtime/plugin,
external write, Memory, Git push/tag/release/deploy/history rewrite, identity,
and direction changes.

## Boundaries

Queue input paths are preflighted before read. Protected paths such as
`state-private/`, secrets, credentials, tokens, cookies, `.env`, and files
outside the workspace are blocked before content is read.

The skeleton must keep these capabilities disabled:

```text
provider_call_authorized=false
service_start_authorized=false
executor_run_authorized=false
external_write_authorized=false
memory_write_authorized=false
runtime_plugin_activation_authorized=false
```

The Markdown task-envelope preview is generated only as a temporary validation
artifact and is deleted after validation. The JSON preview output is the
authoritative machine output.

When the current `NOW` item is `No Active Automatic Construction Item`, the
machine preview also emits a `next_user_action` handoff:

```text
next_user_action.status=route_choice_required
next_user_action.decision_owner=Jenn
next_user_action.accepted_route_ids=A,B,C,D,E
next_user_action.route_auto_selection_authorized=false
next_user_action.active_queue_mutation_authorized=false
next_user_action.queue_promotion_authorized=false
next_user_action.execution_authorized=false
next_user_action.write_performed=false
next_user_action.raw_content_output=false
```

The same stop-state also emits
`route_choice_adoption_bundle_readiness` so Machine can see that the local
Control Chain adoption bundle preview exists, while still refusing to apply it:

```text
route_choice_adoption_bundle_readiness.status=waiting_for_jenn_route_choice
route_choice_adoption_bundle_readiness.decision_owner=Jenn
route_choice_adoption_bundle_readiness.bundle_preview_available=true
route_choice_adoption_bundle_readiness.can_apply_now=false
route_choice_adoption_bundle_readiness.route_auto_selection_authorized=false
route_choice_adoption_bundle_readiness.route_adoption_authorized=false
route_choice_adoption_bundle_readiness.active_queue_mutation_authorized=false
route_choice_adoption_bundle_readiness.queue_promotion_authorized=false
route_choice_adoption_bundle_readiness.execution_authorized=false
route_choice_adoption_bundle_readiness.write_performed=false
route_choice_adoption_bundle_readiness.raw_confirmation_text_output=false
route_choice_adoption_bundle_readiness.raw_template_output=false
route_choice_adoption_bundle_readiness.raw_content_output=false
```

Blocked previews must remain:

```text
actionable=false
execution_authorized=false
requires_jenn_decision=true
```

When a current queue item declares `requires_jenn_decision=true` without the
route-selection stop signal, Machine emits a generic governance handoff:

```text
next_user_action.status=governance_decision_required
next_user_action.decision_owner=Jenn
next_user_action.accepted_route_ids=
next_user_action.exact_confirmation_templates_available=false
actionable=false
execution_authorized=false
```
