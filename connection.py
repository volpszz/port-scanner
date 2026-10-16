"""Fachada para importações antigas; prefira port_scanner em código novo.

Preserva nomes públicos e assinaturas. O menu pertence à CLI e as operações
de rede ficam em probes. Nenhuma tarefa é iniciada durante a importação.
"""
from port_scanner.cli import choose_protocol as connection_choice
from port_scanner.probes import probe_tcp as connection_tcp
from port_scanner.probes import probe_udp as connection_udp

__all__ = ['connection_choice', 'connection_tcp', 'connection_udp']
