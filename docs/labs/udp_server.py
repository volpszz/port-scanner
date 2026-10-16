"""Local UDP echo server; --silent receives but does not reply."""
import argparse
import socket


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--silent', action='store_true')
    args = parser.parse_args()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
        server.bind(('127.0.0.1', 9999))
        print(f'UDP ready on 127.0.0.1:9999; silent={args.silent}', flush=True)
        while True:
            data, peer = server.recvfrom(4096)
            print(f'{peer}: {len(data)} bytes received', flush=True)
            if not args.silent:
                server.sendto(data, peer)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nServer stopped.')
