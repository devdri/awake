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

    def html(self):
        return str(self)

    def optimizedWithContext(self, context):
        return self

    def getDependencies(self):
        out = set()
        for ch in self.childs():
            out |= ch.getDependencies()
        return out

    def needParen(self, priority):
        return False

    def bits(self):
        return 8

    def addToIndex(self, index):
        for ch in self.childs():
            ch.addToIndex(index)

    def childs(self):
        return set()

    def getValueMask(self):
        if self.bits() == 8:
            return 0xFF
        elif self.bits() == 16:
            return 0xFFFF
        elif self.bits() == 1:
            return 1

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

    def getValue(self):
        return self.value

    def html(self):
        return html.span(self, 'constant')

    def __eq__(self, other):
        if not hasattr(other, 'getValue'):
            return False
        return self.getValue() == other.getValue()

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
    def __init__(self, addr, html_class="", link_prefix=""):
        if not hasattr(addr, 'virtual'):
            addr = address.fromVirtual(addr)
        super(AddressConstant, self).__init__(addr.virtual())
        self.addr = addr
        self.html_class = html_class
        self.link_prefix = link_prefix

    def getAddress(self):
        return self.addr

    def __str__(self):
        return str(self.addr)

    def optimizedWithContext(self, ctx):
        if self.addr.isAmbiguous() and ctx.hasConstantValue('ROMBANK'):
            bank = ctx.getValue('ROMBANK').getValue()
            addr = self.addr.withBankSpecified(bank)
            return self.__class__(addr)
        return self

    def html(self):
        return html.addr_link(self.link_prefix, self.getAddress(), self.html_class)


class ProcAddress(AddressConstant):
    def __init__(self, addr):
        super(ProcAddress, self).__init__(addr, 'proc-addr', '/proc/')

class LabelAddress(AddressConstant):
    def __init__(self, addr):
        super(LabelAddress, self).__init__(addr, 'label-addr', '#')

class DataAddress(AddressConstant):
    def __init__(self, addr):
        super(DataAddress, self).__init__(addr, 'data-addr', '/data/')

class JumpTableAddress(AddressConstant):
    def __init__(self, addr):
        super(JumpTableAddress, self).__init__(addr, 'jumptable-addr', '/jump/')

class Register(Operand):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def html(self):
        return html.span(self.name, 'register')

    def optimizedWithContext(self, context):
        if context.hasValue(self.name):
            return context.getValue(self.name)
        return self

    def getDependencies(self):
        return regutil.splitRegister(self.name)

    def __eq__(self, other):
        return isinstance(other, Register) and self.name == other.name

    def bits(self):
        if self.name in regutil.REGS16:
            return 16
        else:
            return 8

class Condition(Register):
    def __init__(self, name):
        super(Condition, self).__init__(name)

    def negated(self):
        tab = dict(FZ='FNZ', FNZ='FZ', FC='FNC', FNC='FC')
        if self.name in tab:
            return Condition(tab[self.name])
        else:
            return Condition('not ' + self.name)

    def alwaysTrue(self):
        return self.name == 'ALWAYS'

    def bits(self):
        return 1

class Dereference(Operand):
    def __init__(self, target, addr=None):
        self.addr = addr
        if hasattr(target, "getAddress"):
            self.target = target
        if hasattr(target, "getValue"):
            if addr is not None:
                self.target = DataAddress(address.fromVirtualAndCurrent(target.getValue(), addr))
            else:
                self.target = DataAddress(address.fromVirtual(target.getValue()))
        else:
            self.target = target

    def __str__(self):
        return '[{0}]'.format(self.target)

    def html(self):
        return '[{0}]'.format(self.target.html())

    def optimizedWithContext(self, ctx):
        target = self.target.optimizedWithContext(ctx)
        #if not hasattr(target, "getAddress") and hasattr(target, "getValue"):
        #    target = DataAddress(address.fromVirtualAndCurrent(target.getValue(), self.addr)).optimizedWithContext(ctx)
        return Dereference(target, self.addr)

    def getDependencies(self):
        return set(['mem']) | self.target.getDependencies()

    def __eq__(self, other):
        return isinstance(other, Dereference) and self.target == other.target

    def childs(self):
        return set([self.target])

    def getMemreads(self):
        if hasattr(self.target, 'getAddress'):
            return set([self.target.getAddress()])
        return set()

