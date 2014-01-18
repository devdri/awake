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

from . import operand
from . import address

class JumpTable(object):
    def __init__(self, addr):
        self.addr = addr

        self.targets = []

        from . import disasm
        rom = disasm.cur_rom

        for i in range(256):
            a = addr.offset(i*2)
            lo = rom.get(a)
            hi = rom.get(a.offset(1))
            value = address.fromVirtualAndCurrent((hi<<8) | lo, addr)

            if not value.inPhysicalMem():
                break

            self.targets.append(operand.ProcAddress(value))

    def html(self):
        out = '<h1>Jump table at ' + str(self.addr) + '</h1>'
        out += '<pre>'
        i = 0
        for t in self.targets:
            out += str(i) + ' -> ' + t.html() + '\n'
            i += 1
        out += '</pre>'
        return out
