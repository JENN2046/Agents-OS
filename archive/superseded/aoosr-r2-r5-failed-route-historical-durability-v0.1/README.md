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

The source set was reconciled against:

```text
main commit: 2ab3b0ff0d2d92e1fff21802e5c76f4d65c1a84f
main tree:   bbad8469a397bfd56f4e5c03bb6f04622c7059da
```

It contains 37 objects absent from that tree and three superseded historical
versions of files that now have different, hardened mainline bytes.

The opaque objects retain 67 historical `/home/jenn/` path-label occurrences
and zero `file://` URI occurrences. Those labels are historical scope evidence,
not runtime readiness or authority. This bundle is intended only for the
private repository.

## Integrity validation

Run these commands from this directory. They are read-only and do not execute
any archived object:

```bash
python3 -c 'import json; d=json.load(open("manifest.v0.1.json")); assert d["status"] == "BLOCKED" and d["labels"] == ["HISTORICAL_ONLY", "NO_AUTHORITY"] and d["inventory"]["object_count"] == len(d["objects"]) == 40'

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
