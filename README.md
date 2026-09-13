# AGENTS OS Workspace

Navigation revision: `2026-09-13.1`.

Start with [AGENTS.md](AGENTS.md) for the single root operating-rule entry,
[CURRENT_STATE.md](CURRENT_STATE.md) for the one-page current view,
[WORKSPACE_MANIFEST.md](WORKSPACE_MANIFEST.md) for project structure, and
[WORKSPACE_MAP.md](WORKSPACE_MAP.md) for machine locations, source branches and
unverified deployment fields. Historical full text remains in original D
(`/home/ubuntu/Agents-OS-docs-20260913`); it was not admitted or copied into this
candidate. See [candidate verification scope](#candidate-verification-scope) for exclusions and validation.

This is Jenn's local AGENTS OS construction workspace.

The workspace is a private local control-plane and runtime-lab, not a public
service, package, or deployment root.

## Current Shape

- `AGENTS.md` is the local operating contract for agents.
- `CURRENT_STATE.md` is the current reality snapshot and handoff.
- `WORKSPACE_MANIFEST.md` gives the directory map and safe-entry notes.
- `control-plane/` holds governance contracts, validators, policies, registries,
  runbooks, and task envelopes.
- `governance/` holds safety boundaries and automation rules.
- `runtime/` holds upstream-trackable runtime cores; treat it as high caution.

## Default Work Rule

Safe local work should proceed automatically, then be validated and reported.
P3/prohibited behavior stops.

Do not read `state-private/`. Do not read or output secrets, tokens, cookies,
private raw memory, provider raw responses, active runtime config values, or raw
logs.

## Local Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
```

## Git Baseline

This repository has a remote `main` baseline. A directory with the same workspace
name does not thereby have valid local Git metadata; consult the machine map.

Use precise staging. Do not use `git add .` unless the workspace is known clean
and the ignored private/runtime boundaries have been checked.

External push is blocked by default for the root workspace repository. Local Git
history has contained private Notion page URLs and working synthesis material.
Do not add a remote or push this repository outside Jenn's local machine unless
Jenn explicitly authorizes a private-history review or history-scrub gate.

## Candidate verification scope

This is a Tencent Cloud document candidate, not adopted rules for another
workspace and not evidence of runtime readiness. Machine observations retain
their recorded source and time; Git source versions are distinct from deployment
versions. The private local preservation commit is
`6ffd8ea8209409051e0dff0b1ebe4c4a8cf79fd0`; a later revised candidate would have a
new identity.

Stage2 evidence: 18 scoped offline document checks passed; independent document
and report reviews had zero remaining actionable findings. Stage3 verified the
18 admitted document blobs and their exact tree delta. These are limited checks,
not system acceptance. Original workspace scripts/docctl, full YAML/schema,
outside-candidate links, runtime/service/provider/deployment checks and private
history review were NOT RUN.

The full README.candidate.md, manifest.json, review.md and validation.json remain
private companion reports outside this Git tree. This summary does not publish
those reports or the held historical full text. Original D retains held history;
its body was not admitted to this candidate. Existing publication and review
gates remain unchanged; neither this summary nor repository privacy authorizes
remote delivery, rule adoption, deployment or retirement.
