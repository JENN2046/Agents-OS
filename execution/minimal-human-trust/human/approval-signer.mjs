// Root, on-demand broker child only. Fixed paths and one bounded request;
// no installation, enrollment mutation, arbitrary path, or command execution.
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import {createPrivateKey} from 'node:crypto';
import {protectedRuntimeFile} from '../authority/runtime-manifest.mjs';
import {verified,exportPublicKey,signed} from '../src/lease-core.mjs';
import {readBoundedOnceInput} from '../src/minimal-trust-issuer-once.mjs';
import {validateHumanProposal,humanApprovalBody,firstTrustReviewedIntent,PROJECTS_ROOT} from './approval-policy.mjs';
import {digest} from '../src/lease-core.mjs';
import {FIRST_CUTOVER_PENDING,FIRST_CUTOVER_POLICY,inspectFirstCutoverInputs,inspectFirstCutoverSigningIntent} from './first-cutover-admission.mjs';
const BASE='/etc/minimal-human-trust/';
const reject=()=>{throw Error('HUMAN_SIGNER_REFUSED');};
function workspaceIdentity(){
 let current='';
 for(const part of PROJECTS_ROOT.split('/').filter(Boolean)){
   current+='/'+part;const st=fs.lstatSync(current);
   if(st.isSymbolicLink()||!st.isDirectory())reject();
 }
 const scope=fs.statSync(PROJECTS_ROOT);
 if(fs.realpathSync(PROJECTS_ROOT)!==PROJECTS_ROOT)reject();
 return {dev:scope.dev,ino:scope.ino};
}
export function approvalUnit(cgroup){
 if(typeof cgroup!=='string'||cgroup.length>8192)reject();
 const rows=cgroup.trim().split('\n').map(line=>line.split(':'));
 if(!rows.length||rows.some(row=>row.length!==3))reject();
 const unified=rows.filter(row=>row[0]==='0'&&row[1]==='');
 if(unified.length!==1)reject();
 const parts=unified[0][2].split('/'),unit=parts.at(-1);
 if(!/^minimal-human-trust-approval@[a-zA-Z0-9_-]{1,96}\.service$/.test(unit??''))reject();
 const template='system-minimal\\x2dhuman\\x2dtrust\\x2dapproval.slice';
 if(JSON.stringify(parts)!==JSON.stringify(['','system.slice',unit])&&
   JSON.stringify(parts)!==JSON.stringify(['','system.slice',template,unit]))reject();
 return unit;
}
export function verifiedCredentialBytes({io=fs,euid=process.geteuid()}={}){
 if(euid!==0)reject();
 const unit=approvalUnit(io.readFileSync('/proc/self/cgroup','utf8'));
 const directory='/run/credentials/'+unit;
 const mountinfo=io.readFileSync('/proc/self/mountinfo','utf8');
 if(typeof mountinfo!=='string'||mountinfo.length>4*1024*1024)reject();
 const mounts=mountinfo.trim().split('\n').map(s=>s.split(' '));
 const found=mounts.filter(s=>s[4]===directory),separator=found[0]?.indexOf('-');
 if(found.length!==1||separator<=5||!found[0][5].split(',').includes('ro')||
   !['tmpfs','ramfs'].includes(found[0][separator+1]))reject();
 let directoryStat;
 for(const p of ['/run','/run/credentials',directory]){
   const st=io.lstatSync(p);if(!st.isDirectory()||st.isSymbolicLink()||st.uid!==0||(st.mode&0o022))reject();
   directoryStat=st;
 }
 const fd=io.openSync(directory+'/human-approval-key',fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);
 try{
   const st=io.fstatSync(fd);
   if(!st.isFile()||st.uid!==0||st.nlink!==1||![0o400,0o440].includes(st.mode&0o7777)||
     st.dev!==directoryStat.dev||st.size<=0||st.size>4096)reject();
   const bytes=io.readFileSync(fd);
   if(!Buffer.isBuffer(bytes)||bytes.length!==st.size)reject();
   return bytes;
 }finally{io.closeSync(fd);}
}
function credentialKey(expected){
 const bytes=verifiedCredentialBytes();
 try{const key=createPrivateKey({key:bytes,type:'pkcs8',format:'der'});
   if(exportPublicKey(key)!==expected)reject();return key;
 }finally{bytes.fill(0);}
}

export const readApprovalInput=async()=>JSON.parse((await readBoundedOnceInput()).toString());

