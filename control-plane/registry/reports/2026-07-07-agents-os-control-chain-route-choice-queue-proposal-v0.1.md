# AGENTS OS Control Chain Route Choice Queue Proposal v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: preview-only queue proposal from Task Producer route-choice preview

## Purpose

This report records a Control Chain change: it can now turn a Task Producer
`route-choice-preview` JSON object into a queue proposal preview.

This is not queue mutation. It does not adopt a route into workspace state. It
does not promote the route to `NOW`. It does not authorize execution.

## Input

The input is a Task Producer preview:

```text
schema_version=agents-os.task-producer.route-choice-preview.v0.1
passed=true
preview_only=true
confirmation_text_included=false
route_choice_detected=true
workspace_route_state_modified=false
active_queue_modified=false
execution_authorized=false
```

## Output

The Control Chain emits:

```text
schema_version=agents-os.queue-manager.route-choice-proposal.v0.1
proposal_only=true
preview_only=true
proposed_queue_item.lane=NEXT
route_adoption_authorized=false
workspace_route_state_modified=false
active_queue_modified=false
write_performed=false
queue_write_authorized=false
queue_promotion_authorized=false
execution_authorized=false
```

The proposed queue item carries the selected route option, first safe package,
and `must_keep` boundary lines. It is review material only.

## Changed Files

```text
execution/agents-os-control-chain/control_chain.py
execution/agents-os-control-chain/test-control-chain.py
execution/agents-os-control-chain/control-chain-manifest.json
execution/agents-os-control-chain/README.md
```

## Boundary

- No route was adopted into workspace state.
- No Active Work Queue mutation was performed.
- No route option was promoted.
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
test-control-chain=PASS cases=23 failures=0
control_chain validate=PASS route_choice_proposal_passed=true route_choice_proposal_active_queue_modified=false route_choice_proposal_execution_authorized=false
producer validate=PASS route_choice_preview.present=true selected_option_id=B
machine validate=PASS
validate-document-registry=PASS documents=307 pass=307 warn=0 fail=0
validate-federated-document-registry=PASS registries=3 pass=3 warn=0 fail=0
docctl status=PASS score=100 eligible_95=True hard_gates=0
docctl doctor=PASS registries=3 documents=349 scanned_files=370 unregistered=0 warn=0 fail=0
```

## Decision

Accepted as a preview-only queue proposal gate. It creates reviewable material
for future route adoption without writing the Active Work Queue or authorizing
execution.
