LATEST_VERSION=2
import sqlite3, argparse, os, shutil
import upgradedb.database_versions as dbv
import upgradedb.database_upgrades as dbu

parser = argparse.ArgumentParser()
parser.add_argument('file', nargs='?', default='roms/blue.gb')

def getDB(filename):
        split=os.path.splitext(filename)
        if split[1]=='.gb':
            return split[0]+'.awakedb'
        if split[1]=='':
            return split[0]+'.awakedb'
        elif split[1]=='.awakedb':
            return filename
        else:
            raise ValueError("Not a rom or database!")

def upgradeDatabase(filename):
    while dbv.detectVersion(filename)!=LATEST_VERSION:
        dbu.upgrade(filename)
    
    
if __name__ == '__main__':
    args = parser.parse_args()
    
    if args.file:
        filename=getDB(args.file)
        ver=dbv.detectVersion(filename)
        print "Database is version",ver
        print "Latest version is",LATEST_VERSION
        if ver!=LATEST_VERSION:
            shutil.copy(filename,filename+".ver"+str(ver)+".bak")
            upgradeDatabase(filename)
            print "Done!"
        else:
            print "Nothing to do!"
    else:
        print "No rom file selected."
