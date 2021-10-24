#!/usr/bin/env python3
import csv
import time
import struct
import atexit
import argparse

from datetime import datetime
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from pymodbus.exceptions import (
    ModbusException,
    ModbusIOException,
    ConnectionException,
)

ENCODINGS = {
    "CHAR": "decoder.decode_string(register_length * 2)",
    "U16": "decoder.decode_16bit_uint()",
    "U32": "decoder.decode_32bit_uint()",
    "U64": "decoder.decode_64bit_uint()",
    "S16": "decoder.decode_16bit_int()",
    "S32": "decoder.decode_32bit_int()",
    "S64": "decoder.decode_64bit_int()",
}

LOG = 0
ERR = 1

average = 100
errors = 0
client = None


def teardown():
    if client is not None:
        print(
            "# closing connection to %s:%s\n"
            "# average: %s, errors: %s"
            % (client.host, client.port, average, errors),
            flush=True,
        )
        client.close()


def init(client, args):
    print("# connecting to %s:%s id %s" % (args.ip, args.port, args.slave))
    start_t = time.time()
    conn = client.connect()
    if not conn:
        exit("# unable to connect to %s:%s" % (args.ip, args.port))

    end_t = time.time()
    time_t = (end_t - start_t) * 1000
    print("# connection established in %dms" % time_t)

    return client


# 0 standard
# 1 error
def log(msg, severity=0):
    global errors

    if severity == 0:
        prefix = "%s" % datetime.now()
    else:
        errors += 1
        prefix = "#! %s" % datetime.now()

    if isinstance(msg, tuple):
        msg = separator.join(str(s) for s in msg)

    print(separator.join((prefix, client.host, msg)), flush=True)


def main(args):
    global average
    global errors
    global client

    client = init(ModbusClient(args.ip, args.port, timeout=args.timeout), args)
    atexit.register(teardown)

    print("# delay: %ss timeout: %ss" % (args.delay, args.timeout))
    print("# smoothing factor %f" % args.factor)
    smoothing_factor = args.factor

    print(
        separator.join(
            (
                "Timestamp",
                "IP",
                "Register",
                "Value",
                "Time (ms)",
                "Average (ms)",
                "Errors",
            )
        ),
        flush=True,
    )

    while True:
        hard_errors = 0
        with open(args.csv_file) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            for row in csv_reader:
                if row[0].startswith("#"):
                    continue

                function = row[0]
                register = int(row[1])
                register_length = int(row[2])
                try:
                    multiplier = float(row[3])
                except ValueError:
                    multiplier = 1
                encoding = row[4]

                # check if socket is still alive, otherwise re-open it
                if not client.is_socket_open():
                    client.connect()

                start_t = time.time()

                try:
                    if function == "3":
                        result = client.read_holding_registers(
                            register, register_length, unit=args.slave
                        )
                    elif function == "4":
                        result = client.read_input_registers(
                            register, register_length, unit=args.slave
                        )
                    else:
                        log(
                            (register, "FUNCTION %s NOT SUPPORTED" % function),
                            ERR,
                        )
                        continue
                except ConnectionException as e:
                    hard_errors += 1
                    log(str(e), ERR)

                    # limit hard failures to 5, then exit
                    if hard_errors < 5:
                        continue
                    else:
                        exit("too many connection attempts")

                end_t = time.time()

                if result.isError():
                    if isinstance(result, ModbusIOException):
                        log((register, "I/O ERROR (TIMEOUT)"), ERR)
                    elif isinstance(result, ModbusException):
                        log((register, "REGISTER NOT FOUND"), ERR)
                    else:
                        log((register, "GENERIC MODBUS ERROR"), ERR)
                    continue

                decoder = BinaryPayloadDecoder.fromRegisters(
                    result.registers,
                    byteorder=Endian.Big,
                    wordorder=Endian.Big,
                )

                try:
                    encoding = encoding.upper()
                    # Add support for encoding guessing
                    if encoding in ("U", "S"):
                        encoding = "%s%s" % (encoding, register_length * 16)

                    if encoding not in ENCODINGS:
                        log((register, "FORMAT %s NOT SUPPORTED" % encoding),
                            ERR)
                        continue

                    decoded = eval(ENCODINGS[encoding])

                    # Apply transformations
                    if isinstance(decoded, bytes):
                        decoded = decoded.decode().rstrip()
                    else:
                        decoded = round(decoded * multiplier, 3)

                except struct.error as e:
                    decoded = "DECODE FAILED (e:'%s' raw:'%s')" % (
                        e,
                        decoder.decode_string(register_length * 2).decode(),
                    )

                time_t = round((end_t - start_t) * 1000, 2)

                average = round(
                    (smoothing_factor * time_t)
                    + (1 - smoothing_factor) * average,
                    2,
                )

                log((register, decoded, time_t, average, errors), LOG)
                time.sleep(args.delay)

        if args.loop == -1:
            break
        time.sleep(args.loop)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("ip",
                        help="Target IP address")
    parser.add_argument("csv_file",
                        help="Modbus map CSV file to be parsed")
    parser.add_argument("--port", "-p", type=int, default=502,
                        help="Target modbus port")
    parser.add_argument("--slave", "-s", type=int, default=1,
                        help="Slave ID")
    parser.add_argument("--timeout", "-t", type=float, default=3,
                        help="Time a client should wait for a request "
                             "to be processed (3 seconds)")
    parser.add_argument("--delay", "-d", type=float, default=0.1,
                        help="Delay between registers polling (100 ms)")
    parser.add_argument("--loop", "-l", type=float, default=-1, const=0,
                        nargs="?",
                        help="Loop over the CSV, with an optional delay")
    parser.add_argument("--comma", "-c", action="store_true",
                        help="Use comma separator in output")
    parser.add_argument("--factor", "-f", type=float, default=0.05,
                        help="Exponential smoothing factor from 0 to 1 (0.05)")
    args = parser.parse_args()

    separator = "," if args.comma else "\t"

    main(args)
