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
from awake.operand import ComplexValue, Register
from awake.operator import HighByte, LowByte, Word, LogicalNot

class NameAssigner(object):
    """Assigns unique temporary variable names"""

    def __init__(self):
        self.assigned_names = defaultdict(int)

    def assignName(self, base='reg'):
        num = self.assigned_names[base]
        self.assigned_names[base] += 1
        return base + str(num)

def substituteRegister(expression, register, value):
    ctx = Context()
    ctx.setValue(register, value)
    return expression.optimizedWithContext(ctx)

class Context(object):
    def __init__(self, values=None, name_assigner=None, use_temporary_regs=False):
        if not values:
            self.values = dict()
        else:
            self.values = dict(values)

        if not name_assigner:
            name_assigner = NameAssigner()
        self.name_assigner = name_assigner
        self.use_temporary_regs = use_temporary_regs

    def setValueComplex(self, register):
        if register in ('BC', 'DE', 'HL'):
            self.setValueComplex(register[0])
            self.setValueComplex(register[1])
        else:
            self.invalidate(register)
            self.values[register] = ComplexValue('ctx')

    def setValue(self, register, value):
        assert not isinstance(value, int)  # detect common errors

        if register in ('BC', 'DE', 'HL'):
            self.setValue(register[0], HighByte(value))
            self.setValue(register[1], LowByte(value))
        elif register == 'AF':
            self.setValue('A', HighByte(value))
            self.setValueComplex('FZ')
            self.setValueComplex('FC')
            self.setValueComplex('FN')
            self.setValueComplex('FH')
        else:
            self.invalidate(register)

            if register in value.getDependencies():
                self.setValueComplex(register)
            else:
                self.values[register] = value

    def setTemporary(self, register, value):
        name = self.name_assigner.assignName(register)
        self.setValue(name, value)
        return name

    def substituteWithTemporary(self, register):
        if self.hasValue(register):
            old_value = self.getValue(register)
        else:
            old_value = ComplexValue('ctx')
        tmp_name = self.setTemporary(register, old_value)
        tmp_value = Register(tmp_name)
        for key in self.values:
            if key is tmp_name:
                continue
            #if isinstance(self.values[key], Register):
            #    continue
            self.values[key] = substituteRegister(self.values[key], register, tmp_value)
        return tmp_name

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
        try:
            return not value.isComplex()
        except AttributeError:
            return True

    def hasConstantValue(self, register):
        return self.hasValue(register) and self.getValue(register).value is not None

    def getValue(self, register):
        if register in ('BC', 'DE', 'HL'):
            return Word(self.getValue(register[0]), self.getValue(register[1])).optimizedWithContext(Context())
        if register == 'FNZ':
            return LogicalNot(self.getValue('FZ')).optimizedWithContext(Context())
        if register == 'FNC':
            return LogicalNot(self.getValue('FC')).optimizedWithContext(Context())
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
        return Context(self.values, self.name_assigner, self.use_temporary_regs)
