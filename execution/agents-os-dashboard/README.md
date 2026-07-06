# AGENTS OS Dashboard v0.1

This directory contains the preview-only local dashboard layer for AGENTS OS.

It reads the Active Work Queue through the Machine parser, runs local docctl
status checks, summarizes open blockers and last closed work, and emits Memory
candidates as drafts only. When the queue is stopped at route selection, it
also surfaces the local route-selection package as preview-only options for
Jenn. It also surfaces the reviewed route adoption gate readiness without
selecting or applying a route. During that stop-state, it also emits a
`next_user_action` handoff that points Jenn to the route-choice confirmation
templates without printing the template body or selecting a route.

It is not a Memory writer, executor, service, provider adapter, ColaMeta runner,
VCPToolBox starter, queue mutator, or task producer.

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-dashboard/dashboard.py summary --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-dashboard/dashboard.py validate
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-dashboard/test-dashboard.py
```

## Output Contract

```text
schema_version=agents-os.dashboard.summary.v0.1
preview_only=true
read_only=true
write_performed=false
execution_authorized=false
formal_memory_write_authorized=false
private_memory_raw_read_authorized=false
route_selection.status=awaiting_jenn_selection|not_active
route_selection.route_auto_selection_authorized=false
route_selection.queue_promotion_authorized=false
route_selection.execution_authorized=false
next_user_action.status=route_choice_required|none
next_user_action.decision_owner=Jenn|null
next_user_action.active_queue_mutation_authorized=false
next_user_action.queue_promotion_authorized=false
next_user_action.execution_authorized=false
route_adoption_gate.status=waiting_for_jenn_route_choice|not_active
route_adoption_gate.active_queue_mutation_authorized=false
route_adoption_gate.queue_promotion_authorized=false
route_adoption_gate.execution_authorized=false
```

Memory candidates are candidate-only records. They may be reviewed later, but
the dashboard cannot write formal Memory or read private raw Memory.

## Boundaries

The dashboard must not:

```text
call providers
start services
run a real executor
activate runtimes or plugins
perform external writes
mutate the Active Work Queue
auto-select or promote a route
write formal Memory
read private raw Memory
read state-private
read or output secrets/tokens/cookies/provider raw response/raw logs
push/tag/deploy/publish
```
