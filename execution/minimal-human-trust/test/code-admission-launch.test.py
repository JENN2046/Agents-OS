"""Initial loader argv/held-bytes boundary tests, no sudo invocation."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('code_launcher', Path(__file__).resolve().parents[1] / 'tools/code-admission-launch.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='code-launch-'); self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name); self.source = root / 'public.py'; self.catalog = root / 'catalog.json'
        self.source.write_text('# isolated never executed\n'); self.catalog.write_text('{}')
        self.argv = ['launch', 'apply', '--source', str(self.source), '--source-sha256', hashlib.sha256(self.source.read_bytes()).hexdigest(),
                     '--catalog', str(self.catalog), '--catalog-sha256', hashlib.sha256(self.catalog.read_bytes()).hexdigest(), '--packet', str(root)]

    def test_initial_apply_uses_fresh_sudo_and_isolated_held_hash_loader(self):
        with patch.object(m.sys, 'argv', self.argv), patch.object(m.os, 'getuid', return_value=1000), \
             patch.object(m.os, 'isatty', return_value=True), patch.object(m.subprocess, 'run') as run:
            run.return_value.returncode = 78
            self.assertEqual(m.main(), 78)
        command = run.call_args.args[0]
        self.assertEqual(command[:7], ['/usr/bin/sudo', '-k', '--', '/usr/bin/python3', '-I', '-B', '-c'])
        self.assertEqual(command[7], m.LOADER)
        self.assertIn("hashlib.sha256(raw).hexdigest()==pin", m.LOADER)
        self.assertIn("exec(compile(raw", m.LOADER)
        self.assertNotIn('PYTHONPATH', run.call_args.kwargs['env'])

    def test_drift_never_requests_root(self):
        self.source.write_text('# changed')
        with patch.object(m.sys, 'argv', self.argv), patch.object(m.subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'DRIFT'): m.main()
            run.assert_not_called()

    def test_redirected_terminal_never_requests_root(self):
        with patch.object(m.sys, 'argv', self.argv), patch.object(m.os, 'getuid', return_value=1000), \
             patch.object(m.os, 'isatty', return_value=False), patch.object(m.subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'TERMINAL'): m.main()
            run.assert_not_called()

    def test_describe_never_sudo(self):
        self.argv[1] = 'describe'
        with patch.object(m.sys, 'argv', self.argv), patch.object(m.subprocess, 'run') as run:
            run.return_value.returncode = 0; self.assertEqual(m.main(), 0)
        self.assertEqual(run.call_args.args[0][:3], ['/usr/bin/python3', '-I', '-B'])
        self.assertNotIn('/usr/bin/sudo', run.call_args.args[0])


if __name__ == '__main__': unittest.main()
