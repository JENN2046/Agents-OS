// Only signed control-plane timestamps may be ahead within this fixed bound.
// Business lease not-before/expiry and release notAfter checks remain strict.
export const MAX_FUTURE_SKEW_MS=1000;
export function controlWindow(value,now,maxLifetime=30000){
 const {issuedAt,expiresAt}=value??{};
 return Number.isSafeInteger(now)&&Number.isSafeInteger(issuedAt)&&Number.isSafeInteger(expiresAt)&&issuedAt>=0&&
  issuedAt-now<=MAX_FUTURE_SKEW_MS&&now<expiresAt&&expiresAt>issuedAt&&expiresAt-issuedAt<=maxLifetime;
}
export function replyWindow(value,requestIssuedAt,now,maxLifetime=30000){
 return Number.isSafeInteger(requestIssuedAt)&&requestIssuedAt>=0&&now>=requestIssuedAt&&
  controlWindow(value,now,maxLifetime)&&value.issuedAt>=requestIssuedAt-MAX_FUTURE_SKEW_MS;
}
export async function waitUntilIssued(issuedAt,expiresAt,{now=Date.now,sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms+1))}={}){
 const before=now();
 const check=ok=>{if(!ok)throw Object.assign(new Error('CLOCK_WINDOW_REJECTED'),{code:'CLOCK_WINDOW_REJECTED'});};
 check(Number.isSafeInteger(before)&&Number.isSafeInteger(issuedAt)&&Number.isSafeInteger(expiresAt)&&issuedAt>=0&&issuedAt<expiresAt&&before<expiresAt&&issuedAt-before<=MAX_FUTURE_SKEW_MS);
 // Timers may fire at a rounded millisecond boundary; the default adds one
 // scheduling millisecond, while the post-wait authority comparison stays exact.
 const delay=issuedAt-before;
 if(delay>0)await sleep(delay);
 // One bounded wait, never retry or move either deadline if the clock changes.
 const after=now();check(Number.isSafeInteger(after)&&after>=issuedAt&&after<expiresAt);
}