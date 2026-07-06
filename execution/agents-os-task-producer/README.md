# AGENTS OS Task Producer Skeleton v0.1

This directory contains the first local AGENTS OS Task Producer skeleton.

It is a preview-only candidate task producer. It turns explicit intent text,
allowlisted local review/report documents, or an explicitly named route option
from the route-selection package into candidate task JSON.
It can also preview an explicit Jenn route-choice confirmation text without
writing route state or the Active Work Queue. It can check route-choice
template coverage without outputting raw template text.

It is not a queue writer, queue promoter, executor, service, provider adapter,
Memory writer, VCPToolBox starter, ColaMeta runner, plugin activator, or Git
publisher. It does not select routes.

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/producer.py from-intent --intent "Build local governance task" --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/producer.py from-review --source control-plane/registry/reports/2026-07-07-agents-os-machine-to-task-producer-queue-transition-v0.1.md --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/producer.py from-route-option --option A --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/producer.py route-choice-preview --confirmation-text "确认选择 AGENTS OS 下一路线：Formal Memory Loop。" --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/producer.py route-choice-template-coverage --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/producer.py validate
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/test-producer.py
```

## Output Rule

Producer output is candidate JSON only:

```text
producer_generated=true
status=candidate_preview
requires_nobao_review=true
review_status=pending
execution_authorized=false
json_output_authoritative=true
source_facts.route_selected=false
authorization.route_auto_selection_authorized=false
```

The producer never writes the Active Work Queue and never promotes any item to
`NOW`. It also never selects a route. Nobao may review a candidate and
separately decide whether a governance queue update is safe after Jenn chooses
a route.

`route-choice-preview` parses a Jenn confirmation text and reports the matched
route option as preview-only JSON. It keeps:

```text
workspace_route_state_modified=false
active_queue_modified=false
queue_write_authorized=false
queue_promotion_authorized=false
route_auto_selection_authorized=false
execution_authorized=false
confirmation_text_included=false
```

`route-choice-template-coverage` checks the package templates A-E. Templates
A-D must parse as preview-only route choices, Template E's placeholder goal must
be rejected, and an internal concrete-goal fixture must prove option E can parse
after Jenn supplies a concrete target. It does not output template bodies.

## Boundaries

The skeleton must keep these capabilities disabled:

```text
queue_write_authorized=false
execution_authorized=false
provider_call_authorized=false
service_start_authorized=false
executor_run_authorized=false
external_write_authorized=false
memory_write_authorized=false
runtime_plugin_activation_authorized=false
plugin_execution_authorized=false
route_auto_selection_authorized=false
```

Review/report input paths are preflighted before read. Protected paths such as
`state-private/`, secrets, credentials, tokens, cookies, `.env`, and files
outside the workspace are blocked before content is read.

Allowlisted file input is limited to Markdown under:

```text
control-plane/registry/reports/
control-plane/registry/reviews/
```

Source body raw content is not included in candidate output. Review/report
candidate output includes only path metadata, headings, counts, risk signals,
and the candidate task fields.
