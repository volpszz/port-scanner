"""Exercise actual processes and sockets, not only mocked CLI dispatch."""
from pathlib import Path
import socket
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class EntryPointTests(unittest.TestCase):
    def test_script_and_module_can_scan_local_listener(self):
        with socket.socket() as server:
            server.bind(('127.0.0.1', 0))
            server.listen(4)
            port = server.getsockname()[1]
            for entry in (['main.py'], ['-m', 'port_scanner']):
                with self.subTest(entry=entry):
                    result = subprocess.run(
                        [sys.executable, *entry, '127.0.0.1', '--ports', str(port), '--timeout', '0.2'],
                        cwd=ROOT, capture_output=True, text=True, timeout=5,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn(f'{port}/tcp: open', result.stdout)
                    self.assertEqual(result.stderr, '')

    def test_module_interactive_both_scans_real_sockets(self):
        with socket.socket() as tcp, socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
            tcp.bind(('127.0.0.1', 0))
            tcp.listen()
            port = tcp.getsockname()[1]
            udp.bind(('127.0.0.1', port))
            result = subprocess.run(
                [sys.executable, '-m', 'port_scanner', '--ports', str(port), '--timeout', '0.05'],
                input='3\n127.0.0.1\n', cwd=ROOT, capture_output=True, text=True, timeout=5,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f'{port}/tcp: open', result.stdout)
            self.assertIn(f'{port}/udp: open|filtered', result.stdout)

    def test_overlong_hostname_returns_one_without_traceback(self):
        for entry in (['main.py'], ['-m', 'port_scanner']):
            with self.subTest(entry=entry):
                result = subprocess.run(
                    [sys.executable, *entry, 'a' * 64 + '.invalid', '--ports', '80'],
                    cwd=ROOT, capture_output=True, text=True, timeout=5,
                )
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn('Cannot resolve target', result.stderr)
                self.assertNotIn('Traceback', result.stderr)
                self.assertNotIn('80/tcp:', result.stdout)

    def test_giant_finite_timeout_returns_two_without_traceback(self):
        for entry in (['main.py'], ['-m', 'port_scanner']):
            with self.subTest(entry=entry):
                result = subprocess.run(
                    [sys.executable, *entry, '127.0.0.1', '--ports', '80', '--timeout', '1e20'],
                    cwd=ROOT, capture_output=True, text=True, timeout=5,
                )
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn('Invalid configuration: Timeout', result.stderr)
                self.assertIn('socket', result.stderr)
                self.assertNotIn('Traceback', result.stderr)
                self.assertNotIn('80/tcp:', result.stdout)

    def test_module_invalid_config_returns_two(self):
        result = subprocess.run(
            [sys.executable, '-m', 'port_scanner', '127.0.0.1', '--ports', '0'],
            cwd=ROOT, capture_output=True, text=True, timeout=5,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
