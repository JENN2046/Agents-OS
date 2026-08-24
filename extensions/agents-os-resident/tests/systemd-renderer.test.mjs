import assert from 'node:assert/strict';
import test from 'node:test';

import { renderSystemdUnit } from '../tools/render-systemd-unit.mjs';
import {
  PREFLIGHT_CONTINUITY_EVIDENCE_JSON,
  PREFLIGHT_GENESIS_PROVISIONING_AUTHORITY_JSON
} from '../tools/validate-companion-projection.mjs';

test('projection preflight authority fixtures satisfy the exact renderer transport contract', () => {
  const rendered = renderSystemdUnit({
    continuityEvidenceJson: PREFLIGHT_CONTINUITY_EVIDENCE_JSON,
    genesisProvisioningAuthorityJson:
      PREFLIGHT_GENESIS_PROVISIONING_AUTHORITY_JSON,
    nodeBinary: '/usr/bin/node',
    pluginRoot: '/tmp/agents-os-resident-projection-test',
    activationRoot:
      '/tmp/agents-os-resident-projection-test/state/agents-os-resident-local-owner-v1',
    buildId: `sha256:${'c'.repeat(64)}`
  });

  assert.match(rendered, /--continuity-evidence/);
  assert.match(rendered, /evidence:projection-preflight/);
  assert.match(rendered, /--genesis-provisioning-authority/);
  assert.match(rendered, /authority:projection-preflight/);
});

test('systemd renderer preserves the companion isolation and independent lifetime boundary', () => {
  const rendered = renderSystemdUnit({
    continuityEvidenceJson: '{"availability":"AVAILABLE","evidenceId":"evidence:renderer","protocol":"MMR0_CONTINUITY_EVIDENCE_V1","state":"EMPTY","witnessId":"witness:renderer"}',
    genesisProvisioningAuthorityJson: '{"authorityId":"authority:renderer","protocol":"MMR0_GENESIS_PROVISIONING_V1","provisioningId":"provisioning:renderer","residentId":"resident:LOCAL_OWNER_SESSION_V1:jenn"}',
    nodeBinary: '/usr/bin/node',
    pluginRoot: '/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/Plugin/AGENTSOSResident',
    activationRoot: '/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/Plugin/AGENTSOSResident/state/agents-os-resident-local-owner-v1',
    buildId: `sha256:${'d'.repeat(64)}`
  });

  assert.match(rendered, /RestrictAddressFamilies=AF_UNIX/);
  assert.match(rendered, /IPAddressDeny=any/);
  assert.match(rendered, /RuntimeDirectoryMode=0700/);
  assert.match(rendered, /StandardOutput=null/);
  assert.match(rendered, /StandardError=null/);
  assert.match(rendered, /WantedBy=default\.target/);
  assert.match(rendered, /--continuity-evidence/);
  assert.match(rendered, /--genesis-provisioning-authority/);
  assert.doesNotMatch(rendered, /PartOf=/);
  assert.doesNotMatch(rendered, /BindsTo=/);
  assert.doesNotMatch(rendered, /MemoryDenyWriteExecute=/);
  assert.doesNotMatch(rendered, /SystemCallFilter=/);
});

test('systemd renderer rejects malformed or non-object continuity transport values', () => {
  const base = {
    nodeBinary: '/usr/bin/node',
    pluginRoot: '/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/Plugin/AGENTSOSResident',
    activationRoot: '/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/Plugin/AGENTSOSResident/state/agents-os-resident-local-owner-v1',
    buildId: `sha256:${'e'.repeat(64)}`
  };
  for (const continuityEvidenceJson of ['not-json', '[1,2]', '"string"', 'null']) {
    assert.throws(
      () => renderSystemdUnit({ ...base, continuityEvidenceJson, genesisProvisioningAuthorityJson: '{"a":1}' }),
      /SYSTEMD_RENDER_INPUT_INVALID/
    );
  }
  for (const genesisProvisioningAuthorityJson of ['not-json', '[]', '42']) {
    assert.throws(
      () => renderSystemdUnit({ ...base, continuityEvidenceJson: '{"a":1}', genesisProvisioningAuthorityJson }),
      /SYSTEMD_RENDER_INPUT_INVALID/
    );
  }
});
