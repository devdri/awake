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

import os.path
import Tkinter as tk
import ttk
from tkFileDialog import askopenfilename
from awake.export import ExportDialog
from awake.project import Project
from awake.pages import dispatchUrl
from awake.server import ServerDialog
from awake.textrenderer import TkRenderer
from awake.util import getTkRoot

style = {
    'default': '#3333FF',
    'line-address': '#FF5555',
    'comment': '#777777',
    'op-signature': '#888888',
    'op-name': '#3333FF',
    'procedure': '#000000',
    'register': '#00AA00',
    'constant': '#000000'
}

class MainWindow(tk.Toplevel):

    def __init__(self, parent=None, filename=None, url=None):
        if not parent:
            parent = getTkRoot()
        tk.Toplevel.__init__(self, parent)
        self.parent = parent

        title = "Awake"
        if filename:
            title += ' - ' + os.path.basename(filename)
        self.title(title)

        if filename:
            self.proj = Project(filename)
        else:
            self.proj = None

        self.panes = tk.PanedWindow(self, orient='horizontal', sashwidth=10)
        self.panes.pack(side='top', fill='both', expand=True)

        self.tool_pane = ttk.Frame(self.panes)
        self.panes.add(self.tool_pane)
        self.main_pane = ttk.Frame(self.panes)
        self.panes.add(self.main_pane)

        toolbar = ttk.Frame(self.main_pane)
        toolbar.pack(side='top', fill='x', padx=5, pady=5)

        open_button = ttk.Button(toolbar, text="Open...", command=self.selectRom)
        open_button.pack(side='left')
        
        self.history = History(toolbar)
        self.history.pack(side='left')

        self.server_button = ttk.Button(toolbar, text="Start server...", width=15, command=self.showServer)
        self.server_button.pack(side='right')
        self.export_button = ttk.Button(toolbar, text="Export...", width=10, command=self.showExport)
        self.export_button.pack(side='right')

        self.main = MainFrame(self.main_pane, self.proj)
        self.main.pack(side='top', fill='both', expand=True)
        self.main.setLinkCallback(self.history.navigate)
        self.history.setOpenPageCallback(self.main.openPage)

        #bank_frame = ttk.Frame(self.tool_pane)
        #bank_frame.pack(side='top', fill='x', padx=5, pady=5)

        #self.bank_select = ttk.Combobox(bank_frame, state='readonly', values=['All banks', 'Bank 00', 'Bank 01'], width=10)
        #self.bank_select.pack(side='left', fill='x', expand=True)

        #bank_names_button = ttk.Button(bank_frame, text='...', width=3)
        #bank_names_button.pack(side='left')

        #symbol_frame = ttk.Frame(self.tool_pane)
        #symbol_frame.pack(side='top', fill='x')

        #self.symbol_list = tk.Listbox(symbol_frame, relief='flat', highlightthickness=0)
        #self.symbol_list.pack(side='left', fill='both', expand=True)
        #symbol_sb = ttk.Scrollbar(symbol_frame, orient="vertical", command=self.symbol_list.yview)
        #symbol_sb.pack(side="right", fill="y")
        #self.symbol_list.configure(yscrollcommand=symbol_sb.set)

        self.protocol("WM_DELETE_WINDOW", self.quit)

        if not url and self.proj:
            url = '/proc/150'

        if url:
            self.history.navigate(url)

        if not self.proj:
            self.export_button.configure(state='disabled')
            self.server_button.configure(state='disabled')
            self.history.disable()

    def showExport(self):
        if self.proj:
            ExportDialog(self, self.proj)

    def showServer(self):
        if self.proj:
            ServerDialog(self, self.proj)

    def selectRom(self):
        filename = askopenfilename(title="Select ROM file", parent=self, filetypes=[('Gameboy rom files (*.gb)', '*.gb'), ('Gameboy Color rom files (*.gbc)', '*.gbc'), ('All files', '*.*')])
        if not filename:
            return

        fresh = MainWindow(getTkRoot(), filename)
        fresh.geometry(self.geometry())
        self.destroy()

    def wait(self):
        self.wait_window(self)

    def quit(self, *args):
        self.destroy()
        self.parent.destroy()

