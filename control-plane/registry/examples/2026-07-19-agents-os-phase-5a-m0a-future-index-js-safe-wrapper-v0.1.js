'use strict';

function projectArgs(args) {
  return {
    commandRef: args.commandRef,
    commandFingerprint: args.commandFingerprint,
    payload: args.payload
  };
}

async function processToolCall(args) {
  const nativeFrame = projectArgs(args);
  return residentNative.process(nativeFrame);
}

module.exports = { processToolCall };
