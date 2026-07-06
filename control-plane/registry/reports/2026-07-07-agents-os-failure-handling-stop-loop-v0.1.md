# AGENTS OS Failure Handling Stop Loop v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: local control-chain failure classification and stop-loop result

## Result

The Control Chain now classifies failed local track output into a reportable
failure category before any queue movement.

Implemented categories:

```text
validation_failed
scope_violation
protected_path_detected
dirty_worktree_conflict
unknown_action_type
p3_signal_detected
executor_output_invalid
```

The stop-loop result keeps:

```text
queue_promoted=false
repair_attempt_performed=false
silent_retry_performed=false
destructive_cleanup_performed=false
provider_call_performed=false
external_write_performed=false
memory_write_performed=false
requires_nobao_review=true
```

## Repair Policy

```text
validation_failed: repair_attempt_allowed=true, max_repair_attempts=1
all other categories: repair_attempt_allowed=false, max_repair_attempts=0
```

This batch defines the repair policy only. It does not execute a repair loop,
does not silently retry, and does not create a repair patch.

## Validation Summary

```text
test-control-chain: PASS cases=21 failures=0
control_chain validate: PASS
py_compile control chain: PASS
test-machine: PASS cases=13 failures=0
test-producer: PASS cases=14 failures=0
validate-document-registry: PASS documents=260 pass=260 warn=0 fail=0
validate-federated-document-registry: PASS registries=3 pass=3 warn=0 fail=0
docctl status: PASS score=100
docctl doctor: PASS documents=302 unregistered=0 warn=0 fail=0
machine preview-now: PASS NOW=Dashboard And Memory Candidate Layer
```

Fixture coverage includes validation failure, protected path detection, dirty
worktree conflict, scope violation, unknown action type, P3 signal, invalid
executor output, stop-loop no-effect guards, and failed-result queue proposal
blocking.

## Files

```text
execution/agents-os-control-chain/README.md
execution/agents-os-control-chain/control-chain-manifest.json
execution/agents-os-control-chain/control-chain.schemas.json
execution/agents-os-control-chain/control_chain.py
execution/agents-os-control-chain/test-control-chain.py
control-plane/registry/reports/2026-07-07-agents-os-control-chain-v0.1.md
```

## Boundary

No `state-private/` content was read. No secrets, tokens, cookies, credentials,
private raw memory, provider raw response, active runtime config values, or raw
logs were read or output. No service was started. No real executor run, provider
call, VCPToolBox activation, plugin activation, external write, formal Memory
write, Git push, tag, release, deploy, publish, or history rewrite was
performed.

## Next

Move the Active Work Queue to `Dashboard And Memory Candidate Layer`. The next
layer should expose state and memory candidates without writing formal Memory.