class MainFrame(ttk.Frame):
    def __init__(self, parent, proj=None):
        ttk.Frame.__init__(self, parent)
        self.proj = proj
        self.text = SmartText(self, width=40, height=32)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)

        self.text.configure(foreground=style['default'])
        for key, value in style.iteritems():
            self.text.tag_config(key, foreground=value)

        self.openSplashPage()

    def setLinkCallback(self, cb):
        self.text.linkCallback = cb

    def openPage(self, url):
        self.text.delete(1.0, 'end')

        if not self.proj:
            self.text.insert('end', 'Project is not open')
            return

        page = dispatchUrl(self.proj, url)
        if not page:
            self.text.insert('end', '404 Not found')
        else:
            renderer = TkRenderer(self.proj.database, self.text)
            page.load()
            page.render(renderer)

    def openSplashPage(self):
        self.text.delete(1.0, 'end')
        self.text.insert('end', 'Awake\n\n')
        self.text.insert('end', 'To begin, open a rom file.')

class History(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.back_button = ttk.Button(self, text="<", width=1, state='disabled', command=self.back)
        self.back_button.pack(side='left')
        self.forward_button = ttk.Button(self, text=">", width=1, state='disabled', command=self.forward)
        self.forward_button.pack(side='left')
        self.address_var = tk.StringVar()
        self.address_bar = ttk.Entry(self, textvariable=self.address_var)
        self.address_bar.pack(side='left')
        self.address_bar.bind("<Return>", self.go)
        self.go_button = ttk.Button(self, text="Go", width=3, command=self.go)
        self.go_button.pack(side='left')

        self.back_stack = []
        self.forward_stack = []
        self.current_url = None
        self.openPageCallback = None

    def setOpenPageCallback(self, openPageCallback):
        self.openPageCallback = openPageCallback

    def back(self, *args):
        if self.back_stack:
            url = self.back_stack.pop()
            if self.current_url:
                self.forward_stack.append(self.current_url)
            self.openPage(url)

    def forward(self, *args):
        if self.forward_stack:
            url = self.forward_stack.pop()
            if self.current_url:
                self.back_stack.append(self.current_url)
            self.openPage(url)

    def go(self, *args):
        self.navigate(self.address_var.get())

    def navigate(self, url):
        if self.current_url != url:
            if self.current_url:
                self.back_stack.append(self.current_url)
            self.forward_stack = []
        self.openPage(url)

    def openPage(self, url):
        self.current_url = url
        self.address_var.set(self.current_url)

        if self.back_stack:
            self.back_button.configure(state='normal')
        else:
            self.back_button.configure(state='disabled')

        if self.forward_stack:
            self.forward_button.configure(state='normal')
        else:
            self.forward_button.configure(state='disabled')

        if self.openPageCallback:
            self.openPageCallback(url)

    def disable(self):
        self.back_button.configure(state='disabled')
        self.forward_button.configure(state='disabled')
        self.go_button.configure(state='disabled')
        self.address_bar.configure(state='disabled')

class SmartText(tk.Text):
    def __init__(self, parent, **kwargs):
        tk.Text.__init__(self, parent, bd=0, wrap='char', font=("Menlo", 12, 'normal'), highlightthickness=0)
        self.configure(**kwargs)

        self.tag_config("link", foreground='blue', underline=True)
        self.tag_bind("link", "<1>", self._linkActivated)
        self.tag_bind("link", "<Enter>", self._linkEnter)
        self.tag_bind("link", "<Leave>", self._linkLeave)
        self.linkCallback = None

        self._orig_cmd = self._w+'_orig'
        self.tk.call("rename", self._w, self._orig_cmd)
        self.tk.createcommand(self._w, self._dispatch)

    def close(self):
        self.tk.deletecommand(self._w)
        self.tk.call("rename", self.orig_cmd, self._w)

    def _dispatch(self, operation, *args):
        if operation in ('insert', 'delete'):
            return 'break'
        return self.tk.call(self._orig_cmd, operation, *args)

    def insert(self, *args):
        return self.tk.call(self._orig_cmd, "insert", *args)

    def delete(self, *args):
        return self.tk.call(self._orig_cmd, "delete", *args)

    def insertLink(self, text, url, tags=None):
        if not tags:
            tags = tuple()
        self.insert('end', text, ('link', 'link-'+url) + tags)

    def _linkEnter(self, *args):
        self.config(cursor="hand2")

    def _linkLeave(self, *args):
        self.config(cursor="")

    def _linkActivated(self, *args):
        for tag in self.tag_names('current'):
            if tag.startswith('link-'):
                if self.linkCallback:
                    self.linkCallback(tag[5:])
