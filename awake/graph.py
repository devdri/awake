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

from collections import defaultdict
from PIL import Image
from awake import address

def addr_symbol(addr):
    return 'A' + str(addr).replace(':', '_')

def save_dot(database, procs):
    with open('data/graph.dot', 'w') as f:
        f.write("digraph crossref {\n")
        for addr in procs:
            tags = ''

            info = database.procInfo(addr)

            if info.has_switch:
                tags += ' switch'
            if info.suspicious_switch:
                tags += ' suspicious_switch'
            if info.has_nop:
                tags += ' nop'
            if info.has_ambig_calls:
                tags += ' ambig_calls'
            if info.has_suspicious_instr:
                tags += ' suspicious'

            f.write('    ' + addr_symbol(addr) + ' [label="' + database.nameForAddress(addr) + tags + '"];\n')
            if tags:
                f.write('    ' + addr_symbol(addr) + ' [color="green"];\n')



            """"q = len(procedure.at(addr).instructions)

            if q < 32:
                intensity = 0
            elif q < 128:
                intensity = 64
            elif q < 512:
                intensity = 128
            elif q < 2048:
                intensity = 192
            else:
                intensity = 255
            """
            intensity = 0

            f.write('    ' + addr_symbol(addr) + ' [fillcolor="#FF{0:02x}{0:02x}"];\n'.format(255-intensity))
            f.write('    ' + addr_symbol(addr) + ' [style="filled"];\n')

            for c in info.calls:
                f.write('    ' + addr_symbol(addr) + ' -> ' + addr_symbol(c) + ';\n')
            for c in info.tail_calls:
                f.write('    ' + addr_symbol(addr) + ' -> ' + addr_symbol(c) + ' [color="blue"];\n'
)
        f.write("}\n")

def save_dot_for_bank(database, bank):
    bank_name = '{:04X}'.format(bank)

    with open('data/bank'+bank_name+'.dot', 'w') as f:
        f.write("digraph crossref {\n")

        cur = database.connection.cursor()
        cur.execute('select addr from procs where substr(addr, 0, 5)=?', (bank_name,))
        for proc_result in cur.fetchall():
            addr = address.fromConventional(proc_result[0])
            tags = ''

            info = database.procInfo(addr)

            is_public = False

            for c in info.callers:
                if c.bank() != bank:
                    is_public = True

            if info.has_switch:
                tags += ' switch'
            if info.suspicious_switch:
                tags += ' suspicious_switch'
            if info.has_nop:
                tags += ' nop'
            if info.has_ambig_calls:
                tags += ' ambig_calls'
            if info.has_suspicious_instr:
                tags += ' suspicious'

            if tags:
                f.write('    ' + addr_symbol(addr) + ' [color="green"];\n')

            if is_public:
                tags += ' public'

            f.write('    ' + addr_symbol(addr) + ' [label="' + database.nameForAddress(addr) + tags + '"];\n')
            f.write('    ' + addr_symbol(addr) + ' [style="filled"];\n')

            for c in info.calls:
                if c.bank() == bank:
                    f.write('    ' + addr_symbol(addr) + ' -> ' + addr_symbol(c) + ';\n')
            for c in info.tail_calls:
                if c.bank() == bank:
                    f.write('    ' + addr_symbol(addr) + ' -> ' + addr_symbol(c) + ' [color="blue"];\n')
        cur.close()
        f.write("}\n")

def produce_map(proj, ownership):

    granularity = 4
    romsize = 512*1024
    width = 64
    height = romsize/granularity/width

    img = Image.new('RGB', (width, height))

    for i in range(romsize/granularity):
        owners = set()
        for j in range(i*granularity, (i+1)*granularity):
            addr = address.fromPhysical(j)
            owners |= ownership[addr]

        color = (0, 0, 0)
        addr = address.fromPhysical(i*granularity)
        if len(owners) == 1:
            color = (0, 255, 0)
        elif len(owners) >= 2:
            color = (255, 0, 0)
        elif addr.bank() in (0x08, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13, 0x1C, 0x1D):
            color = (0, 0, 255)
        elif addr.bank() == 0x16 and addr.virtual() >= 0x5700:
            color = (0, 0, 255)
        elif addr.bank() == 0x09 and addr.virtual() >= 0x6700:
            color = (0, 0, 255)
        elif proj.rom.get(addr) == 0xFF:
            color = (0, 0, 127)

        x = i % width
        y = i / width
        img.putpixel((x, y), color)

    img.save('ownership.png')
    print('image saved')


