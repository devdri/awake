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
import operand
import operator
import context
import expression

class Test(unittest.TestCase):


    def testConstantOptimize(self):
        ctx = context.Context()
        ctx.setValue('A', operand.Constant(1))
        e = expression.parse("1+A")
        e = e.optimizedWithContext(ctx)
        self.assertEquals(e.value, 2)

    def testBlah(self):
        e = expression.parse("(A>>7)<<1")
        e = e.optimizedWithContext(context.Context())
        self.assertEquals(str(e), "(A >> 6) & 2")

        e = expression.parse("(A>>4)<<6")
        e = e.optimizedWithContext(context.Context())
        self.assertEquals(str(e), "(A << 2) & 0xc0")

if __name__ == "__main__":
    unittest.main()