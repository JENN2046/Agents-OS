import assert from 'node:assert/strict';

import {
  runIntegratedQuarantinedHostSmokeWitness,
  validateQuarantinedHostSmoke
} from '../tools/validate-quarantined-host-smoke.mjs';
import { activeOwnedQuarantineRootCount } from '../tools/prepare-quarantined-host-smoke.mjs';

const expected = {
  wp0: 'WP0_SEALED_SOURCE_AND_HOST_COMMITMENTS_VERIFIED',
  wp1: 'WP1_OWNED_QUARANTINE_TOPOLOGY_VERIFIED',
  wp2: 'WP2_BLOCKED_MANIFEST_RULE_VERIFIED',
  wp3: 'WP3_INERT_LIFECYCLE_CONTRACT_VERIFIED',
  wp4: 'WP4_CLEANUP_AND_RESIDUE_CONTRACT_VERIFIED',
  wp5: 'QUARANTINED_HOST_SMOKE_PREFLIGHT_READY'
};

for (const [stage, resultCode] of Object.entries(expected)) {
  const result = validateQuarantinedHostSmoke({ stage });
  assert.equal(result.result, resultCode, JSON.stringify(result));
  assert.equal(result.vcptoolbox_worktree_accessed, false);
  assert.equal(result.archive_delivery_performed, false);
  assert.equal(result.plugin_enabled, false);
  assert.equal(result.host_lifecycle_invoked, false);
  assert.equal(result.native_napi_invoked, false);
  assert.equal(result.runtime_usable, false);
  assert.equal(result.terminal_outcome, 'NOT_EXECUTED');
}

const witness = runIntegratedQuarantinedHostSmokeWitness();
assert.equal(witness.result, 'QUARANTINED_HOST_SMOKE_PREFLIGHT_WITNESS_PASSED', JSON.stringify(witness));
assert.equal(witness.active_owned_quarantine_roots, 0);
assert.equal(activeOwnedQuarantineRootCount(), 0);

process.stdout.write(`${JSON.stringify({
  result: 'PASS',
  test: 'quarantined_host_smoke_offline_preflight',
  stages: Object.keys(expected).length,
  witness: witness.result,
  runtime_usable: false,
  archive_delivery_performed: false,
  plugin_enabled: false,
  host_lifecycle_invoked: false,
  native_napi_invoked: false,
  terminal_outcome: 'NOT_EXECUTED'
})}\n`);
