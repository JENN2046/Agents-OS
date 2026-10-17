# HOST_ADMIN_CUSTODY identity-key admission

This source implements a future root-installed native entry. This engineering
change does not install code, generate real keys, register a Human, issue a
Release, change Owner, start production services, or accept business operations.

The custody model is **HOST_ADMIN_CUSTODY_NOT_HUMAN_EXCLUSIVE**. Jenn explicitly
approves the local Host Admin generating and retaining two separately generated
Ed25519 keys under systemd host encryption. The resulting public keypair proofs
demonstrate consistency of the generated and sealed keys. They do not demonstrate
exclusive Human possession, a civil identity, or independent physical custody of
the Enrollment key. The Enrollment key is cryptographically distinct; its custody
is on this same trusted host. An alternative physical custody model requires a
different reviewed admission, rather than silently changing this entry.

## Fixed installation contract

The code-only installer may exclusively place these files, without loading or
starting the unit:

| Source | Protected destination | Mode |
| --- | --- | --- |
| `authority/identity-admission.py` | `/usr/lib/minimal-human-trust/authority/identity-admission.py` | 0644 |
| `packaging/minimal-human-trust-identity-admission` | `/usr/lib/minimal-human-trust/packaging/minimal-human-trust-identity-admission` | 0755 |
| `packaging/minimal-human-trust-identity-admission.service` | `/etc/systemd/system/minimal-human-trust-identity-admission.service` | 0644 |
| `packaging/org.jenn.r16.minimal-human-trust.identity-admission.policy` | `/usr/share/polkit-1/actions/org.jenn.r16.minimal-human-trust.identity-admission.policy` | 0644 |

The separate root-owned 0600 freeze file is
`/etc/minimal-human-trust/identity-admission-code.json`:

```json
{"schema":"mht.identity-admission-code-freeze.v1","sourceCommit":"EXACT_40_HEX_REVIEWED_COMMIT","files":{"/usr/lib/minimal-human-trust/authority/identity-admission.py":"EXACT_SHA256","/usr/lib/minimal-human-trust/packaging/minimal-human-trust-identity-admission":"EXACT_SHA256","/etc/systemd/system/minimal-human-trust-identity-admission.service":"EXACT_SHA256","/usr/share/polkit-1/actions/org.jenn.r16.minimal-human-trust.identity-admission.policy":"EXACT_SHA256"}}
```

Placeholders above document the schema; they are deliberately not executable
values. All four real installed hashes and protected ancestor metadata are
verified by the entry. This is separate from the existing first-trust runtime
freeze. A Python `cryptography` backend, systemd-creds with stdin/stdout support,
and an already initialized root-only `/var/lib/systemd/credential.secret` are
prerequisites. The host secret is checked through metadata only, never read by
this entry. No implicit host-key setup is allowed.

## Actual native invocation, when separately approved

The unprivileged default script invocation is `describe`, with zero effects.
Protected `preflight` only reads the code freeze, current signed source19 public
configuration, accepted delivery19, and host-key metadata. It does not decrypt
any existing credential. Protected `status` reads only this admission's public
result and encrypted output hashes.

The future person runs the fixed wrapper using `pkexec` from a real foreground
terminal. The separate polkit action uses uncached `auth_self`; the entry then
requires real Ubuntu host `jenn-System-Product-Name`, UID1000 Jenn, an active local
graphical session, and one consistent actual foreground PTY across stdin/out/err.
It does not mistake the `/dev/tty` alias (device 5:0) for the real PTY inode.

The complete challenge displays the source19 digest, accepted delivery19, four
source-code hashes through their freeze hash, credential targets, explicit
custody model, nonce, and effects. The person types the complete
`ADMIT HOST_ADMIN_CUSTODY <full challenge hash>` line. Identity is verified again
after reading the full line. Only then is a new five-minute authorization minted;
reading the description does not consume that window. There is also a separate
180-second input timeout. The permit also binds the boot ID and five minutes of
monotonic elapsed time, so a wall-clock rollback cannot extend it. No test
callback is reachable from the production CLI.

The admitted foreground process writes a durable authorization, creates only its
protected state/credential directory, records manager-reload and launch intents,
and starts only `minimal-human-trust-identity-admission.service`. The frontend
remains alive until the worker's result. The worker is intentionally not a TTY
client. It consumes the root-only authorization, checks the frontend PID/start,
the exact source freeze, current signed source19/delivery19 and fixed service
cgroup. The unit disables swap and core dumps for it and its children.

The worker first durably records a key-generation intent. Private PKCS8 DER
stays in process memory and is passed only on systemd-creds stdin. Ciphertext is
captured internally and exclusively published to:

- `/etc/credstore.encrypted/minimal-human-trust/human-approval-key.cred`
- `/etc/credstore.encrypted/minimal-human-trust/enrollment-signing-key.cred`

It decrypts only the ciphertext it just created, through stdin/stdout pipes in
the same no-swap/no-core service, to verify the resulting public key and a
nonce-bound keypair challenge. Plaintext is never passed in argv/environment,
written to a file, or sent to user stdout/journal. Python and crypto libraries
may internally copy immutable memory; this implementation does not claim perfect
zeroization. Its mutable DER buffers are cleared best-effort.

The existing Release and Issuer public keys and the two generated public keys
must all differ. The public provenance file
`/etc/minimal-human-trust/identity-key-source.json` records exact targets, public
keys, encrypted hashes and challenge proofs, explicitly labels custody, and says
`enrolled:false`. The final immutable root receipt is written last.

## Partial outcomes and remaining real validation

Every effect is bounded by the same new authorization, including the pending
file create/write and final NOREPLACE rename. Once the generation intent exists,
any interruption without a complete result is `PARTIAL_SEAL_NO_REGENERATION`.
There is no automated key regeneration, resealing, target replacement, private
key export, cleanup, service restart or rollback. An unknown manager start is
not repeated. Completed invocations support historical readback with exact
ciphertext/public-source hash checks; repeating `admit` cannot create new keys.

The future real ceremony still has to verify the installed systemd service,
host-key prerequisite, systemd-creds execution and encrypted credential mount
consumption. Isolated tests do not claim these production actions happened.
After a real custody receipt, the existing proposal/OS approval/enrollment
workflow is still necessary. This helper does not create `issuer.json`, install
trust roots, approve a proposal, sign a production Release, or switch Owner.

Run isolated tests with:

```sh
python3 -B execution/minimal-human-trust/test/identity-admission.test.py -v
```
