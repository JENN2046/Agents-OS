# G3 Human confirmation candidate

This directory is uninstalled source. It does not enroll Jenn, create or change a
Grant, change a trust root, revoke production access, or authorize publication.

The optional desktop entry connects to one fixed root-owned local socket. The
socket starts one broker process; no new resident daemon is introduced. The
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
OS authentication. Existing Human identity must already have an independently
signed, installed enrollment. Keys are read only from the root systemd encrypted
credential mount, never from UI, environment, arguments, project files or chat.

The broker commits a unique proposal intent before signing, then a result. A
partial outcome retains its intent and cannot be retried. No result means no
success claim. Approved signatures remain in the root-only result journal; the
window receives only `APPROVED_NOT_APPLIED`. Nothing dispatches the signature.
The revoke artifact matches the existing issuer's exact Human proof. Grant,
trust-change and enrollment proposals produce `mht.human-reviewed-change.v1`
artifacts; they have no mutation consumer and must not be relabelled as issued
Grants, installed roots or completed enrollment.

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
