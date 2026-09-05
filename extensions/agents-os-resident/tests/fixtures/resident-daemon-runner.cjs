'use strict';

const { main, startDaemon } = require('../../companion/resident-daemon');

// Test-only dependency injection for disposable same-UID daemon fixtures. The
// actual entrypoint retains provisioning, startup, and graceful signal handling.
void main(process.argv.slice(2), {
  start: (options) => startDaemon({ ...options, loadIdentityPolicy: () => null })
});
