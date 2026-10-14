# FIRST_TRUST_BOOTSTRAP_R1 | Protected one-shot publisher

Status: SOURCE / ISOLATED ACCEPTANCE ONLY. Not a production installation or an actual Human enrollment.

This patch remains within G1-D PR #47. One protected on-demand Release signer, the same Grant and Release root, no independent Owner service and no second Crown human license.

## Fixed code and OS identity

Systemd unit: packaging/minimal-human-trust-publisher.service, static Type=oneshot, not enabled.
ExecStart: /usr/bin/node /usr/lib/minimal-human-trust/release/publisher-bootstrap.mjs

The administrator must review a clean, exact-head source freeze built by tools/review-first-trust-source.mjs. The launcher verifies every required source file hash before loading any signing code. A user-controlled VCP request cannot set its paths, role, roots or code identity.

Two OS-sealed credentials are checked against the actual root-owned, read-only systemd credential mount:
- Existing Release root: /etc/credstore.encrypted/r16-release/release-signing-key.cred
- Independently enrolled signing root: /etc/credstore.encrypted/minimal-human-trust/enrollment-signing-key.cred

This patch does not generate or install a production private key. The Host Admin must admit the initial enrollment root, Human public key and exact package via a genuine local consent ceremony. Test fixture identities are never authority.

## Fixed root-owned input files

- /etc/minimal-human-trust/first-trust-code.json: reviewed source freeze and code fingerprints.
- /etc/minimal-human-trust/first-trust-publication.json: exact short-lived R15/R17 STAGE_ONLY transaction plan v2 and full authorization digest.
- /etc/minimal-human-trust/trust-roots.json: exact Release, issuer and enrollment public roots, pinned under trusted Host Admin.
- /etc/minimal-human-trust/reviewed-installation.json: exact R17 reviewed manifest.
- /etc/minimal-human-trust/human-pending.json and human-policy.json: exact R15 Release-root-signed first-use Human proposal.
- /var/lib/minimal-human-trust/human-approval/<proposal-hash>.intent.json and .result.json: physical local OS approval records.
- /etc/minimal-human-trust/first-trust-evidence.json: complete original source R15 participant/UNKNOWN evidence. This frozen evidence is not renewed after consent.
- /run/r16-owner/public-config.json and /var/lib/r16-owner/issuer/state.json: source of truth, read twice for drift.

Crown verification is imported ONLY from the protected and originally signed R15 App manifest: /opt/r16/releases/r16-daily-20261012-r15/app/upstream/src/project-forge-crown-transport.mjs. The exact code hash is checked before dynamic import. The two old FindSymbol UNKNOWN operation identities and hashes are fixed by migration/r17-one-time-recovery-admission.mjs and cannot be substituted.

The stage signer does not require R17 STOP proofs from installed R15. A separate
read-only staged handoff inspection requires fresh R17 three-role STOP proofs in
one review/stop epoch/cloud revision, the durable stage INTENT/RESULT, and an
actually fenced old Owner. STAGE_ONLY does not authorize that stop or installation.

## Durable exactly-once staged signing

The once-only signer uses /var/lib/minimal-human-trust/first-trust-publication/ (0700) with a single-writer flock, intent.json and result.json (0600). Both journal writes are fsynced before their dependent effect.

- Verify exact source, real OS Human confirmation, complete physical file coverage, release identity, original participant evidence, and full STAGE_ONLY constraints.
- Persist the exact intent BEFORE obtaining the private keys.
- Use the existing protected Release key for a staged R17 signature; separately sign the exact Human enrollment under the admitted independent enrollment key.
- Cryptographically verify the staged signatures before persisting the durable RESULT.
- If a successful response is lost, read back the identical result without a second sign.
- If an INTENT exists without a RESULT, return PUBLISHER_EFFECT_UNKNOWN. Never retry the signing effect automatically.

The result is SIGNED_STAGED_NOT_INSTALLED only. It does not modify Grant, clear UNKNOWN, sign a replacement issuer handoff, activate ProjectForge, alter cloud configuration, stop the Owner, or grant business capability.

## Recovery handoff candidate

The signed handoff v2 and snapshot receiver admit only the two exact old readonly
leases under recovery-only mode. Every other project must have authenticated
closure. The pure certificate builder requires the exhaustive original migration
verifier, then binds the whole persisted snapshot and a fresh observation; it
never rewrites the old journal's last-write time. Historical stage validation uses
the durable original approvedAt, with evidence collected no more than five
minutes earlier. The helper itself provides no signing or installation authority.

The cutover transaction and private /tmp rehearsal exercise durable
INTENT/ARTIFACTS/COMMIT, identical-byte crash recovery and read-only historical
COMMIT readback. The formal installer CLI is blocked pending an exact first-use
native Human cutover gate. An already installed issuer is required by generic
change_trust, so that generic flow cannot stand in for first-cutover consent.
See README.md for current boundaries. Historical evidence/review R1 files remain
immutable; this source documentation does not rebind their old acceptance.

## Remaining real-world authorization

A true Human local polkit identity confirmation and an exact root-admin-reviewed source+credential installation have not occurred. The formal R17 signed release, physical role stop evidence, actual cloud publication, and single-writer Owner handoff remain pending. Do not treat a successful test as authorization.

No changes to installed R15 services, root signing material, or the two original production UNKNOWN records are permitted by this source-only acceptance.

## Tests

Run Node test/*.test.mjs with NODE_PATH pinned to the installed VCPChat node_modules.
Run Python test/human-approval-broker.test.py with -B.
Run systemd-analyze verify against packaging/minimal-human-trust-publisher.service.
Run node --check on all published JS files and git diff --check before PR finalization.

Decision states: ISOLATED_SOURCE_PASS or BLOCKED_REAL_HUMAN_AND_ROOT_INSTALL. Never claim G1D_VERIFIED based on synthetic keys.
