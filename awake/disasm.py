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

from awake.opcodedispatcher import OpcodeDispatcher

main_ops = """
00011000 3 JP    v8_rel               @ read:            write: sideeffects;
001FF000 2 JP    v8_rel, #F           @ read: #F         write: sideeffects;
110FF010 3 JP    v16, #F              @ read: #F         write: sideeffects;
11000011 4 JP    v16                  @ read:            write: sideeffects;
11101001 1 JP    HL                   @ read: HL         write: sideeffects;
11NNN111 4 CALL  #N                   @ read:            write: sideeffects;
11001101 6 CALL  v16                  @ read:            write: sideeffects;
110FF100 3 CALL  v16, #F              @ read: #F         write: sideeffects;
110FF000 2 RET   #F                   @ read: #F         write: sideeffects;
11001001 4 RET                        @ read:            write: sideeffects;
11011001 4 RETI                       @ read:            write: sideeffects;

000R0010 1 LD    [#R], A              @ read: A #R       write: mem;
000R1010 1 LD    A, [#R]              @ read: #R mem     write: A;
00SSS110 2 LD    #S, v8               @ read:            write: #S;
01SSSZZZ 1 LD    #S, #Z               @ read: #Z         write: #S;
11100000 3 LD    [FF00_v8], A         @ read: A          write: mem;
11110000 3 LD    A, [FF00_v8]         @ read: mem        write: A;
11100010 2 LD    [0xFF00 +. C], A     @ read: A C        write: mem;
11110010 2 LD    A, [0xFF00 +. C]     @ read: C mem      write: A;
11101010 4 LD    [v16], A             @ read: A          write: mem;
11111010 4 LD    A, [v16]             @ read: mem        write: A;
00001000 5 LD16  [v16], SP            @ read: SP         write: mem;
00RR0001 3 LD16  #R, v16              @ read:            write: #R;
11111001 2 LD16  SP, HL               @ read: HL         write: SP;
00100010 2 LDI   [HL], A              @ read: A HL       write: [HL]:A; HL:HL +. 1; mem;
00101010 2 LDI   A, [HL]              @ read: HL mem     write: A:[HL]; HL:HL +. 1;
00110010 2 LDD   [HL], A              @ read: A HL       write: [HL]:A; HL:HL -. 1; mem;
00111010 2 LDD   A, [HL]              @ read: HL mem     write: A:[HL]; HL:HL -. 1;

00RR0011 2 INC16 #R                   @ read: #R         write: #R:#R +. 1;
00RR1011 2 DEC16 #R                   @ read: #R         write: #R:#R -. 1;
00SSS100 1 INC   #S                   @ read: #S         write: #S:(#S + 1); FZ:(#S == 0); FH; FN:0;
00SSS101 1 DEC   #S                   @ read: #S         write: #S:(#S - 1); FZ:(#S == 0); FH; FN:1;
00RR1001 2 ADD16 HL, #R               @ read: #R HL      write: HL:HL +. #R; FC; FH; FN:0;
11101000 4 ADDSP SP, v8               @ read: SP         write: SP; FC; FZ:0; FN:0; FH:0;
11111000 3 LDADD HL, SP, v8           @ read: SP         write: HL; FC; FZ:0; FN:0; FH:0;

10000SSS 1 ADD   A, #S                @ read: A #S       write: FC:c_add(A, #S); A:(A + #S); FH; FZ:(A == 0); FN:0;
11000110 2 ADD   A, v8                @ read: A          write: FC:c_add(A, v8); A:(A + v8); FH; FZ:(A == 0); FN:0;
10001SSS 1 ADC   A, #S                @ read: A FC #S    write: A:(A + #S + FC); FC; FH; FZ:(A == 0); FN:0;
11001110 2 ADC   A, v8                @ read: A FC       write: A:(A + v8 + FC); FC; FH; FZ:(A == 0); FN:0;
10010SSS 1 SUB   A, #S                @ read: A #S       write: FC:(A < #S); A:(A - #S); FH; FZ:(A == 0); FN:1;
11010110 2 SUB   A, v8                @ read: A          write: FC:(A < v8); A:(A - v8); FH; FZ:(A == 0); FN:1;
10011SSS 1 SBC   A, #S                @ read: A FC #S    write: FC; A:(A - #S - FC); FH; FZ; FN:1;
11011110 2 SBC   A, v8                @ read: A FC       write: FC; A:(A - v8 - FC); FH; FZ; FN:1;
10100SSS 1 AND   A, #S                @ read: A #S       write: A:(A & #S); FZ:(A == 0); FC:0; FH:1; FN:0;
11100110 2 AND   A, v8                @ read: A          write: A:(A & v8); FZ:(A == 0); FC:0; FH:1; FN:0;
10101SSS 1 XOR   A, #S                @ read: A #S       write: A:(A ^ #S); FZ:(A == 0); FC:0; FH:0; FN:0;
11101110 2 XOR   A, v8                @ read: A          write: A:(A ^ v8); FZ:(A == 0); FC:0; FH:0; FN:0;
10110SSS 1 OR    A, #S                @ read: A #S       write: A:(A | #S); FZ:(A == 0); FC:0; FH:0; FN:0;
11110110 2 OR    A, v8                @ read: A          write: A:(A | v8); FZ:(A == 0); FC:0; FH:0; FN:0;
10111SSS 1 CP    A, #S                @ read: A #S       write: FZ:(A == #S); FC:(A < #S); FH; FN:1;
11111110 2 CP    A, v8                @ read: A          write: FZ:(A == v8); FC:(A < v8); FH; FN:1;
00000111 1 RLCA                       @ read: A          write: FC:(A>>7); A:(A<<1)|(A>>7); FN:0; FZ:0; FH:0;
00001111 1 RRCA                       @ read: A          write: FC:(A & 1); A:(A>>1)|(A<<7); FN:0; FZ:0; FH:0;
00010111 1 RLA                        @ read: A FC       write: A:((A<<1) | FC); FC; FN:0; FZ:0; FH:0;
00011111 1 RRA                        @ read: A FC       write: A:((A>>1) | (FC<<7)); FC; FN:0; FZ:0; FH:0;

00100111 1 DAA                        @ read: A FN FH FC write: A; FZ; FC; FH;
00101111 1 CPL                        @ read: A          write: A:(A ^ 0xFF); FN:1; FH:1;

00110111 1 SCF                        @ read:            write: FC:1; FN:0; FH:0;
00111111 1 CCF                        @ read: FC         write: FC:(FC^1); FN:0; FH:0;
11110011 1 DI                         @ read:            write: IME:0; sideeffects;
11111011 1 EI                         @ read:            write: IME:1; sideeffects;

11QQ0001 3 POP   #Q                   @ read: SP mem     write: #Q:popval(SP); SP:popst(SP);
11QQ0101 3 PUSH  #Q                   @ read: SP #Q      write: SP:push(SP, #Q); mem;

00000000 1 NOP                        @ read:            write:
00010000 1 STOP                       @ read:            write: sideeffects;
01110110 1 HALT                       @ read:            write: sideeffects;
"""

