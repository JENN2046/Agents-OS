# Source19 Native maintenance transition

This is a separate, minimal Native maintenance candidate. It does not install
R17, change Owner/Grant, settle UNKNOWN, or establish a business STOP.

## Present boundary

The source driver, publication protocol and isolated tests exist. The new code
is not installed. A real protected foreground admission entry, a complete root
Native checkpoint/OS backend, and authenticated two-host transport are not
provided by this directory. The production path therefore remains blocked.
Passing source tests or supplying a callback with `environment='PRODUCTION'`
does not constitute native administrator admission or an OS proof.

`stop_transition.py` has no production CLI. Running it directly refuses with
exit 78. It cannot be used as an unprotected privileged helper. The admitted
installer must own a locked, durable journal and a fixed OS adapter; the latter
must independently enforce the exact plan before every effect.

## Old Native does not consume the new shutdown API

One new plan binds the actual Source19 identity and five-role baseline. It
installs persistent, plan-owned fences for App, Bridge, Native relay, Owner and
Native. It gracefully stops App, Bridge, relay and Owner, then attempts the old
Native's existing SIGTERM path once. The old Native may refuse because its
business history remains UNKNOWN.

Only the explicit non-drained Native allowance permits the external adapter to
freeze that exact singleton Native, seal checkpoint B, record a durable consumed
signal intent, and issue one pidfd SIGKILL. PID reuse, a foreign writer, another
Native member, a changed checkpoint, unresolved INFLIGHT, or unapproved UNKNOWN
refuses. A lost reply never authorizes another signal. Other roles have no
force-stop allowance.

The result is `STOPPED_FENCED_NOT_DRAINED`, `globalExecution=UNPROVEN`, and
`roleStopReceipt=false`. Checkpoint B follows any legal graceful-stop writes;
it must not be substituted for the earlier live baseline or described as a
graceful drain. SQLite/WAL/SHM must be copied/hashed while the exact Native and
all other registered writers are fenced and frozen/stopped; the collector must
not open the live database. Original signed leases and operations remain.

The installer consumes this result under the same plan and retains the fences
through staging, signing and selection. The original active baseline is kept
for provenance. Recovery keeps a crashed source Native stopped and does not
automatically reopen the App business path. No old APPLY or recovery deadline
is reused or extended.

## Exact inherited uncertainty

The original two business UNKNOWN are distinct from Native dispatcher control
UNKNOWN. A bounded ordinary-user observation on 2026-10-17 found 9,611 control
UNKNOWN; an INFLIGHT control was transiently present. This observation is not a
frozen complete checkpoint and does not approve that set for maintenance.
Stored control records contain id/hash/status and do not establish the missing
operation type or outcome. No success/settlement/replay may be inferred.

A new approval must bind the complete exact control UNKNOWN count and digest,
the original business lease/operation identities, registered Store dev/inode,
and complete checkpoint. The target's protected history descriptor is an
evidence projection of that same stopped journal/checkpoint, not a second
authorization root or an alternative settlement ledger. The maintenance runner
may consume only its exact target/Grant/config/Store binding. A new UNKNOWN or
any INFLIGHT still refuses. The default shutdown path remains strict.

The descriptor must also transport the two original public App-signed operation
envelopes. Their exact original hashes, App signatures and actual old Issuer-
signed lease bindings are checked; a root boolean cannot replace them. The old
App host persists signed envelopes in its own operation records, so a missing
Native result file does not establish that the envelope is lost everywhere.
Those production envelopes have not been collected in this source task.
Missing or invalid material still blocks admission. No envelope is recreated
from an operation hash. The runtime keeps verified transport data in private
branded state and does not expose a new caller override.

## Package scope and version planning

`build.py` requires an ordinary user, a clean exact Git HEAD, the exact installed
Source19 public projection and complete signed code base. It copies the complete
base into a new isolated directory and changes only five Native-only files:

- `host/workspace-dispatcher.mjs`
- `host/native-runner.mjs`
- `host/headless-host.mjs`
- `native/upstream/VCPDistributedServer/Plugin/ProjectForge/ProjectForgeService.js`
- `native/upstream/VCPDistributedServer/Plugin/ProjectForge/indexerClient.js`

App and Bridge manifests/bytes remain identical. The dispatcher is a backport
onto Source19, preserving its R15 recovery guard and legacy reconciliation; the
general R17 business-stop/read-result-settlement features are excluded.

The candidate has no Release signature and no assigned forward/rollback
revision. Production revision planning must inspect actual accepted, signed
and reserved maxima; the old reserved 20 is forbidden. Any earlier unallocated
R17 21/22 planning must be explicitly cancelled/replanned before maintenance
uses those numbers. An isolated 21/22 fixture is not a production allocation.

`verify.py` is an independent stdlib byte verifier. It does not import the
builder or runtime. It compares every payload file against the real Source19
base or the exact reviewed Git source, verifies modes, complete membership,
role manifests, bindings and the externally pinned inventory SHA-256. Its PASS
is only an unsigned byte-verification result.

## Verification

Portable tests run with Node's test runner and Python directly:

```sh
node --test maintenance/source19-native-transition-r1/test_*.mjs
python3 -I -B maintenance/source19-native-transition-r1/test_stop_transition.py
python3 -I -B maintenance/source19-native-transition-r1/test_build.py
```

`test_real_process.py` is separately opt-in through
`R16_NATIVE_PHYSICAL_BACKEND=1`. It runs only ordinary-user disposable children
and stores under `/tmp`; it loads the exact installed old Native code and its
signed dependency closure. It exercises the old SIGTERM refusal, real pidfd
stop/kill, real SQLite/locks and legal dead-PID lock reclamation. Its four other
role/fence observations are isolated adapters, and SIGSTOP stands in for a
cgroup freeze. Generated fixture keys and substituted operation hashes are
test-only. This is not a root/systemd or two-host production acceptance.
