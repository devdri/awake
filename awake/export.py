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

import time, re, os, Queue
import Tkinter as tk
import ttk
from tkFileDialog import asksaveasfilename
from awake import flow, address, procedure, disasm
from awake.util import AsyncTask, RadioGroup, getTkRoot, BankSelect
from awake.database import Database
from awake.textrenderer import HtmlRenderer

class ExportTask(AsyncTask):
    scopes = (
        ("All banks", 'all'),
        ("Single bank", 'bank'),
        ("Single procedure", 'proc')
    )

    modes = (
        ("Symbols", 'symbols'),
        ("Basic disassembly", 'basic'),
        ("Flow disassembly", 'flow')
    )

    def __init__(self, scope='all', mode='flow', bank=None, address=None, filename=''):
        super(ExportTask, self).__init__()
        self.scope = scope
        self.mode = mode
        self.bank = bank
        self.address = address
        self.filename = filename

    def getDefaultFilename(self):
        rom_file = disasm.rom.filename

        a = os.path.dirname(rom_file)
        b = os.path.splitext(os.path.basename(rom_file))[0]
        x = os.path.join(a, b)

        if self.scope == 'bank':
            x += '_bank_' + hex(self.bank)
        elif self.scope == 'proc':
            x += '_proc_' + str(address.fromConventional(self.address)).replace(':', '_')

        if self.mode == 'symbols':
            x += '_symbols.txt'
        elif self.mode == 'basic':
            x += '.disasm'
        elif self.mode == 'flow':
            x += '_flow.disasm'

        return x

    def work(self):
        def strip_tags(text):
            return re.sub(r'<[^><\(\)]*?>', '', text)
        database = Database('data/xxx.db')

        if self.scope == 'all':
            procs = sorted(database.getAll())
        elif self.scope == 'bank':
            procs = sorted(database.getAllInBank(self.bank))
        elif self.scope == 'proc':
            procs = [address.fromConventional(self.address)]
        else:
            raise AttributeError

        num_procs = len(procs)
        i = 0
        with open(self.filename, "wb") as f:

            for addr in procs:
                if self.requestCancel:
                    self.report(i, num_procs, "Cancelled")
                    return
                self.report(i, num_procs, "Analyzing proc: " + str(addr))

                renderer = HtmlRenderer(database)

                if self.mode == 'symbols':
                    if database.tagdb.hasNameForAddress(addr):
                        renderer.add(str(addr) + ' ' + database.tagdb.nameForAddress(addr))
                    else:
                        renderer.add(str(addr))
                elif self.mode == 'basic':
                    procedure.loadProcedureRange(addr, database).render(renderer)
                elif self.mode == 'flow':
                    flow.ProcedureFlow(addr, database).render(renderer)
                else:
                    raise AttributeError

                print >>f, strip_tags(renderer.getContents())

                i += 1

        database.close()
        self.report(i, num_procs, "Done!")

class ExportDialog(tk.Toplevel):
    def __init__(self, parent=None):
        if not parent:
            parent = getTkRoot()
        tk.Toplevel.__init__(self, parent)

        self.task = ExportTask()

        self.resizable(False, False)
        self.title('Awake Export')

        frame = ttk.Frame(self)
        frame.pack(fill='both')

        self.mode_radios = RadioGroup(frame, 'What', self.task.modes, 'flow')
        self.mode_radios.grid(row=1, column=1, columnspan=2, sticky='NESW')

        self.scope_var = tk.StringVar()
        group = ttk.LabelFrame(frame, text='From where')
        group.grid(row=2, column=1, columnspan=2)
        radio = ttk.Radiobutton(group, text='All banks', variable=self.scope_var, value='all')
        radio.grid(row=1, column=1, columnspan=2, sticky='NESW')
        radio = ttk.Radiobutton(group, text='Single bank', variable=self.scope_var, value='bank')
        radio.grid(row=2, column=1, sticky='NESW')
        self.bank_select = BankSelect(group)
        self.bank_select.var.trace('w', self.enableBank)
        self.bank_select.grid(row=2, column=2, sticky='NESW')
        radio = ttk.Radiobutton(group, text='Single procedure', variable=self.scope_var, value='proc')
        radio.grid(row=3, column=1, sticky='NESW')
        self.proc_address = tk.StringVar()
        self.proc_address.set("100")
        self.proc_address.trace('w', self.enableProc)
        address = ttk.Entry(group, textvariable=self.proc_address, width=10)
        address.grid(row=3, column=2, sticky='NESW')
        self.scope_var.set(self.task.scope)

        self.status = ttk.Label(frame, text='')
        self.status.grid(row=3, column=1, columnspan=2, sticky='NESW')
        self.progressbar = ttk.Progressbar(frame, orient="horizontal", mode="determinate")
        self.progressbar.grid(row=4, column=1, columnspan=2, sticky='NESW')

        self.export_button = ttk.Button(frame)
        self.export_button.grid(row=5, column=2, columnspan=1, sticky='NESW')
        self.enableExport()
        self.close_button = ttk.Button(frame, text="Close", command=self.close)
        self.close_button.grid(row=5, column=1, sticky='NESW')
        self.bind('<Return>', self.export)
        self.bind('<Escape>', self.close)

    def update(self):
        try:
            while True:
                done, total, msg = self.task.queue.get_nowait()
                self.progressbar['maximum'] = total
                self.progressbar['value'] = done
                self.status.configure(text=msg)
        except Queue.Empty:
            pass

        if self.task.isFinished():
            self.enableExport()
        else:
            self.after(100, self.update)

    def enableBank(self, *args):
        self.scope_var.set('bank')

    def enableProc(self, *args):
        self.scope_var.set('proc')

    def export(self, *args):
        self.task.mode = self.mode_radios.getValue()
        self.task.scope = self.scope_var.get()
        self.task.bank = self.bank_select.getValue()
        self.task.address = self.proc_address.get()
        self.task.filename = asksaveasfilename(
            title="Select destination file",
            parent=self,
            initialdir=os.path.dirname(self.task.getDefaultFilename()),
            initialfile=os.path.basename(self.task.getDefaultFilename())
        )
        if not self.task.filename:
            return
        self.task.start()

        self.export_button.configure(text='Abort', command=self.abortExport)
        self.update()

    def enableExport(self):
        self.export_button.configure(text='Export', command=self.export)

    def abortExport(self):
        self.task.requestCancel = True
        self.enableExport()

    def close(self, *args):
        self.task.requestCancel = True
        self.destroy()

    def wait(self):
        self.wait_window(self)
