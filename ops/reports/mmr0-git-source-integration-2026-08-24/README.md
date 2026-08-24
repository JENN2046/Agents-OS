# MMR-0 Git source integration validation

Result: **PASS — ready for pull-request review, not authorized for merge or deployment.**

This package closes G0–G7 of the reviewed source-integration plan against frozen remote base `cf23960396a3e7a079f614208fcce152c4b29c0f`.

## Bound lineage

- Source commit: `505ff1b6592bdf3adbe1bb30dc40750aa3e69210`
- Build/integrity commit: `bc398ed5c75d4ca5ba76be24cac700dd3b804fd4`
- Final 109-path source-manifest SHA-256: `43d27272965554e782f47b4814e6746fada349edfd9c14a33b43841b03201efa`
- Native binary SHA-256: `9afe3aeecf844a54a75559e88b8bfdb4a069cf8e9c9937f3942b12f7ae3075bf`
- Companion integrity SHA-256: `32c30b42307a5c01df4424e299764fa6b52717aa5dd6d3453086c8ebd06e2d52`

## Validation result

- Rust regression: 223/223 PASS, 0 failed, 0 ignored.
- Node regression: 80/80 PASS, 0 failed, 0 skipped.
- Companion integration: 2/2 PASS.
- 60-second companion stability: 2/2 PASS.
- Projection preflight, systemd template, and host-presentation source binding: PASS.
- Durable A7-V7: `/dev/nvme0n1` → `/media/jenn/work` → `/dev/sda1` → `/dev/sda`; independent failure domain, exact read-back PASS, CPK-FI-7 query result `PROTECTED`, duplicate effect count 0.
- Fresh B11 targeted revalidation: 5/5 PASS.
- Pinned R3 implementation-receipt validator: `PASS_IMPLEMENTATION_RECEIPT_VALIDATION`, derived phase result `PASS`, derived case count 5, derived next gate `GATE_P5_COMPLETE`.
- Controlled Proof claimed: false.

The machine-readable details and exact hashes are in `Integration_Validation_Summary.json`, `Source_to_Binary_Receipt.json`, and the P5-E receipt/evidence/validator files in this directory.

## Review limitations

- This package is targeted development evidence and receipt validation, not MMR Controlled Proof.
- The companion integration test depends on `tests/fixtures/host-adapter-runner.cjs`, which is absent from frozen remote `main` and outside the authorized 109-path source set. Validation used the exact existing working-copy fixture (`57c12fd…`) as a temporary uncommitted file; it was removed afterward. This baseline gap should be reviewed independently and was not silently added to this PR.
- The frozen authoritative Rust sources are not `rustfmt --check` clean. Exact source hashes were preserved; `git diff --check` passes.
- `npm ci` reported one high-severity dependency advisory. No dependency rewrite or audit fix was authorized.
- No merge, deployment, service restart, cutover, P6, or P7 work was performed.
