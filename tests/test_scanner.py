"""Orchestration tests use injected network boundaries, never public hosts."""
import socket
import unittest
from unittest.mock import Mock

from port_scanner.config import ScanConfig
from port_scanner.scanner import scan


class ScanTests(unittest.TestCase):
    def test_resolves_once_and_scans_in_port_then_protocol_order(self):
        resolver = Mock(return_value='127.0.0.1')
        calls = []

        def probe(ip, port, timeout):
            calls.append((ip, port, timeout))
            return 'open'

        results = list(scan(
            ScanConfig('localhost', ports=(80, 443), protocols=('tcp', 'udp'), timeout=0.2),
            resolver=resolver, probe_functions={'tcp': probe, 'udp': probe},
        ))
        resolver.assert_called_once_with('localhost')
        self.assertEqual([(r.port, r.protocol, r.state) for r in results],
                         [(80, 'tcp', 'open'), (80, 'udp', 'open'),
                          (443, 'tcp', 'open'), (443, 'udp', 'open')])
        self.assertEqual(calls, [('127.0.0.1', p, 0.2) for p in (80, 80, 443, 443)])
        self.assertTrue(all(r.target_ip == '127.0.0.1' for r in results))

    def test_network_error_does_not_stop_next_port(self):
        probe = Mock(side_effect=[OSError('unreachable'), 'closed'])
        results = list(scan(ScanConfig('localhost', ports=(80, 443)),
                            resolver=lambda _: '127.0.0.1', probe_functions={'tcp': probe}))
        self.assertEqual([r.state for r in results], ['error: unreachable', 'closed'])

    def test_dns_failure_propagates_without_probing(self):
        probe = Mock()
        with self.assertRaises(socket.gaierror):
            list(scan(ScanConfig('invalid.test'), resolver=Mock(side_effect=socket.gaierror('missing')),
                      probe_functions={'tcp': probe}))
        probe.assert_not_called()

    def test_overlong_hostname_is_a_lazy_resolution_failure_without_probing(self):
        probe = Mock()
        results = scan(ScanConfig('a' * 64 + '.invalid'), probe_functions={'tcp': probe})
        probe.assert_not_called()
        with self.assertRaises(socket.gaierror) as raised:
            next(results)
        self.assertIsInstance(raised.exception.__cause__, UnicodeError)
        probe.assert_not_called()

    def test_probe_unicode_error_is_not_a_resolution_failure(self):
        with self.assertRaisesRegex(UnicodeError, 'probe bug'):
            list(scan(ScanConfig('localhost'), resolver=lambda _: '127.0.0.1',
                      probe_functions={'tcp': Mock(side_effect=UnicodeError('probe bug'))}))

    def test_unexpected_programming_errors_are_not_hidden(self):
        with self.assertRaisesRegex(RuntimeError, 'bug'):
            list(scan(ScanConfig('localhost'), resolver=lambda _: '127.0.0.1',
                      probe_functions={'tcp': Mock(side_effect=RuntimeError('bug'))}))
