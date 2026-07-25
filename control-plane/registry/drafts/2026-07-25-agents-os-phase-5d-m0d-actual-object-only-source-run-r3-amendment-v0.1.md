# Phase 5D M0-D Actual Object-Only Source Run R3 Amendment v0.1

Date: 2026-07-25
Status: DRAFT_FOR_FRESH_FULL_ATOMIC_INDEPENDENT_REVIEW
Owner: Jenn
Agent steward: Nobao
Terminal outcome: NOT_EXECUTED

## 1. Exact purpose

R3 closes only the three `BLOCK` findings in the immutable R2 independent
review. It does not alter the protected-source boundary, tuple set, Git
inventory, output locations, or any authority boundary.

1. The inherited scanner source must be hash-verified from the fixed R3
   manifest before its Python bytes are compiled or executed.
2. A catchable signal received before terminal commit must produce a
   non-success result; a successful receipt must be written while catchable
   signals remain blocked and immediately followed by process exit without
   restoring their delivery.
3. Fixture mode must use one literal workspace fixture only, read from a
   regular, realpath-exact, `O_NOFOLLOW` descriptor. It accepts no path
   argument.

No VCPToolBox Git command, temporary run root, receipt, Host call, plugin,
runtime, database, provider, private Memory read, sensing, or effect is
authorized while creating or reviewing R3.

## 2. R2 immutable evidence

    R2_manifest_sha256: 6dd1839962de4c30a15e09a72c4ce6eff8d1a4874ae56cb9e90f06e68b0581fe
    R2_independent_review_sha256: ecf3688ae4b9e4693d3649c4a7f2e5fc56d476669a4bfe59e0952ef2d99378fe
    R2_result: BLOCK
    R2_requires_R3: true

R2 files and review bytes remain historical evidence. R3 replaces only its
new execution-harness successor; it does not edit R2 in place.

## 3. R3 execution corrections

### 3.1 Verify before scanner execution

The R3 runner has no top-level scanner import, `runpy`, or dynamic module load.
Before an actual-mode Git command, it verifies the closed R3 manifest record
inventory and all source SHA-256 values through no-follow regular descriptors.
It then compiles and executes the already verified inherited scanner byte
buffer in a non-`__main__` namespace. A substituted scanner with top-level
behavior must therefore fail digest verification before execution.

### 3.2 Signal-safe terminal commit

SIGINT, SIGTERM, and SIGHUP are blocked for the full actual-mode lifetime.
The runner checks the pending set before and after owned-root finalization.
Any pending catchable signal changes the outcome to
`BLOCKED_INTERRUPTED_OR_SIGNALLED`; no success receipt is written.

Only when no pending catchable signal exists may the runner write its
exclusive/no-follow sanitized success receipt. It then exits while those
signals remain blocked, without restoring their delivery. Failure paths may
restore the previous signal mask only after recording a non-success outcome.

### 3.3 Closed fixture input

`--fixture` is a boolean mode, not a path-taking argument. It reads only the
literal R3 fixture under `control-plane/registry/examples/` through the same
no-follow, regular-file and realpath checks used for manifest inputs. A
caller-supplied symlink, protected path, or arbitrary external fixture has no
CLI route.

## 4. Required R3 probes

The offline validator and a fresh reviewer must prove:

1. a scanner substitution whose top-level code would have a side effect is
   rejected before loader execution;
2. an inherited scanner byte buffer with the declared digest is the only
   scanner byte buffer that can be executed;
3. a queued SIGINT, SIGTERM, or SIGHUP before terminal commit downgrades the
   result and prevents success receipt creation;
4. a success terminal commit retains the signal mask until direct exit;
5. `--fixture` has no positional path argument and its literal fixture rejects
   symlink, non-regular and path-escape substitutions; and
6. no self-test or validator invokes actual mode, Git, VCPToolBox, Host,
   runtime, database, provider, private Memory, sensing, or effect code.

## 5. Stop rule

R3 stops at `PHASE_5D_M0D_ACTUAL_OBJECT_ONLY_SOURCE_RUN_DECISION_PACKAGE_R3_FRESH_FULL_ATOMIC_INDEPENDENT_REVIEW`.
It cannot accept, freeze, commit, push, or execute the source run.