cb_ops = """
00000SSS 2 RLC  #S                    @ read: #S         write: FC:(#S>>7); #S:((#S<<1)|(#S>>7)); FZ:(#S == 0); FH:0; FN:0;
00001SSS 2 RRC  #S                    @ read: #S         write: FC:(#S & 1); #S:((#S>>1)|(#S<<7)); FZ:(#S == 0); FH:0; FN:0;
00010SSS 2 RL   #S                    @ read: #S FC      write: #S:((#S<<1)|FC); FZ:(#S == 0); FC; FH:0; FN:0;
00011SSS 2 RR   #S                    @ read: #S FC      write: #S:((#S>>1)|(FC<<7)); FZ:(#S == 0); FC; FH:0; FN:0;
00100SSS 2 SLA  #S                    @ read: #S         write: FC:(#S>>7); #S:(#S<<1); FZ:(#S == 0); FH:0; FN:0;
00101SSS 2 SRA  #S                    @ read: #S         write: FC:(#S & 1); #S:((#S>>1) | (#S & 0x80)); FZ:(#S == 0); FH:0; FN:0;
00110SSS 2 SWAP #S                    @ read: #S         write: #S:((#S>>4) | (#S<<4)); FZ:(#S == 0); FC:0; FH:0; FN:0;
00111SSS 2 SRL  #S                    @ read: #S         write: FC:(#S & 1); #S:(#S>>1); FZ:(#S == 0); FH:0; FN:0;
01IIISSS 2 BIT  #I, #S                @ read: #S         write: FZ:((#S & (1<<#I)) == 0); FH:1; FN:0;
10IIISSS 2 RES  #I, #S                @ read: #S         write: #S:(#S & (0xFF ^ (1<<#I)));
11IIISSS 2 SET  #I, #S                @ read: #S         write: #S:(#S | (1<<#I));
"""

class Z80Disasm(object):
    def __init__(self, proj):
        self.proj = proj
        self.main = OpcodeDispatcher(main_ops.splitlines())
        self.cb = OpcodeDispatcher(cb_ops.splitlines())
        self.cache = dict()
        self.next_addr_cache = dict()

    def _decode(self, addr):
        opcode = self.proj.rom.get(addr)
        if opcode == 0xCB:
            return self.cb.decode(self.proj, addr.offset(1))
        else:
            return self.main.decode(self.proj, addr)

    def decodeCache(self, addr):
        if addr not in self.cache:
            self.cache[addr], self.next_addr_cache[addr] = self._decode(addr)
        return self.cache[addr], self.next_addr_cache[addr]
