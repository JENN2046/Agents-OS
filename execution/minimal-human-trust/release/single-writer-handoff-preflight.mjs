// G1-D single-writer preflight: read-only. Only the actual root-owned
// migration oneshot may call it, after signed three-role business stop.
// A signed oldWriterClosed:true claim alone is never adequate OS evidence.
import fs from 'node:fs';
import {spawnSync} from 'node:child_process';
import {canonical,digest,verified,ROLES} from '../src/lease-core.mjs';
import {protectedRuntimeFile} from '../authority/runtime-manifest.mjs';
const fail=c=>{throw Object.assign(new Error(c),{code:c});};
const need=(x,c='OWNER_WRITER_UNVERIFIED')=>{if(!x)fail(c);};
const same=(a,b)=>canonical(a)===canonical(b);
const OLD='/var/lib/r16-owner/issuer/state.json';
const NEXT='/var/lib/minimal-human-trust/issuer/state.json';

export function readLegacyOwnerUnit(run=spawnSync){
 const r=run('/usr/bin/systemctl',
   ['show','r16-owner.service','-p','ActiveState','-p','SubState','-p','MainPID','-p','UnitFileState'],
   {encoding:'utf8',timeout:5000,maxBuffer:2048,env:{PATH:'/usr/bin:/bin'},
    stdio:['ignore','pipe','ignore']});
 need(r?.status===0&&!r.signal&&!r.error&&typeof r.stdout==='string'&&
   Buffer.byteLength(r.stdout)<=2048,'OWNER_SYSTEMD_UNKNOWN');
 const rows=r.stdout.trim().split('\n').map(s=>s.split('='));
 need(rows.length===4&&rows.every(x=>x.length===2)&&
   same(rows.map(x=>x[0]).sort(),['ActiveState','MainPID','SubState','UnitFileState']),
   'OWNER_SYSTEMD_UNKNOWN');
 const x=Object.fromEntries(rows);
 need(x.ActiveState==='inactive'&&x.SubState==='dead'&&x.MainPID==='0'&&
   ['masked','masked-runtime'].includes(x.UnitFileState),'OWNER_WRITER_STILL_ACTIVE');
 return x;
}
function readSnapshot(path,readProtected=protectedRuntimeFile){
 need(path===OLD||path===NEXT,'ISSUER_PATH');
 const v=JSON.parse(readProtected(path).toString());
 need(v?.schema===1&&Number.isSafeInteger(v.revision)&&v.revision>=0&&
   Number.isSafeInteger(v.maxNow)&&v.maxNow>=0&&
   v.data?.kind==='r16.issuer.v1','ISSUER_STATE_INVALID');
 return v;
}
export function inspectSingleWriterHandoff({
 handoff,enrollmentAuthorityPublicKey,issuerPublicKey,grant,verifiedStopProofHashes,
 readUnit=readLegacyOwnerUnit,readProtected=protectedRuntimeFile,
 lockExists=p=>fs.existsSync(p),now=Date.now(),euid=process.geteuid(),
}){
 need(euid===0,'ROOT_REQUIRED');
 const g=verified(grant,issuerPublicKey,'r16.workspace.v1');
 need(g.id==='r16-projects-daily','HANDOFF_GRANT_SCOPE');
 const b=verified(handoff,enrollmentAuthorityPublicKey,'mht.issuer-handoff.v1');
 need(b.mode==='recovery_only'&&b.oldWriterClosed===true&&
   b.grantId==='r16-projects-daily'&&b.grantHash===digest(grant)&&
   typeof b.issuerSnapshotHash==='string'&&/^[a-f0-9]{64}$/.test(b.issuerSnapshotHash)&&
   Number.isSafeInteger(b.epoch)&&b.epoch>0&&
   Number.isSafeInteger(b.issuedAt)&&Number.isSafeInteger(b.expiresAt)&&
   b.issuedAt<=now&&now<b.expiresAt,'HANDOFF_EXPIRED_OR_DRIFTED');
 need(b.participantClosureHashes&&
   same(Object.keys(b.participantClosureHashes).sort(),ROLES)&&
   verifiedStopProofHashes&&same(Object.keys(verifiedStopProofHashes).sort(),ROLES)&&
   ROLES.every(role=>typeof b.participantClosureHashes[role]==='string'&&
     b.participantClosureHashes[role]===verifiedStopProofHashes[role]),
   'HANDOFF_ROLE_STOP_DRIFT');
 const noWriters=()=>need(!lockExists('/var/lib/r16-owner/issuer/.lock')&&
   !lockExists('/var/lib/minimal-human-trust/issuer/.lock'),'ISSUER_WRITER_LOCK_PRESENT');
 readUnit();noWriters();
 const first=readSnapshot(OLD,readProtected),candidate=readSnapshot(NEXT,readProtected);
 const finalOld=readSnapshot(OLD,readProtected);
 need(same(first,finalOld)&&same(first,candidate)&&
   digest(first.data)===b.issuerSnapshotHash,'ISSUER_SNAPSHOT_CHANGED');
 noWriters();readUnit();
 return Object.freeze({schema:'mht.single-writer-preflight.v1',
   status:'OLD_SERVICE_INACTIVE_MASKED_AND_SNAPSHOT_EXACT',
   epoch:b.epoch,issuerSnapshotHash:b.issuerSnapshotHash,
   signedRoleStopHashes:verifiedStopProofHashes,
   signerAuthority:false,mayStartIssuer:false,mayRetireLegacy:false,
   mayReplayUnknown:false});
}
