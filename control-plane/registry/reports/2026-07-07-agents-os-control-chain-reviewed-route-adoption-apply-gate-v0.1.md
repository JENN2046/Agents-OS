# AGENTS OS Control Chain Reviewed Route Adoption Apply Gate v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: explicit apply gate for reviewed route adoption into NEXT

## Purpose

This report records a Control Chain change: after a route-choice queue proposal
has an accepted Nobao review, Control Chain can run a reviewed route adoption
apply gate.

The gate can append the reviewed route item to `NEXT` only when the caller uses
the explicit `--apply` switch. Without `--apply`, it is a preflight preview.

This is not route auto-selection. It does not promote `NEXT` to `NOW`. It does
not authorize execution.

## Input

The input is:

```text
route-choice queue proposal
accepted Nobao review
queue path
optional explicit --apply flag
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

Without `--apply`, the apply gate emits:

```text
schema_version=agents-os.queue-manager.reviewed-route-adoption-apply-gate.v0.1
preview_only=true
queue_adoption_authorized=true
route_adoption_authorized=false
workspace_route_state_modified=false
active_queue_modified=false
write_performed=false
queue_write_authorized=false
queue_promotion_authorized=false
execution_authorized=false
```

With explicit `--apply` and passing checks, it can emit:

```text
preview_only=false
queue_adoption_authorized=true
route_adoption_authorized=true
workspace_route_state_modified=true
active_queue_modified=true
write_performed=true
queue_write_authorized=true
queue_promotion_authorized=false
execution_authorized=false
mutation.target_lane=NEXT
mutation.left_now_unchanged=true
mutation.promoted_now=false
```

## Fixture Result

Validation used a temporary queue fixture only. The fixture write proved that
the gate can append `AGENTS OS formal Memory candidate gate v0.1` as
`NEXT-001`, leave `NOW` unchanged, and keep execution unauthorized.

The real Active Work Queue was not modified.

## Changed Files

```text
execution/agents-os-control-chain/control_chain.py
execution/agents-os-control-chain/test-control-chain.py
execution/agents-os-control-chain/control-chain.schemas.json
execution/agents-os-control-chain/control-chain-manifest.json
execution/agents-os-control-chain/README.md
```

## Boundary

- No real route was selected by Nobao.
- No real route was adopted into the Active Work Queue.
- No Active Work Queue mutation was performed in this work.
- Temporary test fixtures were written and removed by the test process.
- No route option was promoted from `NEXT` to `NOW`.
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
test-control-chain=PASS cases=25 failures=0
control_chain validate=PASS reviewed_route_adoption_apply_preview_passed=true reviewed_route_adoption_apply_fixture_modified=true reviewed_route_adoption_apply_execution_authorized=false
reviewed-route-adoption-apply-gate CLI=PASS preview_only=false active_queue_modified=true queue_write_authorized=true execution_authorized=false promoted_now=false target_lane=NEXT
producer validate=PASS route_choice_preview.present=true selected_option_id=B
machine validate=PASS
validate-document-registry=PASS documents=313 pass=313 warn=0 fail=0
validate-federated-document-registry=PASS registries=3 pass=3 warn=0 fail=0
docctl status=PASS score=100 eligible_95=True hard_gates=0
docctl doctor=PASS registries=3 documents=355 scanned_files=376 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
```

## Decision

Accepted as an explicit reviewed route adoption apply gate. It enables future
reviewed route adoption into `NEXT` without route auto-selection, queue
promotion, or execution.
