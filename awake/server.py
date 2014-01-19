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

import Queue
import Tkinter as tk
import ttk
import httplib
import webbrowser
from BaseHTTPServer import HTTPServer
from awake import procedure, ui
from awake.util import AsyncTask, getTkRoot
from awake.project import Project

class StoppableHandler(ui.Handler):
    def do_GET(self):
        if self.path == '/quit/':
            self.server.request_stop = True
            self.send_response(200)
            self.end_headers()
        else:
            return ui.Handler.do_GET(self)

    def address_string(self):
        # fix for slow reverse lookup on Windows
        return self.client_address[0]

class StoppableHTTPServer(HTTPServer):
    def serve_forever(self):
        self.request_stop = False
        while not self.request_stop:
            self.handle_request()

class ServerTask(AsyncTask):
    def __init__(self, port=8888):
        super(ServerTask, self).__init__()
        self.port = port
        self.server = None

    def work(self):
        self.report("Loading project")

        proj = Project('roms/zelda.gb')

        self.server = StoppableHTTPServer(('', self.port), StoppableHandler)
        self.server.proj = proj
        self.report("Running server...")
        self.server.serve_forever()

        proj.close()

        self.report("Server stopped.")

    def stop(self):
        connection = httplib.HTTPConnection("127.0.0.1", self.port)
        connection.request('GET', '/quit/')
        connection.getresponse()
        self.server = None

class LogFrame(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.text = tk.Text(self, bd=0, wrap='char', font=("courier",), highlightthickness=0, width=40, height=10)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=self.vsb.set)
        self.text.configure(state='disabled')
        self.text.bind('<1>', lambda *args: self.text.focus_set())
        self.vsb.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)

    def log(self, msg):
        self.text.configure(state='normal')
        self.text.insert('end', msg+'\n')
        self.text.configure(state='disabled')
        self.text.yview_moveto(1)

class ServerFrame(ttk.Frame):
    def __init__(self, parent, log):
        ttk.Frame.__init__(self, parent)

        self.task = ServerTask()
        self.log = log

        self.port_var = tk.StringVar()
        self.port_var.set(self.task.port)

        port_label = ttk.Label(self, text="Port:")
        port_label.grid(row=1, column=1, sticky='NESW')
        self.port_entry = ttk.Entry(self, textvariable=self.port_var, width=5)
        self.port_entry.grid(row=1, column=2, sticky='NESW')

        self.start_button = ttk.Button(self)
        self.start_button.grid(row=1, column=3, rowspan=2, sticky='NESW')
        self.browser_button = ttk.Button(self, text="Open in browser", command=self.openBrowser)
        self.browser_button.grid(row=2, column=1, columnspan=2, sticky='NESW')
        self.enableStartServer()

    def enableStartServer(self):
        self.start_button.configure(text="Start server", command=self.startServer)
        self.browser_button.configure(state='disabled')
        self.port_entry.configure(state='normal')

    def update(self):
        try:
            while True:
                msg, = self.task.queue.get_nowait()
                self.log.log(msg)
        except Queue.Empty:
            pass

        if self.task.isFinished():
            self.enableStartServer()
        else:
            self.after(100, self.update)

    def startServer(self):
        self.start_button.configure(text="Stop server", command=self.stopServer)
        self.browser_button.configure(state='normal')
        self.port_entry.configure(state='disabled')
        self.task.start()
        self.update()

    def stopServer(self):
        self.task.stop()

    def openBrowser(self):
        webbrowser.open_new_tab("http://127.0.0.1:"+self.port_var.get()+"/proc/0100")

class ServerDialog(tk.Toplevel):
    def __init__(self, parent=None):
        if not parent:
            parent = getTkRoot()
        tk.Toplevel.__init__(self, parent)

        self.title("Awake Server")

        frame = ttk.Frame(self)
        frame.pack(fill='x')

        self.log = LogFrame(self)
        self.server_frame = ServerFrame(frame, self.log)
        self.server_frame.pack(side='left', fill='y', padx=10, pady=10)

        self.log.pack(side='bottom', fill='both', expand=True)

    def wait(self):
        self.wait_window(self)
