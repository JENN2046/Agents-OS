# AGENTS OS Phase 5C M0-C Plan R4 Atomic Independent Review Package v0.1

Date: 2026-07-22
Owner: Jenn
Agent steward: Nobao
Status: FIXED_FOR_FRESH_FULL_ATOMIC_HASH_BOUND_INDEPENDENT_REVIEW

## Review unit

```yaml
review_unit: PHASE_5C_M0C_PLAN_BUILD_PROFILE_V0_1_R4_ATOMIC_BUNDLE
atomic: true
partial_review: forbidden
subjects: 9
authority_inputs: 84
author_evidence: 5
declared_inputs: 98
```

Canonical manifest SHA-256:

```text
5fb69183acadaddb5003d63ed80229ed1cbe4ce5363c96bd3c61099ca430575e
```

R4 is a narrow correction of two R3 independent-review blockers. It preserves
all R1–R3 fixed bytes. No R4 Git commit, push, plan freeze, or implementation
start is authorized or claimed.

## Exact R4 questions

1. Does the normative R4 profile determine every byte-affecting POSIX ustar
   header and padding rule, including the selected ASCII 0 typeflag, numeric
   fields, checksum, magic/version, zero-only fields, body padding, and
   terminal blocks?
2. Does the cleanup fault probe actually attempt cleanup while archive.tar
   remains in a newly created owned temp root, observe the post-attempt
   root/residue, emit a fail-closed result, and remove the root only in a
   separate finalizer?

## Required external procedure

The reviewer must:

1. Verify ZIP CRC, paths, duplicates, symlinks, traversal protection,
   CHECKSUMS.sha256, and ARCHIVE_MAP.json.
2. Recompute and fully read all 98 manifest-bound inputs in the extracted
   archive; author evidence is not an independent conclusion.
3. Run all nine manifest commands in both the supplied workspace snapshot and a
   no-Git extracted archive.
4. Rebuild the ZIP with the inherited deterministic R3 review-package builder,
   the supplied MANIFEST.yaml and REPORT.md, using the R4 manifest SHA as the
   source snapshot ID; compare resulting bytes with the supplied archive.
5. Construct fully re-signed adversarial cases and identify target-semantic
   rejection rather than stale-hash or fixed-fixture-only rejection.

## Required attacks

At minimum, independently exercise:

* ASCII 0 to NUL typeflag substitution; numeric padding/terminator, checksum,
  magic/version, link/device/prefix/unused-header, body-padding, and
  terminal-block drift;
* header-profile field removal, renaming, reordering, unknown-key, or
  value-contract drift;
* suppression or forgery of the actual post-cleanup root/residue observation,
  cleanup fault result, or finalizer ordering; and
* unknown fields, wrong types, unsafe integers, non-NFC paths, and duplicate
  JSON keys.

An accepted attack is a blocker. A useful rejection must arise from the
normative R4 byte or cleanup-fault semantics, a fixed trusted source, or the
actual owned-root re-execution — not merely from stale fingerprints or equality
with author fixture bytes.

## Boundary

This is a planning-only synthetic proof. It does not build, install, enable,
load, or start a plugin; modify the extension or VCPToolBox; access runtime,
database, provider, private Memory, sensing, or effect boundaries; or create
new permission, identity, Task, Command, or effect authority.

Allowed independent-review results are PASS_NO_BLOCKER and BLOCK. Neither
result automatically freezes the plan or starts implementation.
