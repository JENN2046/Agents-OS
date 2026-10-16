# First-stop R7: isolated controlled-crash-stop core

This is a proposal implementation and isolated fault model. It has no production
OS adapter, root command, subprocess, signal implementation, active approval,
nonce, service, credential, signing key, or installation entry. Running
`python3 -I -B controlled_crash_stop.py` refuses with exit 78.

The operation is explicitly non-graceful. `drainStatus` is always `UNPROVEN` and
upstream work already accepted may continue. A count of zero durable INFLIGHT
rows means only that the inspected local durable collection contains no such
row; it is not a count of HTTP requests, promises, allocations waiting before
persistence, remote jobs, or all tools.

## Exact proposed boundary

The isolated approval payload requires three distinct acknowledgements:
`allowNonGracefulOnce`, `acceptUnprovenInflight`, and
`acceptPossibleUpstreamContinuation`. It binds the original App service, cloud
host, boot ID, PID/start ticks, exact cgroup and original reviewed source hashes.
Only the one original main process may be in the cgroup. It also binds the
expected two original UNKNOWN operation identities/hash/generation/result and
complete active/closing/pending lease hashes by semantic digest. This is a
policy binding; it does not ask a human to preapprove every live heartbeat hash.
Synthetic fixture approvals are not production authority.

The proposed future trusted reader must enumerate the complete registered App
store file set without accepting caller paths, validate exclusive writer facts
and original signatures with the existing public trust root, and confirm there
are no other writers. The injected checkpoint supplies bytes and file metadata;
this core independently parses JSON, checks exact original operation and lease
bindings, rejects missing stores/locks, additional durable INFLIGHT, unresolved
allocations, corrupt/duplicate JSON, temporary `.next*`/`.reclaim*` files,
nonregular/symlink/hardlinked files, foreign writer locks and unsafe modes. No
temporary or stale lock file is deleted.

## Ordered effects and recovery

1. Read exact target identity, then acquire its identity-bound pidfd capability.
2. Persist fence intent; install and read back an owned automatic restart fence.
3. Persist freeze intent; freeze the exact cgroup, then verify fully frozen,
   ownership and unchanged single-process membership. A future backend must wait
   for the actual kernel frozen completion, not only command success.
4. Generate a complete frozen checkpoint and persist its manifest/hash.
5. Persist a single `SIGNAL_INTENT`, consuming the attempt before the syscall.
   Recheck target, cgroup, freeze, fence and deadline, then call only the injected
   pidfd SIGKILL interface once. Its future OS implementation must repeat the
   deadline check at its own syscall boundary. Never invoke systemctl stop after
   freeze, repeat TERM, enable SendSIGKILL, or fall back to a numeric-PID signal.
6. Fresh readback must prove the original process exited and the cgroup empty,
   the owned restart fence remains, and all checkpoint file bytes/hash/modes are
   unchanged. Only then report `CONTROLLED_CRASH_STOPPED_NOT_DRAINED`.

A known failure before the durable signal intent may thaw and remove only this
operation's owned fence after fresh original identity readback. Target drift,
unknown ownership, or a failed restore remains recovery-required. An intent or
unknown signal return is never replayed, even when fresh readback still sees the
old process alive or the signal was never actually issued. There is no automatic
thaw/restart after that irreversible boundary. After the deadline only readback
or pre-signal rollback is permitted. A historical terminal receipt is read-only.

A future exact separately approved installation/recovery operation must perform
any service start. Original ProtectedStore dead-PID/start lock recovery must be
used; startup INFLIGHT-to-UNKNOWN transitions must not be disguised as unchanged
whole-state hashes. This core neither settles nor replays business work and
creates no CLOSED evidence, Grant, Owner, Crown authority or identity enrollment.

## Validation

`python3 -I -B test_controlled_crash_stop.py` runs 27 isolated tests. The fake
backend has no subprocess or real signals. It covers durable-intent crash
boundaries, unknown delivery, no replay after deadlines, exact original-byte
preservation, PID reuse, cgroup membership changes, owner/freeze drift, unsafe
file metadata, corrupt/temporary store files, original operation/lease drift,
registered host/project graph, all persistent-collection UNKNOWN scope, other durable work/writers and recovery of owned pre-signal effects.

The original-R15 counterexample and independent review are separate files owned
by the reviewer. Passing fixtures do not prove actual production drain, stop,
persistence, root approval, installation, rollback, or real dual-host acceptance.
