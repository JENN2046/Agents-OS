# AGENTS OS Machine Skeleton Hardening v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: local hardening fixes after Machine Skeleton code review

## Result

Fixed the Machine Skeleton review findings:

```text
queue path preflight added before file reads
state-private queue path blocked before read
outside-workspace queue path blocked before read
denied signal coverage expanded for external writes, database writes, GitHub/Notion/email/upload/publish/deploy actions
blocked preview now emits actionable=false
queue-item schema required_false is now read by validation logic
tests expanded from 8 to 12 covered cases
```

## Validation Summary

```text
test-machine: PASS cases=12 failures=0
machine validate: PASS
protected queue path: blocked before read
outside workspace queue path: blocked before read
preview-now: execution_authorized=false actionable=true for current unblocked NOW
```

## Boundary

No `state-private/` content was read. The protected-path validation used a path
preflight and stopped before reading. No secrets, tokens, cookies, credentials,
private raw memory, provider raw response, active runtime config values, or raw
logs were read or output. No service, executor, provider call, runtime/plugin
activation, VCPToolBox activation, external write, formal Memory write, Git
push, tag, release, deploy, publish, or history rewrite was performed.

## Residual Risk

Denied signal detection is still string-pattern based. It is intentionally
conservative, but future Task Producer work should avoid treating this detector
as a full natural-language safety system.
