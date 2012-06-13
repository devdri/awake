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

import address
import regutil
import html

class Operand(object):
    bits = 8
    childs = ()
    value = None

    @property
    def value_mask(self):
        if self.value is not None:
            return self.value
        elif self.bits == 8:
            return 0xFF
        elif self.bits == 16:
            return 0xFFFF
        elif self.bits == 1:
            return 1

    def html(self):
        return str(self)

    def optimizedWithContext(self, context):
        return self

    def getDependencies(self):
        out = set()
        for ch in self.childs:
            out |= ch.getDependencies()
        return out

    def needParen(self, priority):
        return False

    def getMemreads(self):
        return set()

class Constant(Operand):
    def __init__(self, value):
        assert isinstance(value, (long, int))
        self.value = value

    def __str__(self):
        if 0 <= self.value <= 9:
            return str(self.value)
        return hex(self.value)

    def html(self):
        return html.span(self, 'constant')

    def __eq__(self, other):
        return self.value == other.value

    @property
    def bits(self):
        if self.value > 0xFF:
            return 16
        else:
            return 8

class ComplexValue(Operand):
    def __init__(self, hint='complex', deps=None):
        self.hint = hint
        if deps:
            self.deps = deps
        else:
            self.deps = set()

    def isComplex(self):
        return True

    def getDependencies(self):
        return self.deps

    def __str__(self):
        return '#'+self.hint+':'+(','.join(regutil.joinRegisters(self.deps)))+'#'


class AddressConstant(Constant):
    def __init__(self, addr):
        if not hasattr(addr, 'virtual'):
            addr = address.fromVirtual(addr)
        super(AddressConstant, self).__init__(addr.virtual())
        self.addr = addr

    def getAddress(self):
        return self.addr

    def __str__(self):
        return str(self.addr)

    def optimizedWithContext(self, ctx):
        if self.addr.isAmbiguous() and ctx.hasConstantValue('ROMBANK'):
            bank = ctx.getValue('ROMBANK').value
            addr = self.addr.withBankSpecified(bank)
            return self.__class__(addr)
        return self

    def html(self):
        return html.addr_link(self.link_prefix, self.getAddress(), self.html_class)


class ProcAddress(AddressConstant):
    link_prefix = "/proc/"
    html_class = "proc-addr"

class LabelAddress(AddressConstant):
    link_prefix = "#"
    html_class = "label-addr"

class DataAddress(AddressConstant):
    link_prefix = "/data/"
    html_class = "data-addr"

class JumpTableAddress(AddressConstant):
    link_prefix = "/jump/"
    html_class = "jumptable-addr"

class Register(Operand):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def html(self):
        return html.span(self, 'register')

    def optimizedWithContext(self, ctx):
        if ctx.hasValue(self.name):
            return ctx.getValue(self.name)
        return self

    def getDependencies(self):
        return regutil.splitRegister(self.name)

    def __eq__(self, other):
        return isinstance(other, Register) and self.name == other.name

    @property
    def bits(self):
        if self.name in regutil.REGS16:
            return 16
        else:
            return 8

class Condition(Register):
    bits = 1

    def negated(self):
        return Condition(dict(FZ='FNZ', FNZ='FZ', FC='FNC', FNC='FC')[self.name])

    def alwaysTrue(self):
        return self.name == 'ALWAYS'

    @property
    def value(self):
        if self.alwaysTrue():
            return 1
        else:
            return None


class Dereference(Operand):
    def __init__(self, target, addr=None):
        self.addr = addr
        if hasattr(target, "getAddress"):
            self.target = target
        if target.value is not None:
            if addr is not None:
                self.target = DataAddress(address.fromVirtualAndCurrent(target.value, addr))
            else:
                self.target = DataAddress(address.fromVirtual(target.value))
        else:
            self.target = target

        self.childs = (self.target,)

    def __str__(self):
        return '[{0}]'.format(self.target)

    def html(self):
        return '[{0}]'.format(self.target.html())

    def optimizedWithContext(self, ctx):
        target = self.target.optimizedWithContext(ctx)
        return Dereference(target, self.addr)

    def getDependencies(self):
        return set(['mem']) | self.target.getDependencies()

    def __eq__(self, other):
        return isinstance(other, Dereference) and self.target == other.target

    def getMemreads(self):
        if hasattr(self.target, 'getAddress'):
            return set([self.target.getAddress()])
        return set()

