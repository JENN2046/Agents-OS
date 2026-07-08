# ColaMeta PR #12 Retrospective: Installed-Only Runtime File Detection

Date: 2026-07-09
Source project: ColaMeta
Source PR: https://github.com/JENN2046/colameta/pull/12
Scope: Engineering review lesson extracted for AGENTS OS.

## What Happened

PR #12 fixed a packaged-runtime verification gap: the verifier compared the
expected checkout runtime file set against the installed package file set, but
did not reject package-installable runtime files that existed only in the
installed distribution.

The concrete risk was stale packaged code. A non-editable stable install could
still contain an old `runner/*.py` file that had been removed from
`expected_head`. If all remaining expected files matched, the runtime evidence
could incorrectly look current enough for readiness gates.

The fix made package verification bidirectional:

- expected checkout runtime files must exist in the installed package;
- compared expected files must hash-match;
- installed package runtime files must not contain installed-only entries;
- non-package operational files, such as standalone shell scripts, stay outside
  the package file set;
- installed-only runtime files now report
  `extra_installed_runtime_files`, `extra_installed_file_count`, and
  `extra_installed_files`;
- that state is reload-blocking and fail-closed.

## Why This Took So Long

The costly part was not the final patch. The costly part was discovering the
right invariant.

The original mental model treated packaged-runtime verification as
"all expected files match". For a safety gate, that is only one direction of the
proof. The real invariant is set equality over the installable runtime file set,
plus content equality, plus clean source evidence.

This PR chain also crossed several risk surfaces at once:

- runtime provenance;
- package metadata and package-data boundaries;
- healthz readiness evidence;
- production Beta Gate policy;
- remote preflight behavior;
- OAuth/public endpoint validation;
- redaction and bounded validation behavior.

Those surfaces make small implementation details security-relevant. A missing
negative case is not just a test gap; it can become a false-ready production
signal.

## The Better Review Frame

For gate-like code, review must start from invariants, not from implementation
shape.

Before accepting a readiness or provenance fallback, write the proof obligation
as a small table:

| Claim | Evidence Required | Rejection Cases |
| --- | --- | --- |
| Running package matches expected runtime | expected file set equals installed package runtime file set; every shared file hashes equal | missing expected file; extra installed runtime file; mismatch; unverified fingerprint |
| Source checkout is safe to trust | runtime source roots clean against expected Git HEAD | dirty roots; unavailable cleanliness evidence |
| Public endpoint is really public | canonical public URL and connected peer/DNS evidence match the validated target | rebinding; private/loopback/multicast; proxy path; split-horizon mismatch |
| External OAuth is external | canonicalized authorization server is public HTTPS and not self-reference | equivalent self-reference spelling; too many candidates; non-public address |
| Error output is safe | rejected values are redacted before printing | secret-like path or URL reaches stderr |

Then make the code and tests prove each row.

## Required Negative Matrix For Safety Gates

Every gate fallback should carry explicit negative tests for:

- missing expected artifact;
- extra supplied artifact;
- content mismatch;
- dirty trusted source;
- unavailable evidence;
- stale but superficially matching metadata;
- equivalent but differently spelled self-reference;
- non-public address classes, including multicast;
- resource exhaustion inputs, such as oversized candidate lists;
- proxy/environment interference when direct endpoint proof is required;
- redaction before any early return.

If a gate has a status field, the negative case should assert both behavior and
status. A status enum is part of the operator contract, not merely debug output.

## AGENTS OS Lesson

Builder context is biased toward finishing the intended fix. Reviewer context
must be colder.

For PRs that affect readiness, runtime provenance, public endpoint validation,
auth routing, package verification, or redaction, AGENTS OS should prefer this
review posture:

1. Re-state the invariant independently from the PR description.
2. Identify all fallback branches that can produce `ready`, `match`, or
   equivalent positive status.
3. For each fallback, ask what evidence is absent but still lets it pass.
4. Compare sets in both directions whenever the claim is equivalence.
5. Treat every normalization step as a possible time-of-check/time-of-use
   boundary.
6. Treat every status field as a public contract requiring negative-path tests.
7. Run a cold review after the author believes the PR is done.

This is not bureaucracy. It is how small edge cases stop becoming late-stage
security review findings.

## Reusable Rule

For any AGENTS OS gate:

```text
Do not ask "did the happy evidence match?"
Ask "is there any unproven state that can still make the gate report ready?"
```

For any equivalence claim:

```text
Prove A contains B, prove B contains A, then prove shared members match.
```

For any fallback:

```text
Fallbacks are not shortcuts. They are alternate proof paths with their own
explicit blockers, statuses, and regression tests.
```

## Outcome

PR #12 added the installed-only runtime file blocker, exposed the new status
fields, added regression coverage, updated operator documentation, pushed a
branch, opened a draft PR, and passed GitHub CI.

The larger value is the review discipline: future gate work should begin with
the proof matrix above before code is considered ready.
