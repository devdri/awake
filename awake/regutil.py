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

ALL_REGS = set(['B', 'C', 'D', 'E', 'H', 'L', 'SP', 'A', 'mem', 'ROMBANK', 'FZ', 'FC', 'FN', 'FH'])
REGS16 = set(['BC', 'DE', 'HL', 'SP', 'AF'])

def splitRegister(name):
    if name in ('BC', 'DE', 'HL'):
        return set([name[0], name[1]])
    elif name == 'AF':
        #return set(['A', 'FZ', 'FC', 'FN', 'FH'])
        return set(['A'])
    elif name == 'FNZ':
        return set(['FZ'])
    elif name == 'FNC':
        return set(['FC'])
    elif name == 'FF00+C':
        return set(['C'])
    return set([name])

def splitRegisters(regs):
    out = set()
    for x in regs:
        out |= splitRegister(x)
    return out

def joinRegisters(regs):
    out = set(regs)
    for big in ('BC', 'DE', 'HL'):
        if splitRegister(big) <= out:
            out -= splitRegister(big)
            out.add(big)
    return out
