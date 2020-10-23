#!/usr/bin/env python3
import csv
import time
import argparse

from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from pymodbus.compat import iteritems

def main(ip, csv_name, loop, delay):
    client = ModbusClient(ip, port=502)
    client.connect()
    while True:
        with open(csv_name) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                result  = client.read_input_registers(int(row[0]), int(row[1]),  unit=1)
                decoder = BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.Big, wordorder=Endian.Big)
                decoded = {
                    'string': decoder.decode_string(16),
                }
                for _, value in iteritems(decoded):
                    print ("%s:\t" % row[0], value)
                time.sleep(delay)
        if not loop:
            break
            
    client.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ip', help='target IP address')
    parser.add_argument('csv', help='csv file to be parsed')
    parser.add_argument('--delay', type=float, default=1, help='delay')
    parser.add_argument('--loop', action='store_true', help='loop')
    args = parser.parse_args()
    main(args.ip, args.csv, args.loop, args.delay)
