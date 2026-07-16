# AGENTS OS F3 R1 Independent Review Package v0.1

Date: 2026-07-16
Status: `READY_FOR_FRESH_HASH_BOUND_INDEPENDENT_REVIEW`
Owner: Jenn
Agent steward: Nobao
Scope: fixed F3 R1 atomic contract subject

## 1. Review unit

```yaml
review_unit_id: F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R1
subject_count: 1
partial_review: forbidden
review_mode: fresh_full_atomic_independent_review
author_self_review_is_independent: false
F3_accepted: false
F3_frozen: false
implementation_authorized: false
runtime_activation_authorized: false
```

The sole review subject is:

```text
path: control-plane/registry/drafts/2026-07-16-agents-os-f3-resident-singleton-napi-identity-continuity-v0.1-r1.draft.md
sha256: e439b3178984ac28ae584a961e2e0dc2248002592f0fb571e5e0db05d117a70e
lines: 1050
```

## 2. Canonical manifest

```text
path: control-plane/registry/reports/2026-07-16-agents-os-f3-r1-independent-review-package-v0.1.manifest.yaml
sha256: 40b07f20be1bd3d25dee62cf2a54dd6a0d8d9246b6d7774f98632ed27c35a2a6
```

The manifest is the canonical hash-bound pointer bundle. It binds the R1
subject, governing authority inputs, accepted F2 predecessor surface, author
review lineage, required questions, reviewer constraints, and output contract.
This presentation report is deliberately excluded from the manifest to avoid a
digest cycle.

## 3. Independence rule

The R1 author and author self-review cannot supply the independent result. A
reviewer must:

```text
state a concrete independence basis
start from the manifest and recompute every listed digest
review the complete fixed R1 bytes
derive findings from source clauses, not from the author's conclusion
return BLOCK on any hash mismatch, missing input, or partial review
```

The author self-review is preserved as lineage and may help identify the
intended proof surface. It is not evidence that the independent questions pass.

## 4. Required review surfaces

### Resident identity and singleton authority

Verify that a process, model, session, prompt, database row, PID, stale marker,
or epoch row cannot independently claim the logical Resident identity or live
writer authority. Verify that Jenn-only identity decisions, the process lock,
canonical epoch, and READY projection form a total fail-closed boundary.

### Writer and N-API boundary

Verify that exactly one Rust ledger thread and one authoritative connection are
constructible without a second writer or query pool. Verify that the five
accepted N-API method names are closed and that F5-owned methods remain
non-operational.

### Command proof DAG

Verify the complete ordering:

```text
CommandTypeDefinition
-> CanonicalCommand
-> F2 AuthenticationAssertion / Assessment
-> AuthenticatedCommandContext
-> CommandEnvelope
-> AuthenticatedActorActionRef or DelegationActivationAcknowledgementRef
-> domain facts and Event
```

No field may depend on its own fingerprint or on a descendant object. Caller
claims may not substitute for Rust-derived committed facts.

### Currentness, replay, and races

Verify deterministic behavior for revocation-before-commit,
commit-before-revocation, duplicate command IDs, changed bytes, crash before
commit, commit with lost response, restart at a higher epoch, and corrupted
replay/envelope/action indexes.

### F2 and downstream separation

Verify exact preservation of the frozen F2 action-ref and delegation activation
replay formulas, the Temporary Worker ACTIVE gate, and exact
`WORKER_ASSIGNMENT_HANDSHAKE` mode binding. Verify that F3 does not silently
define F4 TaskPermit/host/fence, F5 delivery, F6 Validation decision,
implementation, production authentication, runtime, provider, database, or
service authority.

### Constructive M0 witness

Verify that the synthetic witness can be constructed using only the frozen F2
synthetic surface, one synthetic Resident identity, one writer, deterministic
ledger-only activation, replay, crash/restart, and dual-start denial—with no
real credential, host, provider, service, private Memory, or runtime activation.

## 5. Required adversarial checks

At minimum, try to construct these counterexamples:

```text
two live writers each satisfying a different half of the singleton proof
stale or rolled-back epoch accepted after restart
model/session continuity accepted without canonical identity evidence
identity DISCONTINUITY or INDETERMINATE reaching READY
JavaScript/direct SQL or a read pool becoming a second authority path
unknown N-API method or schema escalating into a reducer call
caller-supplied authenticated context, envelope, Event sequence, or action ref
authentication assertion / Command fingerprint circularity
same command_id with changed payload overwriting the original replay entry
lost response causing a second mutation
revocation and Command using different currentness watermarks
pending Delegation used as its own activation responsibility source
Temporary Worker using Actor ACTIVE without exact responsibility ACTIVE
WORKER_ASSIGNMENT_HANDSHAKE accepted without the exact payload mode
F3 envelope treated as TaskPermit or host effect admission
reserved Outbox/reconcile method performing a partial operation
recovery silently repairing a fork or corrupt historical fact
synthetic M0 witness depending on real secrets, provider, host, or runtime
```

## 6. Required result format

The review result must conform to
`agents-os.hash-bound-independent-review.v0.1` and include:

```yaml
reviewer:
  identity:
  independence_basis:

manifest:
  path: control-plane/registry/reports/2026-07-16-agents-os-f3-r1-independent-review-package-v0.1.manifest.yaml
  sha256: 40b07f20be1bd3d25dee62cf2a54dd6a0d8d9246b6d7774f98632ed27c35a2a6
  all_input_hashes_verified: true | false

subject:
  path: control-plane/registry/drafts/2026-07-16-agents-os-f3-resident-singleton-napi-identity-continuity-v0.1-r1.draft.md
  sha256: e439b3178984ac28ae584a961e2e0dc2248002592f0fb571e5e0db05d117a70e
  bytes_reviewed_unchanged: true | false

result: PASS_NO_BLOCKER | BLOCK
summary:
  blocker_count:
  major_count:
  minor_count:
  requires_R2: true | false

mandatory_counts:
  identity_spoofing:
  dual_writer:
  circular_proof:
  authority_expansion:
  fail_open_currentness:
  replay_ambiguity:
  downstream_boundary_leak:
  M0_impossibility:
  internal_contradiction:

findings:
  - id:
    severity: BLOCKER | MAJOR | MINOR
    section:
    evidence:
    required_correction:
```

`PASS_NO_BLOCKER` is valid only when every manifest question is answered and no
blocker remains. A reviewer must not convert an unreviewed or unclear surface
into a zero count.

## 7. Post-review routing

```text
BLOCK
  -> author finding disposition
  -> R2 only when required
  -> new complete hash-bound independent review

PASS_NO_BLOCKER
  -> fixed review result registration
  -> Jenn-only atomic accept/freeze decision surface
```

Neither outcome automatically accepts F3, starts F4, or authorizes
implementation/runtime/database/authentication/provider/service work.

## 8. Reproduction

The reviewer must parse the manifest and recompute each `path` digest over the
entire regular file with no canonicalization. The manifest's own digest is
external. Any mismatch invalidates the package until a new manifest is created.
