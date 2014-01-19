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

def span(database, contents, klass):
    return '<span class="{1}">{0}</span>'.format(contents, klass)

def addr_link(database, prefix, addr, klass):
    return '<a class="{0}" href="{1}{2}">{3}</a>'.format(klass, prefix, addr, database.tagdb.nameForAddress(addr))

def label(database, addr):
    return '<a name="{0}">label_{1}</a>:\n'.format(addr, database.tagdb.nameForAddress(addr))

def pad(database, indent):
    return '    ' * indent

def instruction(database, addr, name, operand_html='', indent=0, signature=''):
    out = span(database, str(addr).rjust(9), 'op-addr')
    out += ' '
    out += span(database, pad(database, indent) + name.ljust(10), 'op-name')
    out += span(database, operand_html, 'op-operands')
    out += span(database, signature, 'op-signature')
    return out + '\n'
