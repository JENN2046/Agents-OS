# AGENTS OS F4 R1 Atomic Independent Review Package v0.1

Date: 2026-07-16  
Status: `READY_FOR_FRESH_HASH_BOUND_INDEPENDENT_REVIEW`  
Owner: Jenn  
Agent steward: Nobao  
Scope: fixed three-subject F4 R1 atomic contract unit

## 1. Review unit

```yaml
review_unit_id: F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R1_ATOMIC_BUNDLE
subject_count: 3
partial_review: forbidden
review_mode: fresh_full_atomic_independent_review
author_self_review_is_independent: false
F4_accepted: false
F4_frozen: false
implementation_authorized: false
runtime_activation_authorized: false
```

The exact subjects are:

```text
1. normative contract
   path: control-plane/registry/drafts/2026-07-16-agents-os-f4-taskpermit-host-authentication-effect-admission-v0.1-r1.draft.md
   sha256: 3378396108f090469984facb8ddcb238ae122be9cab71afe2f8c3bd1cd577db3

2. constructive M0-A fixture
   path: control-plane/registry/examples/2026-07-16-agents-os-f4-taskpermit-host-authentication-effect-admission-m0a-witness-v0.1.json
   sha256: e13f501ebf5d120778a9971f9d5884764b8635a557dc2fa387f3adfb0873fd75

3. deterministic offline validator
   path: control-plane/registry/validate-f4-m0a-witness.py
   sha256: a39b860c627124c0c0304a5bca51bda6fa806d0f7c778078706e60c9235e89aa
```

## 2. Canonical manifest

```text
path: control-plane/registry/reports/2026-07-16-agents-os-f4-r1-atomic-independent-review-package-v0.1.manifest.yaml
sha256: 29b695a5c882ae5571040ac0c5514cbaa4f40f96e7cd84639faf6f66c4c2ae54
```

The manifest is the canonical hash-bound pointer bundle. It binds all three
subjects, F1/F2/F3 frozen prerequisites, architecture inputs, the immutable F4
start decision, author-review lineage, required questions, exact validator
expectations, reviewer constraints, and output contract. This presentation
report is excluded from the manifest to avoid a digest cycle.

## 3. Independence rule

The R1 author and author self-review cannot supply the independent result. The
reviewer must:

```text
state a concrete independence basis
start from the manifest and recompute every listed digest
review all three fixed subjects without substitution
run the exact offline validator
derive findings from the fixed bytes, not from the author conclusion
return BLOCK on any hash mismatch, missing input, partial review or validator mismatch
```

The author self-review records the construction lineage and seven corrected
author findings. It is not evidence that the independent questions pass.

## 4. Required semantic surfaces

### Authority and identity

Verify exact preservation of current F1 Task/commitment/dependency authority,
F2 Actor/Principal/Authentication/Responsibility/Delegation/action authority,
and F3 Resident/Command/continuity/writer authority. A prompt, process,
session, callback, hostname, UI, IPC or network origin must not substitute for
any bound fact.

### Permit and Host boundary

Verify immutable TaskPermit identity, previous-plus-one execution epoch,
current Task/Host/effect fences, exact Host identity revision, authentication
challenge/epoch/revocation state, capability/resource bounds, secret-handle
revision/ownership/revocation state, permit attestation, human presence, Jenn
authorization, time and invocation bounds.

### Admission and writer boundary

Verify that the 18-check local decision is advisory only; the Rust canonical
writer re-runs all authority in one transaction before accepting one exact
invocation. Verify that final Host recheck, successful start disposition and
accepted-effect handoff are one serializable transaction and cannot open a
revocation race or second-writer path.

### Revocation, replay and outcome

Verify monotonic non-resurrectable fences, terminal Host compromise,
fail-closed incomplete revocation propagation, exact replay identities,
lookup-first unknown-commit recovery, and the separation between acceptance,
handoff, physical start and F5 outcome. Silence/crash must not prove
`NOT_EXECUTED`; `UNKNOWN_AFTER_CRASH` must not authorize automatic retry.

### F3/F5 and phase separation

