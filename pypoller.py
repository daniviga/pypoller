#!/usr/bin/env python3
import csv
import time
import struct
import argparse

from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from pymodbus.exceptions import ConnectionException


def log_error(error, msg):
    print(separator.join((str(error), msg)))


def main(args):
    print("# connecting to %s:%s id %s" % (args.ip, args.port, args.slave))
    start_t = time.time()
    client = ModbusClient(args.ip, args.port)
    c = client.connect()
    if not c:
        exit("# unable to connect to %s:%s" % (args.ip, args.port))

    end_t = time.time()
    time_t = (end_t - start_t) * 1000
    print("# connection established in %dms" % time_t)

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
                try:
                    decoder = BinaryPayloadDecoder.fromRegisters(
                        result.registers,
                        byteorder=Endian.Big,
                        wordorder=Endian.Big,
                    )
                except Exception:
                    log_error(register, "REGISTER NOT FOUND")
                    continue

                try:
                    if encoding.upper() == "CHAR":
                        decoded = (
                            decoder.decode_string(register_length * 2)
                            .decode()
                            .rstrip()
                        )
                    elif encoding.upper() == "U8":
                        decoded = decoder.decode_8bit_uint() * multiplier
                    elif encoding.upper() == "U16":
                        decoded = decoder.decode_16bit_uint() * multiplier
                    elif encoding.upper() == "U32":
                        decoded = decoder.decode_32bit_uint() * multiplier
                    elif encoding.upper() == "S8":
                        decoded = decoder.decode_8bit_int() * multiplier
                    elif encoding.upper() == "S16":
                        decoded = decoder.decode_16bit_int() * multiplier
                    elif encoding.upper() == "S32":
                        decoded = decoder.decode_32bit_int() * multiplier
                    else:
                        log_error(encoding.upper(), "FORMAT NOT SUPPORTED")
                        continue
                except struct.error as e:
                    decoded = "DECODE FAILED (e:'%s' raw:'%s')" % (
                        e,
                        decoder.decode_string(register_length * 2).decode(),
                    )

                time_t = round((end_t - start_t) * 1000, 2)

                print(
                    separator.join((str(register), str(decoded), str(time_t)))
                )
                time.sleep(args.delay)

        if args.loop == 0:
            break
        time.sleep(args.loop)

    client.close()


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
    parser.add_argument("--delay", "-d", type=float, default=0.1,
                        help="Delay between registers polling. "
                             "Default is 100ms")
    parser.add_argument("--loop", "-l", type=float, default=0,
                        help="Loop over the CSV, with a delay")
    parser.add_argument("--comma", "-c", action="store_true",
                        help="Use comma separator")
    args = parser.parse_args()

    if args.comma:
        separator = ","
    else:
        separator = "\t"

    main(args)