export function runHumanApprovalOperation({input,readProtected=protectedRuntimeFile,
 now=Date.now,loadHumanKey=credentialKey,readWorkspaceIdentity=workspaceIdentity,
 euid=process.geteuid()}={}){
 if(euid!==0||!input||Object.keys(input).sort().join(',')!=='operation,proposalHash'||
   !['preview','sign','preview_first_cutover','sign_first_cutover'].includes(input.operation)||
   typeof now!=='function')reject();
 const cutover=input.operation.endsWith('_first_cutover'),preview=input.operation.startsWith('preview');
 const read=file=>JSON.parse(readProtected(file).toString());
 const load=()=>{
   const proposal=read(cutover?FIRST_CUTOVER_PENDING:BASE+'human-pending.json');
   const policy=read(cutover?FIRST_CUTOVER_POLICY:BASE+'human-policy.json');
   const roots=read(BASE+'trust-roots.json');
   const time=now(),checked=validateHumanProposal({proposal,policy,roots,now:time});
   if(cutover!==(checked.body.action==='first_cutover_handoff'))reject();
   const scope=readWorkspaceIdentity();
   if(scope.dev!==policy.workspaceDev||scope.ino!==policy.workspaceIno)reject();
   let firstUse=false;
   if(cutover){
     const priorPublicConfig=read('/run/r16-owner/public-config.json');
     const reviewManifest=read(BASE+'reviewed-installation.json');
     const inspected=inspectFirstCutoverInputs({proposal,policy,roots,priorPublicConfig,
       reviewManifest,readProtected,now:time,euid});
     if(inspected.humanPublicKey!==policy.humanPublicKey)reject();
   }else{
     // Only the separately typed enrollment action has OS-only first-use intent.
     firstUse=checked.body.action==='enroll_human'&&!fs.existsSync(BASE+'issuer.json');
     if(!firstUse){
       const installed=read(BASE+'issuer.json');
       const enrolled=verified(installed.enrollment,roots.enrollmentAuthorityPublicKey,'mht.human-enrollment.v1');
       if(Object.keys(enrolled).sort().join(',')!=='enrolledAt,expiresAt,grantHash,grantId,humanPublicKey,humanSubject,humanUid,releaseHash,releaseId,schema'||
         !Number.isSafeInteger(enrolled.enrolledAt)||!Number.isSafeInteger(enrolled.expiresAt)||
         enrolled.enrolledAt>time||enrolled.expiresAt<=enrolled.enrolledAt||enrolled.releaseId!==policy.releaseId||
         enrolled.humanUid!==1000||enrolled.humanSubject!=='local-human:1000'||
         enrolled.humanPublicKey!==policy.humanPublicKey||enrolled.grantId!==policy.grantId||
         enrolled.grantHash!==policy.grantHash||enrolled.releaseHash!==policy.releaseHash)reject();
       if(checked.body.action!=='revoke_grant'&&time>=enrolled.expiresAt)reject();
     }
   }
   return {checked,policy,roots,firstUse,time};
 };
 const current=load();
 if(preview){
   if(input.proposalHash!==null)reject();
   return {ok:true,proposalHash:current.checked.proposalHash,summary:current.checked.summary};
 }
 if(input.proposalHash!==current.checked.proposalHash)reject();
 if(current.firstUse){
   return {ok:true,status:'APPROVED_NOT_APPLIED',firstTrustOsConfirmationOnly:true,
     proposalHash:current.checked.proposalHash,reviewedIntent:firstTrustReviewedIntent(current.checked),approval:null};
 }
 const osIntent=cutover?inspectFirstCutoverSigningIntent({checked:current.checked,readProtected,now:current.time}):null;
 if(cutover){
   let recorded=false;
   try{readProtected('/var/lib/minimal-human-trust/human-approval/'+current.checked.proposalHash+'.result.json');recorded=true;}
   catch(e){if(e.code!=='ENOENT')throw e;}
   if(recorded)reject();
 }
 const again=load();
 if(again.time<current.time||digest(again.checked)!==digest(current.checked)||
   digest(again.policy)!==digest(current.policy)||digest(again.roots)!==digest(current.roots))reject();
 const key=loadHumanKey(current.policy.humanPublicKey);
 if(exportPublicKey(key)!==current.policy.humanPublicKey)reject();
 const signTime=now();if(signTime<again.time)reject();
 const result=signed(humanApprovalBody(current.checked,{now:signTime}),key);
 const after=load();
 if(after.time<signTime||digest(after.checked)!==digest(current.checked)||
   digest(after.policy)!==digest(current.policy)||digest(after.roots)!==digest(current.roots))reject();
 if(cutover&&digest(inspectFirstCutoverSigningIntent({checked:current.checked,readProtected,
   now:after.time}))!==digest(osIntent))reject();
 return {ok:true,status:'APPROVED_NOT_APPLIED',...(cutover?{proposalHash:current.checked.proposalHash}:{}),approval:result};
}

if(process.argv[1]===fileURLToPath(import.meta.url)){
 process.stdout.write('{"ok":false,"error":"HUMAN_SIGNER_REQUIRES_REVIEWED_BOOTSTRAP"}\n');process.exitCode=1;
}
