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

import sqlite3

defaults = {
    'IO:FF04': 'IO:DIV',
    'IO:FF05': 'IO:TIMA',
    'IO:FF06': 'IO:TMA',
    'IO:FF07': 'IO:TAC',
    'IO:FF40': 'IO:LCDC',
    'IO:FF41': 'IO:STAT',
    'IO:FF42': 'IO:SCY',
    'IO:FF43': 'IO:SCX',
    'IO:FF44': 'IO:LY',
    'IO:FF45': 'IO:LYC',
    'IO:FF46': 'IO:DMA',
    'IO:FF47': 'IO:BGP',
    'IO:FF48': 'IO:OBP0',
    'IO:FF49': 'IO:OBP1',
    'IO:FF4A': 'IO:WY',
    'IO:FF4B': 'IO:WX',
    'IO:FFFF': 'IO:IE',
    'IO:FF0F': 'IO:IF',
}

class TagDB(object):
    def __init__(self, filename):
        self.connection = sqlite3.connect(filename)

        c = self.connection.cursor()
        c.execute('create table if not exists tags(addr text, name text)')
        c.close()
        self.connection.commit()

    def hasNameForAddress(self, addr):
        if str(addr) in defaults:
            return True

        c = self.connection.cursor()
        c.execute('select name from tags where addr=?', (str(addr),))
        result = c.fetchone()
        c.close()
        return bool(result)

    def nameForAddress(self, addr):
        if str(addr) in defaults:
            return defaults[str(addr)]

        c = self.connection.cursor()
        c.execute('select name from tags where addr=?', (str(addr),))
        result = c.fetchone()
        c.close()

        if result:
            return result[0]
        else:
            return str(addr)

    def setNameForAddress(self, addr, name):
        c = self.connection.cursor()
        c.execute('select name from tags where addr=?', (str(addr),))
        if c.fetchone():
            print('updating')
            c.execute('update tags set name=? where addr=?', (name, str(addr)))
        else:
            print('new')
            c.execute('insert into tags (addr, name) values (?, ?)', (str(addr), name))
        c.close()
        self.connection.commit()

_global_db = None

def setGlobalTagDB(db):
    global _global_db
    _global_db = db

def getGlobalTagDB():
    return _global_db

setGlobalTagDB(TagDB('data/tags.db'))
