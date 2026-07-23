# Phase 5D M0-D Plan Post-Freeze Review-Package Explicit-Input Correction v0.1

Date: 2026-07-24
Owner: Jenn
Agent steward: Nobao
Status: FIXED_FOR_PR_REVIEW

## Purpose and frozen boundary

This is a narrow additive delivery correction for PR #32. It does not modify
the accepted Phase 5D M0-D Plan R1–R2 bundle, its frozen manifest, independent
review, freeze decision, historical builders, or either prior post-freeze
correction.

The immutable R2 builder accepts optional positional manifest/report inputs.
When an arbitrary explicit path is absent, its historical resolver falls back
to workspace defaults. The frozen source remains evidence and is not altered.

## Exact successor behavior

The new R2-only successor verifies the already guarded successor before it
uses any input path. It preserves the historical command grammar, but not the
historical fallback behavior:

```text
OUTPUT_ZIP
OUTPUT_ZIP MANIFEST_PATH REPORT_PATH
```

It has three modes:

```text
no explicit manifest/report pair
  -> delegate through the prior guarded workspace successor

two existing direct explicit paths
  -> delegate through the prior guarded workspace successor

MANIFEST.yaml + REPORT.md from an extracted archive payload/ directory
  -> preflight every archive member, then delegate to the immutable R2 builder
```

The archive alias mode is exact. Both aliases must be present together; the
current working directory must be the direct `payload/` directory; the parent
must contain regular non-symlink `MANIFEST.yaml` and `REPORT.md`; every
manifest-declared member must be a safe, non-protected, regular file under
that `payload/` tree; and the output ZIP must be outside the extracted archive
root.

Every other malformed explicit-input form returns a stable `BLOCK` exit before
the immutable builder reads a manifest payload or writes an output ZIP:

```text
missing manifest
missing report
both missing
one archive alias paired with a non-alias
paired aliases outside payload/
```

In particular, the successor never treats a missing explicit path as a request
for the frozen workspace default. Defaults are available only in the
no-explicit-input form.

## Offline proof boundary

The synthetic validator uses a temporary directory only. It first confirms the
historical fallback exists, then proves the successor rejects the same missing
explicit paths through the same four-argument CLI form without output. It also
proves the no-explicit-input CLI form is the only mode that reproduces the
frozen default. It then builds an R2 archive, extracts it in a
temporary directory, and proves both direct explicit paths and the paired
archive-root aliases reproduce the historical bytes exactly.

No Plan semantics, Host, plugin, VCPToolBox, runtime, database, provider,
authentication, private Memory, sensing, or real effect is created or used.

## Completion boundary

This correction only closes the explicit-input review finding on PR #32. It
does not re-freeze Phase 5D, authorize a Host smoke run, authorize Phase 5D
implementation, or authorize a main merge.
