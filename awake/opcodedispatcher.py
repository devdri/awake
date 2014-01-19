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

from . import singledecoder
from . import instruction

class OpcodeDispatcher(object):

    def __init__(self, opcodeFormats):
        self.dispatchTable = dict()
        for bit_format in opcodeFormats:
            if not bit_format:
                continue

            decoder = singledecoder.SingleOpcodeDecoder(bit_format)
            for i in range(256):
                byte = i & 0xFF
                if decoder.match(byte):
                    self.dispatchTable[byte] = decoder

    def decode(self, database, rom, addr):
        entry = rom.get(addr)
        if entry not in self.dispatchTable:
            print('WARN: bad opcode', addr)
            return instruction.BadOpcode([entry], addr), None
        decoder = self.dispatchTable[entry]
        opcodes = rom.read(addr, decoder.length())
        return decoder.decode(database, opcodes, addr)
