import './r6-driver-precommit.test.mjs';
import './r6-transport-timeout.test.mjs';
import './transaction.test.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {assertFirstBootstrapPreflight,assertUncommittedSource} from './run.mjs';
import {drive} from './transaction-driver.mjs';
import {assertCloudSelectorBaseline} from './cloud.mjs';
import {FIXED} from './maintenance-release-base.mjs';
import {digest} from './io.mjs';
test('old active R15 App fails first-bootstrap preflight before any stop, stage, signing or journal effect',async()=>{
 const records=new Map(),effects=[];const journal={read:n=>records.get(n),write:(n,v)=>records.set(n,structuredClone(v))};
 const adapters={baseline:()=>assertFirstBootstrapPreflight({preflight:{status:'BLOCKED',code:'FIRST_BOOTSTRAP_OLD_APP_STOP_UNPROVEN',appRuntime:{stopped:false,codePhase:'SOURCE',mainPid:123}}}),quiesce:()=>effects.push('stop'),stage:()=>effects.push('stage'),sign:()=>effects.push('sign')};
 const result=await drive({journal,adapters});assert.equal(result.status,'ABORTED_BEFORE_SERVICE_CHANGES');assert.equal(result.failureCode,'FIRST_BOOTSTRAP_OLD_APP_STOP_UNPROVEN');assert.deepEqual(effects,[]);
 assert.doesNotThrow(()=>assertFirstBootstrapPreflight({preflight:{status:'SOURCE_APP_STOP_OBSERVED',appRuntime:{stopped:true,codePhase:'SOURCE',mainPid:0,controlPid:0,cgroupEmpty:true}}}));
});

test('baseline App selector CAS binds all original fields and rejects drift before stage',()=>{
 const original={schema:'r16.app-host.v1',publicConfiguration:'/etc/r16-cloud/public-config.json',codeManifest:FIXED.sourceDirectory+'/app-manifest.json',immutableExtra:'source'};
 assert.doesNotThrow(()=>assertCloudSelectorBaseline(original,digest(original)));
 for(const config of [{...original,immutableExtra:'drift'},{...original,codeManifest:FIXED.targetDirectory+'/app-manifest.json'}])assert.throws(()=>assertCloudSelectorBaseline(config,digest(original)),{code:'BASELINE_APP_SELECTOR_DRIFT'});
 assert.throws(()=>assertCloudSelectorBaseline(original,undefined),{code:'BASELINE_APP_SELECTOR_DRIFT'});
});

test('missing or contradictory actual stop projection fails first bootstrap',()=>{
 for(const patch of [{codePhase:'TARGET'},{controlPid:5},{mainPid:10},{cgroupEmpty:false},{stopped:false}])assert.throws(()=>assertFirstBootstrapPreflight({preflight:{status:'SOURCE_APP_STOP_OBSERVED',appRuntime:{stopped:true,codePhase:'SOURCE',mainPid:0,controlPid:0,cgroupEmpty:true,...patch}}}),{code:'FIRST_BOOTSTRAP_OLD_APP_STOP_UNPROVEN'});
});

test('known unaccepted cloud commit requires unchanged signed delivery, both selector sets, ledger and Owner cache',()=>{
 const delivery={body:{revision:16},signature:'synthetic-only'},publicConfig={synthetic:'public'};
 const current={issuerDataHash:'issuer',configurationInvariantHash:'config',originalUnknown:{a:'UNKNOWN',b:'UNKNOWN'},projectBusinessHashes:{a:'hash-a'},configuration:{delivery:{envelope:delivery,revision:16}}};
 const snapshots={proposal:{p:1},reviewed:{r:1},native:{n:1},cutover:{c:1}};
 const args={context:{snapshots,inputs:{sourcePublicConfig:publicConfig},before:structuredClone(current)},artifacts:{sourceDeliveryHash:digest(delivery)},baseline:{cloudAppSelectorHash:'selector',cloudLedgerHashes:{app:'ledger'}},cloud:{coherent:true,accepted:delivery,appSelectorHash:'selector',ledgerHashes:{app:'ledger'}},local:{...snapshots,public:publicConfig},current};
 assert.equal(assertUncommittedSource(args).status,'SOURCE_CONFIGURATION_UNCHANGED');
 for(const patch of [{cloud:{...args.cloud,coherent:false}},{cloud:{...args.cloud,accepted:{body:{revision:17}}}},{cloud:{...args.cloud,appSelectorHash:'changed'}},{cloud:{...args.cloud,ledgerHashes:{app:'changed'}}},{local:{...args.local,native:{n:2}}},{local:{...args.local,public:{changed:true}}},{current:{...current,configuration:{delivery:{revision:17}}}},{current:{...current,originalUnknown:{a:'KNOWN'}}}])assert.throws(()=>assertUncommittedSource({...args,...patch}));
});
