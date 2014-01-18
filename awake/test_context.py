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

import unittest
from .context import Context
from . import address
from . import operand
from . import placeholders
from . import instruction
from . import regutil

class Test(unittest.TestCase):

    def testDepend(self):
        self.assertFalse('A' in operand.Constant(1).getDependencies())
        self.assertFalse('B' in operand.LabelAddress(address.fromVirtual(1)).getDependencies())
        self.assertTrue('A' in placeholders.A.getDependencies())
        self.assertFalse('A' in placeholders.BC.getDependencies())
        self.assertTrue(regutil.splitRegister('HL') <= regutil.splitRegisters(placeholders.deref_HL.getDependencies()))

    def testContext(self):
        c = Context()
        self.assertFalse(c.hasValue('A'))
        c.setValueComplex('A')
        self.assertFalse(c.hasValue('A'))
        c.setValue('A', placeholders.B)
        self.assertTrue(c.hasValue('A'))
        c.setValue('B', operand.Constant(1))
        self.assertFalse(c.hasValue('A'))
        self.assertTrue(c.hasValue('B'))
        self.assertEquals(c.getValue('B').value, 1)

    def testLoadInstructions(self):
        context = Context()
        q = instruction.LoadInstruction('LD', placeholders.HL, operand.Constant(0xFFFF))
        a = instruction.LoadInstruction('LD', placeholders.A, operand.Constant(1))
        b = instruction.LoadInstruction('LD', placeholders.B, placeholders.deref_HL)
        c = instruction.LoadInstruction('LD', placeholders.deref_HL, placeholders.A)
        q = q.optimizedWithContext(context)
        a = a.optimizedWithContext(context)
        b = b.optimizedWithContext(context)
        c = c.optimizedWithContext(context)
        self.assertEquals(b.source.target.value, 0xFFFF)
        self.assertEquals(c.source.value, 1)

    def testDependencies(self):
        q = instruction.LoadInstruction('LD', placeholders.HL, operand.Constant(0xFFFF))
        a = instruction.LoadInstruction('LD', placeholders.A, operand.Constant(1))
        b = instruction.LoadInstruction('LD', placeholders.deref_HL, placeholders.A)
        c = instruction.LoadInstruction('LD', placeholders.B, placeholders.deref_HL)
        deps = set()
        deps = c.getDependencies(deps)
        self.assertEquals(regutil.joinRegisters(deps), set(['mem', 'HL']))
        deps = b.getDependencies(deps)
        self.assertEquals(regutil.joinRegisters(deps), set(['mem', 'HL', 'A']))
        deps = a.getDependencies(deps)
        self.assertEquals(regutil.joinRegisters(deps), set(['mem', 'HL']))
        deps = q.getDependencies(deps)
        self.assertEquals(regutil.joinRegisters(deps), set(['mem']))

if __name__ == "__main__":
    unittest.main()
