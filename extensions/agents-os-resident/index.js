'use strict';

const { createResidentAdapter } = require('./companion/adapter');

const adapter = createResidentAdapter();

module.exports = {
  initialize: adapter.initialize,
  processToolCall: adapter.processToolCall,
  processMessages: adapter.processMessages,
  shutdown: adapter.shutdown
};
