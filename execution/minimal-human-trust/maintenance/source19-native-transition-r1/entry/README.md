# Protected read-only Source19 preflight source

**Current mode is exclusively `READONLY_PREFLIGHT_SOURCE` and
`executionReady=false`.** The typed preservation/recovery contract for the
new target instance is incomplete. This package must not be presented as a
signing, stopping or installation entry. It is not installed on either host by
this engineering task, and no production preflight has been run here.

`ENTRY_FREEZE.json` has exactly six keys: `schema`, `mode`, `files`,
`packageFiles`, `planTemplate`, `revisionRequest`. Only the read-only mode is
accepted. `revisionRequest` must contain null forward/recovery values and
`CANCELLED_UNALLOCATED_REPLAN`; it reserves no numbers. `packageFiles` may be
empty in this source mode; no target or old protected package is copied or
modified. Every declared source/package row still binds its SHA256, raw size
and exact mode; membership must match the declared closure.

## Fixed code and read-only paths

The code-admission layout, for a separate future accurate code approval, is
`/usr/lib/r16-maintenance/source19-native-transition-r1/runtime/` plus root600
`ROOT/ENTRY_FREEZE.json`. The external code capsule pin is in root600
`/etc/r16-maintenance/source19-native-transition-r1-entry-capsule.json`, schema
`r16.source19-native-transition.installed-entry.v1`. It is a code identity,
never a stop/maintenance grant.

The stdlib bootstrap hashes and holds every declared source before executing a
module, then uses an in-memory Python importer. Node consumers have fixed
paths to the same protected closure. The legacy R8 file library is explicitly
included; its old App authority, target and receipts are not inherited.

The fixed cloud RPC helper template is
`/usr/libexec/r16-source19-native-transition-r1-rpc`. In this mode only
`preflight` can run: it needs the same installed source capsule and fixed root
host, but no invented native maintenance approval, plan, journal or intent.
Every other RPC operation hard-refuses before loading an effect adapter.
The template sudoers rule permits only that read-only verb. The code-admission candidate may explicitly include the cloud-only fixed
helper (0755) and read-only sudoers policy (0440). Single-host preflight needs
the approved protected code; authenticated cross-host preflight additionally
needs approval to install that exact cloud read-only helper/policy. No service
unit is part of that code-admission target set. **Neither helper, sudoers nor
unit is installed or reloaded by this source task.**

The disabled oneshot template and `service_main.py` hard-refuse. It mounts no
credentials. No code here reads Release/Issuer private bytes. The existing
future credential source paths remain the original Release and Issuer
`systemd-creds` files; using them requires a different, fully reviewed native
transition capsule after the missing recovery contract is implemented.

## Real read-only composition

Cloud preparation captures exactly App and Bridge, their real Source19 public
configuration and verified accepted19 delivery, public signature/revision
records, and the two original public App-signed operation envelopes. It does
not invent a Native target, full five-role baseline or stopped checkpoint.

Local preparation independently captures Owner, Native relay and Native,
merges the authenticated fixed cloud projection, and invokes the registered
Native live-preflight collector. That reader preserves the exact historical
UNKNOWN identity/signatures and control uncertainty. It is not atomic frozen
checkpoint B, does not open the live database, and does not claim no foreign
writer/global drain from a live process. Missing collector, wrong signatures,
new UNKNOWN, INFLIGHT, instance changes or root identity drift refuse.

The existing public-state reader validates actual accepted/signed/reserved
records. Unknown revision closure remains explicitly BLOCKED. When complete,
null/null requested revisions return the real inventory plus
`BLOCKED_UNSIGNED_REQUEST_NOT_ALLOCATED`; no temporary revision is invented.
Preflight can report that truthful readback while `executionReady=false`.
Only observation timestamps/derived diagnostic digests are excluded from the
stable facts hash. Source bytes, versions, signatures, maximum revisions and
process identities remain bound. No mutable provider/environment path or
caller boolean supplies production evidence.

## Foreground and transport

Default describe has no root, network or write effect. The ordinary operator's
`--preflight` waits for the person's Enter and performs fresh `sudo -k` root
authentication with inherited TTYs. Its cloud Python launcher preserves the
kernel sudo/PTTY ancestry for the already reviewed HostAdmin guard. This is
`TRUSTED_HOST_ADMIN`, not Human enrollment, civil identity or a localness claim.
The code does not read passwords, fill a confirmation line, or capture the
human TTY session. No actual sudo/desktop chain compatibility is claimed by
isolated tests.

`--run`, `prepare-cloud`, `approve-local`, every mutating RPC, the service and
Native effect capability are hard-disabled by the current source mode. The
retained exact-confirmation helper can be tested in isolation, including EOF
refusal; it is not reachable as a production maintenance approval entry.

Noninteractive transport uses only the existing fixed SSH identity/known-hosts
and fixed root helper. It cannot send an arbitrary shell, path or PID. Lost
stdout/timeouts do not trigger automatic retries. No new SSH identity,
Owner/Crown, signing root or long-lived service is created.

## Isolated verification

Run from `execution/minimal-human-trust`:

```
python3 -I -B maintenance/source19-native-transition-r1/entry/test_entry.py
python3 -I -B maintenance/source19-native-transition-r1/entry/test_orchestration.py
```

The tests exercise temporary real byte/set/mode hashing and NOREPLACE, held-byte
imports, effect hard-refusal before TTY/backend/state writes, fixed RPC/SSH
scope, operator cancellation/failure propagation, real three-plus-two schema
composition, missing collector refusal and explicit unallocated/blocked
revision states. OS/proc/root metadata and external Node/SSH boundaries are
explicit isolated mocks. No root, sudo, SSH, production keys, live database,
production state write or service action occurs.
