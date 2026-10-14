# Minimal Human Trust: G1-D

This package is reviewed implementation and isolated validation work for
[Agents-OS #46](https://github.com/JENN2046/Agents-OS/issues/46). It does not replace
the running R15 Owner service and is not an approved production release.

## Execution boundary

- The issuer is one request per process; no new resident Owner daemon.
- The protected entry accepts recovery only. Caller input cannot enable business.
- Issuer, release and Human enrollment roots are independently installed pins.
- A signed handoff and exact closed snapshot are required before first admission.
- Existing production UNKNOWN records are neither cleared nor replayed.
- Human consent is separate from UID membership and ordinary role signatures.
- Current production registration, signed release, single-writer handoff and live
  cloud delivery remain gated. Synthetic credentials are never production roots.

## First-use signing sequence

The fixed publisher accepts only `mht.first-trust-publisher-stage-plan.v2`.
Its complete `STAGE_ONLY` authorization and digest are embedded in the
Release-root-signed Human proposal, displayed by the native broker and bound
to the protected OS journal. They pin the R15/Grant, exact R17 reviewed file
manifest, complete trust roots, source freeze, reviewed installer source,
unchanged original UNKNOWN evidence, issuer snapshot, epochs and five-minute
window. The fixed reviewed-installer path is
`/etc/minimal-human-trust/stage-installer-reviewed.mjs`; the signer only hashes
it and never executes it. Trusted installation and key-holder provenance are
separate, explicit native-administrator prerequisites, not granted by the plan.

Stage-only signing no longer demands a STOP format that installed R15 cannot
produce. It still verifies the two original signed readonly UNKNOWN records
and closure of all other projects, rechecks complete physical file coverage
before credential access, and re-reads protected inputs/issuer state before
and after signing. Frozen stage evidence can age only within the same
five-minute Human window; it cannot be refreshed or substituted after approval.
The transaction still reserves/fsyncs INTENT first; intent-only is UNKNOWN and
must never be blindly retried. Its output is `SIGNED_STAGED_NOT_INSTALLED` with
no install, business, UNKNOWN settlement or issuer-handoff authority.

The separate staged-R17 handoff inspection requires the durable matching
stage INTENT/RESULT, exact signed R17, **fresh R17** three-role STOP proofs in
the approved stop epoch, signed handoff epoch, actual inactive/masked old
Owner, no writer lock, and identical protected issuer snapshots. STOP expiry
remains at most 30 seconds. This inspection is read-only and cannot install,
activate or start a writer. Restricted R17 STOP instrumentation and any actual
installation/signing/business interruption still require their precise native
authorization; an isolated test cannot supply it.

## Validation commands

On the pinned Jenn host, run:

```sh
NODE_PATH=/home/jenn/AGENTS_OS_Workspace/runtime/VCPChat/node_modules node --test test/*.test.mjs
python3 -B test/human-approval-broker.test.py
```

The actual ProjectForge/SQLite acceptance imports the exact external files listed
in `test/fixtures/actual-adapters-manifest.json`; missing or mismatched dependencies
are failures, not skipped tests. Transport adapters run in-process in disposable
workspaces. These tests do not restart services or access production credentials.

`tools/` contains fixed, synthetic-only root OS proof programs. They are not an
installer or generic root execution API. The executed proof used separately
reviewed root-owned files, an encrypted synthetic key, transient systemd service
and temporary socket units. It verified the real credential mount/public identity,
normal one-request exit, oversized input refusal and a five-second input timeout.
The socket was stopped and only the exact created runtime unit files were removed;
the root-owned encrypted fixture remains for audit. Do not blindly rerun provision.

The Human confirmation candidate and its remaining production prerequisites are
documented in `human/README.md`. No actual Human enrollment or polkit confirmation
has occurred. Approval artifacts for Grant creation and trust changes are not
applied by this package.

App, Bridge and Native include private durable business-stop fences and signed
same-epoch evidence. App evidence waits for complete live request lifecycles,
including allocation and admission. Reconciliation remains available; stop does
not turn UNKNOWN into success or redispatch a mutation.

The existing host administrator policy was available for the scoped root proof;
this work does not remove existing sudo rights or claim protection against an
actor who already controls root. It adds no generic privileged command API.

## Deployment

The packaging directory is source only. Do not install it against production
credentials or ledgers until the six `G1D_*_R1.json` reports under `evidence/` and
the final reviewed-source manifest have passed their stated gates. Evidence and
review documents distinguish actual OS checks, isolated code tests and unperformed
production operations. No production-ready or G1D_VERIFIED claim is made.
