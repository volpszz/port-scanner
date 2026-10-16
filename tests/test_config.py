"""Configuration is validated before any network operation."""
import unittest

from port_scanner.config import ScanConfig


class ScanConfigTests(unittest.TestCase):
    def test_defaults_preserve_original_scan(self):
        config = ScanConfig(' localhost ')
        self.assertEqual(config.target, 'localhost')
        self.assertEqual(config.ports, (53, 22, 80, 111, 139, 443, 32768))
        self.assertEqual(config.protocols, ('tcp',))
        self.assertEqual(config.timeout, 1.0)

    def test_invalid_configuration_is_rejected(self):
        for arguments in (
            {'target': ''}, {'target': '   '},
            {'target': 'localhost', 'ports': ()},
            {'target': 'localhost', 'ports': (0,)},
            {'target': 'localhost', 'ports': (65536,)},
            {'target': 'localhost', 'ports': (True,)},
            {'target': 'localhost', 'protocols': ()},
            {'target': 'localhost', 'protocols': ('icmp',)},
            {'target': 'localhost', 'timeout': 0},
            {'target': 'localhost', 'timeout': -1},
            {'target': 'localhost', 'timeout': float('nan')},
            {'target': 'localhost', 'timeout': float('inf')},
        ):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                ScanConfig(**arguments)

    def test_finite_timeout_too_large_for_socket_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Timeout.*socket'):
            ScanConfig('localhost', timeout=1e20)

    def test_mutable_inputs_are_copied_and_duplicates_removed(self):
        ports = [80, 80, 443]
        config = ScanConfig('localhost', ports=ports, protocols=['udp', 'udp', 'tcp'])
        ports.append(22)
        self.assertEqual(config.ports, (80, 443))
        self.assertEqual(config.protocols, ('udp', 'tcp'))
