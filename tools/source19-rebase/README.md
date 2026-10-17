# Unsigned R17 rebase on the real source19 release

These ordinary-user tools build and inspect an isolated file package. They do
not enroll a Human, issue a signature, read credentials or business journals,
change the Owner or Grant, install files, call a service, or allocate a live
configuration revision. Existing R15 repair/R12/R17 archives remain unchanged.

Run from the repository root after the source19 admission changes and these
tools have been committed and the exact source HEAD is clean:

```sh
python3 -I -B tools/source19-rebase/build_unsigned.py \
  --repo /absolute/repository \
  --base /opt/r16/releases/r16-daily-20261015-r15-app-recovery-r6 \
  --source-public-json /absolute/delivery/SOURCE19_PUBLIC_CONFIG.json \
  --source-head FULL_CLEAN_COMMIT_SHA \
  --output /absolute/new-delivery/package --plan-only
```

Remove `--plan-only` to create the package once. Existing destinations are
refused; partial output is preserved. The plan-only path writes no output.
Save the JSON build receipt outside `package`. Pass its exact
`inventorySha256` and the independently reviewed source HEAD to the verifier:

```sh
python3 -I -B tools/source19-rebase/verify_unsigned.py \
  --package /absolute/new-delivery/package \
  --inventory-sha256 FULL_EXTERNAL_INVENTORY_SHA256 \
  --source-head FULL_CLEAN_COMMIT_SHA \
  --repo /absolute/repository \
  --base /opt/r16/releases/r16-daily-20261015-r15-app-recovery-r6
```

The verifier never imports the builder or runtime. Omitting both `--repo` and
`--base` verifies portable bytes against the external inventory pin, signed-role
content digests, exact role/local-file mappings, repair guards and metadata. It
does not freshly establish source checkout or installed-file provenance. The
full command independently rereads the base and the exact Git source bytes.
No command here establishes live business readiness.

The source public configuration must have canonical digest
`56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec`.
G1's separate real signature/current-delivery readback remains required; the
tools pin that public input and do not claim to perform Ed25519 verification.
The expected source19 delivery digest is
`b8645f6fe206e84dd07c2c6c166bfe4016d1deefca28bf9545dcfa1560f013e9`.
The public configuration alone does not prove the currently accepted delivery
revision. No revision20,21,22 or new execution window is authorized here.

App and Native source manifests come from the repaired release directory.
Bridge deliberately comes from the unchanged signed
`/opt/r16/releases/r16-daily-20261012-r15/bridge-manifest.json`; the repaired
directory does not contain a Bridge manifest. Every role payload byte is read
from the repaired directory and verified against the three signed role-version
digests. The complete base file/directory set is checked, but the existing
root-only `.maintenance-capsule.json` is not opened or changed.

All tracked files in the declared production components are overlaid from the
clean exact HEAD. Git index executable bits and base payload modes are retained
as integers420/493 (`0644`/`0755`). All candidate directories are `0755` and
metadata files `0644`, independent of the caller's umask. Symlinks, hardlinks,
special files, overlaps with different hashes, missing/extra files or
directories, and incomplete role/local-file binding sets are refused. Each
role is expanded to include the recursive literal relative imports of its
controlled JavaScript modules. The independent verifier reads delivered source
with its own token scanner and reconstructs the closure; self-consistent role
versions cannot conceal an omitted dependency. Existing signed upstream trees
are retained; this is not a claim to resolve arbitrary dynamic or bare imports.
The separate isolated runtime/dependency smoke check remains required.

The App runner must remain byte-identical to the installed shutdown repair.
The App admission/drain/physical-shutdown section and Native recovery-fence
section must retain the installed repair's exact bytes. This permits the
additional R17 business-stop code around those sections without reverting to
older App/Native code. Synthetic regression and package runtime smoke tests
remain required; byte preservation does not prove all runtime behavior.

`metadata` contains exactly:

| File | Schema / content |
| --- | --- |
| `UNSIGNED_CONTENT.json` | `r17.source19.unsigned-content.v1` |
| `ROLE_MANIFESTS.json` | `r17.source19.role-manifests.v1` |
| `LOCAL_FILE_BINDINGS.json` | `r17.source19.local-file-bindings.v1` |
| `PROVENANCE.json` | `r17.source19.provenance.v1` |
| `PAYLOAD_INVENTORY.json` | `r17.source19.payload-inventory.v1`; `sourceHead`, `files`, counts/bytes |
| `REVIEWED_SOURCE_FREEZE.json` | `mht.first-trust-code-freeze.v1`; current publisher's required list |
| `IDENTITY_ADMISSION_FREEZE.json` | `mht.identity-admission-code-freeze.v1`; exact identity helper/wrapper/unit/policy |
| `REPAIR_GUARDS.json` | `r17.source19.repair-preservation.v1` |
| `SOURCE_PUBLIC_CONFIG.json` | Exact supplied public JSON bytes |
| `SOURCE_ROLE_MANIFESTS.json` | Original App/Bridge/Native manifests |
| `app-manifest.json`, `bridge-manifest.json`, `native-manifest.json` | `r16.runtime-code.v1` |
| `SHA256SUMS_PAYLOAD.txt` | Exact sorted payload SHA-256 union |

The summary leaves release dates and the planned configuration revision null;
all signing/install/activation/Owner/UNKNOWN permissions are false. Counts and
new role versions are calculated from content; neither 16645 nor 16648 is reused
as a requirement. The target Release ID remains the separately reviewed R17
target `r16-daily-20261012-r17`, without issuing that Release.

Run the disposable-fixture regression:

```sh
python3 -I -B tools/source19-rebase/test_source19_rebase.py
```

Tests create temporary public source/base files and a temporary Git repository.
Synthetic public digests and role versions are injected only into test modules;
there is no runtime override flag, synthetic production approval or private-key
operation. Test imports execute neither packaged applications nor services.
