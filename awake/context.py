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

import operand
import operator
import regutil

def hi(value):
    return operator.HighByte(value)

def lo(value):
    return operator.LowByte(value)

def word(h, l):
    return operator.Word(h, l)

class Context:
    def __init__(self, values=None):
        if not values:
            self.values = dict()
        else:
            self.values = dict(values)

    def setValueComplex(self, register):
        if register in ('BC', 'DE', 'HL'):
            self.setValueComplex(register[0])
            self.setValueComplex(register[1])
        else:
            self.invalidate(register)
            self.values[register] = operand.ComplexValue('ctx')

    def setValue(self, register, value):
        assert not isinstance(value, (long, int))  # detect common errors

        if register in ('BC', 'DE', 'HL'):
            self.setValue(register[0], hi(value))
            self.setValue(register[1], lo(value))
        else:
            self.invalidate(register)

            if register in value.getDependencies():
                self.setValueComplex(register)
            else:
                self.values[register] = value

    def invalidate(self, register):
        delete = set()

        for x in self.values:
            if self.values[x] and register in self.values[x].getDependencies():
                delete.add(x)

        for x in delete:
            del(self.values[x])

    def hasValue(self, register):
        if register in ('BC', 'DE', 'HL'):
            return self.hasValue(register[0]) and self.hasValue(register[1])
        if register == 'FNZ':
            return self.hasValue('FZ')
        if register == 'FNC':
            return self.hasValue('FC')
        if register not in self.values:
            return False
        value = self.values[register]
        return not hasattr(value, 'isComplex') or not value.isComplex()

    def hasConstantValue(self, register):
        return self.hasValue(register) and hasattr(self.getValue(register), 'getValue')

    def getValue(self, register):
        if register in ('BC', 'DE', 'HL'):
            return word(self.getValue(register[0]), self.getValue(register[1])).optimizedWithContext(Context())
        if register == 'FNZ':
            return operator.LogicalNot(self.getValue('FZ')).optimizedWithContext(Context())
        if register == 'FNC':
            return operator.LogicalNot(self.getValue('FC')).optimizedWithContext(Context())
        else:
            return self.values[register].optimizedWithContext(Context())

    def invalidateAll(self):
        self.values = dict()

    def invalidateComplex(self):
        values = set(self.values)
        for v in values:
            if not self.hasConstantValue(v):
                del self.values[v]

    def clone(self):
        return Context(self.values)


