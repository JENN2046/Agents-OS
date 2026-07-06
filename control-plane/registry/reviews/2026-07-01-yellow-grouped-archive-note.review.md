# Review: Grouped Archive Note

Date: 2026-07-01
Status: reviewed
Scope: review the grouped archive note and `docctl doctor` archive-note
handling.

## Review Result

No blocking issue found.

The grouped archive note covers the 50 historical files without moving,
deleting, rewriting, or promoting them. `docctl doctor` now distinguishes three
states:

- current registered files
- known external-scope files
- archived historical files

Validation result:

```text
docctl doctor tests: PASS cases=8 failures=0
registry document registry: PASS documents=58 pass=58 warn=0 fail=0
federated document registry: PASS registries=3 pass=3 warn=0 fail=0
federated validator fixtures: PASS cases=21 failures=0
docctl doctor: PASS registries=3 documents=100 scanned_files=147 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
```

## Boundary Check

- Historical files were preserved in place.
- No bulk move, delete, rewrite, or active promotion was performed.
- Archive note paths must still pass local path safety checks.
- Protected paths must fail instead of being hidden by archive notes.
- No external write, runtime/provider call, or formal Memory registration was
  performed.

## Expected Outcome

The expected outcome was met: `docctl doctor` reports `archived=50` and
`unregistered=0`.

## Residual Risk

- Archive-note parsing is intentionally small: it reads backtick-wrapped local
  source paths from archive notes and checks them through the same path boundary
  logic.
- The files are archived for document-governance purposes only; they remain on
  disk as historical evidence.
