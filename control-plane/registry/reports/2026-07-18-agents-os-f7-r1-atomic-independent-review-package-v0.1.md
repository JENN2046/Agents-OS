# AGENTS OS F7 R1 Atomic Independent Review Package v0.1

Date: 2026-07-18  
Owner: Jenn  
Review unit: `F7_HOME_DOMAIN_MINIMUM_SEMANTICS_V0_1_R1_ATOMIC_BUNDLE`  
Status: `FIXED_FOR_FRESH_FULL_ATOMIC_HASH_BOUND_INDEPENDENT_REVIEW`

## 1. Canonical manifest

```text
path:
control-plane/registry/reports/2026-07-18-agents-os-f7-r1-atomic-independent-review-package-v0.1.manifest.yaml

SHA-256:
c86b8c17b93aa5e800bdf17e641666984c52cfc2e1006a90a38ad7dc61658c5c
```

The manifest binds 36 regular files:

```yaml
subjects: 4
authority_inputs: 31
author_evidence: 1
declared_total: 36
partial_review: forbidden
```

The Markdown report is presentation only and is deliberately excluded from the
manifest to avoid a digest cycle.

## 2. Review request

Perform a fresh full atomic hash-bound independent review. Do not adopt the
author self-review result. Read and hash every declared input, execute all fixed
commands, then independently attack the semantic graph with fully coordinated
and fully re-signed mutations.

Allowed final results are exactly:

```text
PASS_NO_BLOCKER
BLOCK
```

The independent result does not itself accept or freeze F7. Only Jenn may make
the later atomic decision.

## 3. Fixed commands

Run from `/home/jenn/AGENTS_OS_Workspace`:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-f7-r1-home-domain-minimum-semantics.py

tmp="$(mktemp)" && \
PYTHONDONTWRITEBYTECODE=1 python3 \
  control-plane/registry/build-f7-r1-home-domain-minimum-semantics.py \
  --output "$tmp" >/dev/null && \
cmp -s "$tmp" \
  control-plane/registry/examples/2026-07-18-agents-os-f7-r1-home-domain-minimum-semantics-v0.1.json && \
rm -f "$tmp"

git diff --check
```

Expected author-side validator summary:

```yaml
result: PASS
authority_profile_count: 20
decision_case_count: 20
candidate_revision_count: 2
gap_disposition_count: 7
adversarial_mutations_rejected: 31
real_occurrence_count: 0
terminal_outcome: NOT_EXECUTED
fixture_root_fingerprint: 2a5dc56a38de8636a31887a4bc3a954844ed42413a505068d5d2fdd4cf435b54
```

These are author claims, not independent conclusions.

## 4. Required semantic attacks

The reviewer must determine whether F7 remains only a logical bounded context:

1. No class, writer status, reducer result or projection creates a second
   permission, identity, Task, Command or ledger authority.
2. Relationship, trust, closeness, urgency, history and sentiment cannot expand
   upstream authority.
3. `IDENTITY_NARRATIVE` cannot rewrite F2 stable identity, and subjective
   relationship memory cannot establish another party's formal relationship.
4. Session or thought cannot become a canonical Task; Life Stream and Memory
   candidates cannot become formal Memory; Intent cannot become F3 Command.
5. Presence policy, consent, sensing state, recording and Memory remain separate;
   no sensing, recording, retention or device action is authorized.
6. All favorable results are derived from raw current inputs rather than a
   caller-supplied classification or expected answer.
7. The effective result can only narrow to a candidate and always carries
   `action_authority=false`.
8. Candidate revision lineage is contiguous and exact. A fully re-signed changed
   source, payload or context cannot reuse a fixed revision.
9. All 20 semantic classes have exactly one normative authority profile; unknown
   classes and writer statuses fail closed.
10. HD-M0-01 through HD-M0-07 are resolved or explicitly deferred without
    claiming an implementation, runtime, sensing path, Memory bridge or F8 seam.
11. Synthetic references cannot be accepted by a real or runtime profile.
12. Unknown fields, duplicate keys, floats, unsafe integers, bool-as-int,
    non-NFC strings and cross-field contradictions reject before semantic trust.

The reviewer should add independent coordinated mutations beyond the 31 author
cases, especially whole-graph re-signing after changing authority profiles,
candidate lineage, relationship scope or presence facts.

## 5. Evidence boundary

The fixture contains only synthetic commitments under:

```text
environment=SYNTHETIC_TEST
domain_tag=F7_R1_SYNTHETIC_NONAUTHORITY
runtime_usable=false
```

It contains no raw conversation, private Memory, real identity, real
relationship, sensor output, credential, provider response, database write,
Task mutation, Command mutation or external effect.

Do not add or request secrets, credentials, tokens, cookies, production config,
raw provider responses, `state-private/` content or private raw Memory for this
review.

## 6. Governance boundary

```yaml
F7_accepted: false
F7_frozen: false
F8_started: false
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
sensing_or_recording_authorized: false
private_raw_memory_access_authorized: false
Git_delivery_authorized: false
```

A `PASS_NO_BLOCKER` permits only preparation of a Jenn-owned atomic freeze
decision surface. A `BLOCK` requires an evidence-bound narrow amendment. Neither
result starts F8 or implementation.

