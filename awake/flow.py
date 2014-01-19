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
from awake import procedure
from . import regutil
from . import context
from . import flowcontrol
from . import address
from . import depend
from . import operand

def select_any(x):
    return next(iter(x), None)

"""Produce a dict of vert->end_points for each fork vert. End points are places, where fork branches merge"""
def find_merge_points(graph):
    queue = set([graph.start()])
    visited = set()
    branches = defaultdict(set)

    def _update(x, parent):
        updated = False
        for br in branches[parent]:
            if br == (x, 0) or br == (x, 1):
                continue
            if br not in branches[x]:
                branches[x].add(br)
                updated = True
        return updated

    while queue:
        x = queue.pop()
        childs = graph.childs(x)

        visited.add(x)

        if len(childs) > 1:
            i = 0
            for ch in childs:
                branchtag = (x, i)
                if branchtag not in branches[ch]:
                    branches[ch].add(branchtag)
                    queue.add(ch)
                i += 1

        for ch in childs:
            updated = _update(ch, x)
            if updated or ch not in visited:
                queue.add(ch)

    merges = defaultdict(set)

    for x in graph.vertices():
        joined = set()
        for (vert, _) in branches[x]:

            def _has_join(x, vert):
                #return all(((vert, i) in branches[x]) for i in range(len(graph.childs(vert))))
                count = 0
                for i in range(len(graph.childs(vert))):
                    if (vert, i) in branches[x]:
                        count += 1
                return count == len(graph.childs(vert)) or count >= 3
                """
                return (vert, 0) in branches[x] and (vert, 1) in branches[x]
                """

            if not _has_join(x, vert):
                continue

            for p in graph.parents(x):
                if not _has_join(p, vert):
                    joined.add(vert)
                    break

        for y in joined:
            merges[y].add(x)

    return merges


"""Produce a dict of vert -> set of cycles, associating each vertex with cycles it lies on"""
def find_cycles(graph):
    visited = set()
    stack = []

    def _first_dfs(x):
        visited.add(x)
        for ch in graph.childs(x):
            if ch not in visited:
                _first_dfs(ch)
        stack.append(x)

    _first_dfs(graph.start())

    removed = set()

    def _find_cycle(start):
        cycle = set()
        queue = set([start])
        while queue:
            x = queue.pop()
            for p in graph.parents(x):
                if p not in removed and p not in cycle:
                    cycle.add(p)
                    queue.add(p)
        return cycle

    cycles = defaultdict(set)

    while stack:
        x = stack.pop()
        cycle = _find_cycle(x)
        for c in cycle:
            cycles[c].add(tuple(cycle))
        removed.add(x)

    return cycles

"""Find verts that are directly accessible from a vert in cycle, but are not in the cycle"""
def find_cycle_exits(graph, cycle):
    out = set()
    cycle = set(cycle)
    for x in cycle:
        for ch in graph.childs(x):
            if ch not in cycle:
                out.add(ch)
    return out

