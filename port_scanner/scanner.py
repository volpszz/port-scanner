"""Resolve um destino IPv4 e entrega resultados sequenciais de sondagem."""
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
import socket

from .config import ScanConfig
from .probes import probe_tcp, probe_udp

Probe = Callable[[str, int, float], str]
Resolver = Callable[[str], str]


@dataclass(frozen=True)
class ScanResult:
    """Uma observação, não uma garantia de disponibilidade do serviço."""

    target_ip: str
    port: int
    protocol: str
    state: str


def scan(
    config: ScanConfig,
    *,
    resolver: Resolver | None = None,
    probe_functions: Mapping[str, Probe] | None = None,
) -> Iterator[ScanResult]:
    """Resolve uma vez e entrega resultados na ordem de portas e protocolos.

    Erros de rede de uma sondagem viram resultados individuais. Falhas de DNS
    são propagadas. A execução, incluindo DNS, só começa na iteração. As
    dependências opcionais permitem testes e uso sem acoplamento ao terminal.
    """
    resolve = socket.gethostbyname if resolver is None else resolver
    probes = {'tcp': probe_tcp, 'udp': probe_udp} if probe_functions is None else probe_functions
    try:
        target_ip = resolve(config.target)
    except UnicodeError as error:
        raise socket.gaierror(socket.EAI_NONAME, f'Invalid hostname encoding: {error}') from error
    for port in config.ports:
        for protocol in config.protocols:
            try:
                state = probes[protocol](target_ip, port, config.timeout)
            except OSError as error:
                state = f'error: {error}'
            yield ScanResult(target_ip, port, protocol, state)
