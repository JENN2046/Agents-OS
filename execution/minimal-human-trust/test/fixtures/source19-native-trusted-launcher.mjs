// Initial-install trust root: install root-owned, outside writable releases.
import fs from 'node:fs';
import path from 'node:path';
import {createHash,createPublicKey,verify} from 'node:crypto';
import {pathToFileURL} from 'node:url';
const fail=()=>{throw Error('R16_RELEASE_REJECTED');};
const canonical=x=>x===null||typeof x!=='object'?JSON.stringify(x):Array.isArray(x)?'['+x.map(canonical).join(',')+']':'{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
function protectedFile(filename){
 if(!path.isAbsolute(filename)||path.resolve(filename)!==filename)fail();let cursor=path.parse(filename).root;
 for(const component of filename.slice(cursor.length).split(path.sep)){cursor=path.join(cursor,component);const s=fs.lstatSync(cursor);if(s.isSymbolicLink()||s.uid!==0||(s.mode&0o022))fail();}
 const s=fs.lstatSync(filename);if(!s.isFile()||s.nlink!==1||s.size>64*1024*1024)fail();
 return fs.readFileSync(filename);
}
export function verifyNativeRelease(configFile,{cutoverFile='/etc/r16/cutover.json'}={}){
 const config=JSON.parse(protectedFile(configFile));
 if(config.schema!=='r16.native-host.v1')fail();
 const publicConfig=JSON.parse(protectedFile(config.publicConfiguration));
 if(publicConfig.schema!=='r16.runtime-configuration.v1')fail();
 const cutover=JSON.parse(protectedFile(cutoverFile));
 if(cutover.schema!=='r16.local-cutover.v1'||cutover.phase!=='ACTIVE'||!publicConfig.grant?.body?.id||cutover.grantId!==publicConfig.grant.body.id)fail();
 const {body,signature}=publicConfig.release;
 const releaseKey=createPublicKey({key:Buffer.from(publicConfig.releasePublicKey,'base64url'),format:'der',type:'spki'});
 if(releaseKey.asymmetricKeyType!=='ed25519'||!verify(null,Buffer.from('R16-SIGNED\0'+canonical(body)),releaseKey,Buffer.from(signature,'base64url'))||body.schema!=='r16.release.v1'||body.issuedAt>Date.now()||body.notAfter<=Date.now()||!body.formats.includes('r16.workspace.v1'))fail();
 const manifest=JSON.parse(protectedFile(config.codeManifest));
 if(manifest.schema!=='r16.runtime-code.v1'||manifest.role!=='native'||!manifest.files?.[manifest.entry])fail();
 const version=createHash('sha256').update(canonical(manifest)).digest('hex');
 if(version!==body.versions.native||version!==publicConfig.versions.native)fail();
 const directory=path.dirname(config.codeManifest);
 for(const [relative,expected]of Object.entries(manifest.files)){
  if(path.isAbsolute(relative)||relative.split('/').some(p=>!p||p==='.'||p==='..')||relative.includes('\\')||!/^[a-f0-9]{64}$/.test(expected))fail();
  const actual=createHash('sha256').update(protectedFile(path.join(directory,relative))).digest('hex');if(actual!==expected)fail();
 }
 return {config,publicConfig,manifest,directory};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 try{if(process.argv.length!==3)fail();const checked=verifyNativeRelease(process.argv[2]);const entry=await import(pathToFileURL(path.join(checked.directory,checked.manifest.entry)));await entry.startNativeService(checked);}
 catch{process.stderr.write('R16_NATIVE_START_REFUSED; details suppressed.\n');process.exitCode=78;}
}