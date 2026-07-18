# AGENTS OS F6 R1 Atomic Independent Review Package v0.1

Date: 2026-07-17  
Status: `READY_FOR_FRESH_FULL_ATOMIC_HASH_BOUND_INDEPENDENT_REVIEW`  
Owner: Jenn  
Agent steward: Nobao

## 1. Review instruction

Review the exact four-subject unit bound by:

```text
control-plane/registry/reports/2026-07-17-agents-os-f6-r1-atomic-independent-review-package-v0.1.manifest.yaml
sha256 65b73b15dd0ad98c3263a8aa4932dbb13468ae6468de8213c44f3473e77f5e11
```

Return only `PASS_NO_BLOCKER` or `BLOCK` under
`agents-os.hash-bound-independent-review.v0.1`. Partial review and partial
acceptance are forbidden. The author cannot act as the independent reviewer.

The reviewer must hash all 22 declared inputs, read all four subjects and all
17 authority inputs completely, and form fresh judgment before consulting the
author self-review.

## 2. Atomic subjects

```text
normative contract
  control-plane/registry/drafts/2026-07-17-agents-os-f6-validation-requirement-current-decision-v0.1-r1.draft.md
  sha256 2b388a3ae37a0b8bfd265c8a6856d73abdcfd5fd5bf48b25a240c263416fd332

deterministic fixture builder
  control-plane/registry/build-f6-r1-validation-current-decision.py
  sha256 bed7131c45e2d5fad7999d76c9ed5b96f1bf19e97e8081135691e7fa9ef054af

fixed synthetic fixture
  control-plane/registry/examples/2026-07-17-agents-os-f6-r1-validation-current-decision-v0.1.json
  sha256 de45548ad8836c337bd5c978c37da116306734fe50dde4d0361b365679713f5e

independent offline semantic validator
  control-plane/registry/validate-f6-r1-validation-current-decision.py
  sha256 1401e7ef5a586a6be903472a058fc2f50ac10fa4e5af92d6b992d8899279ae10
```

## 3. What F6 R1 owns

R1 closes only:

```text
ValidationRequirement identity, revision, provenance and closed semantics
immutable Validation Set membership and complete provenance-source binding
append-only Validation attempt identity and revision chains
exact evidence currentness, freshness, carry-forward and F5 evidence binding
Jenn-bound Requirement waiver currentness
deterministic current Requirement and Validation Set decisions
fail-closed Task completion eligibility at one F3 current-read barrier
required atomic COMPLETION_ASSESSMENT + DONE seam
```

F6 consumes F1 Task/candidate/dependency assessments, the F3 canonical read
barrier and F5 delivery currentness. It does not reconstruct any upstream
reducer or create Task, Actor, Command, effect, delivery or identity authority.

The F5 completion-blocking `CLEAR | BLOCKED` consumer assessment is explicitly
an `UNACCEPTED_OWNER_INTERFACE_REQUIREMENT`, synthetic-only and nonruntime in
R1. A real positive eligibility decision remains non-issuable until that
separate owner/implementation profile is accepted.

Any role/color/relationship/trust/urgency permission classification, F1/F3/F5
reimplementation, `Run SUCCEEDED`, delivery `ACK`/`APPLIED_CURRENT`, PBL
no-match or synthetic evidence used as automatic Validation `PASSED` or Task
`DONE` is a blocker.

## 4. Highest-risk review questions

### Evidence, attempt and currentness

- Does every terminal attempt bind the exact evidence subject ref and
  fingerprint, rather than a caller-supplied label?
- Can an older favorable `PASSED` mask the unique head of a newer attempt?
- Are future, expired, stale, indeterminate or cross-result evidence facts
  fail-closed?
- Does carry-forward resolve to one earlier original `FRESH_VALIDATION +
  PASSED` chain head, with its equivalence tuple independently recomputed?

### Requirement set and waiver

