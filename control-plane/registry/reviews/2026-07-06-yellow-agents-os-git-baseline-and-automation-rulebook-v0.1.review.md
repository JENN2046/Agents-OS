# AGENTS OS Git Baseline And Automation Rulebook Review v0.1

Status: accepted
Date: 2026-07-06
Owner: Jenn
Agent steward: Nobao
Scope: review of local Git baseline and prohibited-first automation update

## Review

The change reduces AGENTS OS operating friction by making the rule explicit:
safe local work should proceed automatically, while P3/prohibited behavior still
stops. This keeps the governance chain from turning ordinary construction into
micro-confirmation paperwork.

The root `.gitignore` now protects the first Git baseline from accidentally
including private state, runtime source checkouts, caches, build outputs, logs,
databases, dependency directories, and secret/auth/provider files.

## Risk Review

- No P3 boundary was downgraded.
- No runtime source, including `runtime/VCPToolBox`, was changed.
- No state-private, secret, credential, token, cookie, private memory, provider raw response, or raw log content was read.
- No provider call, service startup, executor run, deploy, publish, tag, push, or destructive operation was performed.
- Remaining risk is local-only: future agents must keep using precise staging and avoid `git add .` unless the repo is known clean and the ignored boundaries are verified.

## Validation Expectation

The evidence is valid only when the document registry validator, federated
registry validator, `docctl doctor`, and `docctl status` pass after the registry
updates.
