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
    

    def tableDoesExist(self, objname):
        # self.cursor.execute(""" SELECT COUNT(*) FROM sqlite_master WHERE name = {name}  """.format(name = objname))
        # testCount = self.cursor.fetchone()
        # return bool(testCount[0])

        # Left inside tDE in case method before isn't giving desired functionality.

        if self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='{name}';".format(name=objname)).fetchone():
            return True

        else:
            return False

    def __del__(self):
        self.connection.close()

class AutoReplyDatabase:
    def __init__(self, database_file):
        self.db = PRDatabase(database_file)
        self.conn = self.db.connection
        self.cur = self.db.cursor

        if not self.db.tableDoesExist("GLOBAL"):
            self.cur.execute("CREATE TABLE GLOBAL ( HANDLER TEXT PRIMARY KEY NOT NULL, RESPONSE TEXT NOT NULL, REPLYTF INT NOT NULL, DELETETF INT NOT NULL, DELETETIME INT );")
            self.cur.execute("INSERT INTO GLOBAL VALUES ( 'PlasmaBotTestAutoReply', 'Autoreplies are correctly enabled', 1, 1, 20 );")
            self.conn.commit()

    def findResponse(self, objtable, objhandler):
        if not self.db.tableDoesExist("{tableID}".format(tableID = objtable)):
            autoArray = [1, None, None, None, None]
            return autoArray
        
        self.cur.execute("SELECT * FROM {table} WHERE Name = '{handler}';".format(table = objtable, handler = objhandler))
        autoValue = self.cur.fetchone()
        
        if autoValue is None:
            autoArray = [2, None, None, None, None]
            return autoArray
        
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

        autoArray = [0, autoResponse, autoReply, autoDelete, autoDeleteTime]

        return autoArray
            
    def addAutoReply(self, server, handler, response, reply, delete, delete_time):
        if not self.db.tableDoesExist("S{serverID}".format(serverID = server)):
            self.cur.execute("CREATE TABLE S{serverID} ( HANDLER TEXT PRIMARY KEY NOT NULL, RESPONSE TEXT NOT NULL, REPLYTF INT NOT NULL, DELETETF INT NOT NULL, DELETETIME INT )".format(serverID = server))
            self.conn.commit()
        
        self.cur.execute("SELECT RESPONSE FROM S{serverID} WHERE HANDLER = {autoHandler};".format(serverID = server, autoHandler = handler))
        
        possibleResponse = self.cur.fetchone()
        
        if data is None:
            status = False
            autoResponse = data[0]
        
        else:
            if reply:
                replyINT = 1
            else:
                replyINT = 0

            if delete:
                deleteINT = 1
            else:
                deleteINT = 0
    
            self.cur.execute("INSERT INTO S{serverID} VALUES ({autoHandler}, {autoResponse, {autoReplyINT}, {autoDeleteINT}, {autoDeleteTime} );".format(autoHandler = handler, autoResponse = autoResponse, autoReplyINT = replyINT, autoDeleteINT = deleteINT, autoDeleteTime = delete_time))
            self.conn.commit()
    
            status = True
            autoResponse = response
                
        confirmationArray = [status, autoResponse]
            
        return confirmationArray
    
    def __del__(self):
        self.conn.close()
        del self.db