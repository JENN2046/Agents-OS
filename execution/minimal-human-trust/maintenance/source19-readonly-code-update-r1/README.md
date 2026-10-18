# Exact Source19 read-only code update

This independent entry updates the public-history reader, ENTRY_FREEZE and
capsule PIN from the admitted `620408…` capsule to the uninstalled `dd3df0…`
schema correction. It does not call the old install/APPLY/withdraw entry.
`support_admission.py` and `native_guard.py` are exact copies of the separately
reviewed R2 source (SHA-256 `6333b19b…` and `43f055a7…`). Only their filesystem,
source projection, kernel guard and original-installation readback are reused.
Their old mutating entry points are never invoked.

The original 30 local / 32 cloud protected objects and original installation
receipt must pass exact readback. Both the original lock and the new private
audit lock remain held during target effects. Twenty-nine cloud objects remain
bound to their complete original identity, including ctime. Only three objects
change; every stage, archive and publish has a durable intent and result.

New files are staged in the private audit namespace. Original files are
preserved with same-filesystem renameat2 NOREPLACE, then recorded new inodes
are published in reader, freeze, PIN order. This is not a three-file atomic
transaction. The protected loader refuses mixed bytes/freezes/PINs; read-only
preflight may temporarily refuse, and previously held read-only code may finish.
There is no process signal, service action, signing, configuration change,
Owner/Grant change, key access, business ledger IO or UNKNOWN processing.

The fixed audit namespace, stage/archive/reverted slots, restore-attempt
directories, modes, old lock reference, all helper source hashes, original
receipt hash and old/new target identities are in the new review/challenge.
Jenn must authenticate with fresh native sudo and type the complete current
`UPDATE_READONLY_CODE CLOUD|LOCAL <sha256>` line. A five-minute wall/monotonic
window starts only when that line is received; no old approval or deadline is
reused. No entry claims Human enrollment or physical caller localness.

## Ordinary validation and build

Run from the repository root, as an ordinary user:

```sh
python3 -I -B execution/minimal-human-trust/maintenance/source19-readonly-code-update-r1/test_code_update.py
python3 -I -B execution/minimal-human-trust/maintenance/source19-readonly-code-update-r1/test_launcher.py
```

`build_entry.py` seals the existing old and new code bundles plus the new entry
sources into one ordinary packet. It never contacts a host or changes a target.
The production output is fixed and must be absent; source packets cannot be
overwritten. `launch_code_update.py --verify` verifies all 74 source members
without network, sudo or source execution.

## Genuine native entry

The delivered launcher supports `--cloud` or `--local` with `review`, `update`,
`readback` or `restore`. Default/`--verify` are ordinary and offline. Host modes
first display the scope and wait for Enter before ordinary source staging and
native sudo authentication. Authentication/root phases inherit the real TTY;
passwords and confirmation lines are never captured or filled by the launcher.

Cloud update and separate new-entry readback precede local update. The old
readback entry remains a historical installation verifier and does not admit
the new three-object contents. A zero exit requires the corresponding exact
terminal receipt; it is never business acceptance or successful capability
preflight. That protected read-only capability run remains separate.

## Failure and restoration

After an unknown/partial result, do not rerun update. New namespace presence
also refuses a stale accepted update after acquiring the original lock.
`readback` creates no missing state, lock or receipt. A partial audit without
an intent is explicitly reported as partial.

`restore` requires a new native `RESTORE_READONLY_CODE` confirmation of the
current full observation. It can archive only a recorded new-stage inode and
restore the recorded original inode. Same-byte foreign inodes refuse. This
restores code only; it never starts or stops a service. All artifacts/history
remain. An interrupted restore requires readback and a separate new current
confirmation; it does not repeat an old uncertain syscall or extend an old
authority. Full confirmed identities remain bound during restoration; only
the identities returned by this attempt's own successful renames are updated.
Terminal receipts are guarded by the same complete identities and both clocks.

All tests use disposable ordinary-user files and explicit identity seams. They
do not establish genuine native, two-host installation or business acceptance.
This work does not establish daily Chat/R16 GUI coexistence or upgrade Chat.
