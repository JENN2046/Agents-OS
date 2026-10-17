# Source19 first-STOP negative contract fixture

These 15 public files are byte-for-byte copies from the root-owned installed
release `/opt/r16/releases/r16-daily-20261015-r15-app-recovery-r6`, captured during
the read-only `SOURCE19_PROTECTED_DELIVERY21_22_EXECUTION_R2` investigation.
`PUBLIC_SOURCE_PINS.json` records every copied file's SHA-256, the public
configuration digest and the two actual role-manifest digests. The test hardpins
the complete pin-file bytes and checks all copied files before importing code.
No production configuration containing secrets, key, ledger, database or log is
included. No source bytes were modified, and these files are not runtime
overrides or an installable release.

The full production role manifests are intentionally not duplicated here. The
App manifest digest is `34731b300ccad9a1fbfd45b07422d847e8989d7e9dc052b0dda939cd99adb500`,
Native is `2516e881b0622b3ac2d53c454e6ccf9950441c5cb3c26a53500b45d3b1dbe7b4`,
and the signed public configuration digest is
`56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec`.
The existing public signed19 fixtures remain the signature inputs. This selected
source fixture does not claim to independently verify the complete physical
Source19 installation or the cloud's current process state.

Run from the repository root:

```sh
node --test execution/minimal-human-trust/test/source19-first-stop-contract.test.mjs
```

The eight tests prove **negative contracts**, not Source19 STOP reachability or
`V_SOURCE_INTEGRATED_ISOLATED_ACCEPTANCE_PASS`:

- Real public signed19 fails the existing disconnect-delivery STOP requirement.
- The installed code has no runtime STOP v2 signer interface.
- The exact published participant and dispatcher implementations reject
  historical UNKNOWN operations, both with and without a remaining lease.
- The exact published headless host cannot progress from that refusal to its
  socket, protected-store or lifetime-writer release steps.
- The local 6016 unit is an SSH relay; the Bridge role and Bridge signing key
  belong to the separate cloud service.
- Generic VCP upstream calls have local HTTP timeouts, not remote cancellation
  completion receipts. Empty paired role cgroups cannot alone prove those
  upstream operations are drained.

The dispatcher tests use genuine disposable `ProtectedStore` journals under a
private temporary directory. They execute the copied Source19 modules, not the
current R17 dispatcher. Synthetic keys, Grant, Release and leases are generated
only in memory. The two public operation identifiers, hashes and generations
are represented solely to reproduce the UNKNOWN guard; the synthetic signatures
are not production evidence and no original operation is executed or replayed.
The business engine is never created. The transport peer is inert and has no
socket or network activity. Fixture teardown explicitly disposes the synthetic
stores after asserting failure; that disposal is not an available production
recovery path or a successful shutdown claim.

The Native runner sets `process.exitCode=1` after the failed stop; it does not
force the process to exit. Its live socket and writer-release path have not
been reached. These tests establish that the supported graceful path cannot
certify clean exit. They do not claim that every real process must remain alive
forever: an external socket close or other environmental effect can still occur,
and would not turn the refused drain into a verified drain.

Therefore the current contract result is
`SOURCE19_FIRST_STOP_OR_SNAPSHOT_CONTRACT_BLOCKED`. A root observer must not
replace this missing drain evidence with process exit, freeze, SIGKILL, stable
ledger hashes, or a signature produced by a different process. No Handoff or
protected STOP Backend was added by this investigation.
