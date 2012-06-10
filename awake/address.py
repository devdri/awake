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

from functools import total_ordering

BANK_SIZE = 0x4000

class BadAddressException(Exception):
    def __init__(self, addr):
        self.addr = addr

    def __str__(self):
        return str(self.addr)


def fromVirtual(virtual):
    return Address(virtual)


def fromVirtualAndBank(virtual, bank):
    return Address(virtual + (bank << 16))


def fromVirtualAndCurrent(virtual, current):
    if BANK_SIZE <= virtual < 2 * BANK_SIZE:
        return fromVirtualAndBank(virtual, current.bank())
    else:
        return fromVirtual(virtual)


def fromPhysical(physical):
    if physical < BANK_SIZE:
        return Address(physical)

    bank = physical // BANK_SIZE
    virtual = BANK_SIZE + (physical % BANK_SIZE)
    return fromVirtualAndBank(virtual, bank)


def fromConventional(conventional):
    if ":" not in conventional:
        virtual = int(conventional, 16)
        return fromVirtual(virtual)

    else:
        halves = conventional.split(":", 2)
        virtual = int(halves[1], 16)

        if virtual >= 0x8000 or halves[0] == '(A)':
            return fromVirtual(virtual)

        bank = int(halves[0], 16)
        return fromVirtualAndBank(virtual, bank)
        #if bank == 0:
        #    return fromVirtual(virtual)
        #physical = virtual - BANK_SIZE + bank * BANK_SIZE
        #return fromPhysical(physical)

@total_ordering
class Address(object):


    def __init__(self, address):
        self.address = address


    def virtual(self):
        return self.address & 0xFFFF


    def bank(self):
        return self.address >> 16


    def isAmbiguous(self):
        return self.inBankedSpace() and self.bank() <= 0


    def inBankedSpace(self):
        return BANK_SIZE <= self.virtual() < 2 * BANK_SIZE

    def inPhysicalMem(self):
        return self.virtual() < 2 * BANK_SIZE

    def physical(self):
        if self.address < BANK_SIZE:
            return self.address

        elif self.inBankedSpace() and not self.isAmbiguous():
            return self.virtual() + BANK_SIZE * self.bank() - BANK_SIZE

        else:  # address is ambiguous and cannot be converted to physical location
            raise BadAddressException(self)


    def offset(self, offset):
        return fromVirtualAndCurrent(self.virtual() + offset, self)


    def withBankSpecified(self, bank):
        if not self.inBankedSpace():
            return self
        else:
            return fromVirtualAndBank(self.virtual(), bank)

    def __lt__(self, other):
        return self.address < other.address

    def __eq__(self, other):
        if not hasattr(other, 'address'):
            return False
        return self.address == other.address

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.address)


    def __str__(self):
        if self.isAmbiguous():
            return "(A):{:04X}".format(self.address)

        elif self.virtual() < 2 * BANK_SIZE:
            return "{:04X}:{:04X}".format(self.bank(), self.virtual())

        elif self.virtual() < 0xA000:
            return "VRAM:{:04X}".format(self.virtual())

        elif self.virtual() < 0xC000:
            return "BATT:{:04X}".format(self.virtual())

        elif self.virtual() < 0xE000:
            return "WORK:{:04X}".format(self.virtual())

        elif self.virtual() < 0xFE00:
            return "ECHO:{:04X}".format(self.virtual())

        elif self.virtual() < 0xFF00:
            return "OAM:{:04X}".format(self.virtual())

        elif self.virtual() < 0xFF80 or self.virtual() == 0xFFFF:
            return "IO:{:04X}".format(self.virtual())

        elif self.virtual() < 0xFFFF:
            return "HRAM:{:04X}".format(self.virtual())

        else:
            return "(V):{:04X}".format(self.virtual())
