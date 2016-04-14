Firmware tools
==============

Useful scripts for microcontroller programming.


Description
-----------


### `hex_viewer.py`

View the content of an Intel HEX formatted file.

	./hex_viewer.py image.hex
	./hex_viewer.py -h


### `pic_loader.py`

Command line loader for "Read for PIC" Board.

This script is based on [Grégory Soutadé's](http://blog.soutade.fr/post/2013/03/command-line-loader-for-read-for-pic-board.html) [original script](http://soutade.fr/files/pic_loader.py).

	./pic_loader.py -f image.hex
	./pic_loader.py -f image.hex --port /dev/ttyUSB0 --baudrate 115200
	./pic_loader.py -h


### `./listen_serial.py`

Open a serial connection and display every incoming byte.

	./listen_serial.py
	./listen_serial.py --detailed
	./listen_serial.py --port /dev/ttyUSB0 --baudrate 115200
	./listen_serial.py -h


### `plot_stdin.py`

Plot values received from stdin. Multiple values on the same line are treated as different series.

Very useful to plot data received on serial connection with `./listen_serial.py`.

	echo -e "1\n 2\n 3\n 4\n 5\n" | ./plot_stdin.py -n 1 --xlen 10
	echo -e "1 2 3\n 4 5 6\n" | ./plot_stdin.py -n 3 --xlen 5
	echo "-1 +2.3485 -.654" | ./plot_stdin.py -n 3 --xlen 5
	echo "here is 1 and 2 and 3" | ./plot_stdin.py -n 3 --xlen 5
	./listen_serial.py | ./plot_stdin.py -n 1
	./plot_stdin.py -h


License (GPL v3)
----------------

Original work Copyright (C) 2013 Grégory Soutadé

Modified work Copyright (C) 2016 Federico Poli

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
