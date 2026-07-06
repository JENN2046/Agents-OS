# Review: docctl doctor Should-Register Backlog

Date: 2026-07-01
Status: reviewed
Scope: review the local cleanup that registers the 15 current
`should_register` files from the `docctl doctor` backlog classification.

## Review Result

No blocking issue found.

The cleanup followed the agreed order:

1. Registered the 15 `should_register` files.
2. Updated federated `expected_document_count`.
3. Ran document registry and federated registry validators.
4. Ran `docctl doctor`.
5. Left paired receipt/review evidence and registered them.

Validation result:

```text
registry document registry: PASS documents=53 pass=53 warn=0 fail=0
task-envelope document registry: PASS documents=12 pass=12 warn=0 fail=0
federated document registry: PASS registries=3 pass=3 warn=0 fail=0
federated validator fixtures: PASS cases=21 failures=0
docctl doctor: PASS registries=3 documents=95 scanned_files=142 unregistered=51 warn=51 fail=0
```

## Boundary Check

- `WORKSPACE_REGISTRY.yaml` was not modified.
- Historical archive files were left in place.
- No protected path was registered.
- No external write, runtime/provider call, or formal Memory registration was
  performed.

## Expected Outcome

The expected outcome was met: `docctl doctor` dropped `unregistered` from 66 to
51 while preserving the known historical/archive backlog for later grouped
handling.

## Residual Risk

- `docctl doctor` still reports 51 warnings by design.
- `WORKSPACE_REGISTRY.yaml` remains outside this draft registry cleanup and
  should be handled by a separate active-registry rule if needed.
- The 50 historical files still need a grouped archive-note/registry approach.
