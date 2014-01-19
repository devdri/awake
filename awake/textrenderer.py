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

class HtmlRenderer(object):
    def __init__(self, database):
        self.database = database
        self.content = []
        self.emptyLine = True

    def getContents(self):
        return ''.join(self.content)

    def add(self, text, klass=None):
        text = str(text)
        if klass:
            text = '<span class="{1}">{0}</span>'.format(text, klass)
        self.content.append(text)
        self.emptyLine = False

    def pad(self, indent):
        self.add('    ' * indent)

    def addr_link(self, prefix, addr, klass):
        self.add('<a class="{0}" href="{1}{2}">{3}</a>'.format(klass, prefix, addr, self.database.tagdb.nameForAddress(addr)))

    def label(self, addr):
        self.content.append('<a name="{0}">label_{1}</a>:\n'.format(addr, self.database.tagdb.nameForAddress(addr)))

    def newInstruction(self, addr, indent):
        if not self.emptyLine:
            self.newline()
        self.add(str(addr).rjust(9), 'op-addr')
        self.add(' ')
        self.pad(indent)

    def instructionName(self, name):
        self.add(name, 'op-name')

    def instructionSignature(self, signature):
        self.add(signature, 'op-signature')

    def newline(self): # warn: not used everywhere
        self.add('\n')
        self.emptyLine = True

    def addLegacy(self, text):
        self.add(text)

    def renderList(self, elements, sep=', '):
        prev = False
        for el in elements:
            if prev:
                self.add(sep)
            prev = True
            if hasattr(el, 'render'):
                el.render(self)
            else:
                self.add(el)

    def nameForAddress(self, addr):
        self.add(self.database.tagdb.nameForAddress(addr))
