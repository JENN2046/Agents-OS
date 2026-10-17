# Source19 delivery protocol candidate

Result: **source protocol and isolated persistence integration only**.
Protected production entry: **ENTRY_UNIMPLEMENTED**; installer: **NOT_PROVEN**.
`READY_UNINSTALLED` describes only this protocol candidate. Nothing here registers a
human, loads a private key, installs a privileged command, changes Owner, chooses
an installed code selector, starts a service, or settles historical business.
The fixed production entry remains an uncompleted integration boundary; this
library is not evidence that the running machines support delivery 21/22.

## Fixed contract

`inspectDeliveryPlan({plan,sourceDelivery,targetRelease,now})` requires the exact
signed source19 envelope `b8645f6f…013e9` and public configuration `56e1df18…a5ec`.
The independently admitted plan must bind the signed target release hash and
versions, existing grant hash, nonce, stop epoch, accepted handoff hash, preserved
business state digest, original issuance/expiry/recovery deadline, and the fixed
source19/forward21/recovery22 revisions. It explicitly authorizes
`allowForwardRecovery22:true`. Both new deliveries are ACTIVE,
`connectRequested:false`, `recovery_only`. Neither reuses reserved revision20.
Recovery22 restores source19 public code identity with a NEW signature/revision;
it never restores historical ledger contents or automatically reconnects Owner.

## Same implementation for a future admitted root entry

`runDeliveryTransaction({journal,backend,plan,sourceDelivery,targetRelease,now})`
uses an already opened real `ProtectedStore` journal initialized with
`deliveryTransactionInitialState()`. Its lifetime exclusive lock covers the
whole synchronous protocol. The caller owns and closes that journal. No backend
means `DELIVERY_BACKEND_UNINSTALLED` before any journal mutation.

The future fixed entry must construct a trusted backend, never accept it from
stdin or a network request. Its methods are:

- `require({operation,phase,planHash,stopEpoch,handoffHash,now})`: independently
  enforce native admission/expiry for this exact operation. Must throw on
  refusal. It is called immediately before signing and each durable projection.
- `fresh(request)`: return the exact plan/stop/handoff bindings,
  `singleWriter:'HANDOFF_ACCEPTED_OWNER_FENCED'` and `preservedStateHash` from
  actual protected same-epoch evidence. The test fixture supplies this explicit
  synthetic proof; no real handoff is claimed.
- `sign(body,{phase,planHash})`: one synchronous issuer signing operation. No
  default loader exists. The exact signature is cryptographically checked.
- `commitCloud(envelope)` / `commitLocal(envelope)`: accept the exact stored
  envelope; ACK must include `status:'STORED'`, revision and `deliveryDigest`.
  The old daemon's smaller ACK is not compatible evidence.
- `readCloud()` / `readLocal()`: fresh exact signed accepted envelope, complete
  public/control projections, projected digest and protected business digest.

`createExactCloudReceiver` uses the actual configuration receiver's durable
accepted → public/control → projectedDigest chain. Only trusted in-process code
supplies its verifier/effect guard. The generic stdin CLI and generic projector
retain their old validation and `prior+1` behavior. False connect means ledger
initialization, credentials and service reconciliation are never invoked.

`createFencedLocalReceiver` uses the real protected Owner cache format. It
changes only `delivery` and the injected public projection, preserving all
remaining Owner data. It must never run beside the old Owner writer. The caller
must already hold the actual accepted handoff/single-writer fence, and supply
protected fixed-location read/write/store adapters. This candidate does not
update a proposal, reviewed installation, native selector or cutover phase.
Those remain part of the future reviewed installer, not hidden delivery effects.

## Crash and recovery rules

Each signature INTENT is durable before the private operation; missing RESULT
is UNKNOWN and cannot be signed again, including explicit recovery reentry.
A known signature is saved before checking post-sign expiry. Commit INTENT
reentry only reads back; it never resends an uncertain external call. Exact lost
ACK may become RESULT by readback. A known forward signature plus an approved
plan permits fixed recovery22 after partial21; both receiving stores reject a
late21 once22 was accepted. Any unknown22 remains pending without a new signing
attempt. Original INTENTs and bounded failure codes remain in the journal.

## Verification and explicit limits

Run from repository root:

```sh
node --test execution/minimal-human-trust/test/source19-delivery-transaction.test.mjs execution/minimal-human-trust/test/cloud-signed-delivery.test.mjs
```

Synthetic Ed25519 keys and actual protected temporary stores exercise the same
module/receiver/cache code. The test alone replaces immutable source19 public
pins with synthetic signed fixture pins; production exports have no override.
The pinned original Native trusted launcher fixture is byte-exact
`4583ddd8…85e27`. Its real signature/manifest/file validator runs with an explicit
filesystem adapter. Tests manually supply already-selected matching manifests
and ACTIVE cutover: they prove input compatibility, **not** actual selector
installation, a running Native, real handoff or production acceptance.

Still required before production execution: reviewed fixed privileged bootstrap
and exact native approval contract; actual single-writer/handoff and same-epoch
business attestor; fixed signing credentials/plan guard; protected local/cloud
transport adapters; target selector install/rollback and full end-to-end receipt.
The current issuer-only RECOVERY_SHADOW entry does not silently gain these powers.
