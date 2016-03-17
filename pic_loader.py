#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
  Copyright 2013 Grégory Soutadé

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
import time
import os
import binascii
import time
from optparse import OptionParser
import traceback

class HexReader():

    RECORD_DATA = 0
    RECORD_EOF = 1
    RECORD_EXTENDED_SEGMENT_ADDRESS = 2
    RECORD_START_SEGMENT_ADDRESS = 3
    RECORD_LINEAR_SEGMENT_ADDRESS = 4
    RECORD_START_LINEAR_ADDRESS = 5
    RECORD_MAX = 5

    def __init__(self, filename):
        if not os.path.exists(filename):
            raise AssertionError('%s doesn\'t exists' % filename)

        f = open(filename, 'r')
        
        self.valid_lines = 0
        self.code = []
        self.code_pos = 0

        line_number = 0
        for line in f.readlines():
            line_number += 1
            crc = 0

            if len(line) == 0 or line.startswith('#'): continue

            self.valid_lines += 1

            # Start marker
            if not line.startswith(':'):
                raise AssertionError('Invalid file : line %d does not starts with \':\'' % line_number)
            line = line[1:]

            # Byte count
            try:
                byte_count = int('0x' + line[0:2], 16)
            except:
                raise AssertionError('Invalid file : line %d, invalid byte count' % line_number)
            line = line[2:]

            if len(line)/2 != int(byte_count+2+1+1): # Data + address + record type + CRC
                raise AssertionError('Invalid file : line %d, invalid byte count' % line_number)
            crc += byte_count

            # Address
            try:
                address = int('0x' + line[0:4], 16)
            except:
                raise AssertionError('Invalid file : line %d, invalid address' % line_number)
            crc += int('0x' + line[0:2], 16)
            crc += int('0x' + line[2:4], 16)
            line = line[4:]

            # Record type
            record_type = int(line[0:2])

            if record_type > self.RECORD_MAX:
                raise AssertionError('Invalid file : line %d, invalid record type' % line_number)
            
            line = line[2:]
            crc += record_type


            # CRC
            for i in range(0, byte_count):
                crc += int('0x' + line[i*2:(i*2)+2], 16)

            crc = int(crc) & 0xFF
            crc ^= 0xFF
            crc += 1
            crc &= 0xFF

            if crc != int('0x' + line[byte_count*2:byte_count*2+2], 16):
                raise AssertionError('Invalid file : line %d, invalid crc %d' % (line_number, crc))

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

    def __init__(self, hexfile, port='/dev/ttyUSB0', baudrate=115200, minicom=False):

        # Connect to serial
        # Parity is the most important !!
        self.ser = serial.Serial(port, baudrate, bytesize=serial.EIGHTBITS, parity=serial.PARITY_EVEN, \
                                stopbits=serial.STOPBITS_ONE, xonxoff=False, rtscts=False, \
                                timeout=1, writeTimeout=1)

        self.ser.setDTR(True)
        self.ser.setRTS(True)

        self.ser.flushInput()
        self.ser.flushOutput()

        self.line = 0

        # Read file
        if not hexfile is None:
            self.reader = HexReader(hexfile)

        # Upload file
            print 'File is ok' 

            self.resp = ('y', 'x')
            self.resp_pos = 0

            self.connected = False
            self.connect()

            self.send_code()

        # Go in minicom
        if minicom:
            self.minicom()

        # Close
        self.close(0)


    def close(self, val):
        self.ser.setDTR(False)
        self.ser.setRTS(False)
        self.ser.close()
        sys.exit(val)


    def _send_byte(self, byte):
        self.ser.write(byte)

        # print binascii.hexlify(byte)

        while True:
            c= self.ser.read(1)
            if c != 'g': break

        if c != self.resp[self.resp_pos]:
            if not self.connected:
                print 'Synchronisation lost ' + c
            else:
                print 'synchronisation breaked @ line %d' % (self.line)
            self.close(-1)
            
        self.resp_pos = (self.resp_pos+1)%2


    def connect(self):
        # Wait for start marker
        c = self.ser.read(1)

        if c != 'g':
            print 'Not connected'
            self.close(-1)

        self.connected = True

        self._send_byte('r')
        self.ser.flushInput()


    def send_code(self):
        print 'Sending code'

        self.line = 0
        last_address = 0
        nop = binascii.unhexlify('ff3f')
        pad = binascii.unhexlify('ff')

        while True:
            (address, record_type, code) = self.reader.get_code()
            if address == None: break # EOF
            self.line = self.line + 1
            if record_type != HexReader.RECORD_DATA: break
            # Pad with nop until current address
            while last_address != address:
                self._send_byte(nop[0])
                self._send_byte(nop[1])
                last_address += 2

            # Send current data
            while len(code) != 0:
                self._send_byte(code[0])
                code = code[1:]
                last_address += 1

        while ((last_address % 500) != 0):
            self._send_byte(pad[0])
            last_address = last_address + 1

        print 'Code successfully sent, you can reboot me'

        
    def minicom(self):
        print 'Go into minicom mode'
        # Go in minicom mode
        try:
            while True:
                c = self.ser.read(1)
                sys.stdout.write(c)
                sys.stdout.flush()
        except:
            pass
        self.ser.close()


if __name__ == '__main__':
    usage = 'Usage: %prog [options]\n' \
            '   Upload an HEX file to the Ready for PIC Board'
    optparser = OptionParser(usage=usage)
    optparser.add_option('-f', '--file', dest='file',
                         help='Input HEX file')
    optparser.add_option('-p', '--port', dest='port',
                         help='Port to use (default: /dev/ttyUSB0)',
                         default='/dev/ttyUSB0')
    optparser.add_option('-b', '--baudrate', dest='baudrate',
                         default='115200', type=int,
                         help='Baudrate (default: 115200)')
    optparser.add_option('-m', '--minicom', dest='minicom',
                         action='store_true', default=False,
                         help='Display board output')

    (options, args) = optparser.parse_args(sys.argv[1:])

    try:
        p = PICBoard(options.file, options.port, options.baudrate, options.minicom)
        
    except ValueError:
        pass
    except Exception, e:
        print e
