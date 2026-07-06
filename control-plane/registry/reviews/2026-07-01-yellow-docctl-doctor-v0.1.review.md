# Review: docctl doctor v0.1

Date: 2026-07-01
Status: reviewed
Scope: read-only document governance doctor

## Result

Accepted as a first read-only automation layer.

`docctl doctor` correctly stays in the green/yellow zone:

- it checks only the explicitly listed Federated Document Registry entries
- it runs known local validators
- it reports findings without rewriting registry data
- it treats unregistered source files as warnings
- it treats missing files, protected paths, count drift, and validator failures
  as hard failures

## Evidence

```text
docctl doctor fixture tests: cases=4 failures=0
document registry validator: documents=36 pass=36 warn=0 fail=0
federated registry validator: registries=3 pass=3 warn=0 fail=0
governance registry validator: objects=19 pass=19 warn=0 fail=0
docctl doctor current scan: registries=3 documents=77 scanned_files=139 unregistered=66 warn=66 fail=0
```

## Remaining Risk

- Current document registries still have historical unregistered-file backlog.
- `docctl doctor` should remain read-only until a separate proposal defines
  safe automatic repair.
- The unregistered-file rule may need ignore policies later, but the first
  version should keep surfacing the backlog plainly.
