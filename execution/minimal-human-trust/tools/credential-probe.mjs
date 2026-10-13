// Exactly one real PID1 credential proof, using an isolated synthetic key.
import fs from 'node:fs';
import {createPublicKey,sign,verify} from 'node:crypto';
import {loadRootIssuerPrivateKey} from '../src/systemd-issuer-credential.mjs';
try {
  if(process.argv.length!==2)throw Error();
  const proof=loadRootIssuerPrivateKey();
  const expected=JSON.parse(fs.readFileSync('/var/lib/g1d-os-validation-r1/expected-public.json','utf8'));
  if(expected.purpose!=='synthetic-g1d-os-test-only')throw Error();
  const pub=createPublicKey(proof.key).export({type:'spki',format:'der'}).toString('base64url');
  const challenge=Buffer.from('G1D_REAL_SYSTEMD_CREDENTIAL_PROOF_R1');
  const signature=sign(null,challenge,proof.key);
  if(pub!==expected.publicKey||!verify(null,challenge,createPublicKey(proof.key),signature))throw Error();
  console.log(JSON.stringify({status:'REAL_SYSTEMD_CREDENTIAL_PROOF_PASS',unit:proof.unit,lane:proof.lane,expectedPublicKeyMatched:true,signatureVerified:true,privateKeyDisclosed:false,productionCredentialUsed:false}));
} catch {console.log(JSON.stringify({status:'REAL_SYSTEMD_CREDENTIAL_PROOF_FAIL',privateKeyDisclosed:false}));process.exitCode=1;}
