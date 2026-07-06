# Review: AGENTS OS Control Chain Reviewed Route Adoption Apply Gate v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: review of Control Chain reviewed route adoption apply gate

## Review Result

Accepted with limits.

Control Chain can now perform an explicit reviewed route adoption apply gate.
The write path requires an accepted Nobao review, a safe queue path, no
duplicate `NEXT` route, no proposed route P3 signals, and the explicit `--apply`
flag.

## Evidence Checked

- Accepted review is required.
- Pending review fails.
- Review `source_proposal_id` must match the proposal.
- Queue path must be safe and inside the workspace.
- Exactly one `NOW` item must exist before adoption.
- Proposed route item is scanned for P3 queue signals.
- Duplicate `NEXT` route title is rejected.
- Apply targets `NEXT`.
- Apply leaves `NOW` unchanged.
- Apply does not promote `NOW`.
- Apply keeps `queue_promotion_authorized=false`.
- Apply keeps `execution_authorized=false`.
- Preview mode keeps `active_queue_modified=false`.
- Explicit fixture apply can set `active_queue_modified=true`.

## Denied Authority Confirmed

```text
route_auto_selection_authorized=false
queue_promotion_authorized=false
execution_authorized=false
vcptoolbox_start_authorized=false
plugin_activation_authorized=false
executor_run_authorized=false
provider_call_authorized=false
formal_memory_write_authorized=false
external_write_authorized=false
git_push_authorized=false
history_rewrite_authorized=false
state_private_read_authorized=false
secret_raw_read_authorized=false
provider_raw_response_output_authorized=false
raw_log_output_authorized=false
```

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

## Residual Risk

- The larger AGENTS OS construction objective remains active and incomplete.
- This work did not choose the next route.
- The real Active Work Queue was not modified.
- Future real route adoption still needs a current explicit route choice and a
  reviewed apply invocation.

## Decision

Accepted as reviewed route adoption apply gate. It does not authorize route
auto-selection, queue promotion, or route execution.
