// Child integration explicitly mocks ONLY the impossible-to-forge historical
// migration/Crown fixture provenance. Root entry, target, Ed25519, complete
// bytes, journal, publication and clock guards execute real source code.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {mock} from 'node:test';
import {generateKeyPairSync} from 'node:crypto';
import {digest,verified,signed} from '../../src/lease-core.mjs';
import * as originalMigration from '../../migration/r17-one-time-recovery-admission.mjs';
import {humanProposalFixture,mappedProposalIO} from './human-proposal-fixture.mjs';
mock.module(new URL('../../migration/r17-one-time-recovery-admission.mjs',import.meta.url).href,{namedExports:{...originalMigration,
 inspectReviewedR17MigrationEvidence:(old,hash,crown)=>{
   assert.equal(old.syntheticOnly,true);assert.equal(digest(old.reviewManifest),hash);assert.equal(typeof crown,'function');
   return {status:'PENDING_TRUSTED_QUIESCENCE_AND_SIGNER',other_projects_closed:true};
 }}});
const {runHumanProposalOnce,publishHumanProposalFiles}=await import('../../release/human-proposal-once.mjs');
const {issueHumanProposalOnce}=await import('../../release/human-proposal-transaction.mjs');
const cleanups=[],t={after:f=>cleanups.push(f)};
const f=humanProposalFixture(t),mapping=mappedProposalIO(f.directory);
const tx=path.join(f.directory,'tx');fs.mkdirSync(tx,{mode:0o700});
let keys=0,imports=0,clock=f.now;
const args={frozenManifest:f.sourceFreeze,frozenRawDigest:f.frozenRawDigest,
 readProtected:f.readProtected,now:()=>clock,readWorkspaceIdentity:()=>({dev:1,ino:2}),
 euid:0,argv:['node','fixed-bootstrap'],hostname:'jenn-System-Product-Name',
 cgroup:()=> '0::/system.slice/minimal-human-trust-proposal.service',
 loadCrown:async()=>{imports++;return ()=>{throw Error('synthetic Crown not called');};},
 readKey:()=>{keys++;assert.equal(fs.existsSync(path.join(tx,'intent.json')),true);return f.releaseKey;},
 ensureAbsent:()=>{for(const n of ['human-pending.json','human-policy.json','first-trust-publication.json']){
   if(fs.existsSync(path.join(f.directory,n)))throw Object.assign(Error('existing'),{code:'HUMAN_PROPOSAL_OUTPUT_EXISTS'});
 }},
 transaction:opts=>issueHumanProposalOnce({...opts,directory:tx,uid:process.geteuid()}),
 publish:opts=>publishHumanProposalFiles({...opts,...mapping,uid:process.geteuid()})};
