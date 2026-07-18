# AGENTS OS F6 R3 BLOCK → R4 Atomic Review Package Receipt v0.1

Date: 2026-07-18
Result: PASS
Lane: Yellow bounded governance batch

## Scope

- preserved all fixed F6 R1–R3 subject bytes;
- recorded the R3 independent `BLOCK`, seven synthetic consistency cases and
  five-finding disposition;
- recorded Jenn's narrow R4 start decision;
- created only the five authorized R4 corrections;
- fixed a 16-subject, 49-input atomic independent-review package;
- synchronized the current queue and governance projections.

## Fixed hashes

```text
R3 review:      ffbd04f0ad11846e93d82cdd0009f7236f2883f392ab698e65ab870a59e18180
R3 cases:       c023ecbdd9aaff8e81a73120cbd18518f847b156c9aaf91f6bd5bf635201e443
R3 disposition:a8cc8f0f8c5a863dd8bd4c4a22d4a1a61f98f7a133ac85a099b36131d0aa3722
R4 start:       43f6efd78125cba748255e306175cb4e65ca5694d15ad8cfa7b8f8ac7549b235
R4 amendment:   ae12f429533061beac78e59163345495cd161e6828d9fa5e375342d2c8f79abf
R4 builder:     9ac2f1594afbed21510e11fd307a984d66df601b39183c16dc8e08a4dfcb258e
R4 fixture:     e63bf9fc2c1162672975538590ecce5ad7a1fa6e74679703d3134f820d9c2a47
R4 validator:   4d0e238906a1c634bf12d30f775ba4ef323ab18f339ebd19826b39e97a344d6f
R4 self-review: 6e6e2a9f3506f49702b68d2f03a6ce8411d6dcb8fcd2c30316e085d4617711d7
R4 manifest:    22396132777538619620c6e1e5ceb4b03338d08b9792c60c266a6d744721bb93
R4 presentation:3e194c8fb0e51f1513bbff6fc83863f44c5529a6bd40868a2aead07d9ac79e38
queue v3.5:     8dd786f9f92519e3cea009aee8692a96ae9905e2f64f3cc808c2a94e3d39ef57
offline ZIP:    60f9eb7ccb0f5373de1dfee7267989aea230165c0ed81225460828a3dfbf4bd5
```

## Validation

```yaml
manifest_hashes: 49/49_PASS
R1_R2_R3_fixed_subject_hashes_unchanged: true
builder_byte_reproduction: PASS
fixed_negative_total: 62/62_REJECTED
R2_coordinated_cases: 17/17_REJECTED
R3_independent_cases: 7/7_REJECTED
case_exceptions: 0
five_R4_semantic_surfaces: PASS
real_occurrences: 0
terminal_outcome: NOT_EXECUTED
offline_ZIP_entries: 52
offline_ZIP_checksums: 51/51
```

Excluded and untouched: `memory/**`, `state-private/**`, `ops/reports/**`,
`execution/agents-os-workbench/records/**`, unrelated router work and all secret
or provider-response surfaces.

No commit, push, PR, merge, release, deploy, publish or tag was performed.
F6 remains unaccepted and unfrozen; F7 remains unstarted.
