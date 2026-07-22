# Phase 5C M0-C Plan R4 Narrow Correction Amendment v0.1

Date: 2026-07-22
Status: R4_STARTED_STRICT_SCOPE
Owner: Jenn
Agent steward: Nobao

## Immutable basis

R1–R3 subjects, manifests, author evidence, independent reviews, and finding
dispositions are historical fixed bytes. This amendment consumes the R3
independent review SHA-256
14e07fb392419a45e71b205493907bc9306e3dc6a3ab82a034d51de13b2df4e0
and closes exactly its two blockers.

## Authorized correction

1. The R4 profile must make every byte-affecting ustar header and padding rule
   normative: field offsets and widths, selected regular-file typeflag, numeric
   field form and overflow behavior, checksum preimage/output, magic/version,
   link/device/prefix/unused bytes, body padding, and terminal blocks.
2. The R4 witness must perform an actual incomplete cleanup attempt in a newly
   created, owned, disposable synthetic temporary root; observe the root and
   residue after that attempt; fail closed; and let only a separate finalizer
   remove the root.

## Required proof properties

* A fully re-signed archive with a NUL regular-file typeflag is rejected because
  R4 normatively selects ASCII 0, not because a hidden helper preference is
  compared with a fixture.
* Fully re-signed mutations of numeric form, checksum encoding, magic/version,
  zeroed fields, body padding, or terminal blocks are rejected by the exact
  R4 profile.
* The cleanup fault record is derived from a real post-attempt observation.
  Suppressing the observed root/residue or changing its fail-closed result is
  rejected after recomputing dependent fingerprints.

## Exclusions

R4 does not build, install, enable, load, or start a plugin. It does not modify
the sealed extension or VCPToolBox; access a runtime, database, provider,
private Memory, sensor, or effect boundary; create new authority; change
dependencies, locks, public APIs, or MCP; freeze the plan; or start
implementation.
