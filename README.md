# port-scanner

A networking and security learning project by [volpszz](https://github.com/volpszz), with a modular Python implementation, automated tests, and detailed learning resources.

Repository: [volpszz/port-scanner](https://github.com/volpszz/port-scanner).

An educational **IPv4** port scanner supporting TCP and UDP probes, with no third-party runtime dependencies.

> Only scan systems you own or have explicit permission to test. Even a simple connection can generate logs and alerts. The program does not verify authorization.

## Getting started

Requires **Python 3.10 or newer**. The refactored implementation was validated on Linux with Python 3.14.7. Other Python versions were not exercised during that validation.

Clone the repository:

```sh
git clone https://github.com/volpszz/port-scanner.git
cd port-scanner
```

Run commands from the project root. No package installation or `sudo` is required.

```sh
# Interactive menu: choose TCP, UDP, or both, then enter a target.
python main.py

# Run the same interface as a Python module.
python -m port_scanner

# Non-interactive: an explicit target defaults to TCP.
python -m port_scanner 127.0.0.1 --ports 22,80,443 --timeout 0.2

# Probe TCP and UDP in the specified port order.
python -m port_scanner 127.0.0.1 --protocol both --ports 8000,9999 --timeout 0.2

python -m port_scanner --help
```

`main.py` also accepts these arguments. Without `--ports`, the original list is used: `53,22,80,111,139,443,32768`. The default timeout is `1.0` second per socket operation. Without a target, the program prompts for a protocol unless `--protocol` is already provided, then prompts for the target.

- `--protocol`: `tcp`, `udp`, or `both`.
- `--ports`: comma-separated integers between 1 and 65535. Ranges are not supported. Duplicates are removed while preserving order.
- `--timeout`: a positive, finite number of seconds accepted by `socket.settimeout` in the current environment. Configuration checks the supported range using a local socket that is closed without connecting. Excessively large finite values, such as `1e20`, are rejected as invalid configuration with exit code `2`; the project does not impose an arbitrary fixed upper limit. This is not a scan-wide deadline and does not limit DNS resolution time.
- The target may be an IPv4 address or hostname. Only one address returned by the resolver is scanned.

## Understanding the output

Each result follows the format `port/protocol: state`.

| State | Meaning |
| --- | --- |
| `open` | The TCP handshake succeeded or a UDP response was received. |
| `closed` | An explicit refusal was received. UDP refusal delivery depends on the operating system. |
| `filtered/unknown` | The TCP attempt was inconclusive because of a timeout or temporary unavailability. This alone does not prove that a firewall is present. |
| `open\|filtered` | No UDP response arrived before the timeout; an open port cannot be distinguished from filtered traffic. |
| `error: ...` | Another network error occurred. Do not interpret this as a closed port. |

The UDP payload is only `b'probe'`. DNS and other services may ignore it even when their ports are open. The scanner does not identify services, versions, or vulnerabilities. It does not support IPv6, SYN scans, parallel probing, host discovery, or subnet scans.

### Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Execution completed; results may still include closed ports, inconclusive states, or individual probe errors. |
| `1` | The target could not be resolved. |
| `2` | Invalid arguments or configuration. |
| `130` | Interrupted with Ctrl+C or end of interactive input. |

Configuration and resolution errors, along with interruption messages, go to `stderr`. Results and prompts go to `stdout`. Programming errors are not converted into network results.

## Running the tests

```sh
python -m unittest -v
```

Tests cover configuration, orchestration, CLI behavior, compatibility, and real sockets on `127.0.0.1`. Test servers use temporary ports and do not depend on public hosts. See the [contributing guide](CONTRIBUTING.md) (Portuguese) for details.

## Using the scanner as a library

```python
from port_scanner.config import ScanConfig
from port_scanner.scanner import scan

config = ScanConfig(
    target='127.0.0.1',
    ports=(8000, 9999),
    protocols=('tcp', 'udp'),
    timeout=0.2,
)
for result in scan(config):
    print(result.target_ip, result.port, result.protocol, result.state)
```

`scan()` is a generator: resolution and probing start when it is iterated. Resolution failures propagate as `socket.gaierror`. Hostname encoding failures during resolution, such as an ASCII label containing 64 characters, are normalized to that exception and produce CLI exit code `1`. This conversion does not wrap probe execution. An individual probe's `OSError` becomes a `ScanResult` with an error state.

## Documentation and learning resources

The README and GitHub repository description are in English. The detailed documentation and study materials below are in **Portuguese**.

- [Complete study guide — PDF](docs/guia-do-projeto.pdf): networking fundamentals, a module-by-module walkthrough, tests, modification recipes, and numbered source listings.
- [Editable study guide — Markdown](docs/GUIA-DO-PROJETO.md): the source used to generate the PDF. Chapter 12 explains how to regenerate it; PDF dependencies are optional and do not affect the scanner.
- [Architecture and design decisions](docs/ARQUITETURA.md): a map of the codebase, execution flow, contracts, and extension points.
- [Contributing guide](CONTRIBUTING.md): how to change, test, and review the project.
- [Earlier study material](docs/LEIA-ME.md): historical workbook, source snapshot, and labs. These describe an earlier implementation, not the current module structure.

## Refactoring and compatibility

The logic previously concentrated in `main.py` and `connection.py` is now separated by responsibility under `port_scanner/`. The interactive menu, legacy probe names, TCP/UDP states, default ports, and default timeout are preserved. The refactor adds command-line arguments, validated configuration, and tests organized by layer.

`connection.py` is a compatibility facade; new code should import the package. The legacy `main.PORTS` and `main.TIMEOUT` attributes remain available for reading, but changing them no longer configures the scanner: use `ScanConfig` or CLI options. Error messages now use `stderr`.

The previous repository entry point, `simplePort_scanner.py`, has been replaced by `main.py` and the `port_scanner/` package. Its original contents remain available in Git history.

## License

[MIT](LICENSE), preserving the original authorship of volpsz.
