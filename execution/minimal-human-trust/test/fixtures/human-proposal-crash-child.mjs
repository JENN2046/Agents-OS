// Disposable child-process crash/lock fixture. No production keys or services.
import fs from 'node:fs';
import path from 'node:path';
import {generateKeyPairSync,sign,verify,createPublicKey} from 'node:crypto';
import {issueHumanProposalOnce} from '../../release/human-proposal-transaction.mjs';
import {canonical,digest} from '../../src/lease-core.mjs';
const directory=process.argv[2],stage=process.argv[3];
if(!directory||!['none','after_intent','after_effect','after_result','after_publish'].includes(stage))process.exit(4);
const body={schema:'synthetic.proposal.v1',purpose:'test-only'};
const identity={schema:'mht.human-proposal-signing-intent.v1',action:'enroll_human',
 requestHash:digest('disposable-request'),sourceFreezeDigest:digest('disposable-source'),
 proposalBodyHash:digest(body),policyTemplateHash:digest('disposable-policy')};
try{
 issueHumanProposalOnce({directory,identity,produce:()=>{
  const {privateKey,publicKey}=generateKeyPairSync('ed25519');
  fs.writeFileSync(path.join(directory,'synthetic-effect.marker'),'called',{flag:'wx',mode:0o600});
  return {body,publicKey:publicKey.export({format:'der',type:'spki'}).toString('base64url'),
   signature:sign(null,Buffer.from(canonical(body)),privateKey).toString('base64url')};
 },verifyResult:artifacts=>{
  const key=createPublicKey({key:Buffer.from(artifacts.publicKey,'base64url'),format:'der',type:'spki'});
  if(digest(artifacts.body)!==digest(body)||!verify(null,Buffer.from(canonical(artifacts.body)),key,
   Buffer.from(artifacts.signature,'base64url')))throw Error('SYNTHETIC_SIGNATURE_INVALID');
 },publish:artifacts=>fs.writeFileSync(path.join(directory,'published.json'),canonical(artifacts),{flag:'wx',mode:0o600}),
 fault:name=>{if(name===stage)process.exit(91);}});
}catch(error){process.stderr.write(String(error.code??error.message)+'\n');process.exit(3);}
