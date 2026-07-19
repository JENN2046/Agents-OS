# AGENTS OS F8 R4 BLOCK Governance Reconciliation Receipt v0.1

Date: 2026-07-19  
Lane: Yellow Work Batch  
Owner: Jenn  
Agent steward: Nobao  
Result: PASS

## Result

The external F8 R4 independent review outputs were verified against the
user-provided Windows archive, preserved byte-for-byte in the canonical Linux
workspace, and independently dispositioned. Both blockers are reproducible
from the fixed R4 bytes. R5 was not started.

## Preserved Evidence

```yaml
source_archive: C:\Users\51529\Downloads\2026-07-19-f8-r4-independent-review-outputs.zip
source_archive_sha256: e0a6abb1a5b9555122d778309e3c6d0193e20912fb88e379c64f29d89c43eac5
archive_entries: 4
archive_path_safety: PASS
external_review_sha256: 77b16f35d6798d42bbf50043d22185eb7ef2ab9b58e5c78a60008b9fe3e22d11
attack_results_sha256: eeac0ac0808bf602922744f3691f3e78d5065f68cff1c79c5978b81dcca50434
probe_sha256: 5405e30b0992ada0b5d43e98fccba84c5fba1253098af2d5ac43285c41b37ed2
checksums_sha256: 1b30319ed76ff301057e3a32c1325283c3343f27ddfe31cbd090eecba319039e
preserved_hashes: 4/4_MATCH
```

## Independent Disposition

```yaml
review_result: BLOCK
requires_R5: true
findings:
  F8-R4-B01: ACCEPTED_REPRODUCIBLE_FAVORABLE_INVALID_PATH
  F8-R4-B02: ACCEPTED_REPRODUCIBLE_INHERITED_PROFILE_DRIFT
H01_exact_owner_commitment_resolution: false
H01_claimed_result_rederived_through_merged_rules: false
non_NFC_stable_ref_rejected: false
NFC_internal_space_stable_ref_accepted: false
disposition_path: control-plane/registry/reviews/2026-07-19-agents-os-f8-r4-independent-review-disposition-v0.1.yaml
disposition_sha256: 8877b0e3e8c23a34731769a6bca48086f5f543dbdd53b7c564f1172f1e60691c
```

## Governance Projection

```yaml
active_work_queue: control-plane/registry/reports/2026-07-19-agents-os-active-work-queue-v5.9.md
active_work_queue_sha256: d7fa6b440c315c18143580b94851efc842ebe3f386368fa59b65810da4ecf25f
F8_status: R4_BLOCK_AWAITING_JENN_R5_NARROW_START_DECISION
R5_started: false
F8_accepted: false
F8_frozen: false
Phase_5A_started: false
implementation_authorized: false
runtime_activation_authorized: false
database_or_provider_authorized: false
production_authentication_authorized: false
private_raw_memory_access_authorized: false
sensing_or_recording_authorized: false
real_effect_authorized: false
```

## Safety

No R1, R2, R3 or R4 subject or manifest byte was modified. The external probe
source was preserved but was not executed as an external runner. No
`state-private/`, secret, credential, token, provider raw response or private
raw Memory content was read or copied. No commit, push, F8 acceptance, freeze,
Phase 5A start or R5 start was performed.
