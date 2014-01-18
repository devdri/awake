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

from . import regutil
from . import placeholders
import re
from . import expression

class OpcodeEffect(object):
    def __init__(self, text):
        m = re.search('^\s*read:(.*)write:(.*)$', text)
        assert m

        reads = []
        for name in m.group(1).split():
            reads.append(name.strip())

        writes = []
        values = dict()

        for w in m.group(2).split(';'):
            w = w.strip()
            if not w:
                continue
            if ':' in w:
                name, value = w.split(':', 2)
                values[name] = value
            else:
                name = w
            writes.append(name)

        self.reads = reads
        self.writes = writes
        self.values = values

    def filled(self, params, ctx):
        reads = set()
        writes = set()
        values = dict()
        loads = []

        for x in self.reads:
            if x.startswith("#"):
                assert(len(x) == 2)
                value = params[x[1]]
                operand = placeholders.get(x[1], value)
                # XXX: solution here: just add operand.getDependencies()
                if hasattr(operand, 'target'):
                    reads.add('mem')
                    reads |= regutil.splitRegister('HL')  # TODO: XXX: bad
                else:
                    reads |= regutil.splitRegister(operand.name)
            else:
                reads |= regutil.splitRegister(x)

        for x in self.writes:
            if x.startswith("#"):
                assert(len(x) == 2)
                value = params[x[1]]
                operand = placeholders.get(x[1], value)
                if hasattr(operand, 'target'):
                    name = '['+operand.target.name+']'
                    writes.add('mem')
                    reads |= regutil.splitRegister('HL')  # TODO: XXX: bad
                else:
                    name = operand.name
                    writes |= regutil.splitRegister(name)
                if x in self.values:
                    e = expression.parse(self.values[x])
                    values[name] = e.optimizedWithContext(ctx)
                    loads.append((name, values[name]))
            else:
                writes |= regutil.splitRegister(x)
                if x in self.values:
                    e = expression.parse(self.values[x])
                    values[x] = e.optimizedWithContext(ctx)
                    loads.append((x, values[x]))

        #values = dict() # TODO: XXX:
        #loads = []

        return reads, writes, values, loads
