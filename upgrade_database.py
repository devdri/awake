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

def upgradeDatabase(name):
    ver=dbv.detectVersion(name)
    for i in xrange(LATEST_VERSION-ver):
        dbu.upgrade(name)
    
def doUpgrade(name):
    filename=getDB(name)
    ver=dbv.detectVersion(filename)
    if ver==0:
        print "Unknown database version!"
        print "Skipping upgrade check."
        return
    print "Database is version",ver
    print "Latest version is",LATEST_VERSION
    if ver!=LATEST_VERSION:
        shutil.copy(filename,filename+".ver"+str(ver)+".bak")
        upgradeDatabase(filename)
        print "Done!"
    else:
        print "Nothing to do!"
    
if __name__ == '__main__':
    args = parser.parse_args()
    
    if args.file:
        doUpgrade(args.file)
    else:
        print "No rom file selected."
