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
from contextlib import closing
from awake import address
from awake.depend import decodeDependencySet, encodeDependencySet, unknownDependencySet
from awake.operand import ProcAddress
from awake.textrenderer import HtmlRenderer

def convert_address(text):
    return address.fromConventional(text)

def adapt_address(addr):
    return str(addr)

sqlite3.register_converter('address', convert_address)
sqlite3.register_adapter(address.Address, adapt_address)

def getFirst(x, alt=None):
    if x:
        return x[0]
    else:
        return alt

class ProcInfo(object):
    def __init__(self, connection, addr, result=None):

        c = connection.cursor()
        c.execute('select type, depset, has_switch, suspicious_switch, has_suspicious_instr, has_nop, has_ambig_calls, length from procs where addr=?', (addr,))
        assert c.rowcount <= 1
        result = c.fetchone()

        self.addr = addr
        if result:
            self.type = result[0]
            self.depset = decodeDependencySet(result[1])
            self.has_switch = result[2]
            self.suspicious_switch = result[3]
            self.has_suspicious_instr = result[4]
            self.has_nop = result[5]
            self.has_ambig_calls = result[6]
            self.length = result[7]
        else:
            self.type = "proc"
            self.depset = unknownDependencySet()
            self.has_switch = False
            self.suspicious_switch = False
            self.has_suspicious_instr = False
            self.has_nop = False
            self.has_ambig_calls = True
            self.length = 0

        self.calls = set()
        self.tail_calls = set()
        c.execute('select destination, type from calls where source=?', (addr,))
        for dest, calltype in c.fetchall():
            if calltype == 'tail':
                self.tail_calls.add(dest)
            else:
                self.calls.add(dest)

        self.memreads = set()
        self.memwrites = set()
        c.execute('select addr, type from memref where proc=?', (addr,))
        for addr, reftype in c.fetchall():
            if reftype == 'read':
                self.memreads.add(addr)
            else:
                self.memwrites.add(addr)

        self.callers = set()
        c.execute('select source from calls where destination=?', (addr,))
        for src, in c.fetchall():
            self.callers.add(src)

        c.close()

    def save(self, connection):
        c = connection.cursor()
        c.execute('select addr from procs where addr=?', (self.addr,))
        if not c.fetchone():
            c.execute('insert into procs(addr) values (?)', (self.addr,))
        c.execute('update procs set type=?, depset=?, has_switch=?, suspicious_switch=?, has_suspicious_instr=? , has_nop=?, has_ambig_calls=?, length=? where addr=?',
                  (self.type, encodeDependencySet(self.depset), int(self.has_switch), int(self.suspicious_switch), int(self.has_suspicious_instr), int(self.has_nop), int(self.has_ambig_calls), self.length, self.addr))

        c.execute('delete from calls where source=?', (self.addr,))
        c.execute('delete from memref where proc=?', (self.addr,))

        for x in self.calls:
            c.execute('insert into calls(source, destination, type) values (?, ?, "call")', (self.addr, x))
        for x in self.tail_calls:
            c.execute('insert into calls(source, destination, type) values (?, ?, "tail")', (self.addr, x))
        for x in self.memreads:
            c.execute('insert into memref(addr, proc, type) values (?, ?, "read")', (x, self.addr))
        for x in self.memwrites:
            c.execute('insert into memref(addr, proc, type) values (?, ?, "write")', (x, self.addr))
        c.close()
        connection.commit()

    def render(self, renderer):
        pass

