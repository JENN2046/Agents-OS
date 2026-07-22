# Phase 5C M0-C Plan Post-Freeze Review-Package Builder Correction — Independent Review Package v0.1

Date: 2026-07-22
Owner: Jenn
Agent steward: Nobao
Status: FIXED_FOR_FRESH_FULL_INDEPENDENT_REVIEW

## Review unit

```yaml
review_unit: PHASE_5C_M0C_PLAN_POST_FREEZE_REVIEW_PACKAGE_BUILDER_CORRECTION_V0_1
atomic: true
partial_review: forbidden
semantic_plan_amendment: false
```

This package reviews only a post-freeze review-package builder correction.  It
does not modify or re-accept the frozen Phase 5C M0-C Plan R1–R4 subjects.

## Exact questions

1. Does the successor verify the exact historical R3 builder SHA-256 before
   parsing declared inputs, loading the historical module, or writing output?
2. Does it reject each exact manifest-path collision with all five generated
   archive member names before source payload reads or output creation?
3. Does a valid non-colliding synthetic package remain byte-identical to an
   invocation of the immutable historical builder?
4. Does the correction preserve the frozen R4 manifest, decision, independent
   review, accepted subjects, and historical builder bytes?

## Required procedure

1. Verify ZIP CRC, safe member paths, no duplicates or symlinks,
   `CHECKSUMS.sha256`, and `ARCHIVE_MAP.json`.
2. Recompute and fully read every manifest-bound input.  Author self-review is
   evidence only, never an independent conclusion.
3. Run every listed fixed command in both the supplied workspace snapshot and a
   no-Git extracted archive.
4. Independently construct collision manifests for all five reserved names,
   ensure the requested output file remains absent, and verify a valid
   non-colliding control against the historical builder.
5. Confirm the correction has not changed R1–R4 semantic subjects or opened an
   implementation, VCPToolBox, plugin, runtime, database, provider, private
   Memory, sensing, authentication, or real-effect boundary.

## Required adversarial cases

At minimum, test exact collisions for:

```text
MANIFEST.yaml
REPORT.md
SOURCE_SNAPSHOT_ID.txt
ARCHIVE_MAP.json
CHECKSUMS.sha256
```

Also test an unchanged valid control and a malformed collision row.  A useful
rejection must arise from the generated-member collision guard or immutable
historical source seal, not from a stale checksum, an absent payload, or a
fixed-fixture-only comparison.

Allowed results are `PASS_NO_BLOCKER` and `BLOCK`.  Neither result changes the
frozen Phase 5C Plan or authorizes Git delivery, implementation, activation,
or any real external effect.
