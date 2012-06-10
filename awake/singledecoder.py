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

from collections import defaultdict
import instruction
import operand
import placeholders
import opcodeeffect
import context
import expression

def fillOperand(text, params, argument, next_addr):
    e = expression.parse(text)
    ctx = make_context(params, argument, next_addr)
    return e.optimizedWithContext(ctx)

def make_context(params, argument, next_addr):
    ctx = context.Context()
    if next_addr.bank() > 0:
        ctx.setValue('ROMBANK', operand.Constant(next_addr.bank()))
    ctx.setValue('v8', operand.Constant(argument))
    ctx.setValue('FF00_v8', operand.Constant(0xFF00 + argument))
    ctx.setValue('v16', operand.Constant(argument))
    offset = argument
    if offset & 0x80:  # convert to signed offset
        offset -= 0x100
    ctx.setValue('v8_rel', operand.Constant(next_addr.offset(offset).virtual()))
    for p in params:
        value = placeholders.get(p, params[p])
        ctx.setValue('#'+p, value)
    return ctx

class SingleOpcodeDecoder(object):
    def __init__(self, text):

        bit_format, effect_format = text.split('@', 2)

        items = bit_format.split(None, 3)

        self.bitPattern = items[0]
        self.cycles = int(items[1])
        self.name = items[2];

        operandText = "";
        if len(items) >= 4:
            operandText = items[3]

        if not operandText:
            self.operands = []
        else:
            self.operands = [x.strip() for x in operandText.split(", ")]

        if "v16" in operandText:
            self.argSize = 2;
        elif "v8" in operandText:
            self.argSize = 1;
        else:
            self.argSize = 0;

        assert len(self.bitPattern) == 8

        self.effect = opcodeeffect.OpcodeEffect(effect_format)


    def matchBits(self, opcode):
        params = defaultdict(int)
        opcode_bits = bin(opcode)[2:].zfill(8)

        for (x, y) in zip(self.bitPattern, opcode_bits):
            if x in ('0', '1'):
                if x != y:
                    return None
            else:
                # update according parameter
                params[x] <<= 1
                params[x] |= int(y)

        return params

    def match(self, opcode):
        return self.matchBits(opcode) is not None

    def length(self):
        return 1 + self.argSize

    def decode(self, opcodes, addr):
        assert len(opcodes) == self.length()

        params = self.matchBits(opcodes[0])

        argument = 0
        if self.argSize == 1:
            argument = opcodes[1]
        elif self.argSize == 2:
            argument = (opcodes[2] << 8) | opcodes[1];

        next_addr = addr.offset(self.length())

        out_operands = [
            fillOperand(text, params, argument, next_addr) for text in self.operands
        ]

        reads, writes, values, loads = self.effect.filled(params, make_context(params, argument, next_addr))

        return instruction.make(self.name, out_operands, addr, reads, writes, values, loads), next_addr

