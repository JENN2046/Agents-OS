# AOOSR R2-R5 Failed-Route Historical Durability v0.1

```text
STATUS: BLOCKED
CLASSIFICATION: HISTORICAL_ONLY
AUTHORITY: NO_AUTHORITY
RUNTIME_USABLE: false
```

## Purpose

This bundle preserves the exact 40-file byte set needed to audit and reproduce
the failed Actual Object-Only Source Run (AOOSR) R2-R5 governance route. It
exists only to retain historical facts that are absent from, or superseded by,
the current mainline tree.

The bundle does not revive the route, validate its old PASS claims, authorize
an actual run, or make any archived runner, validator, fixture, decision, or
queue current.

## Isolation

- Every historical source is stored as a content-addressed `objects/*.blob`
  object with mode `0644`.
- Original paths and extensions exist only as metadata in `manifest.v0.1.json`.
- No archived Python file is present under an active execution or registry
  source path.
- The objects are marked non-text and non-diffable by the bundle-local
  `.gitattributes`.
- The existing mainline runner, validator, queue, registry, and
  `CURRENT_STATE.md` remain authoritative and unchanged.
- Restoring, importing, parsing as authority, or executing an object from this
  bundle is forbidden without a new, separately reviewed route and authority.

## Historical disposition

The preserved evidence records a consumed attempt that failed closed with
`BLOCKED_REVIEW_BINDING_MISMATCH`, zero Git commands, zero Host operations, no
created worktree, and a clean result.

Later independent reviews remained blocked:

- R4 identified a delayed scanner-thread/module-mapping race.
- R5 identified malformed disposition bytes, forbidden source-mutation
  acceptance, and receipt-provenance weakness.

The R4 disposition object with SHA-256
`1ec8cfea9f35f6bd9dda3a964bad9bfcc0b9782212014fd393be924683a49bb4`
contains malformed YAML/patch contamination. It is retained only as opaque
bytes. It must not be parsed, normalized, repaired in place, or treated as an
authoritative review disposition.

The failed AOOSR route was superseded by the separately governed MEHS route.
Nothing in this bundle transfers, recreates, or reuses any Gate 1, Host,
runtime, provider, merge, release, deploy, or publish authority.

## Provenance and disclosure

`Base` and `mainline` in this bundle mean only this hash-bound remote-tracking
ref observation:

```text
ref:    refs/remotes/origin/main
commit: 2ab3b0ff0d2d92e1fff21802e5c76f4d65c1a84f
tree:   bbad8469a397bfd56f4e5c03bb6f04622c7059da
```

It never means local `refs/heads/main`.

The source worktree had:

```text
HEAD: 310a7358f96b6749f0c31dd3e39517c9df87c50c
tree: 23ee143739e9a60fdade57c934f4f902d23aab94
```

That HEAD is context only. It does not bind the historical source bytes:

- all 55 candidate paths were absent from that source tree;
- all 55 candidate paths were `UNTRACKED` (`??`) in the source worktree;
- all 40 selected paths were therefore also `UNTRACKED`;
- `source_bytes_commit_bound` is explicitly `false`.

The delivered archive binds the 40 retained bytes without relying on an
intermediate branch ref or commit object. Audit the delivered `objects/`
subtree at Git OID `e0b38c332631aafb06632ee4d243703991a634e4`,
then require every manifest entry to match its declared path, mode, size, and
SHA-256. This archive makes no claim about which commit first durably bound the
bytes and asserts no provenance-successor relationship.

The candidate universe is deterministic:

1. Recursively enumerate regular, non-symlink files below
   `control-plane/registry` whose basename contains the case-sensitive literal
   `object-only-source-run`, excluding paths containing `__pycache__`
   (`53` paths).
2. Add the exact queue paths `v18.8` and `v18.9` listed in the manifest
   (`2` paths, no overlap).
3. Sort the resulting `55` repository-relative POSIX paths by ascending UTF-8
   byte order.
4. Select a path exactly when it is absent from the bound Base tree or its
   SHA-256 differs from the bytes at that Base path.

The closure is:

```text
55 candidates = 15 Base-identical exclusions
              + 37 Base-missing selections
              + 3 Base-different selections
```

The 40 selections are `$.objects`; the 15 exclusions are materialized in
`$.provenance.selection_closure.excluded_base_identical`. Their complete-set
digests and serialization are recorded in the manifest.

The opaque objects retain 67 historical `/home/jenn/` path-label occurrences
and zero `file://` URI occurrences. Those labels are historical scope evidence,
not runtime readiness or authority. This bundle is intended only for the
private repository.

## Integrity validation

Run these commands from this directory. They are read-only and do not execute
any archived object:

```bash
python3 -c 'import json; d=json.load(open("manifest.v0.1.json")); p=d["provenance"]; r=p["selection_closure"]["result"]; assert d["status"] == "BLOCKED" and d["labels"] == ["HISTORICAL_ONLY", "NO_AUTHORITY"] and d["inventory"]["object_count"] == len(d["objects"]) == 40 and p["main_base_ref"] == "refs/remotes/origin/main" and p["source_bytes_commit_bound"] is False and p["selected_source_status_at_capture"] == {"classification":"UNTRACKED","git_porcelain_v1_code":"??","count":40} and r == {"candidate_count":55,"base_identical_excluded_count":15,"missing_from_base_selected_count":37,"different_from_base_selected_count":3,"selected_count":40}'

python3 -c 'import json; d=json.load(open("manifest.v0.1.json")); print("\n".join(o["sha256"] + "  " + o["blob_path"] for o in d["objects"]))' |
  sha256sum --check --strict -

test "$(find objects -type f -perm /111 -print -quit)" = ""
test "$(find objects -maxdepth 1 -type f -name '*.blob' | wc -l)" -eq 40
```

The manifest is the path-to-object binding. The SHA-256 in each object filename
and manifest entry must match the exact object bytes.

## Retention

This bundle is a historical audit asset, not an active dependency. Retain it
until a later, explicit durability decision supersedes it. Do not delete it as
ordinary cleanup and do not copy its objects back to their original paths.
