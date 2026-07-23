# Phase 5D M0-D Plan Post-Freeze Review-Package Builder Correction v0.1

Date: 2026-07-23
Owner: Jenn
Agent steward: Nobao
Status: FIXED_FOR_PR_REVIEW

## Purpose and non-semantic status

This is a narrow post-freeze delivery correction. It does not amend the
accepted Phase 5D M0-D Plan R1–R2 semantic bundle, its six accepted subjects,
its frozen manifest, its independent review, or its freeze decision.

The correction resolves two coupled delivery facts:

1. historical R1/R2 builders must remain at the exact hashes committed in the
   frozen manifests, so the accepted R2 package can be reproduced from its
   bound snapshot; and
2. future or re-signed manifests must not be able to make a review-package
   builder read protected workspace material and place it into an archive.

## Immutable historical sources

```yaml
historical_builders:
  r1:
    path: control-plane/registry/build-phase-5d-m0d-plan-r1-review-package.py
    sha256: de811d192f348af5aff68c631738b51e09cc33aa743d4fafa7dcf74ae6475074
  r2:
    path: control-plane/registry/build-phase-5d-m0d-plan-r2-review-package.py
    sha256: 105a4ee485750c7c4f64f7b872f97e4b5e3d9f03bcc9d191a2d0e2c3c56a361b
```

The successor verifies these exact bytes before it reads a manifest-declared
payload or creates an output archive. It never substitutes or rewrites either
historical source.

## Exact successor guard

For every row in `subjects`, `authority_inputs`, and `author_evidence`, the
successor validates the declared `path` before delegation:

```text
strict JSON string
→ relative POSIX workspace path
→ no absolute path, `..`, or backslash
→ no protected directory or sensitive filename
→ resolves inside the workspace
→ resolved path is not protected
→ regular, non-symlink file
→ historical builder may read and archive it
```

Protected path classes include `state-private`, `secret(s)`, `credentials`,
`tokens`, `cookies`, dotenv files except explicit example templates, known
credential filenames, and private-key container suffixes. The successor also
rejects a protected output target within the workspace.

For every rejected entry, the result is a stable `ValueError` before the
historical builder reads the declared payload and before an output ZIP exists.
`.env.example` and `config.env.example` remain allowed template names.

## Delegation and evidence boundary

The guarded successor has no Plan, Host, plugin, runtime, database, provider,
Memory, authentication, permission, identity, Task, Command, sensing, or
effect authority. It only preflights local review-package inputs, then delegates
a valid build to one hash-verified historical builder.

The offline fixture is synthetic. It creates only temporary local manifests and
ZIPs. A valid synthetic input must produce bytes exactly equal to the matching
historical builder. Protected probes create no archive and never read a protected
payload.

## Completion boundary

This correction is reviewable on PR #32. A passing correction does not re-freeze
Phase 5D, authorize a Host smoke run, or authorize Phase 5D implementation.
