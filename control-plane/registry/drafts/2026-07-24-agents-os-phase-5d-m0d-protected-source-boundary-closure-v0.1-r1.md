# Phase 5D M0-D Protected Source Boundary Closure v0.1 R1

Date: 2026-07-24
Status: `DRAFT_FOR_FRESH_FULL_ATOMIC_INDEPENDENT_REVIEW`
Owner: Jenn
Agent steward: Nobao
Terminal outcome: `NOT_EXECUTED`

## 1. Purpose and exact scope

This narrow draft responds only to the consumed
`BLOCKED_PROTECTED_OR_UNREADABLE_SOURCE` materialization preflight. It defines
an **object-only source inspection candidate** that can verify selected sealed
Git objects without checking out or materializing the complete VCPToolBox tree.

It does not reopen the frozen adapter-binding or lifecycle contracts. It does
not authorize any VCPToolBox worktree, sparse checkout, `git archive`, plugin,
Host lifecycle, native/N-API, runtime, database, provider, authentication,
private Memory, sensing, recording, effect, Git delivery, or actual Host smoke.

## 2. Bound predecessor facts

```yaml
consumed_preflight_receipt:
  path: control-plane/registry/receipts/2026-07-24-yellow-agents-os-phase-5d-m0d-execution-admission-materialization-preflight-v0.1.md
  sha256: e13937d9f334d1ff114c2d77fbd73609aff09c2297c14764b3379489919ec3bd
  result: BLOCKED_PROTECTED_OR_UNREADABLE_SOURCE
prior_preflight_decision_package:
  path: control-plane/registry/reports/2026-07-24-agents-os-phase-5d-m0d-execution-admission-materialization-preflight-decision-package-v0.1.md
  sha256: 72a467b18b1f1a4f4ae859bac86d8dc248507bb0718827d53885e0128046f2b1
sealed_source_preflight:
  path: control-plane/registry/reports/2026-07-24-agents-os-phase-5d-m0d-host-smoke-source-preflight-v0.1.md
  sha256: 3a420c5ff995fc28839ba2340d69a23501bf9bd517d77ef552a9217cdfa14a3d
adapter_binding_freeze_decision:
  path: control-plane/registry/decisions/2026-07-24-agents-os-phase-5d-m0d-host-smoke-adapter-binding-r2-atomic-freeze-decision-v0.1.yaml
  sha256: ba24dd3a7e13d04fd23fc688f9a5a1d941d50daa352ac7cb6cbf6f26f36eb46c
sealed_Host:
  commit: 555b3b538f6eb736e530c2912de678c5941f9985
  tree: fd82d403e79f36f749eb7f555b4736eae3eacdff
```

The predecessor receipt records exactly seven protected `config.env` *names*.
Their bytes, blob OIDs, fingerprints, values and configuration semantics are
outside this draft's schema and may not be added later under the same revision.

## 3. Object-only inspection contract

### 3.1 Permitted source facts

An eventual separately authorized run may inspect only:

1. the sealed commit and tree identity;
2. tree-entry **names and modes only**, sufficient to prove that protected
   names are excluded from payload materialization; and
3. the following seven exact, non-protected blob tuples, addressed by their
   immutable blob OIDs rather than caller-selected paths.

| Path | Blob OID | SHA-256 |
|---|---|---|
| `AGENTS.md` | `28f22b4de495a63f14ede8fe72698278c877cb8d` | `24b2a4c3e45a98107a726c8dfd80b577846052d49068bb1c13479f872bf0374b` |
| `Plugin/AGENTS.md` | `c2d23c041033b1f7d46b9dc3bdb2ba738566c872` | `b060ad148827faa37877deb8b170399a0f00f46bc194797949005c9bb62572d4` |
| `docs/PLUGIN_ECOSYSTEM.md` | `81dc779453ccf2fb56c1f57d1ecde8ff3ffda506` | `f806b90c4f7d46bd2113f8b5af9f773adce49b454d615e7b6aa8445663490a65` |
| `rust-vexus-lite/AGENTS.md` | `0fad4dba9bcbaa2452a362910b01e6275e5c352e` | `e5e68ad817c4fc7da657ce0d9c131db666eff97888b772ac31b9661210c93494` |
| `rust-vexus-lite/Cargo.toml` | `3682f96f45c095f85e0f3c93bc2d6c1f21c98dde` | `01f6f29f824418c58dc1c0a5243df514bd6b2bd5cd6a68de850c13e465e6eea9` |
| `rust-vexus-lite/package.json` | `232a95ef206e6ffab0cdff959826faaa10f6fedb` | `c996185f59cc84208077f854077f2f5451368ea9cd05c775ba0b06028fed7f7c` |
| `Plugin.js` | `5fd77cea37c30ef432f23d9627d05aba862b9744` | `be15f76324b73400fe70052e6f07a0254b2a9c26393009ad1f026793fb36f5a2` |

