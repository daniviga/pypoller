# pypoller
Modbus poller in Python

## Installation

### Virtual env creation
```bash
$ python3 -m venv venv
$ source venv/bin/activate
```

### Installation

#### Master

```bash
$ pip install https://github.com/daniviga/pypoller/archive/master.zip
```

#### Release

```bash
$ pip install https://github.com/daniviga/pypoller/releases/download/X.Y.Z/pypoller-X.Y.Z-py3-none-any.whl
```

### Development installation
```bash
$ git clone https://github.com/daniviga/pypoller.git
$ cd pypoller
$ pip install -r requirements-dev.txt -e .
```

## Usage
```bash
usage: pypoller.py [-h] [--port PORT] [--slave SLAVE] [--timeout TIMEOUT] [--delay DELAY] [--loop LOOP] [--comma] ip csv_file

positional arguments:
  ip                    Target IP address
  csv_file              CSV file to be parsed

optional arguments:
  -h, --help            show this help message and exit
  --port PORT, -p PORT  Target modbus port
  --slave SLAVE, -s SLAVE
                        Slave ID
  --timeout TIMEOUT, -t TIMEOUT
                        Time a client should wait for a request to be processed (3 seconds)
  --delay DELAY, -d DELAY
                        Delay between registers polling (100 ms)
  --loop LOOP, -l LOOP  Loop over the CSV, with a delay
  --comma, -c           Use comma separator

$ pypoller.py 192.168.0.120 demo/registers.csv --port 502 --slave 1 --loop 1 --delay 0.01
```


## Docker
```bash
$ docker run --rm -ti -v $(pwd)/demo:/io daniviga/pypoller 192.168.0.120 /io/registers.csv --port 502 --slave 1 --loop 1 --delay 0.01
```
