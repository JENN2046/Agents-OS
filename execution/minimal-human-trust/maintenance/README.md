# App shutdown and maintenance recovery source

This is reviewed source and isolated regression coverage. It is not an installed
release, an administrator approval, or a production acceptance receipt.

The App's `shutdown()` stops new admission, drains work that actually started,
closes its executor and releases writer locks. It preserves leases, UNKNOWN
operations and signed history. The system runner closes HTTP acceptance in the
same shutdown flight, including when resource cleanup fails. Explicit business
`close()` still requires the original retirement and KNOWN evidence; process
exit does not manufacture business CLOSED evidence.

`transaction-driver.mjs` receives its privileged effects from fixed, admitted
adapters. Restoration and final readback reconcile actual state on every
continuation. Each attempt has a separate record and result hash; a partial
attempt is PENDING. A legacy DONE(partial) record remains unchanged and is
integrity checked, but cannot substitute for current OS state. The driver never
returns from ABORT or ROLLBACK to forward installation, retries unknown signing,
or creates a new approval window. Reconciliation is bounded to 64 attempts per
step; the real adapters additionally enforce the original native deadlines and
refuse to repeat an uncertain start.

The fixed Python adapter sources remain source only. Component directory
creation uses explicit 0700, and the process umask is 077. The maximum graceful
wait is 120 seconds and still stops at the admitted deadline; force termination
is forbidden. A mutating launcher that has no terminal receipt exits 75 rather
than reporting process-level success. Read-only observations remain distinct.

The CI's existing shutdown regression entry imports the new App, transaction and
Python fixture suites. Tests use generated keys, disposable state and loopback
HTTP child processes; they do not read production credentials or call providers.

Production promotion is separate. The R15 App backport must receive new App
manifests/version hashes and a complete package. Cloud staging, selectors,
rollback and all fixed code pins must match that package. The local R5 source
integration's copied R4 package is unchanged test input and does not contain the
App fix. It deliberately has no executable launcher, capsule or signing
approval. Do not install it or reuse an aborted R4 transaction. Existing R4
journals and the independent original-service recovery receipt are preserved.

R6 App+Native physical assembly and protected adapter sources are tracked in
`release-r6/`. Its portable transaction and Python suites run in the existing
CI shutdown entry; full physical staging additionally requires the reviewed
12,592-file local package. The independent verifier and deterministic builder
are in `release-r6/tools`. First installation remains blocked before service
changes until the original running App has an actual safe stopped proof. The
source tree and offline package do not create an APPLY launcher, native
admission, approval window or production signature.
