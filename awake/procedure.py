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

from . import database
from . import disasm
from . import address
from . import html
from . import instruction
from . import operand
from . import tag
from collections import defaultdict

def manualJumptableLimit(addr):
    if addr == address.fromConventional("0001:4187"):
        return 5
    elif addr == address.fromConventional("0001:633D"):
        return 2
    elif addr == address.fromConventional("0003:4976"):
        return 37  # very weird jumptable...
    elif addr == address.fromConventional("0018:7175"):
        return 5
    elif addr == address.fromConventional("0017:430C"):
        return 6
    elif addr == address.fromConventional("0002:6C1F"):
        return 3
    elif addr == address.fromConventional("0006:7383"):
        return 3
    elif addr == address.fromConventional("0006:5824"):
        return 5  # weird jumptable
    elif addr == address.fromConventional("0018:65B3"):
        return 4
    elif addr == address.fromConventional("0019:4942"):
        return 4
    elif addr == address.fromConventional("0015:78E1"):
        return 2
    elif addr == address.fromConventional("0005:62CD"):
        return 5
    elif addr == address.fromConventional("0019:4CB3"):
        return 2
    elif addr == address.fromConventional("0005:461E"):
        return 4
    elif addr == address.fromConventional("0005:4169"):
        return 5
    elif addr == address.fromConventional("0019:5B29"):
        return 2
    elif addr == address.fromConventional("0004:4B52"):
        return 2
    elif addr == address.fromConventional("0004:6802"):
        return 2
    elif addr == address.fromConventional("0004:6081"):
        return 4
    elif addr == address.fromConventional("0004:6EB6"):
        return 13
    elif addr == address.fromConventional("0006:74C5"):
        return 2
    elif addr == address.fromConventional("0004:76B4"):
        return 6
    elif addr == address.fromConventional("0004:4E8C"):
        return 4
    elif addr == address.fromConventional("0005:7210"):
        return 5

    # AGES
    elif addr == address.fromConventional("0007:5E96"):
        return 7

    # BIG SWITCH: bad 0003:5A35

