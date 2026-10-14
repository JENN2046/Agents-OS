// FIRST_TRUST_BOOTSTRAP_R1: fixed, root-owned code hash verifier.
// NO signing credential is loaded until all transitive source files match
// the OS-admin-approved source freeze. This is the only systemd ExecStart.
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {pathToFileURL,fileURLToPath} from 'node:url';

const ROOT='/usr/lib/minimal-human-trust';
const MANIFEST='/etc/minimal-human-trust/first-trust-code.json';
const UNIT='minimal-human-trust-publisher.service';
const fail=()=>{throw new Error('FIRST_TRUST_BOOTSTRAP_REFUSED');};
const need=x=>{if(!x)fail();};
const hash=b=>createHash('sha256').update(b).digest('hex');
export const REVIEWED_SOURCE_FILES=Object.freeze([
 'release/publisher-bootstrap.mjs',
 'release/publisher-once.mjs','release/publisher-credential.mjs',
 'release/publisher-transaction.mjs','release/publisher-inputs.mjs',
 'release/first-trust-release-builder.mjs',
 'release/first-trust-recovery-admission.mjs',
 'release/recovery-handoff-builder.mjs','release/stage-installer-reviewed.mjs',
 'release/cutover-transaction.mjs',
 'migration/r17-one-time-recovery-admission.mjs',
 'human/first-trust-journal.mjs','human/approval-policy.mjs',
 'human/approval-signer.mjs','human/approval-broker.py','human/approval-window.py',
 'packaging/minimal-human-trust-approval.socket',
 'packaging/minimal-human-trust-approval@.service',
 'packaging/minimal-human-trust-approval.desktop',
 'packaging/org.jenn.r16.minimal-human-trust.policy',
 'packaging/minimal-human-trust-publisher.service',
 'authority/stage-authorization.mjs',
 'authority/recovery-handoff.mjs',
 'release/staged-r17-handoff-admission.mjs',
 'release/single-writer-handoff-preflight.mjs',
 'src/lease-core.mjs','src/control-clock.mjs',
 'src/minimal-trust-issuer-once.mjs','src/systemd-issuer-credential.mjs',
 'src/minimal-trust-issuer.mjs','src/signed-business-stop.mjs',
 'src/trusted-launcher.mjs',
 'src/cloud-delivery-projector.mjs','authority/runtime-manifest.mjs',
]);
function rootRead(file,max=32*1024*1024){
 need(path.isAbsolute(file)&&path.normalize(file)===file);
 let parent='/';
 for(const part of path.dirname(file).split('/').filter(Boolean)){
  parent=path.join(parent,part);
  const s=fs.lstatSync(parent);
  need(s.isDirectory()&&!s.isSymbolicLink()&&s.uid===0&&!(s.mode&0o022));
 }
 const st=fs.lstatSync(file);
 need(st.isFile()&&!st.isSymbolicLink()&&st.uid===0&&st.nlink===1&&
   !(st.mode&0o022)&&st.size>0&&st.size<=max);
 const fd=fs.openSync(file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);
 try{
  const opened=fs.fstatSync(fd),raw=fs.readFileSync(fd);
  need(opened.uid===0&&opened.ino===st.ino&&opened.dev===st.dev&&raw.length===st.size);
  return raw;
 }finally{fs.closeSync(fd);}
}
function validateContext(){
 need(process.geteuid()===0&&process.argv.length===2);
 const cg=fs.readFileSync('/proc/self/cgroup','utf8').trim().split('\n');
 const found=cg.map(s=>s.split(':')).filter(p=>p.length===3&&p[0]==='0'&&p[1]==='');
 need(found.length===1&&found[0][2]==='/system.slice/'+UNIT);
}
export function checkReviewedSourceFreeze({
 manifest,read=rootRead,manifestBytes=null,
}){
 need(manifest&&Object.keys(manifest).sort().join(',')==='files,schema,sourceCommit'&&
   manifest.schema==='mht.first-trust-code-freeze.v1'&&
   typeof manifest.sourceCommit==='string'&&/^[0-9a-f]{40}$/.test(manifest.sourceCommit));
 const files=manifest.files;
 need(files&&Object.getPrototypeOf(files)===Object.prototype&&
   Object.keys(files).length===REVIEWED_SOURCE_FILES.length&&
   REVIEWED_SOURCE_FILES.every(x=>Object.hasOwn(files,x)&&/^[a-f0-9]{64}$/.test(files[x])));
 for(const rel of REVIEWED_SOURCE_FILES){
  const absolute=path.join(ROOT,rel);
  need(hash(read(absolute))===files[rel]);
 }
 return {sourceCommit:manifest.sourceCommit,filesChecked:REVIEWED_SOURCE_FILES.length};
}
export async function runBootstrap(){
 validateContext();
 const raw=rootRead(MANIFEST,65536);
 const manifest=JSON.parse(raw);
 const inspected=checkReviewedSourceFreeze({manifest});
 const module=await import(pathToFileURL(path.join(ROOT,'release/publisher-once.mjs')).href);
 need(typeof module.runPublisherOnce==='function');
 return module.runPublisherOnce({frozenManifest:manifest,
   frozenRawDigest:hash(raw)});
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
 try{
  const result=await runBootstrap();
  process.stdout.write(JSON.stringify(result)+'\n');
 }catch{
  process.stdout.write('{"status":"FIRST_TRUST_PUBLISHER_BLOCKED"}\n');
  process.exitCode=1;
 }
}