def getSubgraph(database, start_points):
    queue = set(start_points)
    verts = set()

    while queue:
        x = queue.pop()
        if x in verts:
            continue

        verts.add(x)
        info = database.procInfo(x)
        for c in info.calls:
            queue.add(c)
    return verts

def search(proj):
    """
    input = [
address.fromConventional("0003:6A4B"),
address.fromConventional("0019:4461"),
address.fromConventional("0003:66BF"),
address.fromConventional("0018:7B61"),
address.fromConventional("0003:69C9"),
address.fromConventional("0003:5397"),
address.fromConventional("0003:52BE"),
address.fromConventional("0007:7AE3"),
address.fromConventional("0018:7930"),
address.fromConventional("0003:5844"),
address.fromConventional("0003:6A3D"),
address.fromConventional("0003:5882"),
address.fromConventional("0003:6AE7"),
address.fromConventional("0006:79CD"),
address.fromConventional("0004:7E6B"),
address.fromConventional("0006:7547"),
address.fromConventional("0004:5C04"),
address.fromConventional("0004:5BFF"),
address.fromConventional("0004:5C04"),
#address.fromConventional("0003:5A35"),
address.fromConventional("0007:785E"),
address.fromConventional("0006:797B"),
address.fromConventional("0006:6641"),
address.fromConventional("0006:6641"),
address.fromConventional("0006:7470"),
address.fromConventional("0006:673C"),
address.fromConventional("0006:4ACE"),
address.fromConventional("0006:7CFC"),
address.fromConventional("0006:7CD0"),
address.fromConventional("0015:4EAB"),
address.fromConventional("0006:7F5F"),
address.fromConventional("0006:4F5D"),
address.fromConventional("0006:7727"),
address.fromConventional("0006:65FB"),
address.fromConventional("0006:7EB5"),
address.fromConventional("0003:50B4"),
#address.fromConventional("0003:4D1E"),
#address.fromConventional("0003:4D1E"),
address.fromConventional("0006:760B"),
address.fromConventional("0019:6765"),
address.fromConventional("0004:5A8B"),
address.fromConventional("0004:6C2B"),
address.fromConventional("0015:75E5"),
address.fromConventional("0007:76BC"),
address.fromConventional("0003:5D7F"),
address.fromConventional("0003:60C0"),
address.fromConventional("0003:617D"),
address.fromConventional("0003:5CD0"),
address.fromConventional("0003:5BDC"),
address.fromConventional("0003:5BCB"),
address.fromConventional("0003:5BB0"),
address.fromConventional("0003:5BA0"),
address.fromConventional("0003:5A9C"),
address.fromConventional("0003:5A39"),
address.fromConventional("0003:609D"),
address.fromConventional("0003:5FEE"),
address.fromConventional("0003:5DDA"),
address.fromConventional("0003:5D92"),
address.fromConventional("0003:6083"),
address.fromConventional("0003:6029"),
address.fromConventional("0003:5FFF"),
address.fromConventional("0005:4DE5"),
address.fromConventional("0005:4915"),
address.fromConventional("0005:47E1"),
address.fromConventional("0006:6801"),
address.fromConventional("0018:5E68"),
address.fromConventional("0015:4494"),
address.fromConventional("0015:443F"),
address.fromConventional("0015:4365"),
address.fromConventional("0015:40FD"),
address.fromConventional("0015:41C7"),
address.fromConventional("0015:423A"),
address.fromConventional("0015:42AD"),
address.fromConventional("0003:5395"),
address.fromConventional("0004:7679"),
address.fromConventional("0004:762B"),
address.fromConventional("0004:6E46"),
address.fromConventional("0006:7AB3"),
address.fromConventional("0004:6971"),
address.fromConventional("0004:67E6"),
address.fromConventional("0004:67E6"),
address.fromConventional("0004:5F59"),
address.fromConventional("0004:7D80"),
address.fromConventional("0004:7C90"),
address.fromConventional("0004:5DE9"),
address.fromConventional("0004:5EF7"),
address.fromConventional("0004:569D"),
address.fromConventional("0004:5072"),
address.fromConventional("0004:49C1"),
address.fromConventional("0004:4009"),
address.fromConventional("0005:6C41"),
address.fromConventional("0005:7B05"),
address.fromConventional("0007:694D"),
address.fromConventional("0005:67CD"),
address.fromConventional("0019:4216"),
address.fromConventional("0005:6261"),
address.fromConventional("0005:59BB"),
address.fromConventional("0018:5DEF"),
address.fromConventional("0005:54AA"),
address.fromConventional("0015:4324"),
address.fromConventional("0005:549F"),
address.fromConventional("0015:7458"),
address.fromConventional("0018:53C2"),
address.fromConventional("0005:529E"),
address.fromConventional("0018:5D8B"),
address.fromConventional("0005:452E"),
address.fromConventional("0005:4038"),
address.fromConventional("0006:6BB4"),
address.fromConventional("0019:4894"),
address.fromConventional("0006:6248"),
address.fromConventional("0006:60C3"),
address.fromConventional("0006:60C3"),
address.fromConventional("0006:6248"),
address.fromConventional("0018:4DBF"),
address.fromConventional("0018:4CA4"),
address.fromConventional("0018:4B33"),
address.fromConventional("0006:5CE8"),
address.fromConventional("0006:5ABE"),
address.fromConventional("0006:5C4E"),
address.fromConventional("0006:5D5C"),
address.fromConventional("0006:5EFD"),
address.fromConventional("0006:62DE"),
address.fromConventional("0006:63CD"),
address.fromConventional("0006:642A"),
address.fromConventional("0018:72C6"),
address.fromConventional("0006:6A88"),
address.fromConventional("0006:6C58"),
address.fromConventional("0006:6ED4"),
address.fromConventional("0006:7066"),
address.fromConventional("0006:71C9"),
address.fromConventional("0006:7339"),
address.fromConventional("0006:7C19"),
address.fromConventional("0006:56B5"),
address.fromConventional("0006:53A1"),
address.fromConventional("0006:5107"),
address.fromConventional("0006:5049"),
address.fromConventional("0006:5049"),
address.fromConventional("0006:4EBF"),
address.fromConventional("0006:4F36"),
address.fromConventional("0006:4B92"),
address.fromConventional("0019:4777"),
address.fromConventional("0006:4949"),
address.fromConventional("0006:4247"),
address.fromConventional("0006:451B"),
address.fromConventional("0006:4150"),
address.fromConventional("0007:70AD"),
address.fromConventional("0006:4020"),
address.fromConventional("0019:5AFD"),
address.fromConventional("0019:4805"),
address.fromConventional("0007:7503"),
address.fromConventional("0007:7444"),
address.fromConventional("0007:7314"),
address.fromConventional("0007:71B4"),
address.fromConventional("0007:715E"),
address.fromConventional("0019:4022"),
address.fromConventional("0007:7031"),
address.fromConventional("0007:63F1"),
address.fromConventional("0007:6525"),
address.fromConventional("0007:666D"),
address.fromConventional("0007:61FB"),
address.fromConventional("0007:60BD"),
address.fromConventional("0007:60BD"),
address.fromConventional("0007:6198"),
address.fromConventional("0007:5F54"),
address.fromConventional("0007:5B47"),
address.fromConventional("0007:5D87"),
address.fromConventional("0007:597C"),
address.fromConventional("0019:680A"),
address.fromConventional("0019:680A"),
address.fromConventional("0019:687E"),
address.fromConventional("0007:55D5"),
address.fromConventional("0007:53DC"),
address.fromConventional("0007:52C6"),
address.fromConventional("0007:5109"),
address.fromConventional("0007:4F03"),
address.fromConventional("0015:751C"),
address.fromConventional("0007:4A88"),
address.fromConventional("0007:4CA8"),
address.fromConventional("0007:49A3"),
address.fromConventional("0007:480D"),
address.fromConventional("0007:44D3"),
address.fromConventional("0007:4272"),
address.fromConventional("0018:772B"),
address.fromConventional("0018:77EA"),
address.fromConventional("0007:4015"),
address.fromConventional("0018:6FA8"),
address.fromConventional("0018:69C7"),
address.fromConventional("0018:64A7"),
address.fromConventional("0018:6362"),
address.fromConventional("0018:627D"),
address.fromConventional("0018:6176"),
address.fromConventional("0018:5EB6"),
address.fromConventional("0018:4000"),
address.fromConventional("0018:54F7"),
address.fromConventional("0015:73C9"),
address.fromConventional("0015:734E"),
address.fromConventional("0018:451D"),
address.fromConventional("0018:5298"),
address.fromConventional("0018:50FC"),
address.fromConventional("0018:4E40"),
address.fromConventional("0018:49F5"),
address.fromConventional("0015:44BD"),
address.fromConventional("0019:6B97"),
address.fromConventional("0018:4957"),
address.fromConventional("0019:6E13"),
#address.fromConventional("0018:5132"), #
#address.fromConventional("0018:5180"), # cannot be included until 0018:5168 problems resolved
#address.fromConventional("0018:525D"), #
address.fromConventional("0018:51CA"),
address.fromConventional("0019:5D58"),
address.fromConventional("0019:5918"),
address.fromConventional("0019:5817"),
address.fromConventional("0019:55F3"),
address.fromConventional("0019:56E8"),
address.fromConventional("0019:54C1"),
address.fromConventional("0019:5344"),
address.fromConventional("0019:52E4"),
address.fromConventional("0019:518A"),
address.fromConventional("0019:4C9A"),
address.fromConventional("0019:4A1C"),
address.fromConventional("0019:4527"),
address.fromConventional("0015:768A"),
address.fromConventional("0015:78AC"),
address.fromConventional("0015:4D58"),
address.fromConventional("0015:4BF5"),
address.fromConventional("0015:46BE"),
address.fromConventional("0006:7C19"),
address.fromConventional("0015:5096"),
address.fromConventional("0015:409A"),
address.fromConventional("0017:7547"),
address.fromVirtual(0x100), address.fromVirtual(0x40), address.fromVirtual(0x48)
]
    #input = [address.fromVirtual(0x100), address.fromVirtual(0x40), address.fromVirtual(0x48)]
    """
    input = [
# in 0000:0C40
address.fromConventional("0002:5023"),
address.fromConventional("0002:4D92"),
address.fromConventional("0002:490E"),
address.fromConventional("0002:4D00"),
address.fromConventional("0002:4F30"),
address.fromConventional("0002:50A2"),
address.fromConventional("0002:4EFF"),

# in 0000:0B53
address.fromConventional("0002:5DD5"),
address.fromConventional("0002:5731"),
]

    #database.setInitial(input)

    input = proj.database.getAll()
    #input = database.getUnfinished()

    input = [address.fromConventional("0000:345B")]

    procs = set(input)
    callers = defaultdict(set)
    to_update = list(input)

    for i in range(5000):
        if not to_update:
            break

        x = to_update.pop()

        #if x.bank() in (0x1E, 0x1F, 0x1B):
        #    continue

        proj.flow.refresh(x)

        calls = proj.flow.at(x).calls() | proj.flow.at(x).tailCalls()
        for c in calls:
            callers[c].add(x)
            if c not in procs:
                proj.database.reportProc(c)
                procs.add(c)
                to_update.insert(0, c)

        #affected = set()
        #for c in callers[x]:
        #    if database.procInfo(x).has_ambig_calls:
        #        affected.add(x)
        #to_update = list(affected - set(to_update)) + to_update

    print('saving dot')
    save_dot(proj.database, procs)
    print('saved dot')
