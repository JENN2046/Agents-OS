// Root, on-demand broker child only. Fixed paths and one bounded request;
// no installation, enrollment mutation, arbitrary path, or command execution.
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import {createPrivateKey} from 'node:crypto';
import {protectedRuntimeFile} from '../authority/runtime-manifest.mjs';
import {verified,exportPublicKey,signed} from '../src/lease-core.mjs';
import {readBoundedOnceInput} from '../src/minimal-trust-issuer-once.mjs';
import {validateHumanProposal,humanApprovalBody,firstTrustReviewedIntent,PROJECTS_ROOT} from './approval-policy.mjs';
const BASE='/etc/minimal-human-trust/';
const reject=()=>{throw Error('HUMAN_SIGNER_REFUSED');};
function load(){
 const proposal=JSON.parse(protectedRuntimeFile(BASE+'human-pending.json'));
 const policy=JSON.parse(protectedRuntimeFile(BASE+'human-policy.json'));
 const roots=JSON.parse(protectedRuntimeFile(BASE+'trust-roots.json'));
 const checked=validateHumanProposal({proposal,policy,roots});
 let current='';
 for(const part of PROJECTS_ROOT.split('/').filter(Boolean)){
   current+='/'+part;const st=fs.lstatSync(current);
   if(st.isSymbolicLink()||!st.isDirectory())reject();
 }
 const scope=fs.statSync(PROJECTS_ROOT);
 if(fs.realpathSync(PROJECTS_ROOT)!==PROJECTS_ROOT||scope.dev!==policy.workspaceDev||scope.ino!==policy.workspaceIno)reject();
 return {checked,policy,roots};
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

if(process.argv[1]===fileURLToPath(import.meta.url))try{
 if(process.geteuid()!==0||process.argv.length!==2)reject();
 const input=JSON.parse((await readBoundedOnceInput()).toString());
 if(!input||Object.keys(input).sort().join(',')!=='operation,proposalHash'||
   !['preview','sign'].includes(input.operation))reject();
 const {checked,policy,roots}=load();
 // Initial enrollment has no Human signing key. Only a pre-pinned
 // Release-root-signed first-use proposal may enter OS confirmation.
 // Never mint or install Human authority from this review path.
 const firstUse=checked.body.action==='enroll_human'&&!fs.existsSync(BASE+'issuer.json');
 if(!firstUse){
 // Enrollment is independently signed and installed. UID or polkit alone
 // must never make a caller-provided public key into Human Authority.
 const installed=JSON.parse(protectedRuntimeFile(BASE+'issuer.json'));
 const enrolled=verified(installed.enrollment,roots.enrollmentAuthorityPublicKey,'mht.human-enrollment.v1');
 if(Object.keys(enrolled).sort().join(',')!=='enrolledAt,expiresAt,grantHash,grantId,humanPublicKey,humanSubject,humanUid,releaseHash,releaseId,schema'||
   !Number.isSafeInteger(enrolled.enrolledAt)||!Number.isSafeInteger(enrolled.expiresAt)||
   enrolled.enrolledAt>Date.now()||enrolled.expiresAt<=enrolled.enrolledAt||enrolled.releaseId!==policy.releaseId||
   enrolled.humanUid!==1000||enrolled.humanSubject!=='local-human:1000'||
   enrolled.humanPublicKey!==policy.humanPublicKey||enrolled.grantId!==policy.grantId||
   enrolled.grantHash!==policy.grantHash||enrolled.releaseHash!==policy.releaseHash)reject();
 if(checked.body.action!=='revoke_grant'&&Date.now()>=enrolled.expiresAt)reject();
 }
 if(input.operation==='preview'){
   if(input.proposalHash!==null)reject();
   process.stdout.write(JSON.stringify({ok:true,proposalHash:checked.proposalHash,summary:checked.summary})+'\n');
 }else{
   if(input.proposalHash!==checked.proposalHash)reject();
   if(firstUse){
    // Root broker journals this unsigned record only AFTER fresh polkit.
    // A protected publisher must verify the durable OS confirmation before
    // any enrollment or R17 signing. This signer never self-enrolls.
    const reviewedIntent=firstTrustReviewedIntent(checked);
    process.stdout.write(JSON.stringify({ok:true,status:'APPROVED_NOT_APPLIED',
      firstTrustOsConfirmationOnly:true,proposalHash:checked.proposalHash,
      reviewedIntent,approval:null})+'\n');
   }else{
    const result=signed(humanApprovalBody(checked),credentialKey(policy.humanPublicKey));
    process.stdout.write(JSON.stringify({ok:true,status:'APPROVED_NOT_APPLIED',approval:result})+'\n');
   }
 }
}catch{process.stdout.write('{"ok":false,"error":"HUMAN_SIGNER_REFUSED"}\n');process.exitCode=1;}
