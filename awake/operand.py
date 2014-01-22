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

from awake import address
from awake.regutil import REGS16, splitRegister

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

    def render(self, renderer):
        renderer.add(str(self))

    def optimizedWithContext(self, context):
        return self

    def getDependencies(self):
        return set.union(set(), *(ch.getDependencies() for ch in self.childs))

    def needParen(self, priority):
        return False

    def getMemreads(self):
        return set(dep for dep in self.getDependencies() if isinstance(dep, address.Address))

class Constant(Operand):
    def __init__(self, value):
        assert isinstance(value, int)
        self.value = value

    def __str__(self):
        if 0 <= self.value <= 9:
            return str(self.value)
        return hex(self.value)

    def render(self, renderer):
        renderer.add(str(self), 'constant')

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        try:
            return self.value == other.value
        except AttributeError:
            return False

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
        return '#'+self.hint+':'+(','.join(str(dep) for dep in self.deps if not isinstance(dep, address.Address)))+'#'


class AddressConstant(Constant):
    def __init__(self, addr):
        if not hasattr(addr, 'virtual'):
            if isinstance(addr, int):                       #If addr is an int,
                addr = address.fromVirtual(addr)            #   code path is unchanged.
            else:                                           #Else, addr is a string,
                addr = address.fromConventional(addr)       #   so it should be processed by fromConventional.
        super(AddressConstant, self).__init__(addr.virtual())
        self.addr = addr
        self.value = addr.virtual()

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

    def render(self, renderer):
        addr = self.getAddress()
        renderer.writeSymbol(addr, self.html_class, self.link_prefix + str(addr))

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

    def render(self, renderer):
        renderer.add(str(self), 'register')

    def optimizedWithContext(self, ctx):
        if ctx.hasValue(self.name):
            return ctx.getValue(self.name)
        return self

    def getDependencies(self):
        return splitRegister(self.name)

    def __hash__(self):
        return hash((Register, self.name))

    def __eq__(self, other):
        return isinstance(other, Register) and self.name == other.name

    @property
    def bits(self):
        if self.name in REGS16:
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
        elif target.value is not None:
            if addr is not None:
                self.target = DataAddress(address.fromVirtualAndCurrent(target.value, addr))
            else:
                self.target = DataAddress(address.fromVirtual(target.value))
        else:
            self.target = target

        self.childs = (self.target,)

    def __str__(self):
        return '[{0}]'.format(self.target)

    def render(self, renderer):
        renderer.add('[')
        self.target.render(renderer)
        renderer.add(']')

    def optimizedWithContext(self, ctx):
        target = self.target.optimizedWithContext(ctx)
        if not hasattr(target, 'getAddress') and target.value is not None:
            target = DataAddress(address.fromVirtual(target.value)).optimizedWithContext(ctx)
        return Dereference(target, self.addr)

    def getDependencies(self):
        out = set(['mem']) | self.target.getDependencies()
        if hasattr(self.target, 'getAddress'):
            out |= set([self.target.getAddress()])
        return out

    def __hash__(self):
        return hash((Dereference, self.target))

    def __eq__(self, other):
        return isinstance(other, Dereference) and self.target == other.target

    # XXX
    #def getMemreads(self):
    #    if hasattr(self.target, 'getAddress'):
    #        return set([self.target.getAddress()])
    #    return set()


class ComputedProcAddress(Operand):
    bits = 24

    def __init__(self, bank, addr):
        self.bank = bank
        self.addr = addr
        self.childs = (self.bank, self.addr)

    def __str__(self):
        return '[L {0}:{1}]'.format(self.bank, self.addr)

    def render(self, renderer):
        renderer.add('[L ')
        self.bank.render(renderer)
        renderer.add(':')
        self.addr.render(renderer)
        renderer.add(']')

    def optimizedWithContext(self, ctx):
        bank = self.bank.optimizedWithContext(ctx)
        addr = self.addr.optimizedWithContext(ctx)

        if hasattr(addr, 'value') and addr.value is not None and hasattr(bank, 'value') and bank.value is not None:
            return ProcAddress(address.fromVirtualAndBank(addr.value, bank.value))

        return ComputedProcAddress(bank, addr)

    def getDependencies(self):
        return self.addr.getDependencies() | self.bank.getDependencies()

    def __hash__(self):
        return hash((ComputedProcAddress, self.bank, self.addr))

    def __eq__(self, other):
        return isinstance(other, ComputedProcAddress) and self.addr == other.addr and self.bank == other.bank
