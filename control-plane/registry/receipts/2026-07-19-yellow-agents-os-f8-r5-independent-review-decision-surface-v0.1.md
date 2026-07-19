# AGENTS OS F8 R5 Independent Review Decision Surface Receipt v0.1

Date: 2026-07-19  
Lane: Yellow governance evidence batch  
Result: PASS  
Owner: Jenn  
Agent steward: Nobao

## Scope

Preserved the complete external F8 R5 independent review output byte-for-byte,
verified its checksums and projected `PASS_NO_BLOCKER` to a Jenn-only atomic
freeze decision surface. This receipt does not accept or freeze F8.

## Evidence

```text
manifest:
  control-plane/registry/reports/2026-07-19-agents-os-f8-r5-atomic-independent-review-package-v0.1.manifest.yaml
  SHA-256 c4161d9f4ffaaa094e2aebd9e5697cf40003e35691ca4e2a4de169ba4e83b672

review:
  control-plane/registry/reviews/2026-07-19-yellow-agents-os-f8-r5-nobao-independent-review.yaml
  SHA-256 713358f67cd763bf86d6a6d7f36e2ef3befc04f2ee73ee7667e1629ae271353f

attack results:
  control-plane/registry/reviews/f8_r5_independent_attack_results.json
  SHA-256 c306d7d7839f380ebc1d51b8495b006074d1c7206507368b010cd7e4fabcf25d

probe:
  control-plane/registry/reviews/f8_r5_independent_review_probe.py
  SHA-256 26002ca0e98ee6ae59e91de58d822c24550878a15f64ab8232b28aeda944ad4a

checksums:
  control-plane/registry/reviews/2026-07-19-f8-r5-independent-review-SHA256SUMS.txt
  SHA-256 7f49c7ec4d4b461b7067466467337e8a3f05666bff5e51ee9ce5f90707830124
```

Coverage was 73/73 bound inputs, 20/20 subjects, 49/49 authority inputs,
4/4 author evidence files, 14/14 fixed commands and 126 independent fully
re-signed attacks. Findings were zero blocker, zero major and zero minor, with
zero favorable invalid path and zero legal-input over-rejection.

## Governance projection

```yaml
F8_status: READY_FOR_JENN_R5_ATOMIC_FREEZE_DECISION
F8_R5_independent_review_result: PASS_NO_BLOCKER
requires_R6: false
F8_accepted: false
F8_frozen: false
Phase_5A_started: false
automatic_acceptance: forbidden
```

Created decision surface:

```text
control-plane/registry/reports/2026-07-19-agents-os-f8-r5-atomic-freeze-decision-package-v0.1.md
```

Reconciled current queue:

```text
control-plane/registry/reports/2026-07-19-agents-os-active-work-queue-v6.2.md
```

## Boundary

No F8 acceptance, freeze, R6, Phase 5A start, implementation, runtime,
database, provider, production authentication, private raw Memory access,
sensing, recording, real effect, commit, push, PR, merge, tag, release, deploy
or publish was performed or authorized.

