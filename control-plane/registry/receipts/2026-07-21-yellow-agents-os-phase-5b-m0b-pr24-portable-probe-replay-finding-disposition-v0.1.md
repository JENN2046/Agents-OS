# Receipt: Phase 5B M0-B PR 24 Portable Probe Replay Finding Disposition v0.1

Date: 2026-07-21
Result: `PASS`
Owner: Jenn
Agent steward: Nobao
PR: `JENN2046/Agents-OS#24`
Reviewed head: `6bd58fdd0a8bb6032a5e29e5ccb849a5b0524c02`
Finding: `P2 Derive the probe root instead of hard-coding /tmp`
Review comment ID: `3622683054`

## Disposition

The finding is valid for direct replay of the copied original-session probe.
That source cannot be edited in place because its exact SHA-256 is bound by the
R5 independent review, PASS disposition and immutable plan freeze decision.

The original bytes remain unchanged:

```text
control-plane/registry/reviews/2026-07-21-agents-os-phase-5b-m0b-plan-r5-independent-probe.py
SHA-256 91688b7bdc0532929ad96b3519c50dd8ae66c91f59fbee584ac6cd1243a2180b
```

A separate portable replay helper now verifies that immutable hash, derives the
workspace root from its own `__file__`, substitutes only the original fixed
extraction-root assignment in memory, executes the captured probe and requires
its JSON output to equal the immutable case-results object.

```text
control-plane/registry/replay-phase-5b-m0b-plan-r5-independent-probe.py
SHA-256 1ff2d6d43b99d8850a5b508201a2ad96cc696c9f58588adcf1af311befd322cd
```

## Validation

```yaml
immutable_probe_sha256: MATCH
workspace_replay: PASS
arbitrary_gitless_extraction_replay: PASS
case_result_rows: 42/42_MATCH
case_results_semantic_equality: PASS
original_review_probe_or_case_bytes_modified: false
frozen_subject_bytes_modified: false
implementation_or_runtime_authority_changed: false
git_diff_check: PASS
```

## Boundary

The helper is a deterministic offline evidence-replay adapter. It is not an
accepted plan subject, does not replace the original review evidence, and does
not authorize implementation, runtime, VCPToolBox, database, provider, private
Memory, sensing or any real effect.
