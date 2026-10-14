# Minimal Human Trust: G1-D

This package is reviewed implementation and isolated validation work for
[Agents-OS #46](https://github.com/JENN2046/Agents-OS/issues/46). It does not replace
the running R15 Owner service and is not an approved production release.

## Execution boundary

- The issuer is one request per process; no new resident Owner daemon.
- The protected entry accepts recovery only. Caller input cannot enable business.
- Issuer, release and Human enrollment roots are independently installed pins.
- A signed handoff and exact protected snapshot are required before first admission.
  v1 still requires all leases closed; v2 admits only the two pinned old read
  UNKNOWN leases, under a distinct signed recovery attestation and recovery mode.
- Existing production UNKNOWN records are neither cleared nor replayed.
- Human consent is separate from UID membership and ordinary role signatures.
- Current production registration, signed release, single-writer handoff and live
  cloud delivery remain gated. Synthetic credentials are never production roots.

## Protected pending proposal production

The uninstalled minimal-human-trust-proposal.service now endorses one exact
first enrollment or first cutover proposal through the original Release root,
before the separate native Human ceremony. Its complete freeze, independently
checked pre-Human evidence, durable one-shot journal and immutable fixed pending
files do not sign a Release, enroll Human or install anything.
See [PROTECTED_HUMAN_PROPOSAL_R1.md](PROTECTED_HUMAN_PROPOSAL_R1.md) for exact inputs,
expiry/crash semantics and the remaining real key/install/signing approval gates.

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

## Exact recovery handoff and isolated cutover rehearsal

`mht.issuer-handoff.v2` carries an enrollment-root-signed `recoveryAdmission`.
It pins the original two operation IDs/hashes/generations and exact signed old
leases, R15/R17, stage authorization, original recovery evidence, review, whole
issuer data digest and persisted wrapper digest. Operation hashes never come
from issuer project rows. The certificate builder calls the original exhaustive
migration/Crown verifier before constructing that attestation; matching fixture
labels or newly signed synthetic operations cannot substitute for original bytes.

The one-request receiver validates this signed exception under both issuer and
replay locks before its first durable binding. Other projects must have genuine
signed closure; any extra pending/active project, substituted lease or changed
snapshot refuses admission. The existing v1 all-closed rule remains unchanged.
After registration v2 still requires the exact R17 and recovery-only mode, even
after its initial short window expires. It never issues new business leases or
settles/replays an UNKNOWN. Cleanup may advance the new ledger only through its
existing signed protocols; old state is never restored over those results.

Fresh snapshot observation is different from `maxNow`, the journal's last WRITE
time. v2 binds an explicit fresh signed observation and full wrapper hash while
rereading the fenced Owner and identical snapshots. It does not update old
ledger timestamps merely to pass a freshness check.

`release/stage-installer-reviewed.mjs` is currently **isolated rehearsal only**.
Its exported rehearsal accepts isolated signed inputs and mandatory virtual OS
read callbacks, and derives every output below one private user-owned `/tmp`
directory. It verifies exact physical bindings and stage/STOP/snapshot proofs,
then exercises `INTENT -> ARTIFACTS -> COMMIT` publication with real atomic file
writes and fsync. Every write/rename checkpoint rechecks the clock and writer.
INTENT-only is UNKNOWN and never repeats its effect; durable ARTIFACTS resume
only the identical bytes. A recorded COMMIT is read-only and cannot overwrite an
advanced new ledger. Empty precreated replay directories get a state file;
nonempty replay journals are never reset.

**Its CLI always refuses production installation.** The generic `change_trust`
flow requires an installed issuer. A separately typed first Native confirmation
entry now validates the signed stage and enrollment without that dependency.
It remains uninstalled and has never confirmed an actual Human. STAGE_ONLY's
`mayInstall`, `mayHandoffIssuer` and
`maySettleUnknown` remain false. Real administrator/Human enrollment, a typed
native cutover approval, credential provenance and a rehearsed same-epoch STOP
window must be completed before a production installer can be admitted. There
is no production credential provisioning or signer entry in this rehearsal.

## First Native Human confirmation entry

The native window accepts only its fixed `--first-cutover` route or the standard
route. The existing socket uses an exact first `select_confirmation` frame; the
broker rejects missing/cross-lane frames, obtains kernel UID/process identity,
shows the entire fixed proposal and public-root fingerprints, then requests a
fresh polkit check. No new daemon, credential input or account migration is added.
This is an explicit protocol upgrade; old clients are not silently rerouted.

The fixed Node approval bootstrap verifies root/unit provenance and every frozen
source byte before dynamic signer import or key access. Only the dedicated
`first_cutover_handoff` action uses signed staged enrollment as Human authority;
generic grant/trust actions retain their installed-enrollment requirements. The
new route uses distinct pending files and cannot overwrite the original Stage
proposal or OS receipt. It validates complete source/installer closure and the
unchanged protected snapshot before confirming or signing. Canonical SPKI keys
prevent padding aliases from defeating root/Human separation.

The target pins R15/Grant, signed R17, exact stage/result/review/evidence, full
snapshot, freeze/installer, old roots, epochs and a complete new-root template.
Only the future signed handoffHash is absent from that template. It permits the
specifically reviewed stop/fence/recovery handoff, with no business activation,
UNKNOWN settlement or replay. The signed consent pins the full proposal hash,
nonce, target and original short expiration; the broker keeps unique fsynced
INTENT/RESULT. No credential path or missing issuer file can select this route.

Read-only final admission requires both the genuine Human signature and protected
OS receipt, then fresh post-confirmation R17 control delivery/STOP/handoff and
snapshot, actual old-writer fence and exact completed roots. The isolated native
Human rehearsal rechecks that admission at every publication guard and binds its
Human/OS/nonce/stage/handoff/root hashes into INTENT, ARTIFACTS and receipt. A
historical COMMIT grants no fresh authority and never restores an advanced ledger.
These implemented source paths are not a real Human ceremony, installation,
signing run, service stop, production cutover or production acceptance.

## Validation commands

On the pinned Jenn host, run:

```sh
NODE_PATH=/home/jenn/AGENTS_OS_Workspace/runtime/VCPChat/node_modules node --test test/*.test.mjs
python3 -B test/human-approval-broker.test.py
python3 -B test/human-approval-window.test.py
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

The packaging directory is source only. Historical R1 evidence/reviews are
immutable snapshots, not acceptance of later source. Every new delivery needs
its own exact-head source/physical manifests, actual regression logs, independent
review and native production gates. Never rewrite an old PASS/hash/test count
to bind it to new code. No production-ready or G1D_VERIFIED claim is made.
