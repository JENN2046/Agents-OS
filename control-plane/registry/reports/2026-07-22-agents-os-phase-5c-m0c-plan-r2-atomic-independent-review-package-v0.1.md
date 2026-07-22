# AGENTS OS Phase 5C M0-C Plan R2 Atomic Independent Review Package v0.1

Date: 2026-07-22
Owner: Jenn
Agent steward: Nobao
Status: FIXED_FOR_FRESH_FULL_ATOMIC_HASH_BOUND_INDEPENDENT_REVIEW

## Review unit

```yaml
review_unit: PHASE_5C_M0C_PLAN_BUILD_PROFILE_V0_1_R2_ATOMIC_BUNDLE
atomic: true
partial_review: forbidden
subjects: 5
authority_inputs: 60
author_evidence: 4
declared_inputs: 69
```

Canonical manifest SHA-256:

```text
610b42a8d0eefadefe9e7625ea4b60cd370ac02f24b64b37ab7c9d56360a1a27
```

The reviewer must hash and fully read all 69 declared inputs, execute all six
fixed commands, preserve the R1 immutable lineage, and independently perform
fully re-signed structural attacks. Author self-review and validator PASS are
evidence only; neither is an independent acceptance.

## Exact R2 question

R2 may answer only whether the two R1 blockers are closed:

1. Does the plan now select one exact archive encoding, member mapping,
   checksum preimage, and success/failure output cleanup lifecycle?
2. Does the validator now derive all relevant structural facts from sealed
   records and actual synthetic archive bytes rather than favorable labels?

The full 46-file extension source inventory is a hash-bound read-only input so
the reviewer can independently verify the R2 source-inventory seal. No source
file is modified by this package.

## Required attacks

At a minimum, mutate and fully re-sign each of these classes:

* sealed VCPToolBox commit/path/blob/SHA substitution;
* sealed extension member addition, removal, duplication, reordering, and
  replacement;
* symlink, traversal, absolute path, backslash path, and caller-output-path
  substitution;
* eager native loading and a sixth N-API method;
* enabled-manifest evidence;
* ustar header, member order, metadata, raw byte, checksum, and member-manifest
  drift; and
* success/failure cleanup residue or archive-delivery forgery.

A useful rejection must be attributable to the target contract or a fixed
trusted source, not merely a stale root fingerprint or equality with the
author's fixture bytes.

## Boundary

This review package does not accept or freeze the plan and does not authorize
implementation, extension-source modification, VCPToolBox access or startup,
plugin enablement, native host loading, runtime activation, database access,
production authentication, private Memory, provider, sensing, real effect,
release, deploy, publish, commit, push, or merge.

Allowed independent-review results are only `PASS_NO_BLOCKER` and `BLOCK`.
After review, governance stops at the appropriate Jenn decision surface.
