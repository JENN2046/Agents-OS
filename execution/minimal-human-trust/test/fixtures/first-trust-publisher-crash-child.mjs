// Disposable process-exit test only. No real credentials or OS service.
import fs from 'node:fs';
import path from 'node:path';
import {stagePublisherOnce} from '../../release/publisher-transaction.mjs';
import {digest} from '../../src/lease-core.mjs';
const directory=process.argv[2],stage=process.argv[3];
if(!['after_effect','after_result'].includes(stage)||!directory)process.exit(4);
const identity={schema:'mht.first-trust-signer-intent.v1',
  reviewedManifestHash:digest('fixture-reviewed-r17')};
const fixture={schema:'synthetic-test-signature.v1',hash:digest('not-production')};
stagePublisherOnce({directory,identity,sign:()=>{
  fs.writeFileSync(path.join(directory,'synthetic-effect.marker'),'called',{flag:'wx',mode:0o600});
  return fixture;
},verifyResult:x=>{
 if(x.schema!==fixture.schema||x.hash!==fixture.hash)throw Error('TEST_RESULT_DRIFT');
},fault:name=>{if(name===stage)process.exit(91);}});
