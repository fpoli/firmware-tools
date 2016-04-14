#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import serial
import argparse
import string


def is_printable(c):
    return ord(c) < 127 and c in string.printable and not c.isspace()


def listen_serial(port, baudrate, detailed=False):
    # Connect to serial
    comm = serial.Serial(
        port,
        baudrate,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        xonxoff=False,
        rtscts=False,
        timeout=1,
        writeTimeout=1
    )

    comm.setDTR(True)
    comm.setRTS(True)

    comm.flushInput()
    comm.flushOutput()

    try:
        print >> sys.stderr, "Listening..."
        while True:
            data = comm.read(1)
            if detailed:
                for c in data:
                    print "Received: 0b{:08b} 0x{:02X} {:3} {}".format(
                        ord(c),
                        ord(c),
                        ord(c),
                        "'{}'".format(c) if is_printable(c) else ""
                    )
            else:
                sys.stdout.write(data)
                sys.stdout.flush()
    except Exception as e:
        print >> sys.stderr, "/!\ {}".format(e)

    comm.close()
    print >> sys.stderr, "Closed."


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", "--port",
        default="/dev/ttyUSB0",
        help="Port to use (default: /dev/ttyUSB0)"
    )
    parser.add_argument(
        "-b", "--baudrate",
        type=int,
        default=115200,
        help="Baudrate (default: 115200)"
    )
    parser.add_argument(
        "-d", "--detailed",
        action="store_true",
        help="View details for every received byte"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = get_arguments()
    listen_serial(args.port, args.baudrate, args.detailed)
