# AGENTS OS F3 R4 Atomic Independent Review Package v0.1

Date: 2026-07-16  
Status: `READY_FOR_FRESH_HASH_BOUND_INDEPENDENT_REVIEW`  
Owner: Jenn  
Agent steward: Nobao

## Review unit

```yaml
id: F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R4_ATOMIC_BUNDLE
subject_count: 4
precedence: [R4, R3_other, R2_other, R1_other]
partial_review: forbidden
F3_accepted: false
F3_frozen: false
F4_started: false
implementation_authorized: false
```

| Subject | SHA-256 |
|---|---|
| R1 | `e439b3178984ac28ae584a961e2e0dc2248002592f0fb571e5e0db05d117a70e` |
| R2 | `4cd066dacf0f73d21566640a25c5cf5e90ca800ed4a793827c5088936703b236` |
| R3 | `8a25b247a0618ab06ef6186464405b9d137bf68967a9952647986562cb93244c` |
| R4 | `17b933e2ddf063422d4d695b5f07542d00f34a4a20280765369d0949afcff6ad` |

## Canonical manifest

```text
control-plane/registry/reports/2026-07-16-agents-os-f3-r4-atomic-independent-review-package-v0.1.manifest.yaml
SHA-256 3075cda63fcb2c7937cb800a3bc09cc830d17e2f98b899828db15e09ab9f79ff
```

The manifest is the review authority. It binds 29 complete files: four
subjects, ten governing inputs, and fifteen lineage records. This presentation
is excluded from that manifest and cannot substitute for the fixed bytes.

## R4 correction surface

R3's fresh review returned `BLOCK`, 0 blocker / 4 major / 0 minor. R4 corrects:

1. one immutable restore-lineage claim with contiguous, non-competing retry
   attempts after an exact abandonment;
2. one effective R4 atomic-bundle literal across every canonical graph field
   and fingerprint named `F3_contract_version`;
3. complete registry-revision-4 issuance and activation definitions with exact
   payload/reducer digests and type fingerprints;
4. exact authority-input, READY, and Event schemas plus a 60-entry synthetic
   manifest containing activation descriptors and definition before activation.

## Mandatory recomputation

```text
issuance type fingerprint
f3f728ee416cc9477f25279ffcf436554cd8dde257c62ec86021af4e41755c16

activation payload descriptor SHA-256
7bfc6a067e0cce72a39c4b8fd0cf7d0021ecd28a9f88d2afccae151d3157fd15

activation reducer descriptor SHA-256
8d5ccccc6a80647954472925de5e2addbbacdb54cf17ebdcad0140ba8e2469e1

activation type fingerprint
a40dda2278ba856ab9248f8d0da22b6fd8857ff70f9d1d68aee7a83c20ef610b
```

The reviewer must also reconstruct attempt ordinals, terminal uniqueness,
R4-version propagation, the complete two-type registry, and all 60 exact
synthetic mappings. Matching digests alone is insufficient if the semantics
remain contradictory or broaden authority.

## Fresh-review protocol

The reviewer must start from the canonical manifest, recompute 29/29 hashes,
read all four subjects completely, then perform fresh judgment before using old
reviews as lineage. Author self-review files are digest-only and their content
or conclusions must not be read.

Required coverage:

```yaml
questions: 22
adversarial_checks: 36
derived_values: 4
synthetic_entries: 60
```

Write exactly:

```text
control-plane/registry/reviews/2026-07-16-yellow-agents-os-f3-r4-full-atomic-independent-review.yaml
```

Allowed results are `PASS_NO_BLOCKER` and `BLOCK`. Each finding needs exact
section evidence, counterexample, impact, and correction. A pass requires no
blocker, major, unresolved ambiguity, mapping gap, or hash mismatch.

## Routing and boundary

```text
BLOCK -> preserve R1-R4/review -> disposition -> R5 only if required
PASS  -> prepare Jenn-only atomic accept/freeze decision surface
```

No route automatically accepts/freezes F3, starts F4, or authorizes code,
database, runtime, authentication, service, provider, effect, commit, push, PR,
or merge work.
