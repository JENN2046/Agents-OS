R9 engineering build and readback

This is a new ordinary stopped-source transaction. It consumes the completed,
independent expired-ABORT compensation as historical evidence; it does not call
or renew the old R8 driver or manufacture its missing canonical receipt.

Run the portable source tests with:
python3 -I -B -m unittest discover -s execution/minimal-human-trust/maintenance/recovery-r9 -p 'test_*.py'
The same tests run in the existing exact-head GitHub workflow via the recovery
shutdown regression fixture. Historical first-stop R3 tests retain byte-pinned
historical public R6 inputs instead of silently following the repaired source.

After independent review and a clean source commit, run build.py as Jenn.
It binds that exact Git HEAD; verifies the frozen R6 base and all 12600 files,
bytes and modes; overrides only the two reviewed maintenance modules; generates
19 runtime files in a fresh R9 namespace; and writes a canonical SOURCE_FREEZE.
The App/Native repair payload and existing target release ID remain unchanged.
The output is an unsigned, isolated candidate, not a production approval.

stage.py CAPSULE_SHA256 uses ordinary UID1000 SSH only. It verifies the exact
old user candidate package and moves that directory, using NOREPLACE on the
same filesystem, into the new user candidate. This avoids a duplicate package
on the small cloud disk. Protected old ROOT/STATE packages, records, plans and
business data stay intact. For an exact public package with private 0700 directories, it admits only
0700/0755 root-to-leaf directories, verifies every file first, then normalizes
only those same directory inodes to 0755 in the moved candidate. It rechecks
the complete destination bytes/modes and
runtime files before publishing SOURCE_FREEZE and a verified staging report.
A failed or ambiguous stage is inspected first; it never invokes an installer.
Before any native bootstrap, this ordinary engineering move is reversible by
verifying the same complete closure and moving it back using NOREPLACE.

Seal a delivery copy of operator.py with CAPSULE, ENTRY_SHA, LOADER_SHA and the
exact UTF-8 root-loader.py body. Keep tracked templates unchanged. Verify this
copy and independently run the sealed loader in MODE=preflight on both hosts:
this verifies bytes, historical closure/current source, namespace absence and
space budget without minting authority or performing root writes. Preserve the
exact-head CI result, independent review, source/capsule SHA-256 lists and
physical package receipt alongside the delivery copy.

Only after all these checks may an explanation-only terminal be opened. Human
Enter begins authentication. Separate exact APPLY CLOUD/LOCAL confirmations
are still required; see README_OPERATOR.txt for actions, time limits, cache
cleanup, activation and rollback. No automatic merge or business acceptance.
