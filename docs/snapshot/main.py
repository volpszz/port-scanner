import socket

import connection


PORTS = [53, 22, 80, 111, 139, 443, 32768]
TIMEOUT = 1.0


def main():
    try:
        print('Scan only hosts you own or have permission to test.')
        connection_type = connection.connection_choice()
        target = input('Insert the target IP or hostname: ').strip()
        target_ip = socket.gethostbyname(target)

        print('-' * 50)
        print(f'Scanning {target_ip} ({connection_type})...')
        print('-' * 50)

        probes = []
        if connection_type in ('TCP', 'BOTH'):
            probes.append(('tcp', connection.connection_tcp))
        if connection_type in ('UDP', 'BOTH'):
            probes.append(('udp', connection.connection_udp))

        for port in PORTS:
            for protocol, probe in probes:
                try:
                    state = probe(target_ip, port, TIMEOUT)
                except OSError as error:
                    state = f'error: {error}'
                print(f'{port}/{protocol}: {state}')

    except socket.gaierror as error:
        print(f'Cannot resolve target: {error}')
        return 1
    except (KeyboardInterrupt, EOFError):
        print('\nProgram closed by the user!')
        return 130
    return 0


if __name__ == '__main__':
    exit_code = main()
    if exit_code:
        raise SystemExit(exit_code)
