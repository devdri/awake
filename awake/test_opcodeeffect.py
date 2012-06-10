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
from opcodeeffect import OpcodeEffect

class Test(unittest.TestCase):


    def testBasic(self):
        e = OpcodeEffect('read: write:')
        reads, writes, values = e.filled(None)
        self.assertFalse(reads)
        self.assertFalse(writes)
        self.assertFalse(values)

        e = OpcodeEffect('read: A HL write: BC HL')
        reads, writes, values = e.filled(None)
        self.assertEquals(reads, set(['A', 'H', 'L']))
        self.assertEquals(writes, set(['B', 'C', 'H', 'L']))
        self.assertFalse(values)

        e = OpcodeEffect('read: FC FN write: FN:0 FZ mem FC:1')
        reads, writes, values = e.filled(None)
        self.assertEquals(reads, set(['FC', 'FN']))
        self.assertEquals(writes, set(['FN', 'FZ', 'FC', 'mem']))
        self.assertEquals(values, dict(FN='0', FC='1'))

    def testFill(self):

        params = dict(R=0, S=6, Z=0, F=0)

        e = OpcodeEffect('read: #R #F write: #S #Z #F:0')
        reads, writes, values = e.filled(params)
        self.assertEquals(reads, set(['B', 'C', 'FZ', 'H', 'L']))
        self.assertEquals(writes, set(['mem', 'B', 'FZ']))
        self.assertEquals(values, dict(FZ='0'))


if __name__ == "__main__":
    unittest.main()