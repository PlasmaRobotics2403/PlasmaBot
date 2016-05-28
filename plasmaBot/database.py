import os
import sqlite3

from .exceptions import HelpfulError

class PRDatabase:
    def __init__(self, database_file):
        self.connection = sqlite3.connect(database_file)
        self.connection.execute('pragma foreign_keys = on')
        self.connection.commit()
        self.cursor = self.connection.cursor()
    

    def query(self, arg):
        self.cursor.execute(arg)
        self.connection.commit()
        return self.cur
    

    def doesExist(self, objtype, objname):
        tqcount = self.cursor.execute("SELECT name FROM sqlite_master WHERE type='{type}' AND name='{name}';"\
            .format(type = objtype, name = objname))
    
        if tqcount == 1:
            return True

        return False

    def __del__(self):
        self.connection.close()

class AutoReplyDatabase:
    def __init__(self, database_file):
        self.db = PRDatabase(database_file)
        self.conn = self.db.connection
        self.cur = self.db.cursor

        if not self.db.doesExist("table","DEFAULT"):
            self.cur.execute("CREATE TABLE DEFAULT(HANDLER TEXT PRIMARY KEY NOT NULL, RESPONSE TEXT NOT NULL, REPLY INT NOT NULL, DELETE INT NOT NULL, DELETETIME INT)")
            self.cur.execute("INSERT INTO DEFAULT VALUES('PlasmaBotTestAutoReply', 'Autoreplies are correctly enabled', 1, 20)")
            self.conn.commit()

    def findResponse(self, objtable, objhandler):
        self.cur.execute("SELECT * FROM {table} WHERE Name = '{handler}'"\
            .format(table = objtable, handler = objhandler))
        autoValue = self.cur.fetchone()
        autoResponse = autoValue[1]

        if autoValue[2] == 1:
            autoReply = True
        else:
            autoReply = False

        if autoValue[3] == 1:
            autoDelete = True
        else:
            autoDelete = False

        if autoDelete:
            autoDeleteTime = autoValue[4]
        else:
            autoDeleteTime = 0

        autoArray = [autoResponse, autoReply, autoDelte, autoDeleteTime]

        return autoArray
            
    def addAutoReply(self, server, handler, response, reply, delete, deletetime):
        if not self.db.doesExist("table", "S{serverID}".format(serverID = server)):
            self.cur.execute("CREATE TABLE S{serverID}(HANDLER TEXT PRIMARY KEY NOT NULL, RESPONSE TEXT NOT NULL, REPLY INT NOT NULL, DELETE INT NOT NULL, DELETETIME INT)".format(serverID = server))
        
        self.cur.execute("SELECT RESPONSE FROM S{serverID} WHERE HANDLER = {autoHandler}".format(autoHandler = handler))
        
        possibleResponse = self.cur.fetchone()
        
        if data is None:
            status = False
        else:
            
            
    
    
    
    def __del__(self):
        self.conn.close()
        del self.db