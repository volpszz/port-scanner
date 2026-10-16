"""IPv4 probes. Use only against targets you are authorized to test."""

import errno
import socket


def connection_choice():
    choices = {'1': 'TCP', '2': 'UDP', '3': 'BOTH'}
    while True:
        print('Choose connection type:\n1. TCP\n2. UDP\n3. BOTH')
        choice = input('Enter your choice (1, 2 or 3): ').strip()
        if choice in choices:
            return choices[choice]
        print('Invalid choice. Please select 1, 2 or 3.')


def connection_tcp(target_ip, port, timeout=1.0):
    """A successful TCP handshake means open; timeout is inconclusive."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        result = sock.connect_ex((target_ip, port))

    if result == 0:
        return 'open'
    if result == errno.ECONNREFUSED:
        return 'closed'
    if result in (errno.ETIMEDOUT, errno.EAGAIN, errno.EWOULDBLOCK):
        return 'filtered/unknown'
    return f'error: {errno.errorcode.get(result, result)}'


def connection_udp(target_ip, port, timeout=1.0):
    """Generic UDP probe: silence cannot distinguish open from filtered.

    Services may ignore this payload. ICMP error delivery is OS-dependent.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        try:
            sock.connect((target_ip, port))
            sock.send(b'probe')
            sock.recv(4096)
            return 'open'
        except ConnectionRefusedError:
            return 'closed'
        except socket.timeout:
            return 'open|filtered'
