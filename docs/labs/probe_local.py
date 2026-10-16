"""Probe one loopback port using the project's actual scan functions."""
import argparse
from pathlib import Path
import sys

# The script lives two directories below the project modules.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import connection


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('protocol', choices=['tcp', 'udp'])
    parser.add_argument('port', type=int)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('port must be between 1 and 65535')
    probe = connection.connection_tcp if args.protocol == 'tcp' else connection.connection_udp
    print(probe('127.0.0.1', args.port, 1.0))


if __name__ == '__main__':
    main()
