# AGENTS OS Control Chain v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: commander-first dual-track implementation skeleton

## Result

AGENTS OS now has a first commander-first control chain at:

```text
execution/agents-os-control-chain/
```

It implements:

```text
Commander Decision Layer
Track Selector
shared track_result.json contract
ColaMeta readiness reconciliation
Local Executor local-safe validation action
Queue Manager proposal-only output
Failure Report / Stop Loop output
```

## Authority Model

```text
Commander is the only authorization source.
Track Selector cannot elevate.
ColaMeta Track remains readiness/preview only.
Local Executor only consumes local_safe_only.
Queue Manager produces proposal-only output first, then reviewed mutation only
when an accepted Nobao review object is supplied.
Failure handling produces a local report and stop-loop result before any queue
promotion can happen on failure.
Provider-backed execution is not in scope.
```

## Validation Summary

```text
test-control-chain: PASS cases=21 failures=0
control_chain validate: PASS
commander local task -> route_to_local_executor local_safe_only
commander ColaMeta task -> route_to_colameta none
commander provider task -> stop_needs_jenn_decision blocked_requires_jenn
track selector blocked task -> track_authorized=false
local executor run_validation_command -> PASS
local executor provider_call -> blocked
failure classifier validation_failed -> repair_attempt_allowed=true max_repair_attempts=1
failure classifier protected_path_detected -> queue_promotion_allowed=false
failure classifier dirty_worktree_conflict -> queue_promotion_allowed=false
failure classifier scope_violation -> queue_promotion_allowed=false
failure classifier unknown_action_type -> queue_promotion_allowed=false
failure classifier p3_signal_detected -> requires_jenn_decision=true
failure classifier executor_output_invalid -> queue_promotion_allowed=false
stop loop -> stopped_for_review queue_promoted=false silent_retry_performed=false
failed track result queue proposal -> close_current_now=false promote_next_title=null
ColaMeta readiness -> PASS preview_only=true execution_performed=false provider_call_performed=false
queue proposal -> proposal_only=true active_queue_modified=false
reviewed queue mutation preview -> preview_only=true active_queue_modified=false
reviewed queue mutation fixture apply -> active_queue_modified=true exactly_one_now_after=true
pending review -> mutation blocked
P3 NEXT target -> mutation blocked
```

## Files

```text
execution/agents-os-control-chain/README.md
execution/agents-os-control-chain/control-chain-manifest.json
execution/agents-os-control-chain/control-chain.schemas.json
execution/agents-os-control-chain/control_chain.py
execution/agents-os-control-chain/test-control-chain.py
```

## Boundary

No `state-private/` content was read. No secrets, tokens, cookies, credentials,
private raw memory, provider raw response, active runtime config values, or raw
logs were read or output. No service was started. No real executor run, provider
call, VCPToolBox activation, plugin activation, external write, formal Memory
write, Git push, tag, release, deploy, publish, or history rewrite was
performed.

ColaMeta readiness reused existing summary-only preflight and did not read
`.colameta/memory.md` content.

## Next

Use the Active Work Queue's next item: dashboard and Memory candidate layer.
Formal Memory writing remains blocked until Jenn chooses a Memory entry point.
