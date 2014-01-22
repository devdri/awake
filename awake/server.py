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
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urlparse import urlparse, parse_qs
from awake import address, procedure
from awake.textrenderer import HtmlRenderer
from awake.util import AsyncTask, getTkRoot
from awake.pages import dispatchUrl
from awake.project import Project

def name_form(addr, database):
    out = ''
    out += '<form class="name-form" method="get" action="/set-name">'
    out += '<input type="hidden" name="addr" value="{0}" />'.format(addr)
    out += '<input type="text" name="name" value="{0}" />'.format(database.nameForAddress(addr))
    out += '<input type="submit" value="ok" />'
    out += '</form>'
    return out

class Handler(BaseHTTPRequestHandler):

    def redirect(self, where):
        self.send_response(301)
        self.send_header('Location', where)
        self.end_headers()

    def ok_html(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html;charset=utf-8')
        self.end_headers()

    def do_GET(self):

        print('get', self.path)


        page = dispatchUrl(self.server.proj, self.path)
        if page:

            self.ok_html()
            self.wfile.write("<html><head><link rel=\"stylesheet\" type=\"text/css\" href=\"/style.css\" /></head><body>")

            if page.has_name_form:
                self.wfile.write(name_form(page.addr, self.server.proj.database))

            renderer = HtmlRenderer(self.server.proj.database)

            page.load()
            page.render(renderer)

            self.wfile.write(renderer.getContents())

            self.wfile.write("</body></html>")

        elif self.path == '/style.css':
            self.send_response(200)
            self.send_header('Content-type', 'text/css')
            self.end_headers()
            with open('style.css', 'r') as f:
                self.wfile.write(f.read())

        elif self.path == '/favicon.ico':
            self.send_response(200)
            self.send_header('Content-type', 'image/x-icon')
            self.end_headers()
            with open('favicon.ico', 'r') as f:
                self.wfile.write(f.read())

        elif self.path.startswith('/set-name?'):
            q = urlparse(self.path).query
            p = parse_qs(q)
            print(p, q)
            addr = address.fromConventional(p['addr'][0])
            name = p['name'][0]
            self.server.proj.database.setNameForAddress(addr, name)
            self.redirect(self.headers['Referer'])

        elif self.path == '/quit/':
            self.server.request_stop = True
            self.send_response(200)
            self.end_headers()

        else:
            self.send_response(404)
            self.end_headers()

    def address_string(self):
        # fix for slow reverse lookup on Windows
        return self.client_address[0]

class StoppableHTTPServer(HTTPServer):
    def serve_forever(self):
        self.request_stop = False
        while not self.request_stop:
            self.handle_request()

class ServerTask(AsyncTask):
    def __init__(self, proj, port=8888):
        super(ServerTask, self).__init__()
        self.base_proj = proj
        self.port = port
        self.server = None

    def work(self):
        self.report("Loading project")

        proj = self.base_proj.openCopy()

        self.server = StoppableHTTPServer(('', self.port), Handler)
        self.server.proj = proj
        self.report("Running server...")
        self.server.serve_forever()

        proj.close()

        self.report("Server stopped.")

    def stop(self):
        if self.server:
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
    def __init__(self, parent, log, proj):
        ttk.Frame.__init__(self, parent)

        self.task = ServerTask(proj)
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
    def __init__(self, parent, proj):
        if not parent:
            parent = getTkRoot()
        tk.Toplevel.__init__(self, parent)

        self.title("Awake Server")

        frame = ttk.Frame(self)
        frame.pack(fill='x')

        self.log = LogFrame(self)
        self.server_frame = ServerFrame(frame, self.log, proj)
        self.server_frame.pack(side='left', fill='y', padx=10, pady=10)

        self.log.pack(side='bottom', fill='both', expand=True)

        self.protocol("WM_DELETE_WINDOW", self.quit)

    def quit(self):
        self.server_frame.stopServer()
        self.destroy()

    def wait(self):
        self.wait_window(self)
