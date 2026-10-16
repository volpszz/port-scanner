"""Local TCP listener for the study guide; no application protocol."""
import socket


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('127.0.0.1', 8000))
        server.listen()
        print('TCP ready on 127.0.0.1:8000', flush=True)
        while True:
            client, peer = server.accept()
            with client:
                client.settimeout(2)
                try:
                    data = client.recv(4096)
                    print(f'{peer}: {len(data)} application bytes', flush=True)
                except socket.timeout:
                    print(f'{peer}: no data before timeout', flush=True)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nServer stopped.')
