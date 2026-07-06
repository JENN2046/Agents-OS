# Review: docctl known_external_scope

Date: 2026-07-01
Status: reviewed
Scope: review the `docctl doctor` change that separates known external-scope
files from true unregistered backlog.

## Review Result

No blocking issue found.

The change does what it is supposed to do:

- `known_external_scope` paths are checked with the same local path boundary
  logic as other doctor paths.
- Protected known-scope paths fail instead of being hidden.
- `WORKSPACE_REGISTRY.yaml` is not modified and is no longer counted as
  unregistered draft document backlog.

Validation result:

```text
docctl doctor tests: PASS cases=6 failures=0
registry document registry: PASS documents=55 pass=55 warn=0 fail=0
federated document registry: PASS registries=3 pass=3 warn=0 fail=0
federated validator fixtures: PASS cases=21 failures=0
docctl doctor: PASS registries=3 documents=97 scanned_files=144 known_external_scope=1 unregistered=50 warn=50 fail=0
```

## Boundary Check

- `WORKSPACE_REGISTRY.yaml` is referenced as known external scope but was not
  modified.
- `known_external_scope` paths still go through path safety checks.
- Protected paths must fail instead of being hidden.
- No external write, runtime/provider call, or formal Memory registration was
  performed.

## Expected Outcome

The expected outcome was met: `docctl doctor` dropped `unregistered` from 51 to
50, with `known_external_scope=1`.

## Residual Risk

- The remaining 50 warnings are still real historical archive/evidence backlog.
- The next cleanup should use grouped archive notes rather than registering each
  historical file as a current document object.
