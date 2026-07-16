# AGENTS OS F4 R3 Atomic Independent Review Package v0.1

Date: 2026-07-16  
Status: `READY_FOR_FRESH_HASH_BOUND_INDEPENDENT_REVIEW`  
Owner: Jenn  
Agent steward: Nobao

## Review unit

```yaml
id: F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R3_ATOMIC_BUNDLE
subject_count: 9
precedence: [R3_explicit_replacements, R2_other_explicit_replacements, R1_all_other_clauses]
partial_review: forbidden
F4_accepted: false
F4_frozen: false
F5_started: false
implementation_authorized: false
```

The nine subjects are the fixed R1 contract/M0-A fixture/validator, fixed R2
totality amendment/vectors/validator, and new R3
PRESTART+start-disposition amendment/vectors/validator. Their paths and exact
entire-file hashes are canonical in the manifest.

## Canonical manifest

```text
path: control-plane/registry/reports/2026-07-16-agents-os-f4-r3-atomic-independent-review-package-v0.1.manifest.yaml
sha256: de004a2263258bbc8335039e3a312d8a10a88f80473546f315b418c38fca2ba5
bound_inputs: 31
subjects: 9
required_questions: 26
required_adversarial_checks: 26
```

This presentation is excluded from the manifest to avoid a digest cycle.

## Why R3 exists

R2 independent review returned `BLOCK`, two blockers, no major/minor:

```text
F4-R2-FULL-ATOMIC-IR-B01
  in-window Host lifecycle PRESTART had no canonical rejected reason

F4-R2-FULL-ATOMIC-IR-B02
  HostWorkStartDispositionFactV0_1 remained outside the total reducer;
  three negative rechecks had no reasons and mixed/multiple failure had no precedence
```

R3 accepts both findings without changing any earlier subject or review byte.

## Exact corrections

### PRESTART

The Host reason enum adds `PRESTART`. Current canonical lifecycle PRESTART is
always `REJECTED / PRESTART`, independent of the time window, and dominates
concurrent unavailable evidence. The effective Host rejected order is:

```text
INTEGRITY_FAILURE > COMPROMISED > REVOKED > RETIRED > SUSPENDED > PRESTART
> PROFILE_MISMATCH > CHALLENGE_MISMATCH > EXPIRED > NOT_YET_VALID
```

### Host-work start disposition

The effective reducer normalizes 12 rechecks: integrity, acceptance, expiry,
Host identity, Host authentication, three fences, execution epoch, secret
handles, permit attestation, and human presence.

```text
any REJECTED
  -> NOT_STARTED and the first fixed rejected reason
else any INDETERMINATE
  -> INDETERMINATE / OBSERVATION_UNAVAILABLE
else all PASS or permitted NOT_APPLICABLE
  -> START_AUTHORITY_CURRENT / ALL_RECHECKS_PASS
```

The rejected reason order is:

```text
INTEGRITY_FAILURE > ACCEPTANCE_MISSING > HOST_UNAUTHENTICATED > FENCED
> EPOCH_STALE > EXPIRED > SECRET_HANDLE_STALE > ATTESTATION_STALE
> HUMAN_PRESENCE_STALE
```

Result and reason remain fingerprinted. One observation identity plus exact
evidence yields one first fact; changed bytes conflict. Successful disposition
and handoff remain one serializable transaction and prove no physical effect.

## Required validator reproduction

```bash
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-f4-m0a-witness.py
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-f4-r2-result-reason-totality.py
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-f4-r3-prestart-start-disposition-totality.py
```

Expected fixed results:

```text
R1: PASS, 14 nodes, 36 edges, 22 fingerprints, 1 acceptance, 1 handoff,
    0 effects/providers/secrets, NOT_EXECUTED
R2: PASS, 23 cases (5 Host, 12 permit, 6 admission), 3 mutations rejected,
    0 effects/providers/secrets
R3: PASS, 13 cases (3 Host, 10 start disposition), 3 mutations rejected,
    0 effects/providers/secrets
```

Inspect all validators; output alone is insufficient.

## Fresh-review rules

The reviewer must start from the canonical manifest, recompute 31/31 hashes,
read all nine subjects completely, and form fresh R1+R2+R3 judgment. Prior
reviews are lineage only. The author self-review may be hashed but its content
or conclusion must not be read. The presentation must not be used as authority.

Verify all 14 Host reasons and lifecycle predicates, all 19 permit checks, all
18 admission checks, all 12 start-disposition observations, `I19-R2` and
`I20-R3`, 69/69 adversarial decisions, and 64/64 effective invariants. Recheck
identity, authority, Host revocation/compromise, monotonic fences, one writer,
replay/crash, proof DAG, M0-A, and F5/F6 boundaries.

## Required result

Write exactly:

```text
control-plane/registry/reviews/2026-07-16-yellow-agents-os-f4-r3-full-atomic-independent-review.yaml
```

Result must be `PASS_NO_BLOCKER | BLOCK` under
`agents-os.hash-bound-independent-review.v0.1`. Report 31/31 hashes, nine
unchanged subject reads, all three exact validator outputs, 26 question
results, 26 adversarial results, mapping counts, 69/69, 64/64, finding counts,
mandatory risk counts, and `requires_R4`.

`PASS_NO_BLOCKER` requires every gate above and zero blocker, major, or
unresolved ambiguity.

## Routing and boundaries

```text
BLOCK -> preserve bytes -> exact disposition -> R4 only if required -> fresh review
PASS_NO_BLOCKER -> prepare Jenn-only atomic accept/freeze decision surface
```

Neither route accepts/freezes F4 automatically, starts F5/F6, or authorizes
implementation, runtime, database, Resident, authentication, credential,
provider, Host executor, service, effect, public API, MCP, commit, push, PR,
merge, release, deploy, publish, or tag work.
