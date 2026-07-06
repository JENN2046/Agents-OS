# AGENTS OS Control Chain Reviewed Route Adoption Preview v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: reviewed preview for route-choice queue adoption

## Purpose

This report records a Control Chain change: after a route-choice queue proposal
has an accepted Nobao review, Control Chain can produce a reviewed route
adoption preview.

This is not a queue write. It does not adopt a route into workspace state. It
does not promote `NEXT` to `NOW`. It does not authorize execution.

## Input

The input is:

```text
route-choice queue proposal
accepted Nobao review
Active Work Queue path
```

The review must use:

```text
schema_version=agents-os.queue-manager.review.v0.1
review_status=accepted
reviewer=Nobao
requires_jenn_decision=false
source_proposal_id matches proposal_id
```

## Output

The reviewed route adoption preview emits:

```text
schema_version=agents-os.queue-manager.reviewed-route-adoption-preview.v0.1
preview_only=true
queue_mutation_preview_authorized=true
route_adoption_authorized=false
workspace_route_state_modified=false
active_queue_modified=false
write_performed=false
queue_write_authorized=false
queue_promotion_authorized=false
execution_authorized=false
mutation_preview.target_lane=NEXT
mutation_preview.would_leave_now_unchanged=true
mutation_preview.would_promote_now=false
```

It can show the proposed `NEXT` item title and body lines, but it does not write
them.

## Changed Files

```text
execution/agents-os-control-chain/control_chain.py
execution/agents-os-control-chain/test-control-chain.py
execution/agents-os-control-chain/control-chain.schemas.json
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
test-control-chain=PASS cases=24 failures=0
control_chain validate=PASS reviewed_route_adoption_preview_passed=true reviewed_route_adoption_preview_active_queue_modified=false reviewed_route_adoption_preview_execution_authorized=false
reviewed-route-adoption-preview CLI=PASS active_queue_modified=false write_performed=false would_promote_now=false
producer validate=PASS route_choice_preview.present=true selected_option_id=B
machine validate=PASS
validate-document-registry=PASS documents=310 pass=310 warn=0 fail=0
validate-federated-document-registry=PASS registries=3 pass=3 warn=0 fail=0
docctl status=PASS score=100 eligible_95=True hard_gates=0
docctl doctor=PASS registries=3 documents=352 scanned_files=373 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
```

## Decision

Accepted as reviewed route adoption preview. It closes the local preview chain
from Jenn route-choice text to reviewable queue adoption preview without
writing the Active Work Queue.