class ProcedureRangeAnalysis(object):

    def __init__(self, addr, limit):
        self.start_addr = addr
        self.limit_addr = limit
        self.visited = set()
        self.owned_bytes = set()
        self.labels = set()
        self.block_starts = set([self.start_addr])
        self.jumptable_sizes = defaultdict(int)
        self.queue = set([self.start_addr])
        self.jumptable_queue = set()
        self.suspicious_switch = False
        self.warn = False
        self.log = list()
        self.dfs()
        self.shrinkLimitAndCut(self.firstGap())

    def isLocalAddr(self, addr):
        return self.start_addr <= addr < self.limit_addr

    def shrinkLimit(self, addr):
        if self.isLocalAddr(addr):
            self.limit_addr = addr

    def isAvailableAddr(self, addr):
        return self.isLocalAddr(addr) and addr not in self.owned_bytes

    def ownByte(self, addr):
        if not self.isAvailableAddr(addr):
            print('byte not available', addr, 'visited:', ', '.join(str(x) for x in self.visited))
            print("LOG:", "\n".join(self.log))
        assert self.isAvailableAddr(addr)
        self.owned_bytes.add(addr)

    def ownByteRange(self, addr, size):
        for i in range(size):
            if not self.isLocalAddr(addr.offset(i)):
                print('megawarn: overlap instr', addr, addr.offset(i))
                self.warn = True
                return
            self.ownByte(addr.offset(i))

    def tryExpandJumptable(self, jumptable_addr):

        manual_limit = manualJumptableLimit(jumptable_addr)
        if manual_limit and self.jumptable_sizes[jumptable_addr] >= manual_limit:
            print("INFO: manual jumptable limit", jumptable_addr)
            self.suspicious_switch = True
            return

        next_target_addr = jumptable_addr.offset(self.jumptable_sizes[jumptable_addr] * 2)

        if not manual_limit and not self.isAvailableAddr(next_target_addr):
            return

        rom = disasm.cur_rom
        next_target = address.fromVirtualAndCurrent(rom.get_word(next_target_addr), self.start_addr)

        if not manual_limit:
            if not next_target.inPhysicalMem() or next_target.virtual() <= 0x4A:
                print('WARN: jumptable at', str(jumptable_addr), 'bounded by bad addr', str(next_target))
                self.suspicious_switch = True
                return

        self.log.append('=== expand jumptable === ' + str(next_target))

        # everything ok, expand jumptable
        self.jumptable_sizes[jumptable_addr] += 1
        self.ownByteRange(next_target_addr, 2)
        self.jumptable_queue.add(jumptable_addr)
        self.queue.add(next_target)
        self.labels.add(next_target)
        self.block_starts.add(next_target)

    def visitInstruction(self, addr):

        if addr in self.visited or not self.isLocalAddr(addr):
            return

        if not self.isAvailableAddr(addr):
            print('ERROR: conflict at addr', addr, 'owned_bytes:', ', '.join(str(x) for x in self.owned_bytes), 'visited:', ', '.join(str(x) for x in self.visited))

        self.visited.add(addr)

        instr, next_addr = disasm._decode(addr)

        self.log.append('instr ' + str(addr) + ' ' + str(instr))

        if next_addr:
            length = next_addr.virtual() - addr.virtual()
            self.ownByteRange(addr, length)
        else:  # XXX
            print('WARN: probably bad', addr)
            print("LOG:" + "\n".join(self.log))
            raise "bla"
            self.ownByte(addr)

        if instr.name == 'switch':
            self.jumptable_queue.add(next_addr)
            return

        if instr.hasContinue():
            self.queue.add(next_addr)
            if instr.name == 'RET' or instr.allJumps():  # TODO: XXX: maybe not nicest
                self.block_starts.add(next_addr)

        for jump_addr in instr.jumps():
            self.queue.add(jump_addr)
            self.labels.add(jump_addr)
            self.block_starts.add(jump_addr)

        for call_addr in instr.calls():
            if call_addr != self.start_addr:
                self.shrinkLimit(call_addr)

    def dfs(self):
        while self.queue or self.jumptable_queue:
            if self.queue:
                x = self.queue.pop()
                self.visitInstruction(x)
            else:
                x = self.jumptable_queue.pop()
                self.tryExpandJumptable(x)

    def firstGap(self):
        addr = self.start_addr
        while addr < self.limit_addr and not self.isAvailableAddr(addr):
            addr = addr.offset(1)
        return addr

    def shrinkLimitAndCut(self, limit_addr):
        self.limit_addr = limit_addr
        #self.owned_bytes = set(addr for addr in self.owned_bytes if self.isLocalAddr(addr))
        self.owned_bytes = list(filter(self.isLocalAddr, self.owned_bytes))
        self.visited = set(addr for addr in self.visited if self.isLocalAddr(addr))
        self.labels = set(addr for addr in self.labels if self.isLocalAddr(addr))
        self.block_starts = set(addr for addr in self.block_starts if self.isLocalAddr(addr))
        self.jumptable_sizes = dict((k, v) for (k, v) in self.jumptable_sizes.items() if self.isLocalAddr(k))

    def html(self):
        out = '<h1>Procedure {0}</h1>\n'.format(tag.nameForAddress(self.start_addr));
        out += '<pre class="disasm">';
        from . import disasm
        for addr in sorted(self.visited):
            if addr in self.labels:
                out += html.label(addr)
            out += disasm.decodeCache(addr)[0].html(0)
        out += '</pre>\n'

        return out

    def procgraph(self):
        return ProcedureGraph(self.start_addr, self.limit_addr, self.block_starts, self.jumptable_sizes)

def getLimit(addr):
    if addr.inPhysicalMem():
        bank_limit = address.fromVirtualAndBank(0x4000, addr.bank()+1)
    else:
        bank_limit = address.fromVirtual(0xFFFF)

    next_owned = database.getNextOwnedAddress(addr)

    if not next_owned or bank_limit < next_owned:
        return bank_limit
    else:
        return next_owned

