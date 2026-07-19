# AGENTS OS F8 R1 Atomic Independent Review Package v0.1

Date: 2026-07-19  
Owner: Jenn  
Review unit: `F8_HOME_TO_ORCHESTRATOR_MINIMUM_INTERFACE_V0_1_R1_ATOMIC_BUNDLE`  
Status: `FIXED_FOR_FRESH_FULL_ATOMIC_HASH_BOUND_INDEPENDENT_REVIEW`

## Canonical manifest

```text
control-plane/registry/reports/2026-07-19-agents-os-f8-r1-atomic-independent-review-package-v0.1.manifest.yaml
SHA-256: 920ea2bcbc65b9af41df8eb70ea42d1e20ef7cb4a74b58e2d06d5d984e17a482
```

```yaml
subjects: 4
authority_inputs: 21
author_evidence: 1
declared_total: 26
partial_review: forbidden
```

## Review request

Perform a fresh full atomic hash-bound independent review. Do not adopt the
author self-review as a conclusion. Read and hash all 26 declared inputs and run
every manifest command.

The central question is:

> Can any fully re-signed graph turn an F7 intent candidate into permission, a
> Task, a committed F3 Command, authentication, effect authority or a
> production-usable object without the exact current upstream owner evidence
> and F3's independent intake transaction?

Independently attack at least:

1. change the intent, target, payload or context and synchronously re-sign every
   F8 object while retaining the same assessment revision;
2. change an assessment's subject/context and fingerprint without advancing its
   immutable revision;
3. use a current-looking but wrong-revision assessment consumer;
4. remove, rename, reorder or replace mandatory H01-H25 cases and re-sign the
   entire graph;
5. retain `is_current_head=true` while moving an assessment Event watermark
   behind the trusted handoff observation sequence;
6. mark the prospective F3 requirement accepted or runtime usable;
7. turn `CURRENT_NO_MATCH` into sufficient permission;
8. omit a required Jenn decision or bind one to another target/context;
9. use relationship, trust, role, actor class, urgency or history to widen the
   handoff candidate;
10. forge `ACKNOWLEDGED_COMMITTED` without the exact current F3-owner assessment
   for the same handoff candidate;
11. move the synthetic fixture into a production namespace or set any real
    Task, Command, runtime, database, provider, sensing or effect occurrence.

Each probe must propagate dependent refs/fingerprints and re-sign rows,
sections and root. Confirm rejection comes from the target semantic or schema
rule, not stale hashes, missing propagation or an exception.

## Fixed author results

```yaml
validator: PASS
schema_profiles_verified: 10/10
upstream_assessments_verified: 25/25
handoff_cases_verified: 25/25
candidate_revisions_verified: 2/2
acknowledgement_cases_verified: 6/6
fully_resigned_mutations_rejected: 41/41
parser_probes_rejected: 3/3
builder_byte_reproduction: PASS
real_command_count: 0
provider_call_count: 0
external_effect_count: 0
terminal_outcome: NOT_EXECUTED
```

These are author claims, not independent conclusions.

## Critical boundary

F8 R1 forms only a nonauthoritative, runtime-unusable handoff candidate.

```text
CANDIDATE_FORMED
!= permission
!= authentication
!= F3 admission
!= committed Command
!= Task creation
!= effect admission
```

The prospective F3 interface requirement remains:

```yaml
owner: F3
status: UNACCEPTED_DOWNSTREAM_REQUIREMENT
usable_in_runtime: false
synthetic_fixture_only: true
```

F8 cannot accept an F3 Command type, mint an authentication assertion, create
an authenticated context, write an intake record or bypass F3 replay.

## Allowed result and governance

Allowed independent results are exactly `PASS_NO_BLOCKER` or `BLOCK`. Neither
result accepts or freezes F8. A later exact Jenn atomic decision is required.

```yaml
F8_started: true
F8_accepted: false
F8_frozen: false
Phase_5A_started: false
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
private_raw_memory_access_authorized: false
sensing_or_recording_authorized: false
provider_or_effect_execution_authorized: false
Git_delivery_authorized: false
```
