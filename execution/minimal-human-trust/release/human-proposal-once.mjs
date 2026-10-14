// Fixed protected production entry; uninstalled source until separate admin admission.
// The only private-key operation endorses one exact Human proposal, never a Release.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {canonical,digest,signed,exportPublicKey} from '../src/lease-core.mjs';
import {PROJECTS_ROOT} from '../human/approval-policy.mjs';
import {verifyInstalledManifest} from '../authority/runtime-manifest.mjs';
import {readProposalProtectedFile,checkHumanProposalFreeze} from './human-proposal-bootstrap.mjs';
import {readHumanProposalReleaseKey,HUMAN_PROPOSAL_UNIT} from './human-proposal-credential.mjs';
import {inspectHumanProposalSource,inspectHumanProposalRequest,proposalArtifacts,verifyHumanProposalArtifacts} from './human-proposal-inputs.mjs';
import {verifiedR15CrownVerifier} from './publisher-once.mjs';
import {issueHumanProposalOnce} from './human-proposal-transaction.mjs';
const BASE='/etc/minimal-human-trust/';
const FREEZE=BASE+'first-trust-code.json',REQUEST=BASE+'human-proposal-request.json';
const PUB='/run/r16-owner/public-config.json',OLD='/var/lib/r16-owner/issuer/state.json';
const TX='/var/lib/minimal-human-trust/human-proposals/';
const need=(x,c='HUMAN_PROPOSAL_ENTRY_REFUSED')=>{if(!x)throw Object.assign(Error(c),{code:c});};
const sha=b=>createHash('sha256').update(b).digest('hex');
const same=(a,b)=>canonical(a)===canonical(b);
const syncDir=directory=>{
 const fd=fs.openSync(directory,fs.constants.O_RDONLY|fs.constants.O_DIRECTORY|fs.constants.O_NOFOLLOW);
 try{fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
};
function workspaceIdentity(){
 let current='/';for(const part of PROJECTS_ROOT.split('/').filter(Boolean)){
   current=path.join(current,part);const s=fs.lstatSync(current);need(s.isDirectory()&&!s.isSymbolicLink());
 }
 const s=fs.statSync(PROJECTS_ROOT);need(fs.realpathSync(PROJECTS_ROOT)===PROJECTS_ROOT);return {dev:s.dev,ino:s.ino};
}
export function humanProposalOutputFiles(artifacts){
 need(['enroll_human','first_cutover_handoff'].includes(artifacts.action));
 if(artifacts.action==='enroll_human')return [[BASE+'human-pending.json',artifacts.proposal],
   [BASE+'human-policy.json',artifacts.policy],[BASE+'first-trust-publication.json',artifacts.publicationPlan]];
 need(artifacts.publicationPlan===null);return [[BASE+'first-cutover-human-pending.json',artifacts.proposal],
   [BASE+'first-cutover-human-policy.json',artifacts.policy]];
}
function rootParent(filename){
 let current='/';for(const part of path.dirname(filename).split('/').filter(Boolean)){
   current=path.join(current,part);const s=fs.lstatSync(current);
   need(s.isDirectory()&&!s.isSymbolicLink()&&s.uid===0&&!(s.mode&0o022),'HUMAN_PROPOSAL_OUTPUT_PARENT');
 }
}
function outputAbsent(action){
 const placeholders={action,proposal:null,policy:null,publicationPlan:null};
 for(const [filename] of humanProposalOutputFiles(placeholders)){
   rootParent(filename);
   try{fs.lstatSync(filename);need(false,'HUMAN_PROPOSAL_OUTPUT_EXISTS');}catch(e){if(e.code!=='ENOENT')throw e;}
 }
}
export function publishHumanProposalFiles({artifacts,guard=()=>{},io=fs,uid=0,
 parentCheck=rootParent,sync=syncDir}={}){
 // Injected IO only serves user-owned fixtures. Production paths are fixed above.
 for(const [filename,value] of humanProposalOutputFiles(artifacts)){
   guard();parentCheck(filename);const bytes=Buffer.from(canonical(value));
   need(bytes.length>0&&bytes.length<=8*1024*1024,'HUMAN_PROPOSAL_OUTPUT_SIZE');
   let fd,existing=false;
   try{fd=io.openSync(filename,fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_NOFOLLOW,0o600);}
   catch(e){if(e.code!=='EEXIST')throw e;existing=true;fd=io.openSync(filename,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);}
   try{
     const st=io.fstatSync(fd);need(st.isFile()&&st.uid===uid&&st.nlink===1&&(st.mode&0o7777)===0o600,
       'HUMAN_PROPOSAL_OUTPUT_UNTRUSTED');
     if(existing){
       need(st.size===bytes.length&&io.readFileSync(fd).equals(bytes),'HUMAN_PROPOSAL_OUTPUT_CONFLICT');
     }else{
       let at=0;while(at<bytes.length){const n=io.writeSync(fd,bytes,at,bytes.length-at,at);need(n>0);at+=n;}
     }
     io.fsyncSync(fd);
     const after=io.fstatSync(fd),named=io.lstatSync(filename);
     need(after.dev===st.dev&&after.ino===st.ino&&after.nlink===1&&after.size===bytes.length&&
       named.dev===st.dev&&named.ino===st.ino&&named.isFile()&&!named.isSymbolicLink()&&
       named.uid===uid&&named.nlink===1&&(named.mode&0o7777)===0o600,'HUMAN_PROPOSAL_OUTPUT_DRIFT');
   }finally{io.closeSync(fd);}
   sync(path.dirname(filename));guard();
 }
 return true;
}
export async function runHumanProposalOnce({frozenManifest,frozenRawDigest,
 readProtected=readProposalProtectedFile,now=Date.now,
 readWorkspaceIdentity=workspaceIdentity,readKey=readHumanProposalReleaseKey,
 loadCrown=verifiedR15CrownVerifier,transaction=issueHumanProposalOnce,
 publish=publishHumanProposalFiles,ensureAbsent=outputAbsent,
 euid=process.geteuid(),argv=process.argv,hostname=os.hostname(),
 cgroup=()=>fs.readFileSync('/proc/self/cgroup','utf8')}={}){
 need(euid===0&&Array.isArray(argv)&&argv.length===2&&hostname==='jenn-System-Product-Name',
   'HUMAN_PROPOSAL_NATIVE_CONTEXT');
 const cg=cgroup();need(typeof cg==='string'&&cg.length<=8192);
 const rows=cg.trim().split('\n').map(s=>s.split(':'));
 need(rows.length>0&&rows.every(r=>r.length===3));
 const unified=rows.filter(r=>r[0]==='0'&&r[1]==='');
 need(unified.length===1&&unified[0][2]==='/system.slice/'+HUMAN_PROPOSAL_UNIT,'HUMAN_PROPOSAL_NATIVE_CONTEXT');
 need(/^[a-f0-9]{64}$/.test(frozenRawDigest??''),'HUMAN_PROPOSAL_SOURCE_FREEZE');
 let last=0;const time=()=>{const t=now();need(Number.isSafeInteger(t)&&t>0&&t>=last,'HUMAN_PROPOSAL_CLOCK_DRIFT');last=t;return t;};
 const reads=new Map();
 const read=file=>{const bytes=readProtected(file);need(Buffer.isBuffer(bytes));const hash=sha(bytes);
   need(!reads.has(file)||reads.get(file)===hash,'HUMAN_PROPOSAL_PROTECTED_INPUT_DRIFT');
   if(!reads.has(file))reads.set(file,hash);return bytes;};
 const json=file=>JSON.parse(read(file));
 const sourceFreeze=json(FREEZE);need(same(sourceFreeze,frozenManifest)&&sha(read(FREEZE))===frozenRawDigest,'HUMAN_PROPOSAL_SOURCE_FREEZE');
 checkHumanProposalFreeze({manifest:sourceFreeze,read});
 const request=json(REQUEST),roots=json(BASE+'trust-roots.json'),pub=json(PUB);
 need(roots.installationProfile==='production'&&request.policyTemplate?.installationProfile==='production',
   'HUMAN_PROPOSAL_PRODUCTION_PROFILE');
 const reviewManifest=json(BASE+'reviewed-installation.json');
 const installerBytes=read(BASE+'stage-installer-reviewed.mjs'),wrapper=json(OLD);
 const evidence=request.body?.action==='enroll_human'?json(BASE+'first-trust-evidence.json'):null;
 const workspace=readWorkspaceIdentity();
 inspectHumanProposalSource({request,roots,pub,workspaceIdentity:workspace,now:time()});
 // Validate the entire signed prior App source tree before the dynamic Crown import.
 const r15='/opt/r16/releases/r16-daily-20261012-r15';
 const appManifest=json(r15+'/app-manifest.json');
 const version=verifyInstalledManifest(appManifest,r15,{role:'app',readFile:read});
 need(version===pub.release?.body?.versions?.app,'HUMAN_PROPOSAL_R15_CODE_DRIFT');
 const crown=await loadCrown({pub,readProtected:read});
 const args={request,roots,pub,reviewManifest,sourceFreeze,installerBytes,wrapper,evidence,
   readProtected:read,verifyCrownCall:crown,workspaceIdentity:workspace,now:time()};
 const inspection=inspectHumanProposalRequest(args);
 // Read collection is frozen after complete independent target/evidence inspection.
 const pinned=new Map(reads);
 const guard=()=>{
   const t=time();need(request.body.issuedAt<=t&&t<request.body.expiresAt,'HUMAN_PROPOSAL_EXPIRED');
   for(const [file,hash] of pinned)need(sha(readProtected(file))===hash,'HUMAN_PROPOSAL_PROTECTED_INPUT_DRIFT');
   need(same(readWorkspaceIdentity(),args.workspaceIdentity),'HUMAN_PROPOSAL_WORKSPACE_DRIFT');
   const end=time();need(request.body.issuedAt<=end&&end<request.body.expiresAt,'HUMAN_PROPOSAL_EXPIRED');
 };
 guard();
 const identity={schema:'mht.human-proposal-signing-intent.v1',action:request.body.action,
   requestHash:digest(request),sourceFreezeDigest:digest(sourceFreeze),proposalBodyHash:digest(request.body),
   policyTemplateHash:digest(request.policyTemplate)};
 const verifyResult=artifacts=>verifyHumanProposalArtifacts(artifacts,{inspection,request,roots,now:time()});
 return transaction({directory:TX+identity.action,identity,uid:0,guard,verifyResult,
   produce:()=>{
     guard();ensureAbsent(identity.action);
     const key=readKey({expectedReleaseKey:roots.releasePublicKey});
     need(key?.type==='private'&&key.asymmetricKeyType==='ed25519'&&exportPublicKey(key)===roots.releasePublicKey,
       'HUMAN_PROPOSAL_WRONG_RELEASE_KEY');
     guard();
     const proposal=signed(request.body,key);
     guard();return proposalArtifacts({proposal,inspection,request,roots,now:time()});
   },publish:artifacts=>publish({artifacts,guard})});
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
 process.stdout.write('{"status":"HUMAN_PROPOSAL_REQUIRES_REVIEWED_BOOTSTRAP"}\n');process.exitCode=1;
}
