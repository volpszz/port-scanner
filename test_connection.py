import contextlib
import io
import socket
import threading
import unittest
from unittest.mock import patch

import connection


class ScannerTests(unittest.TestCase):
    def test_tcp_open_and_closed(self):
        with socket.socket() as server:
            server.bind(('127.0.0.1', 0))
            port = server.getsockname()[1]
            server.listen()
            self.assertEqual(connection.connection_tcp('127.0.0.1', port, 0.2), 'open')
        self.assertEqual(connection.connection_tcp('127.0.0.1', port, 0.2), 'closed')

    def test_udp_response_is_open(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
            server.bind(('127.0.0.1', 0))
            server.settimeout(2)
            def reply():
                data, peer = server.recvfrom(4096)
                server.sendto(data, peer)
            worker = threading.Thread(target=reply)
            worker.start()
            try:
                self.assertEqual(connection.connection_udp('127.0.0.1', server.getsockname()[1], 0.5), 'open')
            finally:
                worker.join(timeout=3)

    def test_udp_silence_is_inconclusive(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
            server.bind(('127.0.0.1', 0))
            self.assertEqual(connection.connection_udp('127.0.0.1', server.getsockname()[1], 0.05), 'open|filtered')

    def test_main_dispatches_selected_protocols(self):
        import runpy
        for choice, tcp_calls, udp_calls in [('1', 7, 0), ('2', 0, 7), ('3', 7, 7)]:
            with self.subTest(choice=choice), \
                    patch('builtins.input', side_effect=[choice, '127.0.0.1']), \
                    patch('sys.argv', ['main.py']), \
                    patch.object(connection, 'connection_tcp', return_value='open') as tcp, \
                    patch.object(connection, 'connection_udp', return_value='open|filtered') as udp, \
                    contextlib.redirect_stdout(io.StringIO()):
                runpy.run_path('main.py', run_name='__main__')
                self.assertEqual(tcp.call_count, tcp_calls)
                self.assertEqual(udp.call_count, udp_calls)

    def test_menu_retries_and_offers_both(self):
        output = io.StringIO()
        with patch('builtins.input', side_effect=['invalid', ' 3 ']), contextlib.redirect_stdout(output):
            self.assertEqual(connection.connection_choice(), 'BOTH')
        self.assertIn('3. BOTH', output.getvalue())


if __name__ == '__main__':
    unittest.main()
