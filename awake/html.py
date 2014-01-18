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

from . import tag

def span(contents, klass):
    return '<span class="{1}">{0}</span>'.format(contents, klass)

def addr_link(prefix, addr, klass):
    return '<a class="{0}" href="{1}{2}">{3}</a>'.format(klass, prefix, addr, tag.nameForAddress(addr))

def label(addr):
    return '<a name="{0}">label_{1}</a>:\n'.format(addr, tag.nameForAddress(addr))

def pad(indent):
    return '    ' * indent

def instruction(addr, name, operand_html='', indent=0, signature=''):
    out = span(str(addr).rjust(9), 'op-addr')
    out += ' '
    out += span(pad(indent) + name.ljust(10), 'op-name')
    out += span(operand_html, 'op-operands')
    out += span(signature, 'op-signature')
    return out + '\n'
