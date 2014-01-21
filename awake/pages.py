# This file is part of Awake - GB decompiler.
# Copyright (C) 2014  Wojciech Marczenko (devdri) <wojtek.marczenko@gmail.com>
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
from awake.operand import ProcAddress, DataAddress
from awake.procedure import loadProcedureRange
from awake.jumptable import JumpTable

class Page(object):
    has_name_form = False

    def __init__(self, proj, url):
        self.proj = proj
        self.url = url
        self.load()

class ProcedureFlowPage(Page):
    has_name_form = True

    def load(self):
        p = self.url.split('/')
        self.addr = address.fromConventional(p[2])
        self.info = self.proj.database.procInfo(self.addr)
        self.proj.flow.refresh(self.addr)
        self.proc = self.proj.flow.at(self.addr)

    def render(self, r):
        with r.lineAddress(self.addr), r.comment():
                r.hline()

                r.startNewLine()
                r.write("procedure flow ")
                r.writeSymbol(self.addr, 'procedure')

                r.startNewLine()
                r.write("  callers: ")
                r.writeList(ProcAddress(x) for x in sorted(self.info.callers))

                r.startNewLine()
                r.write("  calls: ")
                r.writeList(ProcAddress(x) for x in sorted(self.proc.calls()))

                r.hline()

        with r.indent():
            self.proc.render(r)

class ProcedureDisasmPage(Page):
    has_name_form = True

    def load(self):
        p = self.url.split('/')
        self.addr = address.fromConventional(p[2])
        self.info = self.proj.database.procInfo(self.addr)
        self.proc = loadProcedureRange(self.proj, self.addr)

    def render(self, r):

        with r.lineAddress(self.addr), r.comment():
                r.hline()

                r.startNewLine()
                r.write("procedure ")
                r.writeSymbol(self.addr, 'procedure')

                r.startNewLine()
                r.write("  callers: ")
                r.writeList(ProcAddress(x) for x in sorted(self.info.callers))

                r.startNewLine()
                r.write("  calls: ")
                r.writeList(ProcAddress(x) for x in sorted(self.info.calls))

                r.hline()
        with r.indent():
            self.proc.render(r, self.proj)

class JumptablePage(Page):
    has_name_form = True

    def load(self):
        p = self.url.split('/')
        self.addr = address.fromConventional(p[2])
        self.jumptable = JumpTable(self.proj, self.addr)
        
    def render(self, renderer):
        self.jumptable.render(renderer)

class DataPage(Page):
    has_name_form = True

    def load(self):
        p = self.url.split('/')
        self.addr = address.fromConventional(p[2])
        self.reads, self.writes = self.proj.database.getDataReferers(self.addr)

    def render(self, r):
        with r.lineAddress(self.addr), r.comment():
                r.hline()

                r.startNewLine()
                r.write("data ")
                r.writeSymbol(self.addr, 'data')

                r.startNewLine()
                r.write("  reads: ")
                r.writeList(ProcAddress(x) for x in sorted(self.reads))

                r.startNewLine()
                r.write("  writes: ")
                r.writeList(ProcAddress(x) for x in sorted(self.writes))

                r.hline()

class SummaryPage(Page):
    def load(self):
        pass
        
    def render(self, renderer):
        c = self.proj.database.connection.cursor()

        c.execute('select addr from procs where has_ambig_calls=1')
        renderer.startNewLine()
        renderer.add('ambig calls:')
        with renderer.indent():
            for addr, in c.fetchall():
                renderer.startNewLine()
                ProcAddress(addr).render(renderer)

        c.execute('select addr from procs where suspicious_switch=1')
        renderer.startNewLine()
        renderer.add('suspicious switch:')
        with renderer.indent():
            for addr, in c.fetchall():
                renderer.startNewLine()
                ProcAddress(addr).render(renderer)

        c.execute('select addr from procs where has_suspicious_instr=1')
        renderer.startNewLine()
        renderer.add('suspicious instr:')
        with renderer.indent():
            for addr, in c.fetchall():
                renderer.startNewLine()
                ProcAddress(addr).render(renderer)

        c.close()

class BankSummaryPage(Page):
    def load(self):
        p = self.url.split('/')
        self.bank = int(p[2], 16)
        
    def render(self, renderer):
        bank_name = "{:04X}".format(self.bank)

        c = self.proj.database.connection.cursor()

        renderer.startNewLine()
        renderer.add('public interface:')
        c.execute('select destination from calls where substr(source, 0, 5)<>? and substr(destination, 0, 5)=? group by destination order by destination', (bank_name, bank_name))
        with renderer.indent():
            for addr, in c.fetchall():
                renderer.startNewLine()
                ProcAddress(addr).render(renderer)

        renderer.startNewLine()
        renderer.add('dependencies:')
        c.execute('select destination from calls where substr(source, 0, 5)=? and substr(destination, 0, 5)<>? group by source order by source', (bank_name, bank_name))
        with renderer.indent():
            for addr, in c.fetchall():
                renderer.startNewLine()
                ProcAddress(addr).render(renderer)

        renderer.startNewLine()
        renderer.add('reads:')
        c.execute('select addr from memref where substr(proc, 0, 5)=? and type=? group by addr order by addr', (bank_name, 'read'))
        with renderer.indent():
            for addr, in c.fetchall():
                renderer.startNewLine()
                DataAddress(addr).render(renderer)

        renderer.startNewLine()
        renderer.add('writes:')
        c.execute('select addr from memref where substr(proc, 0, 5)=? and type=? group by addr order by addr', (bank_name, 'write'))
        with renderer.indent():
            for addr, in c.fetchall():
                renderer.startNewLine()
                DataAddress(addr).render(renderer)

        c.close()

def dispatchUrl(proj, url):
    if url.startswith('/proc/'):
        if url.endswith('/basic'):
            return ProcedureDisasmPage(proj, url)
        return ProcedureFlowPage(proj, url)
    elif url.startswith('/jump/'):
        return JumptablePage(proj, url)
    elif url.startswith('/data/'):
        return DataPage(proj, url)
    elif url.startswith('/home'):
        return SummaryPage(proj, url)
    elif url.startswith('/bank/'):
        return BankSummaryPage(proj, url)
