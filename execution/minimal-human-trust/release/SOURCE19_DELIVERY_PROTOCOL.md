# Source19 delivery and Selector transaction candidate — R2

Scope: isolated protocol/persistence engineering only. The overall R2 source
acceptance remains **PARTIAL / SOURCE19_FIRST_STOP_OR_SNAPSHOT_CONTRACT_BLOCKED**
until the actual Source19 first STOP and final Handoff contract are satisfied.
This increment does not install an entry, sign a production delivery, stop or
start a service, switch Owner, or settle the two historical UNKNOWN operations.
The protected production entry is **ENTRY_UNIMPLEMENTED** and production
acceptance is **NOT_PROVEN**. `READY_UNINSTALLED` describes this source candidate.

## One existing transaction

`runDeliveryTransaction` keeps the original protected journal and exact signed
source19 envelope/public identity. The plan fixes revisions19→21/22, same Grant,
target signed Release/versions, canonical UUID `stopEpoch` (the exact existing
FirstCutover format, never a silent hash), final Handoff hash, protected business
preservation digest, nonce and original issuance/expiry/recovery deadline.
`allowForwardRecovery22:true` explicitly covers failure recovery under that same
approval. Both21 and22 are recovery-only, ACTIVE/connectRequested=false; neither
uses historical revision20 or opens new business. Forward guard rechecks current
target Release validity; recovery22 can restore the authenticated historical
source identity after the target expires, within the original recovery window.

`selectorBindingsHash` additionally binds the complete approved descriptor:
three roles, fixed host/selector filename, source/target raw selector bytes
(base64) and manifest paths. App/Bridge files are
`/etc/r16-cloud/{app,bridge}-host.json`; Native is
`/etc/r16/native-host.json`. Each JSON must have its real role schema, correct
publicConfiguration and codeManifest. Source and target must preserve every
other selector field. Source App/Native use the repaired R6 directory; Source
Bridge uses the existing signed R15 Bridge manifest. Target paths derive from
the approved signed target Release. Descriptor construction/installation and
actual protected host mapping remain future fixed-entry responsibilities; a
fixture filename is not evidence that a production selector was installed.

The forward chain is signature21 → cloud/local configuration → exact dual
readback → `forward-selector` INTENT → physical per-role CAS → Selector RESULT →
independent full manifest/file readback and safe machine proof →
`FORWARD_TERMINAL`. Configuration delivery alone can no longer be terminal.

A known21 signature and the same approved recovery scope allow signature22 →
cloud/local configuration22 → `recovery-selector` INTENT → source physical
selectors → RESULT → safe machine readback → `TERMINAL_RECOVERED`. The prior
forward terminal, if any, is retained as `forwardTerminal`; explicit recovery
is not short-circuited by it. Old configuration-only receipt schemas fail closed
rather than being mistaken for complete R2 terminals.

## Existing store is the only accepted-revision authority

`createExactCloudReceiver`, `createFencedLocalReceiver` and
`createSelectorHostReceiver` must use the SAME real per-host ProtectedStore.
The cloud receiver borrows a no-op-close view; only the owning outer scope closes
the actual store. The Local receiver uses its already-held actual store. No
nested re-open and no second permanent maxRevision/authorization ledger exists.
The accepted envelope revision/digest is the only monotonic authority. Cloud
Selector progress is publication metadata; Local progress is under
`delivery.selectorTransaction`. Both preserve prior phase INTENT/RESULTs across22;
no Grant, Owner authority fields, business ledger or UNKNOWN row is rewritten.

Each per-host operation holds the same store's exclusive lock for its complete
configuration acceptance/projection or physical Selector execution. The two
operations do not claim a continuously held lock across their intervening gap. A concurrent22 cannot pass an active21 writer; once
22 is accepted, a delayed21 selector fails `SELECTOR_SUPERSEDED` against that same
actual store, including after close/reopen. The fixed backend must not bypass
this store or introduce an external delayed writer. Protected snapshots inspected
while the lock is held are borrowed/read-only inputs; a guard must not try to
re-open its own held store.

`createSelectorHostReceiver` validates the complete descriptor, manifest role
version and every physical code-file hash. It checks admitted authority before
pending-file creation/write and immediately before atomic rename; the final CAS
also checks the old bytes and inode/metadata. It fsyncs the new file and parent,
then re-reads the physical selector and full manifest/code. Missing/foreign
files, a mismatched approved descriptor, an unrelated config field change or
unexpected selector bytes are refused, never overwritten as recovery.

## Unknown effects and final machine proof

Signing INTENT without RESULT remains UNKNOWN and never signs again, including
RECOVER reentry. Known signatures are saved before post-sign expiry refusal.
Configuration and Selector INTENT reentry only reads back; it never resends an
uncertain effect. An exact readback can persist a known RESULT. Partial21 may be
superseded by the explicitly approved22, but unknown22 is not replayed. Pending
files and original intent history are preserved, not blindly cleaned.

`backend.commitSelectors(envelope,request)` and
`backend.readSelectors(envelope,request)` extend the existing backend. The latter
returns the approved descriptor, per-role actual selector SHA/manifest/all file
hashes, per-host accepted phase and machine proof. A terminal requires exact22
(or21), zero unknown pending effects, old Owner STOPPED_FENCED with no writer,
new Issuer absent or the exact plan's recovery-only writer, the original Grant
and preservation digest, both original historical UNKNOWN still present, and
**current inflight=0 separately from those historical UNKNOWN**. Every role must
have no pending job and be actually STOPPED (main/control PID0 and empty cgroup) or have a same-epoch effective business fence with admission
closed and restricted writer authority. Running services are not fabricated as
inactive. A still-target Native/App/Bridge selector or unsafe role/Owner/Issuer
state prevents `TERMINAL_RECOVERED`. Terminal reentry re-reads actual selectors
and safe state instead of returning a stale success blindly.

`require`/`fresh` still require actual accepted Handoff, current native plan and
same epochs before each effect. Tests explicitly provide synthetic machine/STOP
proofs. They do not establish Source19 first STOP reachability or produce a real
Handoff. Actual Source19 close/UNKNOWN constraints and any narrowly proposed
first-stop repair are separately reviewed; this increment does not weaken them.

## Verification and evidence limits

```sh
node --test execution/minimal-human-trust/test/source19-delivery-transaction.test.mjs execution/minimal-human-trust/test/cloud-signed-delivery.test.mjs
```

Tests run the same production functions with synthetic Ed25519 keys, real
ProtectedStores and disposable physical JSON selectors/manifests/code. A narrow
filesystem namespace adapter maps fixed logical paths to temporary files; actual
open/write/fsync/rename and byte readback execute. Tests include partial physical
selection, source restoration after22, still-target rejection, lost ACK, unknown
signing/Selector results, late21, held-store exclusion including a different
process, and expiry between the final CAS read and rename. Physical commit
results are not mocked. Role/Owner/Issuer observations remain synthetic backend
inputs and are not actual OS state or production STOP evidence.

The original pinned Native launcher fixture separately verifies signed public
configuration and already-selected matching Native files. It neither installs a
selector nor starts Native. Formal G1/native code installation, real identity
admission, Source19 STOP, final Handoff, fixed production backend and V2/V3 remain
outside this limited increment. No new Human approval layer, authority service,
credential source or production namespace is introduced.
