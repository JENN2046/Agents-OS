# AGENTS OS Control Chain v0.1

This directory contains the commander-first dual-track control chain.

It connects:

```text
Task Producer -> Machine Preview -> Commander Decision -> Track Selector
-> ColaMeta Track / Local Executor Track -> Track Result -> Queue Proposal
-> Failure Report / Stop Loop
```

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-control-chain/control_chain.py validate
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-control-chain/test-control-chain.py
```

## Authority Model

```text
Commander is the only authorization source.
Track Selector can route but cannot elevate.
Route-option candidates stop for Jenn decision and cannot be auto-selected.
ColaMeta Track is readiness/preview only in v0.1.
Local Executor can only run local_safe_only actions.
Queue Manager is proposal-only in v0.1.
Failure handling stops for review and never silently retries.
```

## Boundaries

The control chain must not:

```text
call providers
start services
activate runtimes or plugins
perform external writes
write formal Memory
read state-private
read or output secrets/tokens/cookies/provider raw response/private memory/raw logs
mutate Active Work Queue directly
auto-select a route option
promote a route option into the queue
silently retry failed validation
perform destructive cleanup
push/tag/deploy/publish
```

Queue updates are produced as proposals first. Reviewed queue mutation and
limited auto-promote remain separate gates. The reviewed mutation gate requires
an accepted Nobao review object and never authorizes auto-promote.

Failure handling classifies validation failure, scope violation, protected
path detection, dirty worktree conflict, unknown action type, P3 signal, and
invalid executor output into a local failure report. The stop loop keeps queue
promotion, repair execution, provider calls, external writes, and formal Memory
writes false.
