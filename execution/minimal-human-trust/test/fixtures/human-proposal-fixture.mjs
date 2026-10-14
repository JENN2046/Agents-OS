// Synthetic authorities and logical root paths backed by user-owned memory/temps.
// Enrollment migration proof is NOT forged: integration tests explicitly mock
// that production inspector in a child process; existing pinned-proof tests remain.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {generateKeyPairSync,randomUUID,createHash} from 'node:crypto';
import {canonical,digest,signed,exportPublicKey,ACTIONS,ROLES} from '../../src/lease-core.mjs';
import {runtimeVersion} from '../../authority/runtime-manifest.mjs';
import {STAGE_CONSTRAINTS} from '../../authority/stage-authorization.mjs';
import {REVIEWED_SOURCE_FILES} from '../../release/publisher-bootstrap.mjs';
import {PROJECTS_ROOT} from '../../human/approval-policy.mjs';
export const sha=b=>createHash('sha256').update(b).digest('hex');
export function humanProposalFixture(t){
 const now=1792200000000,key=()=>generateKeyPairSync('ed25519').privateKey;
 const releaseKey=key(),issuerKey=key(),humanKey=key(),enrollmentKey=key();
 const root=fileURLToPath(new URL('../../',import.meta.url)),files=new Map();
 const put=(logical,value)=>files.set(logical,Buffer.isBuffer(value)?value:Buffer.from(JSON.stringify(value)));
 const crownPath='app/upstream/src/project-forge-crown-transport.mjs',crownBytes=Buffer.from('// synthetic Crown module; no production import');
 const appManifest={schema:'r16.runtime-code.v1',role:'app',entry:crownPath,files:{[crownPath]:sha(crownBytes)}};
 put('/opt/r16/releases/r16-daily-20261012-r15/'+crownPath,crownBytes);
 put('/opt/r16/releases/r16-daily-20261012-r15/app-manifest.json',appManifest);
 const peers=Object.fromEntries(ROLES.map(role=>[role,{id:'synthetic-'+role,publicKey:exportPublicKey(key())}]));
 const grant=signed({schema:'r16.workspace.v1',id:'r16-projects-daily',version:1,createdAt:now-86400000,
   workspace:{id:'synthetic-workspace',root:PROJECTS_ROOT,dev:1,ino:2},actions:ACTIONS,channel:'main',peers},issuerKey);
 const versions={app:runtimeVersion(appManifest,'app'),bridge:digest('synthetic-r15-bridge'),native:digest('synthetic-r15-native')};
 const release=signed({schema:'r16.release.v1',id:'r16-daily-20261012-r15',issuedAt:now-86400000,
   notAfter:now+86400000,formats:['r16.workspace.v1'],versions,actions:ACTIONS,permissionVersion:1},releaseKey);
 const roots={schema:'mht.trust-roots.v1',grantId:grant.body.id,issuerPublicKey:exportPublicKey(issuerKey),
   releasePublicKey:exportPublicKey(releaseKey),enrollmentAuthorityPublicKey:exportPublicKey(enrollmentKey),
   releaseHash:digest(release),handoffHash:digest('not-issued-handoff'),installationProfile:'production'};
 const pub={schema:'r16.runtime-configuration.v1',issuerPublicKey:roots.issuerPublicKey,
   releasePublicKey:roots.releasePublicKey,release,grant,versions,peers,channel:'main'};
 const sourceFreeze={schema:'mht.first-trust-code-freeze.v1',sourceCommit:'a'.repeat(40),files:{}};
 for(const rel of REVIEWED_SOURCE_FILES){const b=fs.readFileSync(path.join(root,rel));sourceFreeze.files[rel]=sha(b);put('/usr/lib/minimal-human-trust/'+rel,b);}
 const artifacts={},localFiles=[];
 for(const role of ROLES){
   const entry=role+'/main.mjs',b=Buffer.from('// synthetic '+role);const roleFiles={[entry]:sha(b)};
   put('/opt/r16/releases/r16-daily-20261012-r17/'+entry,b);
   if(role==='native')for(const [rel,h]of Object.entries(sourceFreeze.files)){
     roleFiles[rel]=h;put('/opt/r16/releases/r16-daily-20261012-r17/'+rel,files.get('/usr/lib/minimal-human-trust/'+rel));
   }
   artifacts[role]={schema:'r16.runtime-code.v1',role,entry,files:roleFiles};
   for(const [artifactPath,sha256]of Object.entries(roleFiles))localFiles.push({role,artifactPath,sha256,path:'/opt/r16/releases/r16-daily-20261012-r17/'+artifactPath});
 }
 const reviewManifest={schema:'r16.reviewed-installation.v1',releaseId:'r16-daily-20261012-r17',issuedAt:now-1000,notAfter:now+86400000,artifacts,localFiles};
 const installerBytes=fs.readFileSync(path.join(root,'release/stage-installer-reviewed.mjs'));
 const wrapper={schema:1,revision:4,maxNow:now-2000,data:{kind:'r16.issuer.v1',syntheticOnly:true,
   grants:[{grant,version:1,status:'ACTIVE',projects:[]}]}};
 const old={publicConfiguration:pub,reviewManifest,issuerState:wrapper.data,now:now-2000,syntheticOnly:true};
 const evidence={schema:'mht.first-trust-stage-evidence.v2',existingR15Evidence:old};
 const authorization={schema:'mht.first-trust-stage-authorization.v2',phase:'STAGE_ONLY',sourceReleaseId:release.body.id,
   targetReleaseId:reviewManifest.releaseId,grantId:grant.body.id,grantHash:digest(grant),grantVersion:1,
   r15PublicConfigDigest:digest(pub),reviewedManifestHash:digest(reviewManifest),recoveryEvidenceDigest:digest(old),
   sourceFreezeDigest:digest(sourceFreeze),installerHash:sha(installerBytes),issuerSnapshotHash:digest(wrapper.data),
   trustRootsDigest:digest(roots),stopEpoch:randomUUID(),handoffEpoch:5,issuedAt:now-1000,expiresAt:now+60000,constraints:{...STAGE_CONSTRAINTS}};
 const body={schema:'mht.human-proposal.v1',action:'enroll_human',grantId:grant.body.id,expectedVersion:1,
   expectedGrantHash:digest(grant),releaseId:release.body.id,releaseHash:digest(release),nonce:randomUUID(),
   issuedAt:authorization.issuedAt,expiresAt:authorization.expiresAt,target:{humanUid:1000,humanSubject:'local-human:1000',
     humanPublicKey:exportPublicKey(humanKey),enrollmentExpiresAt:now+86400000,targetReleaseId:reviewManifest.releaseId,
     reviewedManifestHash:digest(reviewManifest),stageAuthorizationHash:digest(authorization),stageAuthorization:authorization}};
 const policyTemplate={schema:'mht.human-pending-policy-template.v1',grantId:grant.body.id,grantHash:digest(grant),
   grantVersion:1,releaseHash:digest(release),releaseId:release.body.id,humanPublicKey:exportPublicKey(humanKey),
   workspaceId:grant.body.workspace.id,workspaceRoot:PROJECTS_ROOT,workspaceDev:1,workspaceIno:2,installationProfile:'production'};
 const request={schema:'mht.human-proposal-request.v1',body,policyTemplate,issuerStateFileHash:digest(wrapper)};
 const paths={'first-trust-code.json':sourceFreeze,'human-proposal-request.json':request,'trust-roots.json':roots,
   'reviewed-installation.json':reviewManifest,'stage-installer-reviewed.mjs':installerBytes,'first-trust-evidence.json':evidence};
 for(const [n,v]of Object.entries(paths))put('/etc/minimal-human-trust/'+n,v);
 put('/run/r16-owner/public-config.json',pub);put('/var/lib/r16-owner/issuer/state.json',wrapper);
 const reads=[];
 const readProtected=file=>{if(!files.has(file))throw Object.assign(Error('fixture missing '+file),{code:'ENOENT'});reads.push(file);return Buffer.from(files.get(file));};
 const directory=fs.mkdtempSync(path.join(os.tmpdir(),'human-proposal-synthetic-'));fs.chmodSync(directory,0o700);
 t.after(()=>fs.rmSync(directory,{recursive:true,force:true}));
 return {now,releaseKey,humanKey,roots,pub,sourceFreeze,request,wrapper,evidence,reviewManifest,installerBytes,
   files,put,reads,readProtected,directory,workspaceIdentity:{dev:1,ino:2},frozenRawDigest:sha(files.get('/etc/minimal-human-trust/first-trust-code.json'))};
}
export function mappedProposalIO(directory){
 const allowed=new Set(['human-pending.json','human-policy.json','first-trust-publication.json',
   'first-cutover-human-pending.json','first-cutover-human-policy.json']);
 const map=filename=>{
   if(!filename.startsWith('/etc/minimal-human-trust/')||!allowed.has(path.basename(filename))||filename!=='/etc/minimal-human-trust/'+path.basename(filename))throw Error('fixture bad output path');
   return path.join(directory,path.basename(filename));
 };
 return {map,io:{...fs,openSync:(p,...a)=>fs.openSync(map(p),...a),lstatSync:p=>fs.lstatSync(map(p))},
   parentCheck:p=>{map(p);},sync:()=>{const fd=fs.openSync(directory,fs.constants.O_RDONLY|fs.constants.O_DIRECTORY);try{fs.fsyncSync(fd);}finally{fs.closeSync(fd);}}};
}
