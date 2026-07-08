# Codex App Server Active Loop Boundary

This directory is an AGENTS OS execution-layer candidate component for local Codex-to-Codex communication.

It may provide:

- Worker, Reviewer, and Verifier message routing
- Bridge-mediated local App Server communication
- read-only snapshot-bound coordination
- local observer and live-tail views
- structured receipts, reports, and review decisions

It must not provide or imply:

- AGENTS.md interpretation authority
- Jenn gate bypass
- provider gate bypass
- Memory gate bypass
- external-write gate bypass
- queue, goal, selector, or validation governance authority
- commit, push, deploy, release, tag, or publication authority
- raw private state, credential, token, cookie, or secret access

The control-plane and workbench decide whether a task may enter this component.
This component only runs within the authority explicitly granted to it.

Runtime outputs, raw message logs, observer HTML/JSON, reports, receipts, snapshots,
and other evidence must stay out of this source tree by default. Importable evidence
belongs in an explicitly reviewed records path, such as:

```text
ops/records/codex-appserver-active-loop-import/
```

The message bus transmits and records information. It does not grant authority.