class Database(object):
    default_tags = {
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

    def __init__(self, filename):
        self.connection = sqlite3.connect(filename, detect_types=sqlite3.PARSE_DECLTYPES)

        c = self.connection.cursor()
        c.execute('create table if not exists procs(addr address, type text, depset text, has_switch integer, suspicious_switch integer, has_suspicious_instr integer, has_nop integer, has_ambig_calls integer, length integer)')
        c.execute('create table if not exists calls(source address, destination address, type text)')
        c.execute('create table if not exists memref(addr address, proc address, type text)')
        c.execute('create table if not exists tags(addr address, name text)')
        c.close()
        self.connection.commit()

    def close(self):
        self.connection.close()

    def hasNameForAddress(self, addr):
        if str(addr) in self.default_tags:
            return True

        with closing(self.connection.cursor()) as c:
            c.execute('select name from tags where addr=?', (addr,))
            return bool(getFirst(c.fetchone()))

    def nameForAddress(self, addr):
        if str(addr) in self.default_tags:
            return self.default_tags[str(addr)]

        with closing(self.connection.cursor()) as c:
            c.execute('select name from tags where addr=?', (addr,))
            return getFirst(c.fetchone(), str(addr))

    def setNameForAddress(self, addr, name):
        c = self.connection.cursor()
        c.execute('select name from tags where addr=?', (addr,))
        if c.fetchone():
            print('updating')
            c.execute('update tags set name=? where addr=?', (name, addr))
        else:
            print('new')
            c.execute('insert into tags (addr, name) values (?, ?)', (addr, name))
        c.close()
        self.connection.commit()

    def procInfo(self, addr):
        return ProcInfo(self.connection, addr)

    def reportProc(self, addr):
        procInfo(self.connection, addr).save(self.connection)

    def getNextOwnedAddress(self, addr):
        with closing(self.connection.cursor()) as c:
            c.execute('select addr from procs where addr > ? order by addr', (addr,))
            return getFirst(c.fetchone())

    def getUnfinished(self):
        with closing(self.connection.cursor()) as c:
            c.execute('select addr from procs where has_ambig_calls=1 and suspicious_switch=0 and has_suspicious_instr=0')
            return [x[0] for x in c.fetchall()]

    def getAll(self):
        with closing(self.connection.cursor()) as c:
            c.execute('select addr from procs order by addr')
            return [x[0] for x in c.fetchall()]

    def getAllInBank(self, bank):
        bank_name = "{:04X}".format(bank)
        with closing(self.connection.cursor()) as c:
            c.execute('select addr from procs where substr(addr, 0, 5)=? order by addr', (bank_name,))
            return [x[0] for x in c.fetchall()]

    def setInitial(self, initial):
        c = self.connection.cursor()
        c.executemany('insert into calls(source, destination) values ("FFFF:0000", ?)', ((x,) for x in initial))
        c.close()
        self.connection.commit()

    def getAmbigCalls(self):
        with closing(self.connection.cursor()) as c:
            c.execute('select addr from procs where has_ambig_calls=1')
            return [x[0] for x in c.fetchall()]

    def getDataReferers(self, data_addr):
        reads = set()
        writes = set()
        c = self.connection.cursor()
        c.execute('select proc, type from memref where addr=?', (data_addr,))
        for addr, reftype in c.fetchall():
            if reftype == 'read':
                reads.add(addr)
            else:
                writes.add(addr)
        c.close()
        return reads, writes

    def produce_map(self, proj):

        romsize = 512*1024
        width = 256
        height = romsize/width

        import Image
        img = Image.new('RGB', (width, height))

        for i in range(512*1024):
            addr = address.fromPhysical(i)
            if addr.bank() in (0x08, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13, 0x1C, 0x1D):
                color = (0, 0, 255)
            elif addr.bank() == 0x16 and addr.virtual() >= 0x5700:
                color = (0, 0, 255)
            elif addr.bank() == 0x09 and addr.virtual() >= 0x6700:
                color = (0, 0, 255)
            elif proj.rom.get(addr) == 0xFF:
                color = (0, 0, 127)
            else:
                color = (0, 0, 0)
            x = i % width
            y = i // width
            img.putpixel((x, y), color)

        c = self.connection.cursor()
        c.execute('select addr, length from procs order by addr')
        for addr, length in c.fetchall():
            for i in range(length):
                byte_addr = addr.offset(i).physical()

                x = byte_addr % width
                y = byte_addr // width
                color = (0, 255, 0)
                img.putpixel((x, y), color)

        c.close()

        img.save('data/ownership.png')
        print('image saved')
