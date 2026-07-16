# AGENTS OS F4 R2 Atomic Independent Review Package v0.1

Date: 2026-07-16  
Status: `READY_FOR_FRESH_HASH_BOUND_INDEPENDENT_REVIEW`  
Owner: Jenn  
Agent steward: Nobao  
Scope: fixed F4 R1+R2 six-subject atomic contract bundle

## 1. Review unit

```yaml
review_unit_id: F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R2_ATOMIC_BUNDLE
subject_count: 6
precedence:
  - R2_explicit_replacements
  - R1_all_other_clauses
partial_review: forbidden
review_mode: fresh_full_atomic_hash_bound_independent_review
author_self_review_is_independent: false
F4_accepted: false
F4_frozen: false
F5_started: false
F6_started: false
implementation_authorized: false
runtime_activation_authorized: false
```

The exact subjects are:

```text
R1 normative contract
path: control-plane/registry/drafts/2026-07-16-agents-os-f4-taskpermit-host-authentication-effect-admission-v0.1-r1.draft.md
sha256: 3378396108f090469984facb8ddcb238ae122be9cab71afe2f8c3bd1cd577db3
lines: 1451

R1 constructive M0-A fixture
path: control-plane/registry/examples/2026-07-16-agents-os-f4-taskpermit-host-authentication-effect-admission-m0a-witness-v0.1.json
sha256: e13f501ebf5d120778a9971f9d5884764b8635a557dc2fa387f3adfb0873fd75
lines: 1036

R1 deterministic M0-A validator
path: control-plane/registry/validate-f4-m0a-witness.py
sha256: a39b860c627124c0c0304a5bca51bda6fa806d0f7c778078706e60c9235e89aa
lines: 875

R2 normative amendment
path: control-plane/registry/drafts/2026-07-16-agents-os-f4-taskpermit-host-authentication-effect-admission-v0.1-r2-amendment.draft.md
sha256: 30cdbf0acb348d4c0c933f95bdcf51c7f3a6326ad678d8fca1f19faf4c85f705
lines: 401

R2 result/reason totality vectors
path: control-plane/registry/examples/2026-07-16-agents-os-f4-r2-result-reason-totality-vectors-v0.1.json
sha256: 048dfdb4856db9324d7e71c55525d447747849ff4dc87d04a5cdf093bfb261ad
lines: 175

R2 deterministic totality validator
path: control-plane/registry/validate-f4-r2-result-reason-totality.py
sha256: 519ce90b04e0084bcc23e4682f6032518f7051d43267bff44d4ca06e60a08941
lines: 285
```

All three R1 subjects remain fixed. R2 must never be reviewed alone.

## 2. Canonical manifest

```text
path: control-plane/registry/reports/2026-07-16-agents-os-f4-r2-atomic-independent-review-package-v0.1.manifest.yaml
sha256: cea14fa96266a0dcac86d9cdea97b533385b802825985d46a9d5c7eba9084b24
```

The manifest is the canonical review authority. It binds 24 complete regular
files: six subjects, thirteen governing inputs, and five review/amendment
lineage records. This presentation is excluded to avoid a digest cycle and may
not substitute for the fixed bytes.

## 3. Why R2 exists

The fresh R1 review returned:

```yaml
result: BLOCK
blocker_count: 1
major_count: 0
minor_count: 0
requires_R2: true
finding: F4-R1-FULL-ATOMIC-IR-B01
```

The blocker found that a mixed tuple such as:

```text
task_binding_current = REJECTED
policy_current = INDETERMINATE
```

could be classified as both `REJECTED` and `INDETERMINATE`, while multiple
simultaneous failures had no unique reason and five permit checks lacked an
explicit reason. Since result and reason enter the canonical fingerprint, the
same evidence could yield different immutable bytes.

R2 accepts the finding completely and changes no unrelated F4 surface.

## 4. Exact R2 correction

### Total result lattice

For Host authentication, TaskPermit currentness, and Host-local admission:

```text
any applicable REJECTED
  -> REJECTED and dominates every concurrent INDETERMINATE

else any applicable INDETERMINATE
  -> INDETERMINATE with the reducer's unique unavailable reason

else all applicable PASS or permitted NOT_APPLICABLE
  -> AUTHENTICATED / VALID / ADMITTED
```

Unknown fields, enum values, or invalid `NOT_APPLICABLE` reject before a
canonical result is emitted.

### Unique reason selection

Each reducer has one exact rejected-reason precedence. The first present
candidate is the only canonical reason. Host authentication classifies all 13
R1 reasons. TaskPermit currentness maps all 19 checks plus lifecycle, time, and
integrity. Host-local admission maps all 18 checks.

R2 adds these previously missing permit reasons:

```text
CAPABILITY_STALE
RESOURCE_STALE
SECRET_HANDLE_STALE
ATTESTATION_STALE
HUMAN_PRESENCE_STALE
```

Known stale evidence is a proven negative. It cannot become
`INDETERMINATE`. Reproducibly incompatible same-watermark facts are
`REJECTED / INTEGRITY_FAILURE`; unavailable evidence is `INDETERMINATE` only
when no proven negative exists.

### Corrected invariants

`I19-R2` applies only when there is no proven negative. `I20-R2` says a proven
negative dominates every concurrent indeterminate observation and fixes the
reason by precedence. All other R1 invariants remain unchanged.

