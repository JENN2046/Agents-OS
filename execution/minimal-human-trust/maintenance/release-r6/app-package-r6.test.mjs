import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {FIXED,inspectPhysicalPackage,digest} from './maintenance-release-base.mjs';
import {createIsolatedPublicationHarness} from './publication.mjs';
import {stagePayload} from './local.mjs';
const inspection=inspectPhysicalPackage(),time=Date.now(),h=createIsolatedPublicationHarness({inspection,now:time});
const artifacts=h.build({approvedAt:time-100,expiresAt:time+299900,releaseNotAfter:time+86400000,freezeDigest:digest('fixture-freeze'),nonce:'isolated-r6-package'});
test('R6 binds old App source and three exact deltas to target App+Native, preserving Bridge',()=>{
 assert.notEqual(FIXED.sourceAppVersion,FIXED.targetAppVersion);assert.equal(inspection.publicConfig.versions.app,FIXED.sourceAppVersion);
 assert.equal(artifacts.releaseBody.versions.app,FIXED.targetAppVersion);assert.equal(artifacts.releaseBody.versions.native,FIXED.nativeVersion);
 for(const row of artifacts.proposalTemplate.localFiles)assert.equal(row.path,(row.role==='bridge'?FIXED.sourceDirectory:FIXED.targetDirectory)+'/'+row.artifactPath);
 const changes=Object.entries(inspection.manifests).flatMap(([role,m])=>Object.keys(m.files).filter(n=>m.files[n]!==inspection.baseManifests[role].files[n]));
 assert.deepEqual(changes.sort(),['app/app-runner.mjs','app/workspace-host.mjs','host/workspace-dispatcher.mjs']);assert.equal(inspection.payloadBytes,149502002);
});
test('R6 stages complete local and cloud role bytes with App+Native manifests and exact modes under umask0077',t=>{
 const root=fs.mkdtempSync(path.join(os.homedir(),'.r6-stage-fixture-'));t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
 const plan={capsuleHash:'a'.repeat(64)},mask=process.umask(0o077);
 try{for(const host of ['local','cloud']){
  const target=path.join(root,host,'target');const options={packageDirectory:FIXED.packageDirectory,targetDirectory:target};
  const a=stagePayload({artifacts,plan},options);assert.equal(a.uniqueFiles,12592);assert.equal(fs.statSync(target).mode&0o7777,0o755);
  for(const role of ['app','native'])assert.equal(digest(JSON.parse(fs.readFileSync(target+'/'+role+'-manifest.json'))),inspection.versions[role]);
  assert.equal(fs.readFileSync(target+'/app/app-runner.mjs','utf8'),fs.readFileSync(FIXED.packageDirectory+'/payload/app/app-runner.mjs','utf8'));
  const inventory=JSON.parse(fs.readFileSync(FIXED.packageDirectory+'/metadata/PAYLOAD_INVENTORY.json'));const executable=Object.keys(inventory).find(n=>inventory[n].mode&0o111);if(executable)assert.equal(fs.statSync(target+'/'+executable).mode&0o7777,inventory[executable].mode);else assert(Object.values(inventory).every(row=>row.mode===0o644));
  assert.deepEqual(stagePayload({artifacts,plan},options),a);
 }}finally{process.umask(mask);}
});
test('R6 staging refuses old App manifest even with an otherwise verified package before creating a target',()=>{
 assert.throws(()=>stagePayload({artifacts:{...artifacts,reviewedInstallation:{artifacts:{...inspection.manifests,app:inspection.baseManifests.app}}},plan:{}},{packageDirectory:FIXED.packageDirectory,targetDirectory:'/unused-not-created'}),{code:'STAGED_ROLE_MANIFEST_DRIFT'});
});
