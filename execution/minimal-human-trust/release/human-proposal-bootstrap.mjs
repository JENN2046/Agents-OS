// Fixed stdlib-only entry. Full freeze checks precede all signing imports.
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
const ROOT='/usr/lib/minimal-human-trust',FREEZE='/etc/minimal-human-trust/first-trust-code.json';
const UNIT='minimal-human-trust-proposal.service';
const need=x=>{if(!x)throw Error('HUMAN_PROPOSAL_BOOTSTRAP_REFUSED');};
const sha=b=>createHash('sha256').update(b).digest('hex');
// The exact complete set is the publisher freeze plus this entry's closure.
export const HUMAN_PROPOSAL_REQUIRED_FILES=Object.freeze([
 'release/human-proposal-bootstrap.mjs','release/human-proposal-once.mjs',
 'release/human-proposal-inputs.mjs','release/human-proposal-credential.mjs',
 'release/human-proposal-transaction.mjs','packaging/minimal-human-trust-proposal.service',
 'release/publisher-bootstrap.mjs','release/publisher-once.mjs','release/publisher-credential.mjs',
 'release/publisher-transaction.mjs','release/publisher-inputs.mjs',
 'release/first-trust-release-builder.mjs','release/first-trust-recovery-admission.mjs',
 'release/recovery-handoff-builder.mjs','release/stage-installer-reviewed.mjs','release/cutover-transaction.mjs',
 'migration/r17-one-time-recovery-admission.mjs',
 'human/first-trust-journal.mjs','human/approval-policy.mjs','human/approval-signer.mjs',
 'human/approval-broker.py','human/approval-window.py','human/approval-bootstrap.mjs','human/first-cutover-admission.mjs',
 'packaging/minimal-human-trust-approval.socket','packaging/minimal-human-trust-approval@.service',
 'packaging/minimal-human-trust-approval.desktop','packaging/minimal-human-trust-first-cutover.desktop',
 'packaging/org.jenn.r16.minimal-human-trust.policy','packaging/minimal-human-trust-publisher.service',
 'authority/stage-authorization.mjs','authority/source-baseline.mjs','authority/recovery-handoff.mjs','authority/first-cutover-authorization.mjs',
 'release/staged-r17-handoff-admission.mjs','release/single-writer-handoff-preflight.mjs',
 'src/lease-core.mjs','src/control-clock.mjs','src/minimal-trust-issuer-once.mjs',
 'src/systemd-issuer-credential.mjs','src/minimal-trust-issuer.mjs','src/signed-business-stop.mjs',
 'src/trusted-launcher.mjs','src/cloud-delivery-projector.mjs','authority/runtime-manifest.mjs',
]);
export function readProposalProtectedFile(filename,max=64*1024*1024){
 need(path.isAbsolute(filename)&&path.normalize(filename)===filename);
 let current='/';
 for(const part of path.dirname(filename).split('/').filter(Boolean)){
   current=path.join(current,part);const s=fs.lstatSync(current);
   need(s.isDirectory()&&!s.isSymbolicLink()&&s.uid===0&&!(s.mode&0o022));
 }
 const fd=fs.openSync(filename,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);
 try{
   const s=fs.fstatSync(fd);need(s.isFile()&&s.uid===0&&s.nlink===1&&!(s.mode&0o7022)&&s.size>0&&s.size<=max);
   const bytes=fs.readFileSync(fd),after=fs.fstatSync(fd);
   need(bytes.length===s.size&&s.dev===after.dev&&s.ino===after.ino&&s.size===after.size&&
     s.mtimeMs===after.mtimeMs&&s.ctimeMs===after.ctimeMs);return bytes;
 }finally{fs.closeSync(fd);}
}
export function checkHumanProposalFreeze({manifest,read=readProposalProtectedFile}={}){
 need(manifest&&Object.getPrototypeOf(manifest)===Object.prototype&&
   Object.keys(manifest).sort().join(',')==='files,schema,sourceCommit'&&
   manifest.schema==='mht.first-trust-code-freeze.v1'&&/^[a-f0-9]{40}$/.test(manifest.sourceCommit??'')&&
   manifest.files&&Object.getPrototypeOf(manifest.files)===Object.prototype&&
   Object.keys(manifest.files).length===HUMAN_PROPOSAL_REQUIRED_FILES.length&&
   HUMAN_PROPOSAL_REQUIRED_FILES.every(n=>Object.hasOwn(manifest.files,n)));
 for(const n of HUMAN_PROPOSAL_REQUIRED_FILES)need(/^[a-f0-9]{64}$/.test(manifest.files[n])&&sha(read(ROOT+'/'+n))===manifest.files[n]);
 return {sourceCommit:manifest.sourceCommit,filesChecked:HUMAN_PROPOSAL_REQUIRED_FILES.length};
}
export async function runHumanProposalBootstrap({euid=process.geteuid(),argv=process.argv,
 cgroup=()=>fs.readFileSync('/proc/self/cgroup','utf8'),read=readProposalProtectedFile,
 load=()=>import(pathToFileURL(ROOT+'/release/human-proposal-once.mjs').href)}={}){
 need(euid===0&&Array.isArray(argv)&&argv.length===2);
 const cg=cgroup();need(typeof cg==='string'&&cg.length<=8192);
 const rows=cg.trim().split('\n').map(r=>r.split(':'));
 need(rows.length>0&&rows.every(r=>r.length===3));
 const unified=rows.filter(r=>r[0]==='0'&&r[1]==='');
 need(unified.length===1&&unified[0][2]==='/system.slice/'+UNIT);
 const raw=read(FREEZE),manifest=JSON.parse(raw);checkHumanProposalFreeze({manifest,read});
 const loaded=await load();need(typeof loaded.runHumanProposalOnce==='function');
 need(sha(read(FREEZE))===sha(raw));checkHumanProposalFreeze({manifest,read});
 return loaded.runHumanProposalOnce({frozenManifest:manifest,frozenRawDigest:sha(raw)});
}
if(process.argv[1]===fileURLToPath(import.meta.url))try{
 const result=await runHumanProposalBootstrap();process.stdout.write(JSON.stringify(result)+'\n');
}catch{process.stdout.write('{"status":"HUMAN_PROPOSAL_BLOCKED"}\n');process.exitCode=1;}
