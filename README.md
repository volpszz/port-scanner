# Python Port Scanner

A simple TCP Port Scanner developed in Python using the built-in `socket` module.

This project was created as a practical exercise to strengthen networking fundamentals, understand how TCP connections work, and gain hands-on experience with basic reconnaissance techniques commonly used in cybersecurity.

## Features

- TCP port scanning
- Hostname to IP resolution
- Custom timeout configuration
- Detection of open ports
- Basic exception handling
- Lightweight and easy to understand implementation

## Technologies Used

- Python 3
- Socket Library
- TCP/IP Networking

## How It Works

The scanner:

1. Receives a target hostname or IP address.
2. Resolves the hostname to an IPv4 address.
3. Iterates through a predefined list of ports.
4. Attempts a TCP connection using `socket.connect_ex()`.
5. Reports ports that accept connections.

## Default Ports

```python
[53, 22, 80, 111, 139, 443, 32768]
```

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/python-port-scanner.git
cd python-port-scanner
```

## Usage

Run the script:

```bash
python port_scanner.py
```

Example:

```text
Insert the target ip: scanme.nmap.org

--------------------------------------------------
be patient, scanning... 45.33.32.156
--------------------------------------------------

port 22 aberta!
port 80 aberta!
port 443 aberta!
```

## Learning Objectives

This project helped me practice:

- Python programming
- Socket programming
- TCP networking concepts
- Port scanning fundamentals
- Basic cybersecurity reconnaissance techniques
- Exception handling

## Disclaimer

This project is intended for educational purposes only. Only scan systems and networks that you own or have explicit permission to test.

## Author

Arthur Volpato Moreira

- Cybersecurity Student
- Linux, Networks and Infrastructure Enthusiast
- Python Developer