- Is every current Requirement present once, revision/fingerprint-bound, and
  represented in the exact source-provenance union?
- Can a nonwaivable Requirement, a current failed attempt or a stale Jenn
  waiver decision be hidden by a valid-looking snapshot hash?
- Can an all-waived or empty required set become completion-satisfying? It
  must not.

### Completion seam

- Does `ELIGIBLE` require one unchanged F3 barrier, Task `VERIFYING`, current
  candidate, satisfied Validation Set, confirmed dependency closure, zero
  nonterminal work/control intent/unresolved effect and F5 `CLEAR`?
- Can a projection, fixture or stale eligibility output commit `DONE`? It must
  not; a future implementation must recheck and atomically commit the
  completion snapshot, Event and Current State.

### Boundary integrity

- Is F5 evidence only necessary for a Requirement that explicitly asks for it
  and still insufficient to create `PASSED`?
- Does any Actor/Task label or permission lane affect a result?
- Can the synthetic positive `ELIGIBLE` witness be imported, recovered or
  treated as runtime authority?

## 5. Reproduction

```bash
PYTHONDONTWRITEBYTECODE=1 python3 \
  control-plane/registry/validate-f6-r1-validation-current-decision.py

tmp="$(mktemp)"
PYTHONDONTWRITEBYTECODE=1 python3 \
  control-plane/registry/build-f6-r1-validation-current-decision.py \
  --output "$tmp" >/dev/null
cmp -s "$tmp" \
  control-plane/registry/examples/2026-07-17-agents-os-f6-r1-validation-current-decision-v0.1.json
rm -f "$tmp"
```

Expected validator surface:

```yaml
result: PASS_NO_BLOCKER
normative_schema_count: 10
decision_vector_count: 54
requirement_case_count: 22
validation_set_case_count: 10
completion_case_count: 22
precedence_raw_trial_count: 342
negative_mutations_rejected: 32
graph_requirement_count: 4
graph_validation_set_count: 2
graph_attempt_revision_count: 6
graph_waiver_event_count: 1
fixture_canonical_sha256: 014c3154bd8d2f75f45b845901c6665211dce16a6580c8e7a4755692f335ccff
derived_eligible_case_count: 1
task_done_mutation_count: 0
accepted_real_task_count: 0
runtime_consumable_count: 0
external_effect_count: 0
provider_call_count: 0
raw_secret_count: 0
terminal_outcome: NOT_EXECUTED
```

Validator PASS is necessary but insufficient. The reviewer must independently
read the contract, compare builder and validator logic, attack the graph and
confirm that every fully re-signed mutation executes without exception and is
rejected for a semantic, schema or identifier-formula reason.

## 6. Required output

Write the fresh result to:

```text
control-plane/registry/reviews/2026-07-17-yellow-agents-os-f6-r1-full-atomic-independent-review.yaml
```

At minimum report:

```text
reviewer identity and independence basis
manifest path and SHA-256
22/22 hash result
4/4 complete subject and 17/17 authority-input read result
blocker/major/minor/unresolved counts
each required question and adversarial result
10 schema, 54 vector, 342 precedence-trial and 32 mutation counts
builder byte equality and fixture canonical hash
all zero-authority/runtime/effect/provider/secret counts
requires_R2
```

Any hash mismatch, unavailable authority input, partial read, upstream reducer
reimplementation, evidence substitution, attempt/waiver branch ambiguity,
carry-forward chain, all-waived completion, stale eligibility reuse, synthetic
authority conversion or unresolved semantic ambiguity requires `BLOCK`.

## 7. Non-authorization

This package confirms only that F6 has started and R1 author bytes are fixed
for review. It does not accept or freeze F6, start F7, authorize implementation,
create or migrate a database, mutate a real Task/Run/Validation/Event/waiver,
start Resident/Worker/Host/validator/service/provider, enable production
authentication, execute or reconcile an effect, or authorize Git delivery,
release, deploy, publish or tag.
