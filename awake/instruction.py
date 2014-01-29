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

from awake import address, placeholders
from awake.depend import DependencySet, unknownDependencySet
from awake.expression import parse
from awake.jumptable import JumpTable
from awake.operand import ComplexValue, ComputedProcAddress, JumpTableAddress, ProcAddress, Register
from awake.regutil import ALL_REGS, joinRegisters, splitRegister, splitRegisters
from awake.context import substituteRegister

class Instruction(object):
    def __init__(self, name, addr=None):
        self.name = name
        self.addr = addr
        if not self.addr:
            self.addr = address.fromVirtual(0)

    def __str__(self):
        out = self.name
        if self.operands():
            out += '\t'
            out += ', '.join(str(op) for op in self.operands())
        return out

    def calls(self):
        return set()

    def jumps(self):
        return []

    def allJumps(self):
        return self.jumps()

    def operands(self):
        return []

    def signature(self):
        return ''  #'...' + (', '.join(str(x) for x in self.getDependencySet().reads))

    def optimizedWithContext(self, ctx):
        ctx.invalidateAll()
        return self

    def getDependencies(self, needed):
        return needed | ALL_REGS

    def getDependencySet(self):
        return unknownDependencySet()

    def optimizeDependencies(self, needed):
        return self

    def splitToSimple(self):
        return [self]

    def render(self, renderer):
        renderer.newInstruction(self.addr)
        renderer.instructionName(self.name)
        renderer.add('    ')
        renderer.renderList(self.operands())
        renderer.instructionSignature(self.signature())

    def hasContinue(self):
        return True

    def getMemreads(self):
        return set()

    def getMemwrites(self):
        return set()


class BaseOp(Instruction):
    def __init__(self, name, operands, addr=None):
        super(BaseOp, self).__init__(name, addr)
        self._operands = operands

    def operands(self):
        return self._operands


class ExpressionOp(BaseOp):
    def __init__(self, name, operands, addr, reads, writes, values, loads):
        super(ExpressionOp, self).__init__(name, operands, addr)
        self._reads = reads
        self._writes = writes
        self._values = values
        self._loads = loads

    def optimizedWithContext(self, ctx):
        for w in self._writes:
            if w not in self._values:
                ctx.setValue(w, ComplexValue(self.name))
            else:
                value = self._values[w]
                value = value.optimizedWithContext(ctx)
                # TODO: mem, etc.
                ctx.setValue(w, value)
        return self

    def getDependencies(self, needed):
        return (needed - self._writes) | self._reads

    def getDependencySet(self):
        return DependencySet(self._reads, self._writes)

    def splitToSimple(self):

        if 'sideeffects' in self._writes:
            return [self]

        writes = set(self._writes) - set(['mem'])

        out = []
        for w in self._loads:
            name = w[0]
            value = w[1]
            target = parse(name)
            writes -= splitRegisters(target.getDependencies())
            instr = LoadInstruction('LD_'+self.name, target, value, self.addr)
            out.append(instr)

        for w in writes:
            value = ComplexValue(self.name, self.getDependencySet().reads)
            target = parse(w)
            instr = LoadInstruction('LD_'+self.name, target, value, self.addr)
            out.append(instr)

        return out

    def optimizeDependencies(self, needed):
        if not (self._writes & needed) and 'sideeffects' not in self._writes and 'mem' not in self._writes:
            return None
        return self

    def getMemreads(self):
        out = set()
        for instr in self.splitToSimple():
            if instr != self:
                out |= instr.getMemreads()
        return out

    def getMemwrites(self):
        out = set()
        for instr in self.splitToSimple():
            if instr != self:
                out |= instr.getMemwrites()
        return out

class BadOpcode(Instruction):
    def __init__(self, opcodes, addr):
        super(BadOpcode, self).__init__("BAD-OP", addr)

    def hasContinue(self):
        return False

class JumpInstruction(Instruction):
    def __init__(self, name, target, cond, addr, reads, writes):
        super(JumpInstruction, self).__init__(name, addr)

        self._reads = reads
        self._writes = writes

        self.cond = cond

        if hasattr(target, 'getAddress'):
            self.targetAddr = target.getAddress()
            self.target = target
        elif target.value is not None:
            self.targetAddr = address.fromVirtualAndCurrent(target.value, addr)
            self.target = ProcAddress(self.targetAddr)
        else:
            self.targetAddr = None
            self.target = target

    def optimizedWithContext(self, ctx):
        return JumpInstruction(self.name, self.target.optimizedWithContext(ctx), self.cond, self.addr, self._reads, self._writes)

    def getDependencies(self, needed):
        return (needed - self._writes) | self._reads

    def getDependencySet(self):
        return DependencySet(self._reads, self._writes)

    def hasContinue(self):
        try:
            return not self.cond.alwaysTrue()
        except AttributeError:
            return True

    def jumps(self):
        if self.targetAddr and not self.targetAddr.isAmbiguous():
            return set([self.targetAddr])
        else:
            return set()

    def allJumps(self):
        if self.targetAddr:
            return [self.targetAddr]
        else:
            return []

    def operands(self):
        if not self.cond.alwaysTrue():
            return [self.target, self.cond]
        else:
            return [self.target]


