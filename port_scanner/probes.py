"""Operações de socket IPv4, sem entrada/saída de terminal ou orquestração."""
import errno
import socket

from .config import DEFAULT_TIMEOUT

UDP_PAYLOAD = b'probe'
UDP_BUFFER_SIZE = 4096
TCP_TIMEOUT_ERRORS = frozenset((errno.ETIMEDOUT, errno.EAGAIN, errno.EWOULDBLOCK))


def probe_tcp(target_ip: str, port: int, timeout: float = DEFAULT_TIMEOUT) -> str:
    """Tenta conectar uma vez. Só uma recusa explícita significa porta fechada.

    Outras exceções de socket são propagadas para o orquestrador.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        result = sock.connect_ex((target_ip, port))

    if result == 0:
        return 'open'
    if result == errno.ECONNREFUSED:
        return 'closed'
    if result in TCP_TIMEOUT_ERRORS:
        return 'filtered/unknown'
    return f'error: {errno.errorcode.get(result, result)}'


def probe_udp(target_ip: str, port: int, timeout: float = DEFAULT_TIMEOUT) -> str:
    """Envia um datagrama genérico; silêncio não distingue aberto de filtrado.

    UDP connect não faz handshake. O serviço pode ignorar o payload; a entrega
    de recusa ICMP depende do sistema. Outros OSError são propagados.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        try:
            sock.connect((target_ip, port))
            sock.send(UDP_PAYLOAD)
            sock.recv(UDP_BUFFER_SIZE)
            return 'open'
        except ConnectionRefusedError:
            return 'closed'
        except TimeoutError:
            return 'open|filtered'
