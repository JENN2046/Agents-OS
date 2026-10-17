# Source19 first STOP and Handoff order

Gate: SOURCE19_FIRST_STOP_OR_SNAPSHOT_CONTRACT_BLOCKED.

The signed Source19 delivery has `connectRequested=true`. The unchanged strict
`verifySignedBusinessStop` rejects it with `STOP_CLOUD_CONTROL`; Source19 App and
Bridge have no same-epoch v2 signing entry. Native suspendBusiness is not a signed
stop and a later successful Owner heartbeat can reopen it.

There is a second, substantive failure: installed Native `close()` waits for
active calls, then calls participant `stop()` and requires every participant's
unresolved set to be empty. Original `r16.stopped.v1` requires every operation to
be KNOWN. Preserving the two original UNKNOWN therefore prevents this close
from succeeding. `headless-host.stop()` subsequently cannot close the socket or
release the process/writer lease; the runner catch only sets failure exitCode.
A stopped PID or empty cgroup alone is not evidence of successful drain.

We evaluated a dedicated HOST_ADMIN_SOURCE19_EXIT_OBSERVER alternative: persistent
OS fences, graceful exits and full protected checkpoint observation, followed by
an explicitly new proof signed in a fixed credential unit. This cannot currently
supply the missing successful Native close or equivalent no-current-inflight
proof. Root freezing/killing and stable ledger bytes cannot measure all pending
runtime work or prove remote completion. No such proof, signer or new authority
was implemented. This is not a missing-key or missing-approval engineering gate.
Original historical read UNKNOWN is not required to become KNOWN; the defect is
that installed Native conflates it with the physical shutdown requirement.

The future correct sequence remains Human approval → Source19 admission closure
→ real three-role STOP/isolation with same-epoch proofs → Owner stop/fence and
writer exit → final protected snapshot B → final Handoff → delivery/selectors.
It cannot start by installing/selecting R17 or by requiring final Handoff first.

Stage snapshot A remains immutable. Human approval must bind A and an exact
allowed-transition policy; final Handoff must bind actual B and the verified A→B
transition. Current first-cutover/proposal code incorrectly requires A==B, and
staged Handoff checks target R17 STOP. The builder also hardpins original R15 as
current source and conflates Source19 with the two UNKNOWN leases' historical
R15 release. These are documented unmodified downstream gaps, not relaxed gates.

Smallest next source design: define physical shutdown preserving exact historical
UNKNOWN separately from actual live-call drain, and establish a reviewed Source19
first-stop proof/entry with its real anti-reentry and upstream observation scope.
Any required pre-control signed revision needs explicit replanning from fresh
accepted state; never occupy20 or silently redefine21. No production retry or
native approval is requested to conceal this source contract gap.
