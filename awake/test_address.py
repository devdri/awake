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
from awake import address


class Test(unittest.TestCase):


    def testFromPhysical(self):
        self.assertEquals(str(address.fromPhysical(0x000000)), "0000:0000")
        self.assertEquals(str(address.fromPhysical(0x002000)), "0000:2000")
        self.assertEquals(str(address.fromPhysical(0x004000)), "0001:4000")
        self.assertEquals(str(address.fromPhysical(0x008000)), "0002:4000")
        self.assertEquals(str(address.fromPhysical(0x008888)), "0002:4888")


    def testFromVirtual(self):
        self.assertEquals(str(address.fromVirtual(0x0000)), "0000:0000")
        self.assertEquals(str(address.fromVirtual(0x2000)), "0000:2000")
        self.assertEquals(str(address.fromVirtual(0x4000)), "(A):4000")
        self.assertEquals(str(address.fromVirtual(0x7FFF)), "(A):7FFF")
        self.assertEquals(str(address.fromVirtual(0x8000)), "VRAM:8000")
        self.assertEquals(str(address.fromVirtual(0xFFFF)), "IO:FFFF")


    def testFromVirtualAndCurrent(self):
        current1 = address.fromPhysical(0x4000)
        current4 = address.fromPhysical(0x10000)
        self.assertEquals(str(address.fromVirtualAndCurrent(0x0000, current1)), "0000:0000")
        self.assertEquals(str(address.fromVirtualAndCurrent(0x0000, current4)), "0000:0000")
        self.assertEquals(str(address.fromVirtualAndCurrent(0x4000, current1)), "0001:4000")
        self.assertEquals(str(address.fromVirtualAndCurrent(0x4000, current4)), "0004:4000")
        self.assertEquals(str(address.fromVirtualAndCurrent(0x7FFF, current1)), "0001:7FFF")
        self.assertEquals(str(address.fromVirtualAndCurrent(0x7FFF, current4)), "0004:7FFF")
        self.assertEquals(str(address.fromVirtualAndCurrent(0x8000, current1)), "VRAM:8000")
        self.assertEquals(str(address.fromVirtualAndCurrent(0xFFFF, current4)), "IO:FFFF")


    def testOffset(self):
        zero = address.fromVirtual(0)
        self.assertEquals(str(zero.offset(0)), "0000:0000")
        self.assertEquals(str(zero.offset(0x3FFF)), "0000:3FFF")
        self.assertEquals(str(zero.offset(0x4000)), "(A):4000")
        self.assertEquals(str(zero.offset(0x8000)), "VRAM:8000")

        first = address.fromPhysical(0x4000)
        self.assertEquals(str(first.offset(-0x4000)), "0000:0000")
        self.assertEquals(str(first.offset(0)), "0001:4000")
        self.assertEquals(str(first.offset(0x3FFF)), "0001:7FFF")
        self.assertEquals(str(first.offset(0x4000)), "VRAM:8000")

        high = address.fromVirtual(0x8000)
        self.assertEquals(str(high.offset(-0x8000)), "0000:0000")
        self.assertEquals(str(high.offset(-0x1000)), "(A):7000")
        self.assertEquals(str(high.offset(0)), "VRAM:8000")
        self.assertEquals(str(high.offset(0x0FFF)), "VRAM:8FFF")


    def testConventional(self):
        a = address.fromConventional("0000:0000")
        self.assertEquals(a.virtual(), 0)
        a = address.fromConventional("(V):0000")
        self.assertEquals(a.virtual(), 0)
        a = address.fromConventional("(A):4000")
        self.assertEquals(a.virtual(), 0x4000)
        a = address.fromConventional("(V):FFFF")
        self.assertEquals(a.virtual(), 0xFFFF)
        a = address.fromConventional("0001:4000")
        self.assertEquals(a.virtual(), 0x4000)
        self.assertEquals(a.bank(), 1)


if __name__ == "__main__":
    unittest.main()
