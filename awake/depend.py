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

def joinDependencies(first, second):
    reads = second.reads - first.writes | first.reads
    writes = first.writes | second.writes
    return DependencySet(reads, writes)

def parallel(a, b):
    reads = a.reads | b.reads
    writes = a.writes | b.writes
    return DependencySet(reads, writes)

def unknown():
    return DependencySet(regutil.ALL_REGS - set(['FZ', 'FC', 'FN', 'FH']), regutil.ALL_REGS - set(['ROMBANK']))

class DependencySet:
    def __init__(self, reads=None, writes=None):
        if reads:
            self.reads = reads
        else:
            self.reads = set()
        if writes:
            self.writes = writes
        else:
            self.writes = set()

    def __str__(self):
        return 'DependencySet({0}, {1})'.format(regutil.joinRegisters(self.reads), regutil.joinRegisters(self.writes))

def encode(depset):
    return ", ".join(str(x) for x in regutil.joinRegisters(depset.reads)) + " -> " + ", ".join(str(x) for x in regutil.joinRegisters(depset.writes))

def decode(text):
    if not text:
        return DependencySet()
    r, w = text.split("->")
    reads = set(x.strip() for x in r.split(","))
    writes = set(x.strip() for x in w.split(","))
    return DependencySet(regutil.splitRegisters(reads), regutil.splitRegisters(writes))

