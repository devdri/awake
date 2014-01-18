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

from . import address
from . import operand
from .operand import Register, Condition, Dereference

BC = Register("BC")
DE = Register("DE")
HL = Register("HL")
SP = Register("SP")
AF = Register("AF")

B = Register("B")
C = Register("C")
D = Register("D")
E = Register("E")
H = Register("H")
L = Register("L")
A = Register("A")
deref_HL = Dereference(HL, address.fromVirtual(0))  # XXX: TODO: very very bad

FNZ = Condition("FNZ")
FZ = Condition("FZ")
FNC = Condition("FNC")
FC = Condition("FC")
ALWAYS = Condition("ALWAYS")

ROMBANK = Register('ROMBANK')

tab = dict(
    R=[BC, DE, HL, SP],
    Q=[BC, DE, HL, AF],
    S=[B, C, D, E, H, L, deref_HL, A],
    Z=[B, C, D, E, H, L, deref_HL, A],
    F=[FNZ, FZ, FNC, FC],
)

def get(name, value):
    if name in tab:
        return tab[name][value]
    elif name == "N":
        return operand.Constant(value * 0x08)
    elif name == "I":
        return operand.Constant(value)