class FlowAnalysis(object):
    def __init__(self, addr, graph):
        self.addr = addr
        self.graph = graph
        self.cycles = find_cycles(self.graph)
        self.merges = find_merge_points(self.graph)
        self.labels = dict()
        self._visited = set()

    def get_unused_cycle(self, x):
        for cycle in self.cycles[x]:
            unused = True
            for y in cycle:
                if y in self._visited:
                    unused = False
                    break
            if unused:
                self.cycles[x].remove(cycle)
                return cycle

    def _process_cascades(self, entry_points, after, break_target, continue_target):
        next_after = after
        cascades = list()
        for e in entry_points:
            e = self.graph.skipSimpleJumps(e)

            if not e:  # single return after if is not desired, unless there isn't anything better
                continue

            if e in self._visited:
                continue

            cascades.append(self.process(e, next_after, break_target, continue_target, True))

            next_after = e

        #if not cascades: # TODO: verify if desirable
        #    e = select_any(entry_points)
        #    e = skipSimpleJumps(e)
        #    if e and e != after:
        #        cascades.append(self.process(e, next_after, break_target, continue_target))
        #        next_after = e

        cascades.reverse()
        out = []
        for c in cascades:
            out += c.contents
        return out, next_after

    def process(self, x, after, break_target, continue_target, need_label=False):
        after = self.graph.skipSimpleJumps(after)
        break_target = self.graph.skipSimpleJumps(break_target)
        continue_target = self.graph.skipSimpleJumps(continue_target)

        out = []
        while True:

            x = self.graph.skipSimpleJumps(x)

            if x is None or x in self._visited:

                if x == after:
                    pass
                elif x == break_target:
                    if x is None and None not in self.labels:
                        self.labels[None] = flowcontrol.Label(address.fromVirtual(0))
                    out.append(flowcontrol.Break(self.labels[x]))
                elif x == continue_target:
                    out.append(flowcontrol.Continue(self.labels[x]))
                elif x is None:
                    out.append(flowcontrol.Return())
                else:
                    out.append(flowcontrol.Goto(self.labels[x]))
                return flowcontrol.Block(out)

            cycle = self.get_unused_cycle(x)
            if cycle:
                exits = find_cycle_exits(self.graph, cycle)
                if exits:
                    exits = set([select_any(exits)])

                cascades, next_after = self._process_cascades(exits, after, break_target, continue_target)

                inner = self.process(x, x, next_after, x, True)
                continue_label = self.labels[x]

                out.append(self.make_while(inner, continue_label))
                return flowcontrol.Block(out + cascades)

            self._visited.add(x)
            childs = self.graph.childs(x)

            if (len(self.graph.parents(x)) > 1 or need_label) and x not in self.labels:
                self.labels[x] = flowcontrol.Label(x)
                out.append(self.labels[x])
                need_label = False

            if len(childs) > 1:
                cascades, next_after = self._process_cascades(self.merges[x], after, break_target, continue_target)

                prev_contents = self.graph.getContents(x)[:-1]

                out += prev_contents

                if self.graph.isSwitch(x):
                    break_target = next_after
                    branches = []
                    for ch in reversed(childs):
                        branches.append(self.process(ch, next_after, break_target, continue_target))
                        next_after = ch
                    branches.reverse()
                    out += self.make_switch(x, branches)

                else:
                    branches = []
                    for ch in childs:
                        branches.append(self.process(ch, next_after, break_target, continue_target))
                    out += self.make_if(x, branches[0], branches[1])

                return flowcontrol.Block(out + cascades)

            else:
                out += self.graph.getContents(x)
                x = select_any(childs)
                continue

    def make_switch(self, x, branches):
        return [flowcontrol.Switch(self.graph.getLast(x).addr, branches)]

    def make_if(self, block, option_a, option_b):
        cond = self.graph.getCondition(block).negated()
        addr = self.graph.getLast(block).addr

        if option_a and option_b:
            if option_a.complexity() > option_b.complexity():
                cond = cond.negated()
                option_a, option_b = option_b, option_a

            if option_a.hasContinue() and not option_b.hasContinue():
                cond = cond.negated()
                option_a, option_b = option_b, option_a

            if not option_a.hasContinue():  # and option_b.hasContinue():
                return [flowcontrol.If(addr, cond, option_a, None)] + option_b.contents

        if not option_a:
            cond = cond.negated()
            option_a, option_b = option_b, option_a

        return [flowcontrol.If(addr, cond, option_a, option_b)]

    def make_while(self, inner, continue_label=None):
        # check for do-while pattern
        if inner:
            last = inner.contents[-1]
            if hasattr(last, 'is_break_condition') and last.is_break_condition():
                postcond = last.cond.negated()
                inner = flowcontrol.Block(inner.contents[:-1])
                last.option_a.contents[0].target_label.breaks.remove(last.option_a.contents[0]) # TODO: XXX: ugly!
                return flowcontrol.DoWhile(inner, postcond, continue_label)
        return flowcontrol.While(inner, continue_label)

    def analyze(self):

        ctx = context.Context()

        if self.addr.virtual() == 0x0A90:
            ctx.setValue('ROMBANK', operand.Constant(1))
        if self.addr.virtual() == 0x3CCA:
            ctx.setValue('ROMBANK', operand.Constant(0x15))
        if self.addr.virtual() in (0x0B34, 0x0B37, 0x0B3A, 0x0B3D):
            ctx.setValue('ROMBANK', operand.Constant(1))
        if self.addr.virtual() in (0x0D68, 0x0E7F, 0x0EFC, 0x0EDB, 0x0C40, 0x149B, 0x15B3, 0x1732, 0x0C10):
            ctx.setValue('ROMBANK', operand.Constant(2))

        if self.addr.inBankedSpace() and not self.addr.isAmbiguous():
            ctx.setValue('ROMBANK', operand.Constant(self.addr.bank()))

        content = self.process(self.graph.start(), None, False, False, True)
        content = content.optimizedWithContext(ctx)
        content = content.optimizeDependencies(set(regutil.ALL_REGS) - set(['FZ', 'FN', 'FC', 'FH']))
        return content

