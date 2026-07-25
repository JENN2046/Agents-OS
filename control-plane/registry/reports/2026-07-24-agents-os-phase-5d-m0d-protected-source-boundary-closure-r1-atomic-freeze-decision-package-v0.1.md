# Phase 5D M0-D Protected Source Boundary Closure R1 Atomic Freeze Decision Package v0.1

Date: 2026-07-24
Owner: Jenn
Agent steward: Nobao
Status: `READY_FOR_JENN_ATOMIC_FREEZE_DECISION`
Terminal outcome: `NOT_EXECUTED`

## 1. Decision purpose

This package asks only whether to accept and freeze the R1 **object-only
protected-source boundary contract**. It does not authorize an actual Git
object run, a VCPToolBox worktree, a checkout, sparse checkout, archive,
quarantine root, payload materialization, Host lifecycle, runtime or effect.

## 2. Atomic acceptance unit

```yaml
review_unit: PHASE_5D_M0D_PROTECTED_SOURCE_BOUNDARY_CLOSURE_V0_1_R1_ATOMIC_BUNDLE
atomic: true
partial_acceptance: forbidden
subjects:
  contract:
    path: control-plane/registry/drafts/2026-07-24-agents-os-phase-5d-m0d-protected-source-boundary-closure-v0.1-r1.md
    sha256: 0b7c58e2df9d939ab7f86acb573f3dfc92d4fa57e70b17e28c6303989e26f6f3
  fixture:
    path: control-plane/registry/examples/2026-07-24-agents-os-phase-5d-m0d-protected-source-boundary-closure-r1-synthetic-witness-v0.1.json
    sha256: 3f7512223d6c5c594c5f1064eb4aaf136f4214858571fefac6f3eb11e7835a49
  builder:
    path: control-plane/registry/build-phase-5d-m0d-protected-source-boundary-closure-r1-witness.py
    sha256: 40628339fb46931e2245f9e6df3f528e5d105136b704a888b40b432067d02d1f
  validator:
    path: control-plane/registry/validate-phase-5d-m0d-protected-source-boundary-closure-r1.py
    sha256: bc698fc465eb8a99bcb10fb776987de8f277d93451f0df91644a674ee5b153aa
manifest:
  path: control-plane/registry/reports/2026-07-24-agents-os-phase-5d-m0d-protected-source-boundary-closure-r1-atomic-independent-review-package-v0.1.manifest.yaml
  sha256: b26584bcbc93219a382d23e4ccd1a9b09650c0fca6920604bc4b06a493ca4b45
independent_review:
  path: control-plane/registry/reviews/2026-07-24-yellow-agents-os-phase-5d-m0d-protected-source-boundary-closure-r1-full-atomic-independent-review.yaml
  sha256: 61e4443e540d413d9e49bfeec114827f3b1feb9eddbb95962543200286e2443c
  result: PASS_NO_BLOCKER
review_disposition:
  path: control-plane/registry/reviews/2026-07-24-agents-os-phase-5d-m0d-protected-source-boundary-closure-r1-independent-review-disposition-v0.1.yaml
  sha256: 334d0ecb9c9c29fd838ae0a96d3bb6e2b28fb4bf0ae8eafcec929fcbf254d87b
```

## 3. What freeze means

Freezing R1 fixes only these boundaries:

1. protected tracked paths may be represented by their names only, never their
   bytes, blob OIDs, content hashes or configuration semantics;
2. only the complete seven-tuple sealed non-protected blob allowlist may be
   an object-only input;
3. no checkout-like mechanism may be reintroduced implicitly; and
4. the witness remains synthetic and cannot become Git, Host, runtime or effect
   authority.

## 4. What freeze does not mean

```yaml
actual_Git_object_run_authorized: false
VCPToolBox_worktree_authorized: false
git_checkout_or_sparse_checkout_authorized: false
quarantine_root_or_payload_materialization_authorized: false
actual_Host_smoke_execution_authorized: false
Host_operation_count: 0
runtime_database_provider_private_Memory_or_effect_authorized: false
Git_delivery_authorized: false
```

A future actual object-only source run still requires a separate, current
Jenn execution decision that binds its exact commands, root ownership, output
scope, cleanup and observation receipt. A future Host execution requires an
additional independently reviewed contract; it cannot be inferred from R1.

## 5. Preconditions

```yaml
review_hash_matches: required
manifest_inputs: 9/9_MATCH
fixed_commands: 4/4_PASS
independent_semantic_attacks: 36/36_REJECTED
protected_content_bytes_read: 0
Host_operation_count: 0
```

## 6. Jenn decision surface

### A. Accept and freeze R1 boundary closure

Exact decision text:

```text
我确认执行 Phase 5D M0-D Protected Source Boundary Closure R1 Atomic Freeze
Decision Package v0.1 第 6 节 A 的完整 Exact decision text。

我接受并冻结 PHASE_5D_M0D_PROTECTED_SOURCE_BOUNDARY_CLOSURE_V0_1_R1_ATOMIC_BUNDLE，
精确绑定 manifest SHA-256
b26584bcbc93219a382d23e4ccd1a9b09650c0fca6920604bc4b06a493ca4b45，
以及独立审查 SHA-256
61e4443e540d413d9e49bfeec114827f3b1feb9eddbb95962543200286e2443c。

本冻结只固定 object-only protected-source boundary；不授权实际 Git object run、
VCPToolBox worktree、checkout、sparse checkout、archive、quarantine root、payload
materialization、Host lifecycle、PluginManager、runtime、database、provider、authentication、
private Memory、sensing、recording 或任何真实 effect。

冻结后停止 R1 修订。任何未来实际 source run 或 Host-smoke 均须以新的、独立的 Jenn
decision 为前提；本决定不授权 commit、push、PR、merge、release、deploy、publish、tag
或后续阶段启动。
```

### B. Do not freeze

Retain the current R1 review evidence and v18.5 stop state. No source or Host
operation may occur.
