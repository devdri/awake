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

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urlparse import urlparse, parse_qs
from awake import address
from awake.jumptable import JumpTable
from awake.operand import ProcAddress
from awake.procedure import loadProcedureRange
from awake.project import Project
from awake.textrenderer import HtmlRenderer

def proc_page(addr, out, server):

    info = server.proj.database.procInfo(addr)

    renderer = HtmlRenderer(server.proj.database)

    renderer.add('callers: ')
    renderer.renderList(ProcAddress(x) for x in info.callers)
    renderer.newline()

    server.proj.flow.refresh(addr)
    #out += 'deps: ' + str(flow.getProcDepSet(addr)) + '<br />'

    renderer.add('calls: ')
    renderer.renderList(ProcAddress(x) for x in server.proj.flow.at(addr).calls())
    renderer.newline()

    server.proj.flow.at(addr).render(renderer)

    loadProcedureRange(server.proj, addr).render(renderer, server.proj)

    out.write(renderer.getContents())

def data_page(addr, server):
    out = ''

    reads, writes = server.proj.database.getDataReferers(addr)

    renderer = HtmlRenderer(server.proj.database)

    renderer.addLegacy('<pre>\n')
    renderer.addLegacy('reads:\n')
    for x in reads:
        ProcAddress(x).render(renderer)
        renderer.newline()
    renderer.addLegacy('writes:\n')
    for x in writes:
        ProcAddress(x).render(renderer)
        renderer.newline()
    renderer.addLegacy('</pre>\n')

    return renderer.getContents()

def jumptable_page(addr, server):
    renderer = HtmlRenderer(server.proj.database)
    JumpTable(addr).render(renderer)
    return renderer.getContents()

def bank_page(bank, server):
    return server.proj.database.bankReport(bank)

def name_form(addr, server):
    out = ''
    out += '<form class="name-form" method="get" action="/set-name">'
    out += '<input type="hidden" name="addr" value="{0}" />'.format(addr)
    out += '<input type="text" name="name" value="{0}" />'.format(server.proj.database.nameForAddress(addr))
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

        if self.path.startswith('/proc/'):

            p = self.path.split('/')

            self.ok_html()
            self.wfile.write("<html><head><link rel=\"stylesheet\" type=\"text/css\" href=\"/style.css\" /></head><body>")
            addr = address.fromConventional(p[2])
            self.wfile.write(name_form(addr, self.server))
            proc_page(addr, self.wfile, self.server)
            self.wfile.write("</body></html>")

        elif self.path.startswith('/home'):

            self.ok_html()
            self.wfile.write("<html><head><link rel=\"stylesheet\" type=\"text/css\" href=\"/style.css\" /></head><body>")
            self.wfile.write(self.server.proj.database.getInteresting())
            self.wfile.write("</body></html>")

        elif self.path.startswith('/data/'):

            p = self.path.split('/')

            self.ok_html()
            self.wfile.write("<html><head><link rel=\"stylesheet\" type=\"text/css\" href=\"/style.css\" /></head><body>")
            addr = address.fromConventional(p[2])
            self.wfile.write(name_form(addr, self.server))
            self.wfile.write(data_page(addr, self.server))
            self.wfile.write("</body></html>")

        elif self.path.startswith('/jump/'):

            p = self.path.split('/')

            self.ok_html()
            self.wfile.write("<html><head><link rel=\"stylesheet\" type=\"text/css\" href=\"/style.css\" /></head><body>")
            addr = address.fromConventional(p[2])
            self.wfile.write(name_form(addr, self.server))
            self.wfile.write(jumptable_page(addr, self.server))
            self.wfile.write("</body></html>")

        elif self.path.startswith('/bank/'):

            p = self.path.split('/')

            self.ok_html()
            self.wfile.write("<html><head><link rel=\"stylesheet\" type=\"text/css\" href=\"/style.css\" /></head><body>")
            bank = int(p[2], 16)
            self.wfile.write(bank_page(bank, self.server))
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

        else:
            self.send_response(404)
            self.end_headers()

def run():
    proj = Project('roms/zelda.gb')

    import traceback
    try:
        print('')
        #start_points = database.getAmbigCalls()
        #graph.save_dot(graph.getSubgraph(start_points))
        #database.produce_map()
        #print "running search"
        #graph.search()
        #print "search finished"
        #graph.save_dot(set(database.getAll()))
        #for bank in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0xC, 0x12, 0x16, 0x39, 0x3F):
        #    print 'saving dot for bank', bank
        #    graph.save_dot_for_bank(bank)
    except Exception as e:
        print(traceback.format_exc())

    #database.produce_map()

    server = HTTPServer(('', 8888), Handler)
    server.proj = proj
    print("Running server...")
    server.serve_forever()

    proj.close()
