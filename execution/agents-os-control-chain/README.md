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
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-control-chain/control_chain.py route-choice-queue-proposal --route-choice-preview-json /path/to/route-choice-preview.json --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-control-chain/control_chain.py reviewed-route-adoption-preview --proposal-json /path/to/proposal.json --review-json /path/to/review.json --queue control-plane/registry/reports/2026-07-17-agents-os-active-work-queue-v2.4.md --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-control-chain/control_chain.py reviewed-route-adoption-apply-gate --proposal-json /path/to/proposal.json --review-json /path/to/review.json --queue /path/to/queue.md --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-control-chain/control_chain.py route-choice-handoff-reconciliation --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-control-chain/control_chain.py route-choice-template-readiness --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-control-chain/control_chain.py route-choice-end-to-end-readiness --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-control-chain/control_chain.py route-choice-adoption-bundle-preview --confirmation-text "确认选择 AGENTS OS 下一路线：Formal Memory Loop。" --json
```

## Authority Model

```text
Commander is the only authorization source.
Track Selector can route but cannot elevate.
Route-option candidates stop for Jenn decision and cannot be auto-selected.
ColaMeta Track is readiness/preview only in v0.1.
Local Executor can only run local_safe_only actions.
Queue Manager is proposal-only in v0.1.
Route-choice queue proposal is preview-only and cannot mutate the queue.
Reviewed route adoption preview can inspect an accepted review but cannot write.
Reviewed route adoption apply gate can append to NEXT only with explicit --apply.
Route-choice handoff reconciliation verifies that Machine and Dashboard agree
on Jenn-owned route choice without selecting or adopting a route.
Route-choice template readiness verifies Task Producer template coverage without
outputting raw templates, selecting a route, or mutating the queue.
Route-choice end-to-end readiness verifies A-E fixture flow through preview,
proposal, reviewed adoption preview, and apply-gate preview without selecting a
route, mutating the real queue, or executing.
Route-choice adoption bundle preview packages future explicit Jenn route-choice
text into route preview, queue proposal, Nobao review, adoption preview, and
apply-gate preview without applying it or mutating the real queue.
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
adopt a selected route into workspace state
promote a route option into the queue
silently retry failed validation
perform destructive cleanup
push/tag/deploy/publish
```

Queue updates are produced as proposals first. Reviewed queue mutation and
limited auto-promote remain separate gates. The reviewed mutation gate requires
an accepted Nobao review object and never authorizes auto-promote.

Explicit reviewed route adoption uses a same-directory, identity-bound
transaction file and atomic `renameat2(RENAME_EXCHANGE)`. It fsyncs file and
directory state, and keeps the replacement bound to the original queue's
`mode`, `uid`, `gid`, and single-link invariant after write, before exchange,
after exchange, and during final-state classification. It revalidates the
displaced old bytes and installed new bytes and reports `NO_WRITE`, `COMMITTED`,
or `PARTIAL_OR_UNKNOWN`. An uncertain post-exchange result never authorizes
further queue mutation and must preserve truthful `write_performed` evidence
for reconciliation. A pre-exchange metadata drift proves `NO_WRITE` only for
the active queue; unresolved transaction-file cleanup remains explicit and
requires Jenn-owned reconciliation. Because the replacement transaction does
not preserve xattrs, POSIX ACLs, SELinux labels, or other extended metadata,
the apply gate rejects any original inode carrying them before exchange.
Extended metadata appearing on a replacement inode also blocks `COMMITTED`;
pre-exchange detection returns `NO_WRITE`, while post-exchange detection must
prove rollback or report `PARTIAL_OR_UNKNOWN`. Every invocation inventories
the bound parent directory for the queue-specific
`.agents-os-txn-*.tmp` namespace before creating a new transaction and again
before final classification. A prior regular-file residue is reported with its
device/inode identity; a link or otherwise uninspectable residue is never
followed. Either form requires explicit reconciliation and blocks adoption.

Failure handling classifies validation failure, scope violation, protected
path detection, dirty worktree conflict, unknown action type, P3 signal, and
invalid executor output into a local failure report. The stop loop keeps queue
promotion, repair execution, provider calls, external writes, and formal Memory
writes false.
