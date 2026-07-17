# AGENTS OS F5 R4 Atomic Independent Review Package v0.1

Status: Fixed for fresh full atomic hash-bound independent review  
Date: 2026-07-17  
Owner: Jenn  
Agent steward: Nobao  
Review unit: `F5_OUTBOX_DELIVERY_RECOVERY_V0_1_R4_ATOMIC_BUNDLE`

## 1. Canonical Manifest

```text
path=control-plane/registry/reports/2026-07-17-agents-os-f5-r4-atomic-independent-review-package-v0.1.manifest.yaml
sha256=5321a45129c18e385314bbcabd034b23709185b61505a026b015873d6ec570e4
declared_input_count=40
subject_count=16
required_review_questions=32
required_adversarial_checks=40
```

The manifest is the canonical review unit. This report is presentation only and
is not included in the manifest digest cycle.

## 2. Review Rule

The reviewer must perform a fresh full atomic judgment over all fixed R1-R4
subjects. Partial review and partial acceptance are forbidden.

```yaml
allowed_results:
  - PASS_NO_BLOCKER
  - BLOCK

PASS_NO_BLOCKER_requires:
  blocker: 0
  major: 0
  minor: 0
  unresolved: 0

hash_mismatch: BLOCK
missing_required_input: BLOCK
partial_subject_read: BLOCK
```

Prior reviews are finding lineage only. They cannot substitute for current
judgment. The current R4 author self-review may be hash-verified but its content
or conclusion must not be opened or used by the independent reviewer.

## 3. Independence And Safety

The reviewer must:

- use a separate fresh reviewer run;
- recompute all 40 hashes from entire regular-file bytes;
- fully read all 16 subjects and all 11 authority inputs;
- leave all subjects unchanged;
- run the five fixed commands;
- reproduce the R4 builder byte-for-byte;
- execute independent fully re-signed counterexamples, not merely inspect the
  fixture's declared adversarial rows;
- write only the requested independent review file.

The reviewer must not access:

```text
state-private/
secrets, credentials, tokens or cookies
private raw memory
provider raw responses
runtime configuration or real providers
```

No web, runtime source, secrets or private memory are required.

## 4. Effective Contract

```text
R4 explicit replacements
> R3 other explicit replacements
> R2 other explicit replacements
> R1 all other clauses
```

The 16 subjects are four files per revision:

```text
normative contract or amendment
deterministic fixture builder
fixed synthetic fixture
independent semantic validator
```

R1-R3 bytes must remain identical to their manifest hashes.

## 5. Three R3 Findings That R4 Must Close

### 5.1 Closed inventories, exact types and matrices

Independently verify:

```text
closed root inventory
closed section inventories
closed proof-row and nested-record inventories
exact effective schema field types
complete arm disposition cross-field matrix
complete receipt disposition cross-field matrix
semantic validation before fingerprint verification
```

At minimum, fully re-sign and attack:

- an unknown root field;
- an unknown section field;
- an unknown `adversarial_cases` row field;
- a profile that weakens a positive field to nonnegative;
- zero in each of the four positive time fields;
- `NEW + SOURCE_ATTESTATION_INVALID + reconciliation_opened=true`;
- `EXACT_DUPLICATE + REJECTED + SYNTHETIC_INPUT + no first refs`;
- extra reason codes outside each disposition error matrix.

### 5.2 Exact reverse precedence proof

Independently establish:

```text
expected unordered pair universe=147
trial count=294
rows per case=2
ordering labels={1,2}
raw row length=2
both reasons distinct and true
ordering 2=exact reverse(ordering 1)
true reason sets equal
derived reason_codes primary_reason and result equal
```

Copy ordering 1 into ordering 2, recompute the second reducer answer, fully
re-sign the section and root, and confirm rejection.

### 5.3 Canonical arm request and stored-first accounting

Independently establish:

```text
closed complete payload
strict duplicate-free JSON
recursive JSON value validity
exact canonical UTF-8 bytes
request_fingerprint=SHA256(exact canonical bytes)
attempt_ID formula from payload
request_ID formula from payload
stored and submitted request identity binding
relation derived from stored state and submitted bytes
no caller previous accounting fields
exact replay delta=0/0
exact replay totals=stored committed accounting
exact replay returned refs/fingerprints=stored first refs/fingerprints
```

