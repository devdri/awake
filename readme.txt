Awake - Gameboy decompiler
Author: Wojciech Marczenko (devdri) <wojtek.marczenko@gmail.com>
License: GPLv3
Python version: 2.7 (some features require PIL)

Easiest way to start:
- put zelda.gb into roms/ (MD5: c4360f89e2b09a21307fe864258ecab7)
- run python main.py
- browse to http://localhost:8888/proc/0000:0150

The code is a mess right now, but here are few pointers where to start:
- awake/disasm.py: rom = rom.Rom("roms/zelda.gb"). I was just too lazy to do it properly. Set your rom path here.
- ui.run() starts server. There are some commented lines that search for new procedures or produce rom maps etc.
- graph.search() - set your entry points there or get them from database with getUnfinished() or getAll() for full refresh.

Have fun!
