// Fixed root-owned bootstrap. Verify native role signed R16/R17 Release
// manifest and every installed file before importing the per-request Issuer.
// This is a source candidate, not currently installed by the trusted publisher.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {protectedRuntimeFile,verifyInstalledManifest,runtimeVersion}
  from '../authority/runtime-manifest.mjs';
import {verified,verifyRelease,ACTIONS,digest,publicKey} from './lease-core.mjs';

const refuse=()=>{throw new Error('MHT_BOOTSTRAP_REJECTED');};
export const BOOTSTRAP_CONFIG='/etc/minimal-human-trust/issuer.json';
export const BOOTSTRAP_ROOTS='/etc/minimal-human-trust/trust-roots.json';
export const ENTRY='src/minimal-trust-issuer-once.mjs';
export function inspectReviewedTrustRuntime({
  readFile=protectedRuntimeFile,
  verify=verifyInstalledManifest,
  euid=process.geteuid(),now=Date.now,
}={}){
  if(euid!==0||process.argv.length!==2)refuse();
  const cfg=JSON.parse(readFile(BOOTSTRAP_CONFIG));
  const roots=JSON.parse(readFile(BOOTSTRAP_ROOTS));
  if(!roots||Object.keys(roots).sort().join(',')!==
    'enrollmentAuthorityPublicKey,grantId,handoffHash,installationProfile,issuerPublicKey,releaseHash,releasePublicKey,schema'||
    roots.schema!=='mht.trust-roots.v1'||!['isolated','production'].includes(roots.installationProfile))refuse();
  for(const key of ['issuerPublicKey','releasePublicKey','enrollmentAuthorityPublicKey']){
    publicKey(roots[key]);if(cfg[key]!==roots[key])refuse();
  }
  if(new Set([roots.issuerPublicKey,roots.releasePublicKey,roots.enrollmentAuthorityPublicKey]).size!==3||
    cfg.grantId!==roots.grantId||digest(cfg.release)!==roots.releaseHash||digest(cfg.handoff)!==roots.handoffHash)refuse();
  if(cfg.schema!=='mht.installed-issuer.v1'||cfg.trustCutoverPhase!=='RECOVERY_SHADOW'||
     cfg.mode!=='recovery_only')refuse();
  const r=verified(cfg.release,roots.releasePublicKey,'r16.release.v1');
  if(r.issuedAt>now())refuse();
  // This fixed entry admits recovery only; expired business releases must not
  // disable signature-authenticated revocation and result closure. The issuer
  // independently rejects prepare/activate regardless of caller input.
  verifyRelease(cfg.release,roots.releasePublicKey,
    {versions:r.versions,actions:ACTIONS,now:r.issuedAt});
  const directory='/opt/r16/releases/'+r.id;
  if(!/^r16-daily-[A-Za-z0-9_-]+$/.test(r.id))refuse();
  const manifest=JSON.parse(readFile(directory+'/native-manifest.json'));
  if(manifest.files?.[ENTRY]===undefined||runtimeVersion(manifest,'native')!==r.versions.native)refuse();
  for(const expected of ['src/systemd-issuer-credential.mjs','src/minimal-trust-issuer.mjs',
    'src/lease-core.mjs','src/control-clock.mjs']){
    if(!manifest.files?.[expected])refuse();
  }
  if(verify(manifest,directory,{role:'native',readFile})!==r.versions.native)refuse();
  return Object.freeze({entry:pathToFileURL(path.join(directory,ENTRY)).href,release:r.id});
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
  try{
    const approved=inspectReviewedTrustRuntime();
    const runtime=await import(approved.entry);
    if(typeof runtime.runProtectedOnce!=='function')refuse();
    const value=await runtime.runProtectedOnce();
    process.stdout.write(JSON.stringify({ok:true,value})+'\n');
  }catch{
    process.stdout.write(JSON.stringify({ok:false,error:'MHT_BOOTSTRAP_REJECTED'})+'\n');
    process.exitCode=1;
  }
}
