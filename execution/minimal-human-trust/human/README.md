# G3 Human confirmation candidate

This directory is uninstalled source. It does not enroll Jenn, create or change a
Grant, change a trust root, revoke production access, or authorize publication.

Both desktop entries connect to one fixed root-owned local socket. The exact
initial select_confirmation frame chooses standard or first_cutover; missing
frames, arbitrary paths and cross-lane actions are rejected. The socket starts
one broker process; no new resident daemon is introduced. The
broker derives peer UID and process start time from the kernel, shows a fixed
publisher-signed and independently pinned proposal, and requires both explicit
confirmation of its digest/challenge and a fresh polkit `auth_self` check for
that same local process. UID 1000 alone is not an approval. The policy has no
`*_keep` authorization and denies inactive/remote subjects. Deployment must
also verify that no installed polkit rule silently overrides this action.

Only `projects`, the existing ProjectForge action set and the `main` channel
are admitted. The scope's real path and device/inode binding are checked again
inside the signer. The protected proposal binds action, Grant, expected version,
Grant hash, exact release hash, nonce and expiry. The signer rereads it after
OS authentication. Standard signed changes require independently signed,
installed enrollment. First Native cutover instead requires the complete
verified historical stage and its signed R17 enrollment; it never selects
authority based on issuer.json existence. Keys are read only from the root systemd encrypted
credential mount, never from UI, environment, arguments, project files or chat.

The broker commits a unique proposal intent before signing, then a result. A
partial outcome retains its intent and cannot be retried. No result means no
success claim. Approved signatures remain in the root-only result journal; the
window receives only `APPROVED_NOT_APPLIED`. Nothing dispatches the signature.
The revoke artifact matches the existing issuer's exact Human proof. Grant,
trust-change and enrollment proposals produce `mht.human-reviewed-change.v1`
artifacts; they have no mutation consumer and must not be relabelled as issued
Grants, installed roots or completed enrollment.

The separately typed first_cutover_handoff produces a
mht.first-cutover-authorization.v1 artifact only after fresh OS intent, complete
source/installer freeze and stage identity validation. Its independent pending
files preserve original Stage Human journals. It binds the complete proposal,
nonce and existing short expiry; the reviewed new-root template lacks only the
future handoffHash. Final read-only admission requires post-Human control
delivery/STOP/handoff, actual fenced writer and the exact snapshot/completed
roots, and binds those hashes into the isolated publication transaction.

The broker invokes the fixed stdlib-only approval-bootstrap.mjs. Root/unit and
source freeze checks precede dynamic signer import or credential access. The
window's --first-cutover route shows temporary business stop, old-writer fencing,
recovery-only handoff, public SPKI fingerprints, preserved UNKNOWNs and rollback
limits. The formatter tests do not run Tk, polkit or a real ceremony.

## Required before a real user confirmation

- A reviewed signed release must include this complete source and all dependency
  files, plus fixed launcher provenance. Root-owned paths alone are not a release
  endorsement.
- The independently provisioned enrollment root, real Human public key and signed
  enrollment must be installed through the trusted publication process. There is
  deliberately no self-enrollment fallback and no generated production root.
- The encrypted `human-approval-key` credential must match the enrolled public
  key. Its absence must block startup; no plaintext fallback is allowed.
- A separate protected pending policy must pin a concrete publisher-signed
  proposal, current Grant/release identity and real workspace device/inode.
- The action-specific polkit rule and fixed socket/service require review and
  installation approval. They have not been installed by the tests.
- Production handoff and any eventual application of the signed result still
  require their actual close evidence and applicable release admission.

Until these conditions hold, the honest state is blocked before Human enrollment
or production activation. The source tests validate isolated policy/protocol
behavior; they do not establish a real polkit authentication, Human presence,
credential provisioning, enrollment or production authorization.