class ProcedureFlow(object):
    def __init__(self, proj, addr):
        self.addr = addr

        graph = procedure.loadProcedureGraph(proj, addr)

        analysis = FlowAnalysis(addr, graph)
        self.content = analysis.analyze()

        self.deps = self.content.getDependencySet()

        self._calls = set()
        self._tail_calls = set()

        self.has_switch = False
        self.suspicious_switch = graph.suspicious_switch
        self.has_suspicious_instr = graph.warn
        self.has_nop = False
        self.has_ambig_calls = False
        self.length = graph.getProcLength()

        self.memreads = set()
        self.memwrites = set()

        for instr in self.getInstructions():

            if instr.name == 'CALL':
                self._calls |= instr.calls()
            elif instr.name == 'tail-call':
                self._tail_calls |= instr.calls()

            if instr.name in ('CALL', 'tail-call') and not instr.calls():
                if instr.targetAddr and instr.targetAddr.virtual() == 0xFFC0:
                    pass
                else:
                    self.has_ambig_calls = True
            if instr.name in ('switch', 'STOP', 'HALT'):
                self.has_suspicious_instr = True
            if instr.name == 'JP' and not instr.allJumps():
                self.has_suspicious_instr = True
            if instr.name == 'switch-highlevel':
                self.has_switch = True

            self.memreads |= instr.getMemreads()
            self.memwrites |= instr.getMemwrites()

            #if instr.name == 'switch-highlevel':
            #    if instr.orig.unknownJumpTable():
            #        self._computedJumps = True

    def getDependencySet(self):
        return depend.DependencySet(self.deps.reads - set(['FZ', 'FN', 'FC', 'FH']), self.deps.writes)

    def getInstructions(self):
        out = set()
        self.content.getInstructions(out)
        return out

    def calls(self):
        return self._calls

    def tailCalls(self):
        return self._tail_calls

    def render(self, renderer):
        renderer.addLegacy('<h1>Procedure flow ')
        renderer.nameForAddress(self.addr)
        renderer.addLegacy('</h1>\n')
        renderer.addLegacy('<pre class="disasm">\n')
        self.content.render(renderer)
        renderer.addLegacy('</pre>\n')

    def addToIndex(self, index):
        for x in self.getInstructions():
            x.addToIndex(index)

def update_info(proc, database):
    print('Updating info for', proc.addr)
    info = database.procInfo(proc.addr)
    info.depset = proc.getDependencySet()
    info.has_switch = proc.has_switch
    info.suspicious_switch = proc.suspicious_switch
    info.has_suspicious_instr = proc.has_suspicious_instr
    info.has_nop = proc.has_nop
    info.has_ambig_calls = proc.has_ambig_calls
    info.length = proc.length
    #info.is_current = all(database.procInfo(sub).is_current for sub in proc.calls())
    info.calls = proc.calls()
    info.tail_calls = proc.tailCalls()
    info.memreads = proc.memreads
    info.memwrites = proc.memwrites
    info.save(database.connection)

cache = dict()
def refresh(proj, addr):
    cache[addr] = ProcedureFlow(proj, addr)
    update_info(cache[addr], proj.database)

def at(proj, addr):
    if addr not in cache:
        cache[addr] = None
        cache[addr] = ProcedureFlow(proj, addr)
        update_info(cache[addr], proj.database)
    return cache[addr]