class ProcedureGraph(object):
    def __init__(self, start_addr, end_addr, block_starts, jumptable_sizes):
        self.start_addr = start_addr
        self.end_addr = end_addr
        self.jumptable_sizes = jumptable_sizes
        block_starts = list(sorted(block_starts))
        self.block_starts = block_starts
        self.block_id_at_addr = dict((block_starts[i], i) for i in range(len(block_starts)))
        self.block_id_at_addr[None] = None
        self._childs = dict()
        self.blocks = [None] * len(block_starts)
        self.addBlocks()
        self._parents = defaultdict(list)
        self._fillParents()

    def addBlocks(self):
        num_blocks = len(self.blocks)
        for i in range(num_blocks):
            start_addr = self.block_starts[i]
            if i+1 < num_blocks:
                end_addr = self.block_starts[i+1]
            else:
                end_addr = self.end_addr
            self.addBlock(i, start_addr, end_addr)

    def addFakeBlock(self, addr):
        pos = len(self.blocks)
        self.block_id_at_addr[addr] = pos

        instr = instruction.TailCall(operand.ProcAddress(addr))

        from .flowcontrol import Block
        self.blocks.append(Block([instr]))

        self.block_starts.append(addr)
        self._childs[pos] = [None]

    def addBlock(self, pos, start_addr, end_addr):

        instructions = []
        addr = start_addr
        while addr < end_addr:
            instr, addr = disasm.decodeCache(addr)
            instructions.append(instr)
            if not instr.hasContinue():
                break

        assert instructions

        childs = []

        last = instructions[-1]

        if last.hasContinue():
            childs.append(end_addr)

        remove_last = False

        if last.name == 'JP':
            childs += last.allJumps()
            if last.cond.alwaysTrue() and last.allJumps():
                remove_last = True
        elif last.name == 'switch':
            childs += last.jumpsForSize(self.jumptable_sizes[addr])  # TODO: XXX: addr is not nice here
        elif last.name == 'RET':
            childs.append(None)
            if not last.hasContinue():
                remove_last = True

        if remove_last:
            instructions = instructions[:-1]

        from .flowcontrol import Block
        block = Block(instructions)
        self.blocks[pos] = block

        for ch in childs:
            if ch not in self.block_starts:
                if ch is not None:
                    self.addFakeBlock(ch)

        self._childs[self.block_id_at_addr[start_addr]] = [self.block_id_at_addr[ch] for ch in childs]

    def _fillParents(self):
        for x in self.vertices():
            for ch in self.childs(x):
                self._parents[ch].append(x)  # important: duplicate childs must be supported

    def start(self):
        return 0

    def parents(self, x):
        return self._parents[x]

    def childs(self, x):
        if x is None:
            return []
        return self._childs[x]

    def vertices(self):
        return set(range(len(self.blocks)))

    def skipSimpleJumps(self, x):
        if x and not self.blocks[x] and len(self.childs(x)) == 1 and self.childs(x)[0] is None:
            return None
        else:
            return x

    def isSwitch(self, x):
        last = self.blocks[x].contents[-1]
        return last.name == 'switch'

    def getContents(self, x):
        return self.blocks[x].contents

    def getCondition(self, x):
        last = self.blocks[x].contents[-1]
        return last.cond

    def getLast(self, x):
        return self.blocks[x].contents[-1]

    def getProcLength(self):
        return self.end_addr.virtual() - self.start_addr.virtual()

    def html(self):
        out = ''
        out += 'Proc graph ' + tag.nameForAddress(self.start_addr)
        out += '<pre class="disasm">'
        for i, b in enumerate(self.blocks):
            out += 'BLOCK' + str(i) + '\n'
            out += b.html()
        out += 'edges:\n'
        for x in self.vertices():
            out += str(x) + ' -> ' + ', '.join(str(y) for y in self.childs(x)) + '\n'
        out += '</pre>\n'
        return out


def loadProcedureRange(addr):
    return ProcedureRangeAnalysis(addr, getLimit(addr))

def loadProcedureGraph(addr):
    r = loadProcedureRange(addr)
    g = ProcedureGraph(addr, r.limit_addr, r.block_starts, r.jumptable_sizes)
    g.suspicious_switch = r.suspicious_switch
    g.warn = r.warn
    return g