Fully re-sign and attack noncanonical JSON bytes, wrong fingerprint, wrong
attempt ID, wrong request ID, different stored/submitted identity, caller-added
previous counts, nonzero replay deltas, changed totals and changed returned
first references.

## 6. Regression And Boundary Review

The reviewer must still independently check:

- all R1-R3 validator commands pass;
- all six coherent graph-level wrong-ID mutations reject;
- receipt compatibility cannot itself produce application;
- the transition universe remains exactly 10 x 10 = 100;
- the synthetic scenario creates no claim, arm, real handoff or call;
- no Actor/Task color, role, relationship, trust, urgency or P0-P3 authority
  classification is introduced;
- F5 does not recompute F1/F2/F3/F4 authority;
- synthetic evidence cannot become production authority;
- no real effect, provider, authentication or runtime behavior exists.

## 7. Fixed Commands

Run exactly from `/home/jenn/AGENTS_OS_Workspace`:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-f5-r1-synthetic-delivery-recovery.py

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-f5-r2-full-effective-delivery-recovery.py

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-f5-r3-seven-finding-closure.py

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-f5-r4-three-finding-proof-closure.py

tmp="$(mktemp)" && PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/build-f5-r4-three-finding-proof-closure.py --output "$tmp" && cmp -s "$tmp" control-plane/registry/examples/2026-07-17-agents-os-f5-r4-three-finding-proof-closure-v0.1.json && rm -f "$tmp"
```

Record exact exit codes and R4 counts. Validator `PASS_NO_BLOCKER` is evidence,
not a substitute for independent semantic review.

## 8. Expected Fixed R4 Counts

The reviewer must independently confirm or contradict:

```yaml
schema_profile_count: 16
schema_shape_example_count: 16
precedence_unordered_pair_count: 147
precedence_ordering_trial_count: 294
precedence_exact_reverse_pair_count: 147
arm_state_derivation_case_count: 4
arm_request_formula_case_count: 4
receipt_compatibility_case_count: 25
receipt_currentness_case_count: 10
transition_state_count: 10
transition_case_count: 100
adversarial_case_count: 20
schema_invalid_resigned_mutations_rejected: 17
closed_inventory_cross_field_mutations_rejected: 4
positive_type_mutations_rejected: 5
graph_level_identity_mutations_rejected: 6
proof_mutations_rejected: 7
arm_request_binding_mutations_rejected: 6
prior_R3_additional_probes_rejected: 7
```

Mandatory zero facts:

```yaml
accepted_real_handoff_count: 0
claim_event_count: 0
armed_dispatch_count: 0
runtime_consumable_count: 0
external_effect_count: 0
provider_call_count: 0
raw_secret_count: 0
terminal_outcome: NOT_EXECUTED
```

## 9. Output

Write only:

```text
control-plane/registry/reviews/2026-07-17-yellow-agents-os-f5-r4-full-atomic-independent-review.yaml
```

Use:

```yaml
schema_version: agents-os.hash-bound-independent-review.v0.1
review_unit: F5_OUTBOX_DELIVERY_RECOVERY_V0_1_R4_ATOMIC_BUNDLE
result: PASS_NO_BLOCKER | BLOCK

findings:
  blocker: 0
  major: 0
  minor: 0
  unresolved: 0

requires_R5: false
R5_truly_required: false
F5_acceptance_ready: false
F5_frozen: false
F6_started: false
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
provider_or_physical_effect_authorized: false
```

If any finding exists, include an ID, severity, fixed-byte evidence, executable
counterexample when applicable, narrow required correction and whether R5 is
truly required. Do not promote implementation-profile preferences into R5.

Even `PASS_NO_BLOCKER` does not accept or freeze F5. It only makes the fixed
R1-R4 bundle eligible for a separate Jenn atomic freeze decision.

## 10. Explicit Non-Authorization

This package authorizes none of:

```text
F5 acceptance or freeze
F6 start
R5 without a new reproducible security finding
implementation
Rust or JavaScript runtime work
database or provider transport
production authentication
runtime activation
real handoff or physical effect
commit, push, PR, merge, release, deploy, publish or tag
formal Memory or private raw-memory access
```
