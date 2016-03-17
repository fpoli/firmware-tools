Firmware tools
==============

Useful scripts for microcontroller programming.


Description
-----------


### `pic_loader.py`

Command line loader for "Read for PIC" Board.

This script is took from [Grégory Soutadé's blog'](http://blog.soutade.fr/post/2013/03/command-line-loader-for-read-for-pic-board.html)([original script](http://soutade.fr/files/pic_loader.py)).

	./pic_loader.py -f image.hex
	./pic_loader.py -f image.hex --port /dev/ttyUSB0 --baudrate 115200
	./pic_loader.py -h


License (GPL v3)
----------------

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
