# AGENTS OS Workspace

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

This workspace has a local Git baseline on `main`.

Use precise staging. Do not use `git add .` unless the workspace is known clean
and the ignored private/runtime boundaries have been checked.