## 5. Required validator reproduction

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-f4-m0a-witness.py
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-f4-r2-result-reason-totality.py
```

The fixed R1 validator must return PASS with:

```text
14 nodes
36 edges
14 node hashes
22 schema fingerprints
1 acceptance
1 accepted handoff
0 external effects
0 provider calls
0 raw secrets
NOT_EXECUTED
```

The fixed R2 validator must return PASS with:

```text
5 Host cases
12 TaskPermit-currentness cases
6 Host-local-admission cases
23 total cases
3 negative expected-result/reason mutations rejected
0 external effects
0 provider calls
0 raw secrets
```

Inspect both validators rather than trusting their outputs alone. Confirm that
the R2 vector reducer matches the normative precedence and that every case's
expected result/reason is recomputed rather than merely counted.

## 6. Fresh-review rule

The reviewer must:

```text
start from the canonical manifest
recompute the manifest and all 24 input digests over entire-file bytes
read all six subjects completely
apply only R2 explicit replacements over R1
form a fresh semantic judgment before using the R1 review as lineage
not read or rely upon the author self-review content or conclusion
run and inspect both offline validators
enumerate all 13 Host reasons, 19 currentness checks, and 18 admission checks
construct mixed REJECTED+INDETERMINATE and multiple-REJECTED tuples
return BLOCK on mismatch, unavailable input, partial review, or ambiguity
```

The old R1 review proves finding lineage only. It cannot substitute for fresh
review of the effective R1+R2 contract.

## 7. Required semantic surfaces

### Totality and determinism

For each reducer, prove that every schema-valid normalized tuple yields exactly
one result and one reason. Check candidate completeness, fixed priority, tie
collapse, invalid positive-plus-negative evidence, impossible time states, and
unavailable evidence with and without a concurrent negative.

### Authority and identity

Recheck exact bindings to accepted F1 Task and commitment facts, frozen F2
Actor/Principal/authentication/responsibility facts, frozen F3
Resident/Command/writer facts, and exact Host identity/authentication epochs.
Model, prompt, session, UI, process, hostname, network location, or advisory
JavaScript output must not substitute for canonical identity or authority.

### Fences, revocation, and compromise

Known stale Task/Host/effect fences and execution epochs must reject.
Revocation and compromise must remain terminal, advance the relevant fences,
and prevent old authentication or permits from becoming current. An
unavailable input must never mask a separately proven stale or revoked fact.

### Replay, crash, and writer boundary

The derived result and reason remain fingerprinted. Identical evidence must
yield identical bytes; changed result/reason must conflict. Advisory admission
must not become a second writer. Lost reply and unknown-after-crash paths must
remain lookup-first and cannot authorize blind retry or physical-effect claims.

### Constructibility and downstream boundaries

Reproduce the zero-effect M0-A DAG and ensure the R2 amendment does not create
a proof cycle or invalidate its unchanged positive path. F5 still owns Outbox,
delivery, retry, reconciliation, and effect outcome. F6 still owns Validation
current decisions and Task completion eligibility. Implementation and
production profiles remain separate.

## 8. Required coverage

The manifest requires:

```yaml
required_questions: 24
required_adversarial_checks: 23
effective_adversarial_decisions: 59
effective_normative_invariants: 64
Host_reason_values: 13
TaskPermit_currentness_checks: 19
Host_local_admission_checks: 18
```

Every item needs an explicit result and evidence. Each finding needs an ID,
severity, exact section evidence, concrete counterexample, impact, and minimum
correction.

## 9. Required result

Write exactly:

```text
control-plane/registry/reviews/
2026-07-16-yellow-agents-os-f4-r2-full-atomic-independent-review.yaml
```

The result must conform to
`agents-os.hash-bound-independent-review.v0.1` and report:

```yaml
result: PASS_NO_BLOCKER | BLOCK
summary:
  blocker_count:
  major_count:
  minor_count:
  requires_R3: true | false

mandatory_counts:
  identity_spoofing_count:
  authority_expansion_count:
  host_authentication_bypass_count:
  revocation_or_compromise_bypass_count:
  fail_open_currentness_count:
  dual_writer_count:
  circular_proof_count:
  crash_or_replay_ambiguity_count:
  downstream_boundary_leak_count:
  M0_impossibility_count:
  internal_contradiction_count:
```

`PASS_NO_BLOCKER` is valid only when all 24 hashes and all six subject reads
complete, both validators reproduce, 24/24 questions and 23/23 adversarial
checks pass, 59/59 adversarial decisions and 64/64 effective invariants pass,
all reason/check mappings are total, and no blocker, major, or unresolved
contract ambiguity remains.

## 10. Post-review routing

```text
BLOCK
  -> preserve R1/R2 and review bytes
  -> disposition exact findings
  -> R3 only if evidence requires it
  -> new fresh full atomic hash-bound review

PASS_NO_BLOCKER
  -> register the fixed result
  -> prepare a Jenn-only atomic accept/freeze decision surface
```

Neither route automatically accepts or freezes F4, starts F5/F6, or authorizes
implementation, runtime, database, authentication, credential, provider, Host,
service, effect, commit, push, PR, merge, release, deploy, publish, or tag work.

## 11. Reproduction

Parse the manifest and recompute every listed path over entire regular-file
bytes with no canonicalization. The manifest self-digest is external. Any
mismatch invalidates the package until a new package is deliberately created.
