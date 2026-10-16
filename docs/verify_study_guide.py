"""Exercise the study guide labs using real loopback traffic."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def probe(protocol, port):
    run = subprocess.run(
        [sys.executable, 'docs/labs/probe_local.py', protocol, str(port)],
        cwd=ROOT, capture_output=True, text=True, timeout=5, check=True,
    )
    return run.stdout.strip()


def experiment(server, arguments, protocol, port, expected):
    process = subprocess.Popen(
        [sys.executable, '-u', f'docs/labs/{server}', *arguments],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        ready = process.stdout.readline().strip()
        if 'ready on' not in ready:
            raise RuntimeError(f'Server did not start: {ready}')
        result = probe(protocol, port)
        assert result == expected, (result, expected)
        return f'{ready}\n{protocol}/{port}: {result}'
    finally:
        process.terminate()
        try:
            process.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()


def main():
    report = [
        experiment('tcp_server.py', [], 'tcp', 8000, 'open'),
        f'tcp/8000 after shutdown: {probe("tcp", 8000)}',
        experiment('udp_server.py', [], 'udp', 9999, 'open'),
        experiment('udp_server.py', ['--silent'], 'udp', 9999, 'open|filtered'),
        f'udp/9999 after shutdown: {probe("udp", 9999)}',
    ]
    assert report[1].endswith(': closed'), report[1]
    assert report[-1].endswith(': closed'), report[-1]
    suite = subprocess.run([sys.executable, '-m', 'unittest', '-v'], cwd=ROOT / 'docs/snapshot',
                           capture_output=True, text=True, timeout=20, check=True)
    text = '\n\n'.join(report) + '\n\n' + suite.stdout + suite.stderr
    (ROOT / 'docs/verificacao-laboratorios.txt').write_text(text)
    print(text)


if __name__ == '__main__':
    main()
