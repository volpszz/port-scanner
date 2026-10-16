"""Interface tests keep user interaction separate from socket operations."""
import contextlib
import io
import socket
import unittest
from unittest.mock import patch

from port_scanner.cli import main, parse_ports
from port_scanner.scanner import ScanResult


class CliTests(unittest.TestCase):
    def test_ports_accept_comma_separated_integers(self):
        self.assertEqual(parse_ports('22, 80,443'), (22, 80, 443))

    def test_bad_ports_are_rejected(self):
        import argparse
        for value in ('', 'abc', '80,', '0', '65536', '1-20'):
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                parse_ports(value)

    def test_arguments_build_config_and_format_result(self):
        output = io.StringIO()
        with patch('port_scanner.cli.scan', return_value=iter([
            ScanResult('127.0.0.1', 80, 'udp', 'open|filtered'),
        ])) as scan_mock, contextlib.redirect_stdout(output):
            self.assertEqual(main(['localhost', '--protocol', 'udp', '--ports', '80', '--timeout', '0.2']), 0)
        config = scan_mock.call_args.args[0]
        self.assertEqual((config.target, config.protocols, config.ports, config.timeout),
                         ('localhost', ('udp',), (80,), 0.2))
        self.assertIn('80/udp: open|filtered', output.getvalue())
        self.assertIn('127.0.0.1', output.getvalue())

    def test_interactive_menu_retries_and_selects_both(self):
        with patch('builtins.input', side_effect=['invalid', ' 3 ', ' localhost ']), \
                patch('port_scanner.cli.scan', return_value=iter([])) as scan_mock, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main([]), 0)
        self.assertEqual(scan_mock.call_args.args[0].protocols, ('tcp', 'udp'))
        self.assertEqual(scan_mock.call_args.args[0].target, 'localhost')

    def test_target_argument_uses_tcp_without_prompting(self):
        with patch('builtins.input', side_effect=AssertionError('must not prompt')), \
                patch('port_scanner.cli.scan', return_value=iter([])) as scan_mock, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(['localhost']), 0)
        self.assertEqual(scan_mock.call_args.args[0].protocols, ('tcp',))

    def test_dns_failure_returns_one(self):
        errors = io.StringIO()
        with patch('socket.gethostbyname', side_effect=socket.gaierror('missing')), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(errors):
            self.assertEqual(main(['invalid.test']), 1)
        self.assertIn('Cannot resolve target', errors.getvalue())

    def test_invalid_timeout_returns_two_without_network(self):
        for value in ('0', '-1', 'nan', 'inf', '1e20'):
            with self.subTest(value=value), patch('port_scanner.cli.scan') as scan_mock, \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(['localhost', '--timeout', value]), 2)
                scan_mock.assert_not_called()

    def test_interrupt_and_eof_return_130(self):
        for error in (KeyboardInterrupt, EOFError):
            with self.subTest(error=error), patch('builtins.input', side_effect=error), \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main([]), 130)

    def test_scan_interrupt_returns_130(self):
        with patch('port_scanner.cli.scan', side_effect=KeyboardInterrupt), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['localhost']), 130)

    def test_probe_value_error_is_not_reported_as_invalid_configuration(self):
        def broken_probe(ip, port, timeout):
            raise ValueError('probe bug')

        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaisesRegex(ValueError, 'probe bug'):
                main(['127.0.0.1'], probe_functions={'tcp': broken_probe})

    def test_argparse_rejects_bad_arguments(self):
        for arguments in (['localhost', '--protocol', 'icmp'], ['localhost', '--ports', 'oops']):
            with self.subTest(arguments=arguments), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    main(arguments)
                self.assertEqual(raised.exception.code, 2)
