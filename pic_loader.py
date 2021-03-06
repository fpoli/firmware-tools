#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
  Original work Copyright 2013 Grégory Soutadé
  Modified work Copyright 2016 Federico Poli

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys
import serial
import os
import binascii
import argparse


class HexReader():
    RECORD_DATA = 0
    RECORD_EOF = 1
    RECORD_EXTENDED_SEGMENT_ADDRESS = 2
    RECORD_START_SEGMENT_ADDRESS = 3
    RECORD_EXTENDED_LINEAR_ADDRESS = 4
    RECORD_START_LINEAR_ADDRESS = 5
    RECORD_MAX = 5

    def __init__(self, filename):
        if not os.path.exists(filename):
            raise AssertionError("%s doesn't exists" % filename)

        f = open(filename, "r")

        self.valid_lines = 0
        self.code = []
        self.code_pos = 0

        line_number = 0
        for line in f.readlines():
            line_number += 1
            crc = 0

            if len(line) == 0 or line.startswith("#"): continue

            self.valid_lines += 1

            # Start marker
            if not line.startswith(":"):
                raise AssertionError("Invalid file : line %d does not starts with \":\"" % line_number)
            line = line[1:]

            # Remove ending whitespaces
            line = line.rstrip()

            # Byte count
            try:
                byte_count = int("0x" + line[0:2], 16)
            except:
                raise AssertionError("Invalid file : line %d, invalid byte count" % line_number)
            line = line[2:]

            if len(line)/2 != int(byte_count+2+1+1): # Data + address + record type + CRC
                raise AssertionError("Invalid file : line %d, invalid byte count" % line_number)
            crc += byte_count

            # Address
            try:
                address = int("0x" + line[0:4], 16)
            except:
                raise AssertionError("Invalid file : line %d, invalid address" % line_number)
            crc += int("0x" + line[0:2], 16)
            crc += int("0x" + line[2:4], 16)
            line = line[4:]

            # Record type
            record_type = int(line[0:2])

            if record_type > self.RECORD_MAX:
                raise AssertionError("Invalid file : line %d, invalid record type" % line_number)

            line = line[2:]
            crc += record_type

            # CRC
            for i in range(0, byte_count):
                crc += int("0x" + line[i*2:(i*2)+2], 16)

            crc = int(crc) & 0xFF
            crc ^= 0xFF
            crc += 1
            crc &= 0xFF

            if crc != int("0x" + line[byte_count*2:byte_count*2+2], 16):
                raise AssertionError("Invalid file : line %d, invalid crc %d" % (line_number, crc))

            self.code.append((address, record_type, binascii.unhexlify(line[0:byte_count*2])))

            if record_type == self.RECORD_EOF:
                break

    def get_code(self):
        if self.code_pos < self.valid_lines:
            ret = self.code[self.code_pos]
            self.code_pos += 1
            return ret

        return (None, None, None)


class PICBoard():
    def __init__(self, hexfile, port="/dev/ttyUSB0", baudrate=115200):
        # Connect to serial
        self.ser = serial.Serial(
            port,
            baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,  # PARITY_EVEN
            stopbits=serial.STOPBITS_ONE,
            xonxoff=False,
            rtscts=False,
            timeout=1,
            writeTimeout=1
        )

        self.ser.setDTR(True)
        self.ser.setRTS(True)

        self.ser.flushInput()
        self.ser.flushOutput()

        self.line = 0

        if hexfile is not None:
            # Read file
            self.reader = HexReader(hexfile)

            print "HEX file is ok"

            self.resp = ("y", "x")
            self.resp_pos = 0

            self.connected = False
            self.connect()

            # Upload file
            self.send_code()

        self.close(0)

    def close(self, val):
        self.ser.setDTR(False)
        self.ser.setRTS(False)
        self.ser.close()
        sys.exit(val)

    def _send_byte(self, byte, address):
        if address >= 0x7CC0:
            raise Exception(
                "Dangerous exception! "
                "This script tried to overwrite the bootloader!"
            )

        self.ser.write(byte)

        while True:
            c = self.ser.read(1)
            if c != "g": break

        if c != self.resp[self.resp_pos]:
            if not self.connected:
                print "Synchronisation lost " + c
            else:
                print "Synchronisation breaked @ line %d" % (self.line)
            self.close(-1)

        self.resp_pos = (self.resp_pos + 1) % 2

    def connect(self):
        # Wait for start marker
        c = self.ser.read(1)

        if c != "g":
            print "Not connected"
            self.close(-1)

        self.connected = True

        self._send_byte("r", 0)
        self.ser.flushInput()

    def send_code(self):
        print "Sending code..."

        self.line = 0
        high_address = 0

        # Address (from 0) of the next byte that is going to be written
        cursor_address = 0

        # What value with wich to fill unused program memory?
        # There is no "Preferred Way", it depends what you want to do:
        #  a. Leave it as it is, in a non-erased state 0xFFFFFF - Compiler
        #     default
        #  b. Fill it with RESET. If code is executed it resets and starts over
        #  c. Fill it with NOP. Will run through NOP's until an invalid
        #     address or another instruction reached
        # Note that code may be stored as Words with low byte first.
        filler = binascii.unhexlify("ffff")

        while True:
            (low_address, record_type, code) = self.reader.get_code()

            if record_type == HexReader.RECORD_EOF or low_address == None:
                print "End of HEX file reached"
                break  # EOF

            self.line += 1

            if record_type == HexReader.RECORD_EXTENDED_LINEAR_ADDRESS:
                assert low_address == 0
                assert len(code) == 2
                high_address = (ord(code[0]) << 8) + ord(code[1])
                continue
            elif record_type != HexReader.RECORD_DATA:
                print "Unknown record_type {} at line {}: aborting".format(
                    record_type,
                    self.line
                )
                break

            address = (high_address << 16) + low_address

            if address >= 0x7CC0:
                print "End of programmable region reached"
                break

            # Pad with filler until current address
            while cursor_address < address:
                filler_pos = cursor_address % len(filler)
                self._send_byte(filler[filler_pos], cursor_address)
                cursor_address += 1

            # Send current data
            for byte in code:
                self._send_byte(byte, cursor_address)
                cursor_address += 1

        # Pad with filler until the end of a block of 64 bytes
        while (cursor_address == 0 or cursor_address % 64 != 0):
            filler_pos = cursor_address % len(filler)
            self._send_byte(filler[filler_pos], cursor_address)
            cursor_address += 1

        print "Code successfully sent, you can reboot the board"


def get_args():
    parser = argparse.ArgumentParser(
        description="Upload an HEX file to the Ready for PIC Board"
    )
    parser.add_argument(
        "-f", "--file",
        help="Input HEX file",
        required=True
    )
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
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()

    PICBoard(
        args.file,
        args.port,
        args.baudrate
    )
