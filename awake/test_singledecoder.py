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
from .singledecoder import SingleOpcodeDecoder
from . import address

class Test(unittest.TestCase):


    def testMatchNop(self):
        op = SingleOpcodeDecoder("00000000 1 NOP");
        self.assertTrue(op.match(0));
        self.assertFalse(op.match(1));

    def testMatch(self):
        op = SingleOpcodeDecoder("11100110 2 AND   A, v8");
        self.assertTrue(op.match(0b11100110));
        self.assertFalse(op.match(0b11000110));

    def testMatchParams(self):
        op = SingleOpcodeDecoder("01SSSZZZ 1 LD    #S, #Z");
        self.assertTrue(op.match(0b01000000));
        self.assertTrue(op.match(0b01111111));
        self.assertFalse(op.match(0b11000000));

    def testLength(self):
        op = SingleOpcodeDecoder("00000000 1 NOP");
        self.assertEquals(op.length(), 1);
        op = SingleOpcodeDecoder("11100110 2 AND   A, v8");
        self.assertEquals(op.length(), 2);
        op = SingleOpcodeDecoder("11100000 3 LD    [FF00+v8], A");
        self.assertEquals(op.length(), 2);
        op = SingleOpcodeDecoder("001FF000 2 JP    v8_rel, #F");
        self.assertEquals(op.length(), 2);
        op = SingleOpcodeDecoder("00001000 5 LD16  [v16], SP");
        self.assertEquals(op.length(), 3);

    def testDecode(self):
        op = SingleOpcodeDecoder("00000000 1 NOP");
        self.assertEquals(str(op.decode([0], address.fromPhysical(0))), "NOP");

        op = SingleOpcodeDecoder("11100110 2 AND   A, v8");
        self.assertEquals(str(op.decode([0b11100110, 0xfa], address.fromPhysical(0))).strip().upper(), "AND\tA, 0XFA");

        op = SingleOpcodeDecoder("11100000 3 LD    [FF00+v8], A");
        self.assertEquals(str(op.decode([0b11100000, 0xfa], address.fromPhysical(0))).strip().upper(), "LD\t[(V):FFFA], A");

        op = SingleOpcodeDecoder("001FF000 2 JP    v8_rel, #F");
        self.assertEquals(str(op.decode([0b00100000, 0x10], address.fromPhysical(0x100))).strip().upper(), "JP\t0000:0112, FNZ");

        op = SingleOpcodeDecoder("00001000 5 LD16  [v16], SP");
        self.assertEquals(str(op.decode([0b00001000, 0xAA,0xBB], address.fromPhysical(0x100))).strip().upper(), "LD16\t[(V):BBAA], SP");


if __name__ == "__main__":
    unittest.main()