const scenario=process.argv[2];
try{
 if(scenario==='positive'){
   const a=await runHumanProposalOnce(args);assert.equal(a.status,'SIGNED_PROPOSAL_ONLY');assert.equal(keys,1);
   const proposal=JSON.parse(fs.readFileSync(path.join(f.directory,'human-pending.json')));
   assert.deepEqual(verified(proposal,f.roots.releasePublicKey,'mht.human-proposal.v1'),f.request.body);
   const policy=JSON.parse(fs.readFileSync(path.join(f.directory,'human-policy.json')));
   const plan=JSON.parse(fs.readFileSync(path.join(f.directory,'first-trust-publication.json')));
   assert.equal(policy.proposalHash,digest(proposal));assert.equal(plan.humanProposalHash,digest(proposal));
   for(const k of ['mayEnroll','maySignRelease','mayInstall','mayCutover'])assert.equal(a[k],false);
   const b=await runHumanProposalOnce({...args,readKey:()=>assert.fail('double-sign')});
   assert.equal(b.status,'SIGNED_PROPOSAL_ALREADY');assert.equal(a.resultHash,b.resultHash);
 }else if(scenario==='partial-publication'){
   let once=true;
   await assert.rejects(runHumanProposalOnce({...args,publish:opts=>{
     publishHumanProposalFiles({...opts,...mapping,uid:process.geteuid(),guard:()=>{
       opts.guard();if(once&&fs.existsSync(path.join(f.directory,'human-pending.json'))){once=false;throw Error('lost publication');}
     }});
   }}));
   assert.equal(keys,1);assert.equal(fs.existsSync(path.join(tx,'result.json')),true);
   const b=await runHumanProposalOnce({...args,readKey:()=>assert.fail('re-sign')});
   assert.equal(b.status,'SIGNED_PROPOSAL_ALREADY');assert.equal(fs.existsSync(path.join(f.directory,'human-policy.json')),true);
 }else if(scenario==='expired-result'){
   await runHumanProposalOnce(args);clock=f.request.body.expiresAt;
   await assert.rejects(runHumanProposalOnce({...args,readKey:()=>assert.fail('re-sign')}));assert.equal(keys,1);
 }else if(scenario==='wrong-key'){
   await assert.rejects(runHumanProposalOnce({...args,readKey:()=>{keys++;return generateKeyPairSync('ed25519').privateKey;}}));
   assert.equal(keys,1);assert.equal(fs.existsSync(path.join(tx,'intent.json')),true);assert.equal(fs.existsSync(path.join(tx,'result.json')),false);
   await assert.rejects(runHumanProposalOnce(args),{code:'HUMAN_PROPOSAL_EFFECT_UNKNOWN'});assert.equal(keys,1);
 }else if(scenario==='post-key-drift'){
   await assert.rejects(runHumanProposalOnce({...args,readKey:()=>{
     keys++;f.put('/etc/minimal-human-trust/human-proposal-request.json',{...f.request,extra:'drift'});return f.releaseKey;
   }}),{code:'HUMAN_PROPOSAL_PROTECTED_INPUT_DRIFT'});assert.equal(keys,1);assert.equal(fs.existsSync(path.join(tx,'result.json')),false);
 }else if(scenario==='protected-repeat-read-drift'){
   let n=0;
   await assert.rejects(runHumanProposalOnce({...args,readProtected:file=>{
     if(file==='/etc/minimal-human-trust/first-trust-code.json'&&++n===2)f.put(file,{...f.sourceFreeze,sourceCommit:'b'.repeat(40)});
     return f.readProtected(file);
   }}),{code:'HUMAN_PROPOSAL_PROTECTED_INPUT_DRIFT'});assert.equal(keys,0);assert.equal(fs.existsSync(path.join(tx,'intent.json')),false);
 }else if(scenario==='during-import-drift'){
   await assert.rejects(runHumanProposalOnce({...args,loadCrown:async()=>{
     f.put('/var/lib/r16-owner/issuer/state.json',{...f.wrapper,revision:5});return ()=>{};
   }}),{code:'HUMAN_PROPOSAL_PROTECTED_INPUT_DRIFT'});assert.equal(keys,0);assert.equal(fs.existsSync(path.join(tx,'intent.json')),false);
 }else if(scenario==='wrong-pub-no-import'){
   f.put('/run/r16-owner/public-config.json',{...f.pub,releasePublicKey:f.roots.issuerPublicKey});
   await assert.rejects(runHumanProposalOnce(args));assert.equal(keys,0);assert.equal(imports,0);
 }else if(scenario==='expiry-during-guard'){
   let timeCalls=0;
   await assert.rejects(runHumanProposalOnce({...args,now:()=>{timeCalls++;return clock;},readProtected:file=>{
     if(timeCalls>=3)clock=f.request.body.expiresAt;return f.readProtected(file);
   }}),{code:'HUMAN_PROPOSAL_EXPIRED'});assert.equal(keys,0);assert.equal(fs.existsSync(path.join(tx,'intent.json')),false);
 }else if(scenario==='clock-reversal'){
   let n=0;await assert.rejects(runHumanProposalOnce({...args,now:()=>++n===1?f.now:f.now-1}),{code:'HUMAN_PROPOSAL_CLOCK_DRIFT'});assert.equal(keys,0);
 }else if(scenario==='existing-output'){
   fs.writeFileSync(path.join(f.directory,'human-pending.json'),'prior',{mode:0o600});
   await assert.rejects(runHumanProposalOnce(args),{code:'HUMAN_PROPOSAL_OUTPUT_EXISTS'});assert.equal(keys,0);
   assert.equal(fs.readFileSync(path.join(f.directory,'human-pending.json'),'utf8'),'prior');
 }else if(scenario==='bad-target'){
   f.put('/etc/minimal-human-trust/human-proposal-request.json',{...f.request,body:{...f.request.body,action:'change_trust'}});
   await assert.rejects(runHumanProposalOnce(args));assert.equal(keys,0);assert.equal(imports,0);
 }else if(scenario==='workspace-drift'){
   await assert.rejects(runHumanProposalOnce({...args,readWorkspaceIdentity:()=>({dev:999,ino:2})}),{code:'HUMAN_PROPOSAL_WORKSPACE_DRIFT'});assert.equal(imports,0);assert.equal(keys,0);
 }else if(scenario==='isolated-profile'){
   f.put('/etc/minimal-human-trust/trust-roots.json',{...f.roots,installationProfile:'isolated'});
   await assert.rejects(runHumanProposalOnce(args),{code:'HUMAN_PROPOSAL_PRODUCTION_PROFILE'});assert.equal(keys,0);assert.equal(imports,0);
 }else if(scenario==='wrong-context'){
   for(const patch of [{euid:1000},{argv:['node','entry','extra']},{hostname:'wrong'},
     {cgroup:()=> '0::/user.slice/minimal-human-trust-proposal.service'}]){
     await assert.rejects(runHumanProposalOnce({...args,...patch,readProtected:()=>assert.fail('must not read')}));
   }
 }else if(scenario==='unsigned-evidence-drift'){
   f.put('/etc/minimal-human-trust/first-trust-evidence.json',{...f.evidence,existingR15Evidence:{...f.evidence.existingR15Evidence,syntheticOnly:'tampered'}});
   await assert.rejects(runHumanProposalOnce(args),{code:'HUMAN_PROPOSAL_STAGE_EVIDENCE_DRIFT'});assert.equal(keys,0);
 }else if(scenario==='dependency-window'){
   f.request.body.target.enrollmentExpiresAt=f.now+1000;f.put('/etc/minimal-human-trust/human-proposal-request.json',f.request);
   await assert.rejects(runHumanProposalOnce(args),{code:'HUMAN_PROPOSAL_DEPENDENCY_WINDOW'});assert.equal(keys,0);
 }else if(scenario==='physical-drift'){
   f.put('/opt/r16/releases/r16-daily-20261012-r17/app/main.mjs',Buffer.from('tampered'));
   await assert.rejects(runHumanProposalOnce(args),{code:'FIRST_TRUST_FILE_DRIFT'});assert.equal(keys,0);
 }else throw Error('unknown fixture scenario');
 console.log('PASS_SYNTHETIC_ONLY '+scenario);
}finally{for(const f of cleanups.reverse())f();}
