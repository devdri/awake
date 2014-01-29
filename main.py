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

from __future__ import print_function
import argparse
from awake.gui import MainWindow
from awake.project import Project
from awake.server import ServerTask

parser = argparse.ArgumentParser()
parser.add_argument('rom_file', nargs='?')
parser.add_argument('start_url', nargs='?')
parser.add_argument('config_file', nargs='?')
parser.add_argument('rom_config_file', nargs='?')
parser.add_argument('--server', action='store_true', default=False)

if __name__ == '__main__':
    args = parser.parse_args()

    if args.server:
        if args.rom_file:
            proj = Project(args.rom_file, args.config_file, args.rom_config_file)
            task = ServerTask(proj)
            task.report = print
            task.executeSynchronous()
        else:
            print("Rom file is required for running server\n")
    else:
        app = MainWindow(None, "roms/blue.gb", args.start_url, args.config_file, args.rom_config_file)
        app.mainloop()
