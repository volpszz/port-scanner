"""Configuração imutável e validação, independentes da interface."""
from dataclasses import dataclass
import math
import socket

DEFAULT_PORTS = (53, 22, 80, 111, 139, 443, 32768)
DEFAULT_TIMEOUT = 1.0
SUPPORTED_PROTOCOLS = ('tcp', 'udp')


@dataclass(frozen=True)
class ScanConfig:
    """Solicitação validada que preserva a ordem de portas e protocolos."""

    target: str
    ports: tuple[int, ...] = DEFAULT_PORTS
    protocols: tuple[str, ...] = ('tcp',)
    timeout: float = DEFAULT_TIMEOUT

    def __post_init__(self) -> None:
        target = self.target.strip()
        ports = tuple(self.ports)
        protocols = tuple(self.protocols)
        if not target:
            raise ValueError('Target must not be empty.')
        if not ports or any(type(port) is not int or not 1 <= port <= 65535 for port in ports):
            raise ValueError('Ports must be integers between 1 and 65535.')
        if not protocols or any(protocol not in SUPPORTED_PROTOCOLS for protocol in protocols):
            raise ValueError('Choose tcp, udp, or both protocols.')
        if not math.isfinite(self.timeout) or self.timeout <= 0:
            raise ValueError('Timeout must be a finite number greater than zero.')
        # Ask the runtime for its supported range without connecting or changing defaults.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.settimeout(self.timeout)
            except (OverflowError, ValueError) as error:
                raise ValueError('Timeout is outside the range supported by socket.settimeout.') from error
        object.__setattr__(self, 'target', target)
        object.__setattr__(self, 'ports', tuple(dict.fromkeys(ports)))
        object.__setattr__(self, 'protocols', tuple(dict.fromkeys(protocols)))
