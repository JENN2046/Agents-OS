# R17_SOURCE19_REBASE_AND_FIRST_TRUST_PREAUTH_R1

This task rebuilds an unsigned, isolated R17 candidate from the actually installed
R15 repair, signed configuration 19. It does not sign, enroll, install, stop a
service, select a release or retire the existing Owner.

The source release is `r16-daily-20261015-r15-app-recovery-r6`. Its public
configuration canonical digest is
`56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec`.
`authority/source-baseline.mjs` fixes the exact release, Grant and App/Bridge/Native
versions. The old source lane remains available for historical protocol tests;
it cannot substitute old App/Native versions into the repaired source19 lane.
The two original UNKNOWN identities and operation hashes remain hard-pinned.

`tools/source19-rebase/build_unsigned.py` verifies the full installed repaired
payload and the actual static Bridge manifest, then overlays the exact clean Git
source. App shutdown and Native recovery repairs are explicitly checked before
construction. The tool recomputes role manifests, physical file inventory and
all role bindings. `verify_unsigned.py` independently checks those outputs and
rejects tampering, missing or extra files. Neither tool imports a signer.

Run the builder and verifier with `--help` for their explicit local inputs.
Candidates have no issuedAt, expiry, nonce, signature or authority. Historical
R17 role counts and old recovery plans are not build inputs.

`tools/source19-preauth.py` creates two separate review objects from the verified
candidate and fresh task evidence. The first binds every proposed new protected
code path, byte digest, ownership and mode. It permits only exclusive placement
of new code after a separate real native administrator approval. It permits no
credential changes, daemon reload, service actions, signing, enrollment, selector
changes, Owner handoff or business operation. It is a review descriptor, not an
installed native executor. The second lists real key/holder and ceremony gaps in
a non-signable schema; absent Human or Enrollment keys are never filled with
fixtures. No chat confirmation is treated as a native authentication result.

The version inventory distinguishes verified signed records from historical
reservations. The observed accepted and signed revision is 19. The old R12 plan
reserved 20 only for its own rollback. Conservatively skipping that historical
number gives unsigned planning revisions 21/22, derived from
`max(accepted, observed signed, historical reserved) + 1/+2`. These numbers are
not allocations, signatures or execution authority. A future admitted delivery
path must support the new exact plan; its automatic `+1` behavior is not proof
of revision 21. Fresh native approval must re-read the signed state and fixed
inventory, refuse drift, and create its own nonce/window. No old deadline is
renewed, inherited or rewritten.

The trust order is: reviewed protected code and candidate placement; real Human
and independent Enrollment key/source admission; existing Release root endorsed
pending proposal; real foreground local `auth_self` and durable OS receipt;
one-shot staged Release/Enrollment signatures; then a separate first-cutover
proposal, real consent and actual single-writer/three-role/snapshot admission.
Initial enrollment's OS confirmation remains `APPROVED_NOT_APPLIED` with
`approval:null`; it does not invent a prior Human journal or require a new Owner
service. The formal production installer remains gated. R17 activation and
business acceptance require subsequent evidence.
