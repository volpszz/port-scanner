"""Real loopback fixtures plus deterministic operating-system error cases."""
import errno
import socket
import threading
import unittest
from unittest.mock import patch

from port_scanner import probes


class ProbeTests(unittest.TestCase):
    def test_tcp_listener_is_open(self):
        with socket.socket() as server:
            server.bind(('127.0.0.1', 0))
            server.listen()
            self.assertEqual(probes.probe_tcp('127.0.0.1', server.getsockname()[1], 0.5), 'open')

    def test_tcp_bound_non_listener_is_closed(self):
        with socket.socket() as server:
            server.bind(('127.0.0.1', 0))
            self.assertEqual(probes.probe_tcp('127.0.0.1', server.getsockname()[1], 0.5), 'closed')

    def test_tcp_timeout_and_unexpected_error_are_distinct(self):
        for code, expected in (
            (errno.ETIMEDOUT, 'filtered/unknown'),
            (errno.EAGAIN, 'filtered/unknown'),
            (errno.EHOSTUNREACH, 'error: EHOSTUNREACH'),
        ):
            with self.subTest(code=code), patch('port_scanner.probes.socket.socket') as factory:
                factory.return_value.__enter__.return_value.connect_ex.return_value = code
                self.assertEqual(probes.probe_tcp('127.0.0.1', 80), expected)

    def test_udp_response_is_open(self):
        failures = []
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
            server.bind(('127.0.0.1', 0))
            server.settimeout(2)

            def reply():
                try:
                    data, peer = server.recvfrom(4096)
                    server.sendto(data, peer)
                except OSError as error:
                    failures.append(error)

            worker = threading.Thread(target=reply)
            worker.start()
            try:
                self.assertEqual(probes.probe_udp('127.0.0.1', server.getsockname()[1], 1), 'open')
            finally:
                worker.join(timeout=3)
            self.assertFalse(worker.is_alive())
            self.assertEqual(failures, [])

    def test_udp_silence_is_not_closed(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
            server.bind(('127.0.0.1', 0))
            self.assertEqual(probes.probe_udp('127.0.0.1', server.getsockname()[1], 0.02), 'open|filtered')

    def test_udp_refusal_is_closed(self):
        # ICMP delivery differs by OS; model refusal at the socket boundary.
        with patch('port_scanner.probes.socket.socket') as factory:
            factory.return_value.__enter__.return_value.recv.side_effect = ConnectionRefusedError()
            self.assertEqual(probes.probe_udp('127.0.0.1', 80), 'closed')

    def test_udp_other_network_errors_propagate(self):
        with patch('port_scanner.probes.socket.socket') as factory:
            factory.return_value.__enter__.return_value.send.side_effect = OSError('unreachable')
            with self.assertRaisesRegex(OSError, 'unreachable'):
                probes.probe_udp('127.0.0.1', 80)
