#!/usr/bin/env python3
import csv
import time
import argparse

from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian


def main(args):
    start_t = time.time()
    client = ModbusClient(args.ip, args.port)
    client.connect()
    end_t = time.time()
    time_t = (end_t - start_t) * 1000
    print("# connection established in %dms" % time_t)

    while True:
        with open(args.csv_file) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            for row in csv_reader:
                if row[0].startswith('#'):
                    continue

                register = int(row[0])
                register_length = int(row[1])
                try:
                    multiplier = float(row[2])
                except ValueError:
                    multiplier = 1
                encoding = row[3]
                start_t = time.time()
                result = client.read_input_registers(
                        register, register_length, unit=1
                )
                end_t = time.time()
                try:
                    decoder = BinaryPayloadDecoder.fromRegisters(
                        result.registers,
                        byteorder=Endian.Big,
                        wordorder=Endian.Big
                    )
                except Exception:
                    continue

                if encoding.upper() == 'CHAR':
                    decoded = decoder.decode_string(
                        register_length*2).decode()
                elif encoding.upper() == 'U8':
                    decoded = decoder.decode_8bit_uint() * multiplier
                elif encoding.upper() == 'U16':
                    decoded = decoder.decode_16bit_uint() * multiplier
                elif encoding.upper() == 'U32':
                    decoded = decoder.decode_32bit_uint() * multiplier
                elif encoding.upper() == 'S8':
                    decoded = decoder.decode_8bit_int() * multiplier
                elif encoding.upper() == 'S16':
                    decoded = decoder.decode_16bit_int() * multiplier
                elif encoding.upper() == 'S32':
                    decoded = decoder.decode_32bit_int() * multiplier
                else:
                    decoded = "FORMAT NOT SUPPORTED"

                time_t = (end_t - start_t) * 1000

                if args.comma:
                    print("%s,%s,%dms" % (register, decoded, time_t))
                else:
                    print("%s:\t%s\t%dms" % (register, decoded, time_t))
                time.sleep(args.delay)

        if not args.loop:
            break

    client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("ip", help="target IP address")
    parser.add_argument("csv_file", help="csv file to be parsed")
    parser.add_argument("--port", "-p", type=int, default=502, help="port")
    parser.add_argument("--delay", "-d", type=float, default=1, help="delay")
    parser.add_argument("--loop", "-l", action="store_true", help="loop")
    parser.add_argument("--comma", "-c", action="store_true",
                        help="use comma separator")
    args = parser.parse_args()
    main(args)
