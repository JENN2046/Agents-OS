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

## Validation

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
