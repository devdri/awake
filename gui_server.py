from awake.server import ServerDialog
from awake.project import Project

if __name__ == '__main__':
    app = ServerDialog(None, Project('roms/zelda.gb'))
    app.wait()
