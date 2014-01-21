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

from awake import address
from awake.operand import ProcAddress

class JumpTable(object):
    def __init__(self, proj, addr):
        self.addr = addr
        self.targets = []

        for i in range(256):
            a = addr.offset(i*2)
            lo = proj.rom.get(a)
            hi = proj.rom.get(a.offset(1))
            value = address.fromVirtualAndCurrent((hi<<8) | lo, addr)

            if not value.inPhysicalMem():
                break

            self.targets.append(ProcAddress(value))

    def render(self, renderer):
        with renderer.lineAddress(self.addr):
            with renderer.comment():
                renderer.hline()
                renderer.startNewLine()
                renderer.write('jumptable ')
                renderer.writeSymbol(self.addr, 'jumptable')
                renderer.hline()
        with renderer.indent():
            i = 0
            for t in self.targets:
                with renderer.lineAddress(self.addr.offset(i*2)):
                    renderer.startNewLine()
                    renderer.write(str(i) + ' -> ')
                    t.render(renderer)
                i += 1
