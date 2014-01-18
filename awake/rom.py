# This file is part of Awake - GB decompiler.
# Copyright (C) 2012  Wojciech Marczenko (devdri) <wojtek.marczenko@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import struct

class Rom(object):
    def __init__(self, filename):
        self.filename = filename
        with open(filename, 'rb') as f:
            self.data = f.read()

    def get(self, addr):
        return struct.unpack('B', self.data[addr.physical()])[0]

    def get_word(self, addr):
        lo = self.get(addr)
        hi = self.get(addr.offset(1))
        return (hi << 8) | lo

    def read(self, addr, length):
        out = []
        for i in range(length):
            out.append(self.get(addr.offset(i)))
        return out

    def numBanks(self):
        num = len(self.data) / 0x4000
        if len(self.data) % 0x4000 or not len(self.data):
            num += 1
        return num
