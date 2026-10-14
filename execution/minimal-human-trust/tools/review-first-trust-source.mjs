// Review helper. Emits canonical source freeze; no keys, writes, or privilege.
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {canonical,digest} from '../src/lease-core.mjs';
import {REVIEWED_SOURCE_FILES} from '../release/publisher-bootstrap.mjs';
const reject=()=>{throw Error('FIRST_TRUST_REVIEW_NOT_CLEAN');};
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
function git(args){
 const result=spawnSync('/usr/bin/git',['-C',root,...args],{
  encoding:'utf8',timeout:5000,maxBuffer:65536,env:{PATH:'/usr/bin:/bin'}});
 if(result.status!==0||result.error||result.signal)reject();
 return result.stdout.trim();
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
 try{
  if(process.argv.length!==2||git(['status','--porcelain=v1'])!=='')reject();
  const commit=git(['rev-parse','HEAD']);
  if(!/^[0-9a-f]{40}$/.test(commit))reject();
  const files={};
  for(const rel of REVIEWED_SOURCE_FILES){
   const name=path.join(root,rel);
   const st=fs.lstatSync(name);
   if(!st.isFile()||st.isSymbolicLink()||st.size<=0||st.size>32*1024*1024)reject();
   files[rel]=createHash('sha256').update(fs.readFileSync(name)).digest('hex');
  }
  const manifest={schema:'mht.first-trust-code-freeze.v1',sourceCommit:commit,files};
  process.stdout.write(canonical(manifest)+'\n');
  process.stderr.write('REVIEW_ONLY sourceFreezeDigest='+digest(manifest)+'\n');
 }catch{
  process.stderr.write('FIRST_TRUST_SOURCE_REVIEW_BLOCKED\n');process.exitCode=1;
 }
}
