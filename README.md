# pypoller
Modbus poller in Python

## Installation

### Virtual env creation
```bash
$ python3 -m venv venv
$ source venv/bin/activate
```

### Dependencies installation
```bash
$ pip install -U pip -r requirements.txt
```

### Dev stuff
```bash
$ pip install -U pip -r requirements.txt -r requirements-dev.txt
```

## Usage
```bash
$ ./pypoller.py 192.168.0.120 demo/registers.csv --port 502 --loop --delay 0.01
```