Verify that F4 consumes an upstream accepted `EFFECT_INTENT` Command definition
without creating a same-subject owner-digest cycle. F4 must not silently start
F5/F6 or authorize Rust, N-API, database, crypto/key custody, Resident,
runtime, production authentication, provider, Host or service execution.

## 5. Constructive witness

Run exactly:

```bash
python3 control-plane/registry/validate-f4-m0a-witness.py
```

The fixed expected result is:

```yaml
result: PASS
node_count: 14
edge_count: 36
node_hashes_verified: 14
schema_fingerprints_verified: 22
acceptance_count: 1
accepted_handoff_count: 1
external_effect_count: 0
provider_call_count: 0
raw_secret_count: 0
terminal_outcome: NOT_EXECUTED
```

The validator must run offline. A real Host, credential, provider, service,
database, runtime, private Memory, network request or external effect is not
required and must not be introduced.

## 6. Required adversarial review

Review every one of the 49 numbered adversarial decisions and all 64 normative
invariants in the contract. At minimum attempt to construct:

```text
Task, Actor, Resident or Host identity substitution
stale/revoked/compromised Host authentication accepted from an old epoch
scope expansion through capability, resource, secret handle or payload mismatch
P3b issuance or RED admission without exact current Jenn authorization
required human presence inferred from UI/session/prompt evidence
permit or handoff accepted with stale attestation, time, epoch or fence
advisory local decision used directly as start authority
two writers or two Hosts committing one invocation
revocation between successful disposition and handoff
unknown commit observation causing a blind second attempt
acceptance or handoff treated as proof of physical success/non-execution
F5 result widening F4 authority or producing automatic retry from UNKNOWN
production Command registry self-hash cycle through the F4 subject
synthetic fixture smuggling a real effect, secret, provider or production fact
```

## 7. Required result format

The result must conform to `agents-os.hash-bound-independent-review.v0.1`:

```yaml
reviewer:
  identity:
  independence_basis:

manifest:
  path: control-plane/registry/reports/2026-07-16-agents-os-f4-r1-atomic-independent-review-package-v0.1.manifest.yaml
  sha256: 29b695a5c882ae5571040ac0c5514cbaa4f40f96e7cd84639faf6f66c4c2ae54
  all_input_hashes_verified: true | false

subjects:
  all_three_bytes_reviewed_unchanged: true | false
  subject_hashes_verified: 3 | exact_count

validator:
  command: python3 control-plane/registry/validate-f4-m0a-witness.py
  exact_expected_result_observed: true | false

result: PASS_NO_BLOCKER | BLOCK
summary:
  blocker_count:
  major_count:
  minor_count:
  requires_R2: true | false

mandatory_counts:
  identity_spoofing:
  authority_expansion:
  host_authentication_bypass:
  revocation_or_compromise_bypass:
  fail_open_currentness:
  dual_writer:
  circular_proof:
  crash_or_replay_ambiguity:
  downstream_boundary_leak:
  M0_impossibility:
  internal_contradiction:
  adversarial_decisions_passed:
  normative_invariants_passed:

findings:
  - id:
    severity: BLOCKER | MAJOR | MINOR
    section:
    evidence:
    required_correction:
```

`PASS_NO_BLOCKER` is valid only when every manifest question is answered, all
three subject hashes and every authority-input hash match, validator output is
exact, all 49 adversarial decisions and 64 invariants pass, and no blocker
remains.

## 8. Post-review routing

```text
BLOCK
  -> author finding disposition
  -> R2 only for exact evidence-bound corrections
  -> new complete three-subject hash-bound review

PASS_NO_BLOCKER
  -> fixed independent result registration
  -> Jenn-only atomic accept/freeze decision surface
```

Neither result automatically accepts F4, starts F5/F6, or authorizes
implementation, database, Resident, runtime, production authentication,
provider, Host, service, commit, push, PR, merge, release or deployment.

## 9. Reproduction

Parse the manifest and recompute each listed `path` digest over the entire
regular file with no canonicalization. The manifest's own digest is external.
Any mismatch invalidates the package until a new manifest is fixed.
