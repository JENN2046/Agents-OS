# R6 App + Native candidate adapters

This directory contains source and isolated tests for the complete R15-based App + Native candidate. The payload changes exactly App workspace-host.mjs, App app-runner.mjs and Native workspace-dispatcher.mjs. Bridge stays on its original R15 selector. Both hosts stage the complete payload with App and Native manifests before selecting it. The actual local source path is this workspace directory; the fixed cloud candidate source is /home/ubuntu/r16-maintenance-app-recovery-r6-candidate.

The original R6 first-bootstrap guard rejects a running source App with FIRST_BOOTSTRAP_OLD_APP_STOP_UNPROVEN. The target shutdown fix cannot stop an already running original R15 App. This generic installer does not implement force termination or repeated SIGTERM workarounds.

A future exact installation plan must state activationScope=START_REVIEWED_TARGET_APP_IF_SOURCE_ALREADY_STOPPED. A genuine source App stopped baseline permits starting the reviewed target App only under that scope. Abort and rollback restore the original stopped App baseline, reported as ACTUAL_FIXED_ROLES_EXPECTED_STATE rather than four running roles. No such production plan or approval is generated here.

Cloud stage compares the full selector hash to the durable pre-quiesce baseline. Commit preserves all selector fields except the exact manifest path; rollback restores the original selector and uses a higher signed revision. Phase-aware OS code pins bind the actual selected source/target App and Native bytes. The original Grant, Issuer, historical human approval, UNKNOWN business operations and leases are preserved.

## Tests

- node --test r6-portable.test.mjs: 83 portable cases; fixed public fixtures/R15_PUBLIC_CONFIG.json and synthetic keys/stores only. Imports transaction.test.mjs, r6-driver-precommit.test.mjs and r6-transport-timeout.test.mjs. No package or installed R15 source is needed.
- node --test publication.test.mjs review-r3-r15-semantics.test.mjs: 23 cases, requiring the local complete package and original signed R15 source for compatibility checks.
- node --test app-package-r6.test.mjs: 3 physical complete package/staging cases. Copies all 12592 files to isolated local temporary targets representing the two host stage operations; this is not a real dual-host install.
- python3 -I -B test_os_entry.py: 92 portable isolated OS cases. The additional 4 test_app_phase_r6.py cases require package manifests; all real subprocess effects are prohibited in OS tests.

IMPLEMENTATION_VALIDATION_R6.json binds exact implementation and tests. Source/isolated success is not production installation, current service stoppability, human identity enrollment, business readiness or actual dual-host acceptance.

The transport timeout correction is future candidate source only: remote stage waits up to 150 seconds outside the 120-second cloud helper; readback and commit remain at 30 seconds. Child ETIMEDOUT is reported as FIXED_COMMAND_TIMEOUT, which does not prove that a remote operation ended. The regression suite verifies that late stage completion cannot return a persisted ABORT to staging or signing.

The R9 transaction is already ABORTED_BEFORE_CONFIGURATION_CHANGE and must not be rerun. Its sealed source and physical package do not contain this correction. A future independently approved namespace must explicitly include and freeze the new run.mjs and io.mjs; this source change creates no new capsule or deployment. IMPLEMENTATION_VALIDATION_R6.json remains the historical validation record for its original source pins.
