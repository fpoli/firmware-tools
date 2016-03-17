#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from pic_loader import HexReader
import struct

record_type_name = {
    HexReader.RECORD_DATA: "data",
    HexReader.RECORD_EOF: "eof",
    HexReader.RECORD_EXTENDED_SEGMENT_ADDRESS: "extended segment address",
    HexReader.RECORD_START_SEGMENT_ADDRESS: "start segment address",
    HexReader.RECORD_EXTENDED_LINEAR_ADDRESS: "extended linear address",
    HexReader.RECORD_START_LINEAR_ADDRESS: "start linear address"
}


def view_hex(hex_reader):
    high_address = 0
    last_address = 0

    while True:
        (low_address, record_type, code) = hex_reader.get_code()

        if record_type == HexReader.RECORD_EOF or low_address is None:
            break  # EOF
        elif record_type == HexReader.RECORD_EXTENDED_LINEAR_ADDRESS:
            assert low_address == 0
            assert len(code) == 2
            high_address = (ord(code[0]) << 8) + ord(code[1])
            print "=== {}: {:04X}".format(
                record_type_name[record_type],
                high_address
            )
            continue
        elif record_type != HexReader.RECORD_DATA:
            print "=== {}: {}".format(
                record_type_name[record_type],
                " ".join([x.encode("hex") for x in code])
            )
            continue

        address = (high_address << 16) + low_address

        # Unprogrammed address range
        unprogrammed_len = address - last_address
        if unprogrammed_len > 0:
            print "::: From {:04X} to {:04X} ({} bytes): <unprogrammed>".format(
                last_address,
                last_address + unprogrammed_len - 1,
                unprogrammed_len
            )

        last_address = address

        # Send current data
        print "::: From {:04X} to {:04X} ({} bytes): {}".format(
            last_address,
            last_address + len(code) - 1,
            len(code),
            " ".join([x.encode("hex") for x in code])
        )

        if last_address % 4 == 0 and len(code) >= 4:
            # Read two little endian words (1 word = 16 bits)
            istr = [ord(code[x]) for x in (1, 0, 3, 2)]
            if istr[0] == 0xEF and istr[2] & 0xF0 == 0xF0:
                dst = ((((istr[2] & 0x0F) << 8) + istr[3] << 8) + istr[1]) << 1
                print "    GOTO {:05X}".format(dst)

        last_address += len(code)


def get_arguments():
    parser = argparse.ArgumentParser(
        description="View an HEX file"
    )
    parser.add_argument(
        "file",
        help="Input HEX file"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = get_arguments()
    hex_reader = HexReader(args.file)
    view_hex(hex_reader)
