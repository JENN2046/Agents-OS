import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {canonical,digest} from '../src/lease-core.mjs';
import {publishHumanProposalFiles,humanProposalOutputFiles} from '../release/human-proposal-once.mjs';
import {mappedProposalIO} from './fixtures/human-proposal-fixture.mjs';
function fixture(t,action='enroll_human'){
 const directory=fs.mkdtempSync(path.join(os.tmpdir(),'proposal-pending-synthetic-'));fs.chmodSync(directory,0o700);
 t.after(()=>fs.rmSync(directory,{recursive:true,force:true}));
 const mapping=mappedProposalIO(directory);
 const artifacts={action,proposal:{synthetic:'signed'},policy:{synthetic:'pinned'},publicationPlan:action==='enroll_human'?{synthetic:'stage-only'}:null};
 const publish=extra=>publishHumanProposalFiles({artifacts,uid:process.geteuid(),...mapping,...extra});
 return {directory,mapping,artifacts,publish};
}
test('actual fixed publication is durable and identical-byte retry never overwrites',t=>{
 const f=fixture(t);f.publish();
 const names=fs.readdirSync(f.directory).sort();assert.deepEqual(names,['first-trust-publication.json','human-pending.json','human-policy.json']);
 const before=names.map(n=>[n,fs.statSync(path.join(f.directory,n)).ino,fs.readFileSync(path.join(f.directory,n))]);f.publish();
 for(const [n,ino,b]of before){assert.equal(fs.statSync(path.join(f.directory,n)).ino,ino);assert.deepEqual(fs.readFileSync(path.join(f.directory,n)),b);}
});
test('first-cutover fixed lane preserves original stage pending and publication plan',t=>{
 const f=fixture(t,'first_cutover_handoff');f.publish();
 assert.deepEqual(fs.readdirSync(f.directory).sort(),['first-cutover-human-pending.json','first-cutover-human-policy.json']);
 assert.equal(humanProposalOutputFiles(f.artifacts).length,2);
});
test('partial publication resumes only exact durable bytes after a crash',t=>{
 const f=fixture(t);let n=0;
 assert.throws(()=>f.publish({guard:()=>{if(++n===3)throw Error('crash');}}));
 const file=f.mapping.map('/etc/minimal-human-trust/human-pending.json'),ino=fs.statSync(file).ino;
 f.publish();assert.equal(fs.statSync(file).ino,ino);assert.equal(fs.readdirSync(f.directory).length,3);
});
test('modified or truncated pending files refuse without replacement or new policy',t=>{
 for(const bytes of [Buffer.from('partial'),Buffer.from(canonical({changed:true}))]){
   const f=fixture(t),p=f.mapping.map('/etc/minimal-human-trust/human-pending.json');fs.writeFileSync(p,bytes,{mode:0o600});
   assert.throws(()=>f.publish(),{code:'HUMAN_PROPOSAL_OUTPUT_CONFLICT'});assert.deepEqual(fs.readFileSync(p),bytes);
   assert.equal(fs.readdirSync(f.directory).length,1);
 }
});
test('symlink, hardlink and weak modes cannot become protected output',t=>{
 for(const variant of ['symlink','hardlink','mode']){
   const f=fixture(t),p=f.mapping.map('/etc/minimal-human-trust/human-pending.json');
   const other=path.join(f.directory,'other');fs.writeFileSync(other,canonical(f.artifacts.proposal),{mode:0o600});
   if(variant==='symlink')fs.symlinkSync(other,p);
   else if(variant==='hardlink')fs.linkSync(other,p);
   else{fs.writeFileSync(p,canonical(f.artifacts.proposal),{mode:0o644});fs.chmodSync(p,0o644);}
   assert.throws(()=>f.publish());assert.equal(fs.existsSync(path.join(f.directory,'human-policy.json')),false);
 }
});
test('expired or changed guard never writes any pending target',t=>{
 const f=fixture(t);assert.throws(()=>f.publish({guard:()=>{throw Error('expired');}}));assert.equal(fs.readdirSync(f.directory).length,0);
});
test('arbitrary action or cross-lane stageplan is refused',t=>{
 const f=fixture(t);assert.throws(()=>humanProposalOutputFiles({...f.artifacts,action:'change_trust'}));
 assert.throws(()=>humanProposalOutputFiles({...f.artifacts,action:'first_cutover_handoff'}));
});
test('publication fsyncs each file before its directory and following guard',t=>{
 const f=fixture(t),events=[];
 const io={...f.mapping.io,fsyncSync:fd=>{events.push('fileSync');fs.fsyncSync(fd);}};
 f.publish({io,sync:()=>events.push('directorySync'),guard:()=>events.push('guard')});
 assert.deepEqual(events,Array.from({length:3},()=>['guard','fileSync','directorySync','guard']).flat());
});
