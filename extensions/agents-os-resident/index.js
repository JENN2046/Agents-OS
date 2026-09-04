'use strict';

const { createResidentAdapter } = require('./companion/adapter');

const adapter = createResidentAdapter();
const hostContract = {
  initialize: adapter.initialize,
  processToolCall: adapter.processToolCall,
  processMessages: adapter.processMessages,
  shutdown: adapter.shutdown
};

Object.defineProperty(hostContract, 'sealProviderAttempt', {
  configurable: false,
  enumerable: false,
  value: adapter.sealProviderAttempt,
  writable: false
});

Object.defineProperty(hostContract, 'publishMemoryBody', {
  configurable: false,
  enumerable: false,
  value: adapter.publishMemoryBody,
  writable: false
});

module.exports = Object.freeze(hostContract);
