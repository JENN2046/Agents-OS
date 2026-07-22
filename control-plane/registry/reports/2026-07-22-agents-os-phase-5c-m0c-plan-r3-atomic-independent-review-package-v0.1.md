# AGENTS OS Phase 5C M0-C Plan R3 Atomic Independent Review Package v0.1

Date: 2026-07-22
Owner: Jenn
Agent steward: Nobao
Status: FIXED_FOR_FRESH_FULL_ATOMIC_HASH_BOUND_INDEPENDENT_REVIEW

## Review unit

```yaml
review_unit: PHASE_5C_M0C_PLAN_BUILD_PROFILE_V0_1_R3_ATOMIC_BUNDLE
atomic: true
partial_review: forbidden
subjects: 7
authority_inputs: 72
author_evidence: 6
declared_inputs: 85
```

Canonical manifest SHA-256:

```text
e71ea4b04b676c98de6b660fb5985b25c84e9d35aa7956e38f42c24e475ed205
```

The author package is fixed by the manifest-bound bytes and a deterministic
review archive. No R3 Git commit, push, plan freeze, or implementation start is
authorized or claimed.

## Exact R3 question

R3 may answer only whether all three R2 blockers are closed:

1. Is the member-manifest preimage one exact eleven-field canonical projection
   in the normative R3 profile, builder, fixture, and validator?
2. Do success, failure, cleanup-residue, and wrong-return results derive from
   actual byte and owned-temporary-root observations, rather than favorable
   lifecycle labels?
3. Does the complete review ZIP contain every declared input and run all eight
   fixed commands after extraction without a Git checkout or missing R1
   dependency?

R1 and R2 fixed subjects, manifests, author evidence, independent reviews,
finding dispositions, and recorded commits remain historical immutable bytes.

## Required external procedure

The reviewer must:

1. Verify ZIP safety: CRC, duplicate paths, symlinks, absolute/traversal/
   backslash paths, `CHECKSUMS.sha256`, and `ARCHIVE_MAP.json`.
2. Recompute and fully read all 85 manifest-declared inputs in the extracted
   archive; do not rely on author self-review or validator output as an
   independent conclusion.
3. Execute all eight manifest commands from an extracted directory containing
   no `.git` directory. The R1 validator and R1 fixture are deliberately
   present because inherited fixed command 3 requires them.
4. Rebuild the R3 archive from the extracted `MANIFEST.yaml` and `REPORT.md`
   with `build-phase-5c-m0c-plan-r3-review-package.py`, using the manifest SHA
   as `--snapshot-id`, and compare the resulting archive bytes with the
   supplied archive.
5. Construct fully re-signed adversarial cases that distinguish target semantic
   rejection from stale-hash, missing-propagation, or exact-fixture rejection.

## Required attacks

At a minimum, independently exercise these classes:

* five-field versus eleven-field preimage substitution, header metadata,
  member order, checksum, raw archive byte, and canonical JSON drift;
* forged success/failure return bytes, claimed cleanup residue, suppressed
  residue probe, and suppressed wrong-return probe;
* sealed VCPToolBox commit/path/blob/SHA substitution; sealed source-member
  addition/removal/duplication/reordering/replacement; and unsafe path/kind
  substitutions;
* eager native loading, sixth N-API method, and enabled-manifest evidence;
* removal of the R1 validator or R1 fixture from an independently rebuilt
  archive; and
* unknown fields, wrong types, unsafe integers, non-NFC paths, and duplicate
  JSON keys.

An accepted attack is a blocker. A useful rejection must be attributable to
the target contract or a fixed trusted source, not merely a stale root
fingerprint or equality with the author fixture bytes.

## Boundary

This package remains a planning-only synthetic proof. It does not build,
install, enable, or load a plugin; modify extension source or VCPToolBox;
access a runtime, database, provider, private Memory, sensor, or effect
boundary; or create any new loader, service, writer, permission, identity,
Task, Command, or effect authority.

Allowed independent-review results are only `PASS_NO_BLOCKER` and `BLOCK`.
Neither result automatically freezes the plan or starts implementation.