class CallInstruction(Instruction):
    def __init__(self, proj, name, target, cond, addr):
        super(CallInstruction, self).__init__(name, addr)

        # XXX: IDIOM [CALL HL]
        if hasattr(target, 'value') and target.value == 0x00A0:
            target = placeholders.HL

        # XXX: IDIOM [CALL BC]
        if hasattr(target, 'value') and target.value == 0x0CDA:
            target = placeholders.BC

        # XXX: IDIOM [CALL LONG E:HL]
        if hasattr(target, 'value') and target.value == 0x008A:
            target = ComputedProcAddress(placeholders.E, placeholders.HL)

        self.cond = cond
        if hasattr(target, 'getAddress'):
            self.targetAddr = target.getAddress()
            self.target = ProcAddress(self.targetAddr)
        elif hasattr(target, 'value') and target.value is not None:
            self.targetAddr = address.fromVirtualAndCurrent(target.value, addr)
            self.target = ProcAddress(self.targetAddr)
        else:
            self.targetAddr = address.fromVirtual(0x4000)  # XXX: ambiguous address
            self.target = target

        self.target_depset = proj.database.procInfo(self.targetAddr).depset

        self.returns_used = ALL_REGS
        self.constant_params = dict()

    def getDependencies(self, needed):
        #return flow.getProcDeps(self.targetAddr, needed)
        deps = self.getDependencySet()
        return (needed - deps.writes) | deps.reads

    def getDependencySet(self):
        reads = set(self.target_depset.reads)
        for r in joinRegisters(reads):
            if r in self.constant_params:
                reads -= splitRegister(r)
        return DependencySet(reads, self.target_depset.writes)

    def optimizeDependencies(self, needed):
        self.returns_used = needed & self.getDependencySet().writes
        return self

    def optimizedWithContext(self, ctx):

        self.target = self.target.optimizedWithContext(ctx)
        if hasattr(self.target, 'getAddress'):
            self.targetAddr = self.target.getAddress()
        elif hasattr(self.target, 'value') and self.target.value is not None:
            self.targetAddr = address.fromVirtualAndCurrent(self.target.value, self.addr)
            self.target = ProcAddress(self.targetAddr)
        else:
            pass  # XXX

        deps = self.getDependencySet()

        ins = joinRegisters(deps.reads - set(['mem']))

        for param in ins:
            if ctx.hasConstantValue(param):
                self.constant_params[param] = ctx.getValue(param)

        for w in deps.writes:
            ctx.setValueComplex(w)

        # TODO: XXX
        if self.targetAddr.virtual() == 0x07B9:
            if 'A' in self.constant_params:
                ctx.setValue('ROMBANK', self.constant_params['A'])

        return self

    def calls(self):
        if self.targetAddr.inPhysicalMem() and not self.targetAddr.isAmbiguous():
            return set([self.targetAddr])
        else:
            return set([])

    def operands(self):
        if not self.cond.alwaysTrue():
            return [self.target, self.cond]
        else:
            return [self.target]

    def fillParamIfKnown(self, param):
        if param in self.constant_params:
            return param + '=' + str(self.constant_params[param])
        else:
            return param

    def signature(self):
        x = ''
        if not self.cond.alwaysTrue():
            x = 'CONDITIONAL'

        depset = self.getDependencySet().onlyRegisters()
        ins = joinRegisters(depset.reads - set(['mem']))
        outs = joinRegisters(self.returns_used - set(['mem']))

        ins |= set(param+'='+str(self.constant_params[param]) for param in self.constant_params)

        ins = ', '.join(sorted(ins))
        outs = ', '.join(sorted(outs))
        if ins:
            ins = ' @ (' + ins + ')'
        if not outs:
            outs = 'void'
        return x + ins + ' -> ' + outs


class TailCall(CallInstruction):
    def __init__(self, proj, target):
        super(TailCall, self).__init__(proj, 'tail-call', target, placeholders.ALWAYS, target.getAddress())


