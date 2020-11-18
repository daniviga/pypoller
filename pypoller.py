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
from pymodbus.exceptions import ModbusIOException

ENCODINGS = {
    "CHAR": "decoder.decode_string(register_length * 2)",
    "U8": "decoder.decode_8bit_uint()",
    "U16": "decoder.decode_16bit_uint()",
    "U32": "decoder.decode_16bit_uint()",
    "S8": "decoder.decode_8bit_int()",
    "S16": "decoder.decode_16bit_int()",
    "S32": "decoder.decode_32bit_int()",
}


def teardown():
    if client is not None:
        print("# closing connection to %s:%s" % (client.host, client.port), flush=True)
        client.close()


def log_error(error, msg):
    print(separator.join((str(error), msg)), flush=True)


def main(args):
    global client

    print("# connecting to %s:%s id %s" % (args.ip, args.port, args.slave))
    start_t = time.time()
    client = ModbusClient(args.ip, args.port, timeout=args.timeout)
    conn = client.connect()
    if not conn:
        exit("# unable to connect to %s:%s" % (args.ip, args.port))

    end_t = time.time()
    time_t = (end_t - start_t) * 1000
    print("# connection established in %dms" % time_t)
    print("# delay: %ss timeout: %ss" % (args.delay, args.timeout))

    while True:
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
                start_t = time.time()
                if function == "3":
                    result = client.read_holding_registers(
                        register, register_length, unit=args.slave
                    )
                elif function == "4":
                    result = client.read_input_registers(
                        register, register_length, unit=args.slave
                    )
                else:
                    log_error(register, "FUNCTION %s NOT SUPPORTED" % function)
                    continue
                end_t = time.time()

                if result.isError():
                    if isinstance(result, ModbusIOException):
                        log_error(register, "I/O ERROR (TIMEOUT)")
                    else:
                        log_error(register, "REGISTER NOT FOUND")
                    continue

                decoder = BinaryPayloadDecoder.fromRegisters(
                    result.registers,
                    byteorder=Endian.Big,
                    wordorder=Endian.Big,
                )

                try:
                    encoding = encoding.upper()
                    if encoding not in ENCODINGS:
                        log_error(encoding, "FORMAT NOT SUPPORTED")
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

                print(
                    separator.join(
                        (str(datetime.now()),
                         str(register),
                         str(decoded),
                         str(time_t))
                    ), flush=True
                )
                time.sleep(args.delay)

        if args.loop == 0:
            break
        time.sleep(args.loop)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("ip",
                        help="Target IP address")
    parser.add_argument("csv_file",
                        help="CSV file to be parsed")
    parser.add_argument("--port", "-p", type=int, default=502,
                        help="Target modbus port")
    parser.add_argument("--slave", "-s", type=int, default=1,
                        help="Slave ID")
    parser.add_argument("--timeout", "-t", type=float, default=3,
                        help="Time a client should wait for a request "
                             "to be processed (3 seconds)")
    parser.add_argument("--delay", "-d", type=float, default=0.1,
                        help="Delay between registers polling (100 ms)")
    parser.add_argument("--loop", "-l", type=float, default=0,
                        help="Loop over the CSV, with a delay")
    parser.add_argument("--comma", "-c", action="store_true",
                        help="Use comma separator")
    args = parser.parse_args()

    separator = "," if args.comma else "\t"

    atexit.register(teardown)
    main(args)
