// Fixed broker child. Only Node builtins load until reviewed code matches.
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
const ROOT='/usr/lib/minimal-human-trust',MANIFEST='/etc/minimal-human-trust/first-trust-code.json';
const reject=()=>{throw new Error('HUMAN_BOOTSTRAP_REFUSED');};
const need=x=>{if(!x)reject();};
const sha=b=>createHash('sha256').update(b).digest('hex');
export const APPROVAL_REQUIRED_FILES=Object.freeze([
  'human/approval-bootstrap.mjs','human/approval-signer.mjs','human/approval-policy.mjs',
  'human/approval-broker.py','human/approval-window.py','human/first-trust-journal.mjs',
  'human/first-cutover-admission.mjs','authority/first-cutover-authorization.mjs',
  'authority/runtime-manifest.mjs','authority/stage-authorization.mjs','authority/source-baseline.mjs','authority/recovery-handoff.mjs',
  'src/lease-core.mjs','src/control-clock.mjs','src/minimal-trust-issuer-once.mjs',
  'src/systemd-issuer-credential.mjs','src/minimal-trust-issuer.mjs',
  'src/signed-business-stop.mjs','src/cloud-delivery-projector.mjs',
  'migration/r17-one-time-recovery-admission.mjs','release/publisher-bootstrap.mjs',
  'release/staged-r17-handoff-admission.mjs','release/single-writer-handoff-preflight.mjs',
  'packaging/minimal-human-trust-approval@.service','packaging/minimal-human-trust-approval.socket',
  'packaging/minimal-human-trust-approval.desktop','packaging/minimal-human-trust-first-cutover.desktop',
  'packaging/org.jenn.r16.minimal-human-trust.policy',
]);
function rootRead(file,max=32*1024*1024){
  need(path.isAbsolute(file)&&path.normalize(file)===file);
  let current='/';
  for(const part of path.dirname(file).split('/').filter(Boolean)){
    current=path.join(current,part);const s=fs.lstatSync(current);
    need(s.isDirectory()&&!s.isSymbolicLink()&&s.uid===0&&!(s.mode&0o022));
  }
  const fd=fs.openSync(file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);
  try{
    const s=fs.fstatSync(fd);need(s.isFile()&&s.uid===0&&s.nlink===1&&!(s.mode&0o7022)&&s.size>0&&s.size<=max);
    const raw=fs.readFileSync(fd),after=fs.fstatSync(fd);
    need(raw.length===s.size&&s.ino===after.ino&&s.dev===after.dev&&s.size===after.size&&
      s.mtimeMs===after.mtimeMs&&s.ctimeMs===after.ctimeMs);return raw;
  }finally{fs.closeSync(fd);}
}
export function checkApprovalSourceFreeze({manifest,read=rootRead}={}){
  need(manifest&&Object.keys(manifest).sort().join(',')==='files,schema,sourceCommit'&&
    manifest.schema==='mht.first-trust-code-freeze.v1'&&/^[a-f0-9]{40}$/.test(manifest.sourceCommit??'')&&
    manifest.files&&Object.getPrototypeOf(manifest.files)===Object.prototype&&
    Object.keys(manifest.files).length<=128&&APPROVAL_REQUIRED_FILES.every(p=>Object.hasOwn(manifest.files,p)));
  for(const [rel,hash] of Object.entries(manifest.files)){
    need(typeof hash==='string'&&/^[a-f0-9]{64}$/.test(hash)&&!path.isAbsolute(rel)&&
      !rel.includes('\\')&&!/[\x00-\x1f\x7f]/.test(rel)&&
      !rel.split('/').some(p=>!p||p==='.'||p==='..'||['__proto__','constructor','prototype'].includes(p)));
    need(sha(read(ROOT+'/'+rel))===hash);
  }
  return {sourceCommit:manifest.sourceCommit,filesChecked:Object.keys(manifest.files).length};
}
export async function runApprovalBootstrap({read=rootRead,load=()=>import(pathToFileURL(ROOT+'/human/approval-signer.mjs').href),
  euid=process.geteuid(),cgroup=()=>fs.readFileSync('/proc/self/cgroup','utf8')}={}){
  need(euid===0&&typeof cgroup==='function');
  const rows=cgroup().trim().split('\n').map(x=>x.split(':'));
  need(rows.length>0&&rows.every(r=>r.length===3));
  const found=rows.filter(r=>r[0]==='0'&&r[1]==='');
  need(found.length===1&&/^\/system\.slice\/(?:system-minimal\\x2dhuman\\x2dtrust\\x2dapproval\.slice\/)?minimal-human-trust-approval@[A-Za-z0-9_-]{1,96}\.service$/.test(found[0][2]));
  const raw=read(MANIFEST),manifest=JSON.parse(raw);
  checkApprovalSourceFreeze({manifest,read});
  const module=await load();need(typeof module.runHumanApprovalOperation==='function'&&
    typeof module.readApprovalInput==='function');
  need(sha(read(MANIFEST))===sha(raw));checkApprovalSourceFreeze({manifest,read});
  return module.runHumanApprovalOperation({input:await module.readApprovalInput(),readProtected:read});
}
if(process.argv[1]===fileURLToPath(import.meta.url))try{
  need(process.argv.length===2);const result=await runApprovalBootstrap();
  process.stdout.write(JSON.stringify(result)+'\n');
}catch{process.stdout.write('{"ok":false,"error":"HUMAN_BOOTSTRAP_REFUSED"}\n');process.exitCode=1;}
