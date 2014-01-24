import sqlite3
import upgradedb.database_versions as dbv
DEBUG=True
def upgrade(conn):
    ver=dbv.detectVersion(conn)
    c=conn.cursor()
    print "Upgrading database from version "+str(ver)+" to version "+str(ver+1)
    if ver==1:
        if (DEBUG):
            print "Changing memref::proc from type text to type addr\n\tCreating TEMP_TABLE"
        c.execute("CREATE TABLE TEMP_TABLE (addr address, proc address, type text)")
        if (DEBUG):
            print "\tTransferring values from memref to TEMP_TABLE"
        c.execute("INSERT INTO TEMP_TABLE SELECT * FROM memref")
        if (DEBUG):
            print "\tDropping memref"
        c.execute("DROP TABLE memref")
        if (DEBUG):
            print "\tRenaming TEMP_TABLE to memref"
        c.execute("ALTER TABLE TEMP_TABLE RENAME TO memref")
    else:
        raise ValueError("Don't know about version "+str(ver+1)+" yet!")
    c.close()
    conn.commit()
