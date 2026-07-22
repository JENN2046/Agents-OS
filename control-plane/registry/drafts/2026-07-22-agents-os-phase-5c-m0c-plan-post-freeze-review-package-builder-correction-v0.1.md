# Phase 5C M0-C Plan Post-Freeze Review-Package Builder Correction v0.1

Date: 2026-07-22
Owner: Jenn
Agent steward: Nobao
Status: FIXED_FOR_FRESH_FULL_INDEPENDENT_REVIEW

## Purpose and non-semantic status

This is a narrow post-freeze correction to the review-package delivery helper.
It does not amend the accepted Phase 5C M0-C Plan R1–R4 semantic bundle.
The R1–R4 accepted subjects, manifests, independent reviews, freeze decision,
and the historical R3 builder remain immutable historical bytes.

The correction closes one delivery-integrity defect: the historical builder
uses a dictionary for archive entries and therefore cannot detect a manifest
input whose archive path equals a generated metadata member.  Without a guard,
a later generated member could overwrite the manifest-declared input bytes.

## Immutable historical source

The guarded successor must verify this exact source before delegating a valid
non-colliding build:

```yaml
historical_builder:
  path: control-plane/registry/build-phase-5c-m0c-plan-r3-review-package.py
  sha256: 8ddffa24d935189f733929b1aa0df16b997f0b65db946411fdfd0c5b889bcfd4
```

It must never modify, replace, or silently substitute that source.  If its
bytes differ, the successor must fail closed before reading manifest-declared
payloads or writing an archive.

## Exact correction contract

Before any manifest-declared source is read and before an output path is
created, the successor must derive the declared archive paths using the
historical parser and reject any exact collision with this closed set:

```text
MANIFEST.yaml
REPORT.md
SOURCE_SNAPSHOT_ID.txt
ARCHIVE_MAP.json
CHECKSUMS.sha256
```

The result for a collision is a stable `ValueError` whose message identifies
the colliding generated member.  The result must leave the requested output
file absent.  A non-colliding input delegates to the immutable historical
builder and must reproduce the R4 review archive byte-for-byte when given the
R4 manifest, report, and snapshot id.

## Evidence boundary

The fixture is synthetic.  It introduces no Plan subject, plugin, host,
runtime, database, provider, Memory, Session, authentication, permission,
identity, Task, Command, sensing, or effect authority.  It writes only a
temporary local ZIP while exercising the valid control; collision paths write
no archive.

## Completion boundary

This correction may only advance to a fresh independent review of this narrow
delivery-integrity unit.  A PASS does not reopen or re-freeze the Phase 5C
semantic plan and does not authorize implementation, Git delivery, a plugin,
or activation.
