# AGENTS OS F6 R4 BLOCK → R5 Atomic Review Package Receipt v0.1

Date: 2026-07-18
Result: PASS

Preserved R1–R4 fixed bytes, recorded the independent R4 `BLOCK`, accepted its
single finding, created only the contextual evidence assessment R5 correction,
and fixed a 20-subject/58-input atomic review package.

```yaml
R4_review_sha256: 852da403282eaff2226a63e3e2325b23a1637c8330d8d6cda28be5e9fe286791
R4_case_sha256: 97348e9dbeb0c6fbc9d609e40151f11db47184ffe42495ba127c52de76289c72
R4_disposition_sha256: 76ed7cc38a40a2c39ce94dbe5f652fde999a40417657703c21d9008c52908627
R5_manifest_sha256: bb506ba3213a68d4e12797ae142fc73ef0a49f32166802972b70dde662f8c43b
R5_fixture_sha256: 07b1f45c88438763eef169ad17903924cc6ecfcac382ecc41508ba1993a3bbc6
R5_ZIP_sha256: ae8aaa18f1ece3a421d2386da5d9c4610aaa2de78431df2a192cb5b836344b50
manifest_hashes: 58/58_PASS
ZIP_entries: 61
ZIP_checksums: 60/60_PASS
fixed_cases: 62/62_REJECTED
R2_cases: 17/17_REJECTED
R3_cases: 7/7_REJECTED
R4_context_case: 1/1_REJECTED_BY_TARGET_R5_SEMANTIC
exceptions: 0
real_occurrences: 0
```

Excluded and untouched: `memory/**`, `state-private/**`, `ops/reports/**`,
`execution/agents-os-workbench/records/**`, unrelated router work and secret or
provider-response surfaces. No commit, push, PR, merge, release or runtime work
was performed. F6 remains unaccepted and unfrozen; F7 remains unstarted.
