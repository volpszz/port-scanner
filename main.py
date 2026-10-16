"""Entrada de script compatível com a versão anterior; delega a port_scanner."""
from collections.abc import Sequence

import connection
from port_scanner.cli import main as run_cli
from port_scanner.config import DEFAULT_PORTS, DEFAULT_TIMEOUT

# Mantidos para importações existentes; use ScanConfig em código novo.
PORTS = list(DEFAULT_PORTS)
TIMEOUT = DEFAULT_TIMEOUT


def main(argv: Sequence[str] | None = None) -> int:
    return run_cli(argv, probe_functions={
        'tcp': connection.connection_tcp,
        'udp': connection.connection_udp,
    })


if __name__ == '__main__':
    exit_code = main()
    if exit_code:
        raise SystemExit(exit_code)
