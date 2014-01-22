from awake.export import ExportDialog
from awake.project import Project

if __name__ == '__main__':
    app = ExportDialog(None, Project('roms/zelda.gb'))
    app.wait()
