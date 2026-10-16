"""Argumentos, perguntas interativas, apresentação e códigos de saída."""
import argparse
from collections.abc import Mapping, Sequence
import socket
import sys

from .config import DEFAULT_PORTS, DEFAULT_TIMEOUT, ScanConfig
from .scanner import Probe, scan

PROTOCOL_GROUPS = {'TCP': ('tcp',), 'UDP': ('udp',), 'BOTH': ('tcp', 'udp')}


def choose_protocol() -> str:
    """Repete entradas inválidas sem recursão e devolve o rótulo legado."""
    choices = {'1': 'TCP', '2': 'UDP', '3': 'BOTH'}
    while True:
        print('Choose connection type:\n1. TCP\n2. UDP\n3. BOTH')
        choice = input('Enter your choice (1, 2 or 3): ').strip()
        if choice in choices:
            return choices[choice]
        print('Invalid choice. Please select 1, 2 or 3.')


def parse_ports(value: str) -> tuple[int, ...]:
    """Lê portas separadas por vírgulas; intervalos não são suportados."""
    try:
        ports = tuple(int(item.strip()) for item in value.split(','))
    except ValueError as error:
        raise argparse.ArgumentTypeError('Ports must be comma-separated integers.') from error
    if any(not 1 <= port <= 65535 for port in ports):
        raise argparse.ArgumentTypeError('Ports must be between 1 and 65535.')
    return ports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Sequential IPv4 TCP/UDP port scanner.')
    parser.add_argument('target', nargs='?', help='IPv4 address or hostname; omit for interactive mode')
    parser.add_argument('--protocol', choices=('tcp', 'udp', 'both'),
                        help='default: tcp with a target; otherwise ask interactively')
    parser.add_argument('--ports', type=parse_ports, default=DEFAULT_PORTS,
                        help='comma-separated ports (default: %(default)s)')
    parser.add_argument('--timeout', type=float, default=DEFAULT_TIMEOUT,
                        help='per-socket timeout in seconds (default: %(default)s)')
    return parser


def main(argv: Sequence[str] | None = None, *, probe_functions: Mapping[str, Probe] | None = None) -> int:
    """Executa a interface; argparse trata erros de sintaxe com SystemExit(2)."""
    args = build_parser().parse_args(argv)
    try:
        print('Scan only hosts you own or have permission to test.')
        protocol = args.protocol.upper() if args.protocol else ('TCP' if args.target is not None else choose_protocol())
        target = args.target if args.target is not None else input('Insert the target IP or hostname: ')
        try:
            config = ScanConfig(target, args.ports, PROTOCOL_GROUPS[protocol], args.timeout)
        except ValueError as error:
            print(f'Invalid configuration: {error}', file=sys.stderr)
            return 2
        first_result = True
        for result in scan(config, probe_functions=probe_functions):
            if first_result:
                print('-' * 50)
                print(f'Scanning {result.target_ip} ({protocol})...')
                print('-' * 50)
                first_result = False
            print(f'{result.port}/{result.protocol}: {result.state}')
    except socket.gaierror as error:
        print(f'Cannot resolve target: {error}', file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print('\nProgram closed by the user!', file=sys.stderr)
        return 130
    return 0
