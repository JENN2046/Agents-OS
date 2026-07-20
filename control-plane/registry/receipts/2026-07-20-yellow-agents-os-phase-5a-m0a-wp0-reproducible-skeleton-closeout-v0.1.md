# AGENTS OS Phase 5A M0-A WP0 Reproducible Skeleton Closeout v0.1

Date: 2026-07-20
Lane: Yellow bounded implementation batch
Result: PASS
Owner: Jenn
Agent steward: Nobao

## Scope

WP0 created the frozen 41-file external source package at
`extensions/agents-os-resident/`. It established only the deterministic layout,
exact toolchain and dependency locks, inert JavaScript boundary, blocked plugin
manifest, canonical package manifest and clean-worktree projection proof.

No WP1 canonical primitive was implemented. No database was created. No
VCPToolBox core file, existing dirty VCPToolBox worktree, active configuration,
runtime, provider, private Memory, sensing or real effect was used.

## Bound commits and digests

```yaml
implementation_branch: agent/phase-5a-m0a-wp0
start_closeout_commit: 9e6da0b82d90ff483acef11ed6ac31ddd5c61821
source_payload_commit: 313aebfe8f12f131bb5c661dd8926df23052491f
package_manifest_commit: c93e295461a8100debbfb4042d09bc05dc2d2ae0
source_root: extensions/agents-os-resident
planned_source_inventory: 41/41_MATCH
source_payload_files_at_source_commit: 40/40_BYTE_EQUAL
content_tree_sha256: a7a3145e4267064c02b3c80fd9f13b9f3eb3ba3dfaf48793dbcb89afe2124fe8
package_manifest_sha256: 4f95b1bd4056deaba15b38701f4dda7bd09f871a5b87ad050a2cfbf7a8f35327
blocked_plugin_manifest_sha256: 25a6084a0ecd2500e89075ed2ad502e791d95352b2638540b8c0aa1563ce8cc0
direct_entrypoint_sha256: 06517ae19cf58687eaf089ecc482e25bdc4333d7f0db784f699dd07bb5503774
Cargo_lock_sha256: 4c58cbdf47ecfec1e5ff0525d1b3e1026b7ad1037047d6170e89cf1aefb6545d
package_lock_sha256: 7f677892a70f9157b7e8b3ca35709cb79abdf3d2fbc91c538b35de0f1dfbfe55
```

`package-manifest.json` is excluded from the compared content trees and binds
the preceding 40-file source payload commit. This avoids a self-referential Git
commit digest while preserving exact byte ownership for every content-tree
leaf.

## Validation

```yaml
rustc: 1.96.1 (31fca3adb 2026-06-26)
cargo: 1.96.1 (356927216 2026-06-26)
node: v22.23.1
npm: 10.9.8
Cargo_lock_second_generation: BYTE_EQUAL
package_lock_second_generation: BYTE_EQUAL
exact_direct_dependency_versions: 11/11_MATCH
cargo_metadata_locked_offline: PASS
index_js_R6_fixture_byte_equality: PASS
blocked_manifest_canonical_exact_value: PASS
enabled_plugin_manifest_present: false
symlinks_or_non_regular_inventory_entries: 0
native_binary_count: 0
SQLite_database_count: 0
node_modules_present: false
target_directory_present: false
```

The source package was copied into a temporary clean linked VCPToolBox
worktree at commit `555b3b538f6eb736e530c2912de678c5941f9985` and then removed.

```yaml
linked_worktree_HEAD_match: true
git_status_before_materialization_empty: true
source_tree_sha256: a7a3145e4267064c02b3c80fd9f13b9f3eb3ba3dfaf48793dbcb89afe2124fe8
installed_tree_sha256: a7a3145e4267064c02b3c80fd9f13b9f3eb3ba3dfaf48793dbcb89afe2124fe8
source_install_files: 41/41_BYTE_EQUAL
tracked_VCPToolBox_core_diff: ZERO
tracked_VCPToolBox_index_diff: ZERO
overlay_status: 41/41_ALLOWED_UNTRACKED_ONLY
temporary_linked_worktree_removed: true
```

The first projection validator run failed closed because its diagnostic used
absolute paths instead of paths relative to the install root. No package or
VCPToolBox byte changed. The corrected relative-path comparison then passed the
complete projection validation above.

## Advancement

```yaml
WP0_status: PASS_COMPLETE
WP0_source_tree_hash_reproduces: true
WP0_install_tree_hash_reproduces: true
WP0_blocked_manifest_only: true
WP0_VCPToolBox_core_diff_zero: true
WP0_runtime_database_provider_or_real_effect_occurrence: 0
WP1_start_condition_satisfied: true
next_work_package: WP1_CANONICAL_PRIMITIVES
```

WP1 remains limited to strict JSON decoding, duplicate-key rejection, NFC,
safe integers, JCS bytes and SHA-256 against the frozen vectors. WP2 and later
packages remain blocked by their direct-predecessor gates.