class SwitchInstruction(BaseOp):
    def __init__(self, proj, addr):
        super(SwitchInstruction, self).__init__('switch', [placeholders.A, JumpTableAddress(addr.offset(1))], addr)
        self.jt = JumpTable(proj, addr.offset(1))

    def optimizedWithContext(self, ctx):
        return self

    def hasContinue(self):
        return False

    """
    def jtSize(self):
        x = self.addr.offset(1).physical()
        if x == 0x04B3:  # serious_jt
            return 33
        elif x in (0xAB9A, 0xAB4E, 0xAB74): # simple
            return 4
        elif x == 0x1B6E: # simple
            return 17
        elif x == 0x0AD2: # simple
            return 12
        elif x == 0x215F: # simple
            return 15
        elif x == 0x5C88B:
            return 9
        elif x == 0x5C30C:
            return 6

        # inner switches
        elif x == 0x5C9D7: # simple
            return 25
        elif x == 0x5D95B: # simple
            return 5
        elif x == 0x5D8A6: # simple
            return 4
        elif x == 0x5DAAB: # simple
            return 5
        elif x == 0x5DF25: # simple
            return 9
        elif x == 0x5EAC6: # simple
            return 7
        elif x == 0x5EBEE: # simple
            return 6

        elif x == 0x5DBF2: # simple
            return 3
        elif x == 0x5CF73: # simple(dfs)
            return 18

        elif x == 0x51001: # simple
            return 16
        elif x == 0x3114:
            return 18
        elif x == 0x30FB:
            return 9

    def unknownJumpTable(self):
        return self.jtSize() is None

    def jumps(self):

        limit = self.jtSize()
        if limit is None:
            limit = 0

        return [t.getAddress() for t in self.jt.targets][:limit]  # TODO: XXX
    """
    def jumpsForSize(self, size):
        return [t.getAddress() for t in self.jt.targets][:size]


class RetInstruction(Instruction):
    def __init__(self, name, cond, addr):
        super(RetInstruction, self).__init__(name, addr)
        self.cond = cond

    def optimizedWithContext(self, ctx):
        return self

    def hasContinue(self):
        return not self.cond.alwaysTrue()

    def operands(self):
        if not self.cond.alwaysTrue():
            return [self.cond]
        else:
            return []

class LoadInstruction(ExpressionOp):
    def __init__(self, name, target, source, addr=None):

        reads = source.getDependencies()
        writes = set()
        if hasattr(target, 'target'):
            reads |= target.getDependencies()
            writes.add('mem')
        else:
            writes |= target.getDependencies()

        super(LoadInstruction, self).__init__(name, [target, source], addr, reads, writes, dict(), [])
        self.target = target
        self.source = source

    def splitToSimple(self):
        return [self]

    def optimizedWithContext(self, ctx):
        source = self.source.optimizedWithContext(ctx)
        target = self.target
        out = []

        if hasattr(target, 'target'):
            # Dereference target
            target = target.optimizedWithContext(ctx)

            # Detect bank switching -- replace target with ROMBANK register
            if hasattr(target.target, 'getAddress'):
                addr = target.target.getAddress()
                if 0x2000 <= addr.virtual() < 0x4000:
                    target = placeholders.ROMBANK

            if hasattr(target, 'target'):
                ctx.setValueComplex('mem')

        if hasattr(target, 'name'):
            # Register target

            if ctx.use_temporary_regs:
                tmp_name = ctx.substituteWithTemporary(target.name)
                source = substituteRegister(source, target.name, Register(tmp_name))
                source = source.optimizedWithContext(ctx)
                ctx.setValue(target.name, source)

                out.append(LoadInstruction(self.name, Register(tmp_name), Register(target.name), self.addr))
            else:
                ctx.setValue(target.name, source)

        out.append(LoadInstruction(self.name, target, source, self.addr))
        return out

    def render(self, renderer):
        renderer.newInstruction(self.addr)
        self.target.render(renderer)
        renderer.add(' = ')
        self.source.render(renderer)
        renderer.instructionSignature(self.signature())

    def getMemreads(self):
        out = set()
        out |= self.source.getMemreads()
        try:
            out |= self.target.target.getMemreads()
        except AttributeError:
            pass
        return out

    def getMemwrites(self):
        try:
            return set([self.target.target.getAddress()])
        except AttributeError:
            return set()


def make(proj, name, operands, addr, reads, writes, values, loads):
    if (name == "JP" or name == "JR") and len(operands) == 1:
        return JumpInstruction(name, operands[0], placeholders.ALWAYS, addr, reads, writes)

    elif (name == "JP" or name == "JR") and len(operands) == 2:
        return JumpInstruction(name, operands[0], operands[1], addr, reads, writes)

    elif name == "CALL" and len(operands) == 1:

        # XXX IDIOM
        if operands[0].value == 0:
            return SwitchInstruction(proj, addr)

        return CallInstruction(proj, name, operands[0], placeholders.ALWAYS, addr)

    elif name == "CALL" and len(operands) == 2:
        return CallInstruction(proj, name, operands[0], operands[1], addr)

    elif name in ("RET", "RETI") and not operands:
        return RetInstruction(name, placeholders.ALWAYS, addr)

    elif name in ("RET", "RETI") and len(operands) == 1:
        return RetInstruction(name, operands[0], addr)

    elif name in ("LD", "LD16"):
        return LoadInstruction(name, operands[0], operands[1], addr)

    return ExpressionOp(name, operands, addr, reads, writes, values, loads)
