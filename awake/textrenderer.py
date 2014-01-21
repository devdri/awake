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

class Indent(object):
    def __init__(self, renderer):
        self.renderer = renderer

    def __enter__(self):
        self.renderer.indent(1)

    def __exit__(self, type, value, traceback):
        self.renderer.indent(-1)

class RendererSettingBlock(object):
    """Sets a renderer setting on entering a with block and restores it on leaving."""

    def __init__(self, renderer, setting_name, setting_value):
        self.renderer = renderer
        self.setting_name = setting_name
        self.setting_value = setting_value

    def __enter__(self):
        self.old_value = getattr(self.renderer, self.setting_name)
        setattr(self.renderer, self.setting_name, self.setting_value)

    def __exit__(self, type, value, traceback):
        setattr(self.renderer, self.setting_name, self.old_value)

class Renderer(object):
    def __init__(self, database):
        self.database = database
        self.currentIndent = 0
        self.currentLineAddr = None
        self.inComment = False

    def indent(self, d=None):
        if d:
            self.currentIndent += d
        else:
            return Indent(self)

    def lineAddress(self, addr):
        return RendererSettingBlock(self, 'currentLineAddr', addr)

    def comment(self):
        return RendererSettingBlock(self, 'inComment', True)

    def pad(self, num=None):
        if not num:
            num = self.currentIndent
        self.add('  ' * num)

    def newInstruction(self, addr):
        self.add('\n')
        self.add(str(addr).rjust(9), 'line-address')
        self.add(' ')
        self.pad()

    def instructionName(self, name):
        self.add(name, 'op-name')

    def instructionSignature(self, signature):
        # TODO: make it proper
        if not isinstance(signature, str):
            signature = str(signature)

        self.add(signature, 'op-signature')

    def label(self, addr, signature=None):
        self.add('\n')
        self.add(str(addr), 'line-address')
        self.add(' ')
        self.write('label_'+str(addr)+':', 'label')
        if signature:
            self.instructionSignature(signature)

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
        self.add(self.database.nameForAddress(addr))

    def add(self, text, klass=None, url=None):
        assert isinstance(text, str)
        if self.inComment and not klass:
            klass = 'comment'
        self._add(text, klass, url)

    def write(self, text, klass=None, url=None):
        self.add(text, klass, url)

    def startNewLine(self):
        self.add('\n')
        self.add(str(self.currentLineAddr), 'line-address')
        self.add(' ')
        self.pad()
        if self.inComment:
            self.add('# ', 'comment')

    def writeList(self, elements, sep=', '):
        return self.renderList(elements, sep)

    def writeSymbol(self, addr, klass, url=None):
        return self.add(self.database.nameForAddress(addr), klass, url)

    def hline(self):
        with self.comment():
            self.startNewLine()
            self.write('-'*40)

class HtmlRenderer(Renderer):
    def __init__(self, database):
        super(HtmlRenderer, self).__init__(database)
        self.content = []

    def getContents(self):
        return '<pre>' + (''.join(self.content)) + '</pre>'

    def _add(self, text, klass=None, url=None):
        text = str(text)
        if klass:
            text = '<span class="{1}">{0}</span>'.format(text, klass)
        if url:
            text = '<a href="{1}">{0}</a>'.format(text, url)
        self.content.append(text)

class PlainTextRenderer(Renderer):
    def __init__(self, database):
        super(PlainTextRenderer, self).__init__(database)
        self.content = []

    def getContents(self):
        print self.content
        print [str(x) for x in self.content]
        return ''.join(self.content)

    def _add(self, text, klass=None, url=None):
        self.content.append(text)

class TkRenderer(Renderer):
    def __init__(self, database, tk_text):
        super(TkRenderer, self).__init__(database)
        self.tk_text = tk_text

    def _add(self, text, klass=None, url=None):
        if url:
            self.tk_text.insertLink(text, url, (klass,))
        else:
            self.tk_text.insert('end', text, (klass,))