The source reader is allowlisted by the complete `(path, blob_oid, sha256)`
tuple. It must reject a path substitution, a new tuple, an omitted tuple, an
OID-only alias, an unknown field, a protected-object identifier, or a request
to resolve a module dynamically.

### 3.2 Prohibited mechanisms

```yaml
forbidden:
  - git_worktree_add
  - git_checkout
  - git_sparse_checkout
  - git_archive
  - generic_tree_blob_enumeration
  - arbitrary_git_show_path
  - protected_blob_object_lookup
  - protected_path_content_read
  - Host_lifecycle_or_plugin_operation
```

`git sparse-checkout` is deliberately not treated as an implicit fix. It may
become a future proposal only if a separate contract freezes the exact sparse
universe, Git filter behavior, file-mode behavior, Host prerequisites and
post-cleanup evidence. This R1 draft grants none of those facts.

### 3.3 Result semantics

```yaml
object_only_inspection_pass: OBJECT_ONLY_PRECHECK_CANDIDATE
missing_or_changed_allowlist_tuple: BLOCKED_ALLOWLIST_TUPLE_MISMATCH
exact_expected_protected_name_inventory_with_zero_content_read: PROTECTED_PATHS_EXCLUDED
missing_renamed_or_additional_protected_name: BLOCKED_PROTECTED_PATH_INVENTORY_MISMATCH
any_protected_blob_identifier_or_content: BLOCKED_PROTECTED_SOURCE_BOUNDARY
checkout_worktree_archive_or_sparse_operation: BLOCKED_UNAUTHORIZED_MATERIALIZATION_METHOD
dynamic_or_environment_dependent_module_resolution: BLOCKED_HERMETIC_DEPENDENCY_INVENTORY_UNAVAILABLE
any_Host_or_runtime_operation: BLOCKED_OUT_OF_SCOPE_HOST_OPERATION
```

`OBJECT_ONLY_PRECHECK_CANDIDATE` is evidence only. It cannot create a Host
worktree, prove an executable Host dependency closure, authorize an enabled
manifest, or promote into actual Host smoke.

## 4. Synthetic-only constructive witness

The paired witness is synthetic and contains only the sealed public tuple data,
the protected path *names*, and no protected blobs or contents. Its validator
enforces an exact closed schema before accepting the candidate result. It is a
proof of the boundary rule, not a substitute for a later authorized Git-object
run.

## 5. Review scope

Fresh review must attack at least:

1. adding a protected object ID, hash or content-shaped field;
2. swapping or reordering an allowlisted tuple;
3. changing the sealed commit or tree;
4. adding `git_worktree_add`, `git_checkout`, `git_sparse_checkout` or
   `git_archive` to the operation sequence;
5. changing `Host_operation_count`, `runtime_usable` or execution authority;
6. accepting unknown keys, duplicate JSON keys, non-boolean booleans or
   mixed protected-path metadata.

## 6. Non-authority statement

```yaml
current_R1_status: DRAFT_ONLY
actual_Git_object_run_authorized: false
VCPToolBox_worktree_authorized: false
quarantine_root_authorized: false
actual_Host_smoke_execution_authorized: false
Host_operation_count: 0
```

Only a future Jenn decision made after fresh independent review may consume a
successor. Until then, the current v18.5 queue remains the governing stop.
