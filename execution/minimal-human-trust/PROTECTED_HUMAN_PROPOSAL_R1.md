# Protected exact Human proposal producer

Status: uninstalled source and isolated acceptance only. This is not Human
confirmation, enrollment, Release issuance, installation or Owner cutover.
One fixed on-demand oneshot uses the existing Release root. It adds no Owner
daemon, second Crown license or whole-account migration prerequisite. The model
remains TRUSTED_HOST_ADMIN; it cannot defend against a hostile host root.

## Exact request and ordering

Fixed root-protected input: /etc/minimal-human-trust/human-proposal-request.json.
Its only keys are schema (mht.human-proposal-request.v1), body (complete closed
mht.human-proposal.v1), policyTemplate (mht.human-pending-policy-template.v1,
existing pending policy fields minus the future signed envelope proposalHash),
and issuerStateFileHash (canonical whole old snapshot, including revision/maxNow).
The body includes the exact nonce, original issuedAt/expiresAt, Grant/Release and
action-specific target. Only enroll_human and first_cutover_handoff are accepted.
No input path, callback, clock refresh or arbitrary signing payload is exposed
through argv, stdin, environment or a network. Unsigned input grants nothing.
Canonical Ed25519 SPKI and four distinct Release/issuer/enrollment/Human keys are
required; the actual workspace device/inode must match the signed existing Grant.

Initial enrollment validates the signed actual R15/Grant, complete source freeze,
all actual candidate file bindings, exact stage-only target and protected old
snapshot. Original two UNKNOWN and all other-project closure evidence use the
exhaustive migration inspector with the signed-R15 Crown verifier. It does not
invent or require a future Human approval journal. The complete candidate must
first be placed at exact protected R17 paths under separate preparation approval;
physical presence does not activate a Release or install an Issuer.

First cutover validates the complete historical signed Stage/Enrollment, derives
the exact existing root template/whole snapshot and reads all current staged role
files. R17 body comparison uses the original approvedAt, not a refreshed clock.
Historical Stage authorization expiry is not reused as a new approval window.
Current R15/R17/Enrollment expiry remains mandatory. Every freeze file must be
bound at the same bytes by Native. Initial evidence/reviewed-manifest freshness
remains five minutes. A request whose expiry exceeds any current dependency
window is rejected, never rewritten or extended.

Independent roots and actual R15/Grant identity are checked before any dynamic
Crown import; the complete signed prior App manifest is also byte-verified.

## Fixed code and single effect

minimal-human-trust-proposal.service has no Install/WantedBy activation. Its fixed
ExecStart is the stdlib-only human-proposal-bootstrap.mjs. All 44 frozen files
are checked before signing imports, and rechecked afterwards. The only credential
is the existing Release key in this service's read-only tmpfs/ramfs systemd mount.
Unit/root/device/ownership/modes/links/bytes/canonical public identity are checked;
parsed temporary buffers are cleared. There is no plaintext or path fallback.

Separate fixed private journals for the two actions reside under
/var/lib/minimal-human-trust/human-proposals/. A canonical 0600 INTENT is fsynced
before credential access or signing, binding the complete request/source/body/
policy hashes. A single flock and namespace checks cover the full operation.
The Ed25519 proposal and all exact output identities are independently verified
before RESULT is fsynced. Neither the callback nor public receipt grants authority.

- INTENT-only is HUMAN_PROPOSAL_EFFECT_UNKNOWN: never automatically sign again.
- RESULT recovery validates the original signature and exact target and resumes
  only original bytes while original inputs and time remain valid.
- Expired/different request/nonce or missing/tampered journal blocks; never reset
  a journal, renew the window or overwrite historical Human records.

After durable RESULT, enrollment exclusively publishes human-pending.json,
human-policy.json and the exact first-trust-publication.json stage-only plan.
The last two bind the actual resulting signed envelope digest, avoiding a hash
bootstrap loop. Cutover writes only its separate first-cutover-human-* pair,
preserving original Stage approval and plan. Each file and directory is fsynced.
Existing files must be identical bytes with strict metadata; no replacement.
Partial publication resumes only from durable RESULT. Partial/corrupt files
remain a conflict; incomplete pairs fail broker admission.

All source/request/public/roots/evidence/whole snapshot/physical file bytes are
pinned at FIRST read. Later differing reads immediately refuse. Before/after
signing and each publication step, complete hashes and workspace identity are
rechecked, followed by a fresh clock after the entire readback.

## Separate real gates and validation limits

Actual keys/holder provenance and sealed credentials require Host Admin admission.
Exact code/unit/policy, independently pinned public roots, candidate files and
protected request/evidence require separate installation approval. Production
proposal endorsement itself is a separate explicit Release-key operation, not
Human approval, enrollment, R17 signing, stop or cutover. A real native Human
ceremony must still consume the exact displayed proposal; stage-only Release/
Enrollment issuance, subsequent machine gates and production installer/COMMIT
retain their separate requirements. The formal installer CLI stays blocked.
No unit is installed, enabled or started by this source change.

Isolated enrollment wiring explicitly mocks otherwise impossible-to-forge original
production recovery/Crown provenance in a child process. It does not claim actual
ledger, polkit, holder or production acceptance. Target checks, cryptography,
complete bytes, durable journals, real temporary-file/crash/lock behavior and
expiry/drift/publication failures run actual source with synthetic keys. Existing
pinned migration tests remain. No production key, root service, enrollment or
installation is used. See test/human-proposal-*.test.mjs and the preserved runtime
regression suite. CI checks these tests and both uninstalled oneshot units.
