# AGENTS OS F8 R5 Fresh Full Atomic Independent Review Package v0.1

Date: 2026-07-19  
Owner: Jenn  
Agent steward: Nobao  
Status: fixed for fresh full atomic hash-bound independent review

## 1. Review unit

```yaml
review_unit: F8_HOME_TO_ORCHESTRATOR_MINIMUM_INTERFACE_V0_1_R5_ATOMIC_BUNDLE
atomic: true
partial_review: forbidden
subjects:
  R1: 4
  R2: 4
  R3: 4
  R4: 4
  R5: 4
  total: 20
authority_inputs: 49
author_evidence: 4
declared_inputs: 73
manifest: control-plane/registry/reports/2026-07-19-agents-os-f8-r5-atomic-independent-review-package-v0.1.manifest.yaml
manifest_sha256: c4161d9f4ffaaa094e2aebd9e5697cf40003e35691ca4e2a4de169ba4e83b672
```

The only allowed review results are `PASS_NO_BLOCKER` and `BLOCK`. Author
self-reviews are evidence of author-side execution only and must not substitute
for independent judgment.

## 2. R5 scope

R5 is limited to the two accepted R4 blockers:

1. bind all seven non-null upgraded R2 H01 consumers to exact immutable
   R3-style owner-source commitments and rederive H01 through fixed R2
   assessment semantics, R3 exact commitment resolution and R4 nullability;
2. restore `stable_ref` to strict JSON string, nonempty and NFC, without an
   internal-whitespace prohibition.

R1–R4 subjects and manifests are immutable historical bytes. R5 does not
reopen their review units.

## 3. Integrity gate

The reviewer must independently:

```text
recompute 73/73 declared input SHA-256 values
fully read 20/20 subjects
fully read 49/49 authority inputs
read 4/4 author evidence without adopting its conclusion
confirm R1-R4 subjects and manifests retain their declared hashes
verify archive path safety, duplicate paths, symlinks, traversal, CRC and CHECKSUMS
execute all 14 manifest commands from a plain extracted archive without .git
```

An unavailable required input or unexecuted required command yields `BLOCK`.

## 4. Required semantic review

### Exact owner-source binding

Independently verify that each non-null H01 consumer resolves the exact:

```text
commitment ref
commitment revision
commitment fingerprint
assessment id
assessment revision
assessment fingerprint
owner contract
issued Event commitment
```

The trusted owner-source anchor must remain outside caller-controlled fixture
re-signing. A coordinated rewrite of source row, consumer, resolution row,
section fingerprints and root must still fail.

### Merged H01 derivation

Confirm that `CANDIDATE_FORMED` is obtained only after:

```text
fixed R2 H01 resolution
R4 all-null / all-non-null validation
seven exact R3-style immutable commitment resolutions
zero lookup for optional all-null Jenn exact decision
execution of the fixed hash-verified R2 derive_case reducer
```

Changing only `derived_decision` or a caller claim must not create a favorable
result.

### stable_ref restoration

Confirm the exact profile is:

```text
type(value) is str
and value is nonempty
and NFC(value) == value
```

An NFC ref containing an internal space must be accepted. A non-NFC ref must
be rejected. R5 must not add a no-whitespace rule.

## 5. Independent attack minimum

Construct fresh fully re-signed attacks covering at least:

```text
commitment ref substitution
commitment revision substitution
commitment fingerprint substitution
cross-role commitment tuple substitution
source plus consumer plus resolution coordinated rewrite
trusted source row deletion duplication and reorder
R2 assessment tuple change with fixed commitment
claimed result substitution
non-NFC ref
NFC internal-space legal input
unknown missing wrong-type duplicate-key float NaN and integer-as-boolean input
runtime_usable command_authority task_write_authority or effect_authority forgery
```

For every rejection, report whether it came from the target semantic rule,
stale hash or unpropagated dependency. A stale-hash rejection is not proof of
the target rule.

## 6. Fixed commands

Run the 14 exact `validator_commands` from the manifest. They cover R1–R5
validators, five builder byte-reproduction comparisons, and R2–R5 portable
whitespace checks. R5's validator must report:

```yaml
result: PASS
H01_cases_verified: 1
non_null_owner_commitments_verified: 7
all_null_optional_consumers_verified: 1
trusted_owner_source_anchor_verified: true
merged_R2_R3_R4_derivation_verified: true
stable_ref_internal_space_positive_verified: true
regression_failures: 0
parser_failures: 0
runtime_usable: false
terminal_outcome: NOT_EXECUTED
```

## 7. Authority and safety questions

The reviewer must explicitly report whether R5:

- creates a second permission, identity, Task or Command authority;
- recomputes an upstream authority result instead of consuming it;
- accepts a caller-authored commitment as owner evidence;
- makes synthetic evidence runtime- or production-usable;
- accesses real Home data, private Memory, sensing, authentication, provider,
  database or real effect surfaces.

Any such path is a blocker.

## 8. Output contract

The independent YAML must bind the exact manifest and ZIP hashes and report:

```yaml
result: PASS_NO_BLOCKER | BLOCK
manifest_inputs: N/73
subjects_fully_read: N/20
authority_inputs_fully_read: N/49
author_evidence_read: N/4
fixed_commands: N/14
independent_fully_resigned_attack_count:
favorable_invalid_path_count:
legal_input_over_rejection_count:
findings:
  blocker:
  major:
  minor:
requires_R6:
F8_accepted: false
F8_frozen: false
Phase_5A_started: false
```

`PASS_NO_BLOCKER` is permitted only when all integrity, semantic, legal-input
and boundary checks pass with no blocker. The review does not itself accept or
freeze F8.

## 9. Governance boundary

```yaml
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
Git_delivery_authorized: false
next_gate: F8_R5_FRESH_FULL_ATOMIC_HASH_BOUND_INDEPENDENT_REVIEW
```
