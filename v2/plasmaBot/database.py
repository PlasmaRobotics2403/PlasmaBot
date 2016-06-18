import os
import sqlite3

from SQLiteHelper import SQLiteHelper as sq
from .exceptions import HelpfulError

#import os
#import sqlite3
#
#from .exceptions import HelpfulError
#
#class PRDatabase:
#    def __init__(self, database_file):
#        self.connection = sqlite3.connect(database_file)
#        self.connection.execute('pragma foreign_keys = on')
#        self.connection.commit()
#        self.cursor = self.connection.cursor()
#
#
#    def query(self, arg):
#        self.cursor.execute(arg)
#        self.connection.commit()
#        return self.cur
#
#
#    def tableDoesExist(self, objname):
#        # self.cursor.execute(""" SELECT COUNT(*) FROM sqlite_master WHERE name = {name}  """.format(name = objname))
#        # testCount = self.cursor.fetchone()
#        # return bool(testCount[0])
#
#        # Left inside tDE in case method before isn't giving desired functionality.
#
#        if self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='{name}';".format(name=objname)).fetchone():
#            return True
#
#        else:
#            return False
#
#    def __del__(self):
#        self.connection.close()
#
#class AutoReplyDatabase:
#    def __init__(self, database_file):
#        self.db = PRDatabase(database_file)
#        self.conn = self.db.connection
#        self.cur = self.db.cursor
#
#        if not self.db.tableDoesExist("GLOBAL"):
#            self.cur.execute("CREATE TABLE GLOBAL ( HANDLER TEXT PRIMARY KEY NOT NULL, RESPONSE TEXT NOT NULL, REPLYTF INT NOT NULL, DELETETF INT NOT NULL, DELETETIME INT );")
#            print("creating database: GLOBAL")
#            self.cur.execute("INSERT INTO GLOBAL VALUES ( 'ping', 'pong', 1, 1, 20 );")
#            print("Values: ['ping', 'pong', 1, 1, 20] inserted into GLOBAL")
#            self.conn.commit()
#
#    def findResponse(self, objtable, objhandler):
#        if not self.db.tableDoesExist("{tableID}".format(tableID = objtable)):
#            print("[DBError]: Table {tableID} does not exist.".format(tableID=objtable))
#            autoArray = [1, None, None, None, None]
#            return autoArray
#
#        self.cur.execute("SELECT * FROM {table} WHERE Name = '{handler}';".format(table = objtable, handler = objhandler))
#        autoValue = self.cur.fetchone()
#
#        if autoValue is None:
#            autoArray = [2, None, None, None, None]
#            return autoArray
#
#        autoResponse = autoValue[1]
#
#        if autoValue[2] == 1:
#            autoReply = True
#        else:
#            autoReply = False
#
#        if autoValue[3] == 1:
#            autoDelete = True
#        else:
#            autoDelete = False
#
#        if autoDelete:
#            autoDeleteTime = autoValue[4]
#        else:
#            autoDeleteTime = 0
#
#        autoArray = [0, autoResponse, autoReply, autoDelete, autoDeleteTime]
#
#        return autoArray
#
#    def addAutoReply(self, server, handler, response, reply, delete, delete_time):
#        if not self.db.tableDoesExist("S{serverID}".format(serverID=server.ID)):
#            print("creating database: S{serverID}...".format(serverID=server.ID))
#            self.cur.execute("CREATE TABLE S{serverID} ( HANDLER TEXT PRIMARY KEY NOT NULL, RESPONSE TEXT NOT NULL, REPLYTF INT NOT NULL, DELETETF INT NOT NULL, DELETETIME INT )".format(serverID = server))
#            self.conn.commit()
#
#        self.cur.execute("SELECT RESPONSE FROM S{serverID} WHERE HANDLER = {autoHandler};".format(serverID = server.ID, autoHandler = handler))
#
#        possibleResponse = self.cur.fetchone()
#
#        if data is None:
#            status = False
#            autoResponse = data[0]
#
#        else:
#            if reply:
#                replyINT = 1
#            else:
#                replyINT = 0
#
#            if delete:
#                deleteINT = 1
#            else:
#                deleteINT = 0
#
#            self.cur.execute("INSERT INTO S{serverID} VALUES ({autoHandler}, {autoResponse, {autoReplyINT}, {autoDeleteINT}, {autoDeleteTime} );".format(autoHandler = handler, autoResponse = autoResponse, autoReplyINT = replyINT, autoDeleteINT = deleteINT, autoDeleteTime = delete_time))
#            self.conn.commit()
#
#            status = True
#            autoResponse = response
#
#        confirmationArray = [status, autoResponse]
#
#        return confirmationArray
#
#    def __del__(self):
#        self.conn.close()
#        del self.db

class plasmaBotDatabase:
    def __init__(self, database_file):
        self.file_path = database_file
        self.db = sq.Connect(database_file)
        self.con = self.db.getConn()
        self.cur = self.con.cursor()

    def tableExists(self, table):
        self.cur.execute("""
                SELECT COUNT(*)
                FROM sqlite_master
                WHERE type = 'table'
                AND table_name = '{0}'
                """.format(table))
        table_count = self.cur.fetchone()[0]
        return bool(table_count)

    def __del__(self):
        self.con.close()
        del self.db
        del self.con
        del self.cur

class autoReplyDatabase(plasmaBotDatabase):
    def __init__(self, database_file):
        super().__init__(database_file)

        if not super().tableExists("GLOBAL"):
            self.db.table("GLOBAL").withColumns("HANDLER", "REPLY", "REPLYBOOL", "DELETEBOOL", "DELETETIME").withDataTypes("TEXT PRIMARY KEY NOT NULL", "TEXT", "INT", "INT", "INT").createTable()
            self.db.table("GLOBAL").insert("ping", "pong", "0", "1", "30").into("HANDLER", "REPLY", "REPLYBOOL", "DELETEBOOL", "DELETERESPONSE")
            print("[DATA] GLOBAL AUTOREPLY DATABASE CREATED WITH AUTOREPLY [ping][pong][0][1][30]")

    def globalDoesExist(self, handler):
        self.cur.execute("""
                SELECT COUNT(*)
                FROM 'GLOBAL'
                WHERE HANDLER = '{0}'
                """.format(handler))
        HandlerCount = self.cur.fetchone()[0]
        return bool(HandlerCount)

    def localDoesExist(self, handler, serverTable):
        self.cur.execute("""
                SELECT COUNT(*)
                FROM '{SID}'
                WHERE HANDLER = '{HANDLER}'
                """.format(SID = serverTable, HANDLER = handler))
        HandlerCount = self.cur.fetchone()[0]
        return bool(HandlerCount)

    def addGlobal(self, handler, reply, replybool, deletebool, deletetime):
        try:
            if deletebool = True:
                deletebool = 1
            else:
                deletebool = 0
                deletetime = 0

            if replybool = True:
                replybool = 1
            else:
                replybool = 0

            if not self.globalDoesExist(handler):
                self.db.table("GLOBAL").insert(handler, reply, replybool, deletebool, deletetime).into("HANDLER", "REPLY", "REPLYBOOL", "DELETEBOOL", "DELETERESPONSE")
                return [True, True]

            else:
                print("GLOBAL HANDLER ALREADY EXISTS")
                print [True, False]
        except:
            print("[DATA] ERROR IMPORTING [{HANDLER}][{REPLY}][{REPLYBOOL}][{DELETEBOOL}][{DELETETIME}] into GLOBAL AUTOREPLIES DATABASE".format(HANDLER = handler, REPLY = reply, REPLYBOOL = replybool, DELETEBOOL = deletebool, DELETETIME = deletetime))
            return [False, False]

    def addLocal(self, serverID, handler, reply, replybool, deletebool, deletetime):

        serverTable = S + serverID

        try:
            if deletebool = True:
                deletebool = 1
            else:
                deletebool = 0
                deletetime = 0

            if replybool = True:
                replybool = 1
            else:
                replybool = 0

            if not super().tableExists(serverTable):
                self.db.table(serverTable).withColumns("HANDLER", "REPLY", "REPLYBOOL", "DELETEBOOL", "DELETETIME").withDataTypes("TEXT PRIMARY KEY NOT NULL", "TEXT", "INT", "INT", "INT").createTable()
                self.db.table(serverTable).insert(serverTable, "Server Autoreplies are Active", "1", "1", "30").into("HANDLER", "REPLY", "REPLYBOOL", "DELETEBOOL", "DELETERESPONSE")

            if not self.localDoesExist(handler, serverTable):
                self.db.table(serverTable).insert(handler, reply, replybool, deletebool, deletetime).into("HANDLER", "REPLY", "REPLYBOOL", "DELETEBOOL", "DELETERESPONSE")
                return [True, True]
            else:
                return [True, False]

        except:
            print("[DATA] ERROR IMPORTING [{HANDLER}][{REPLY}][{REPLYBOOL}][{DELETEBOOL}][{DELETETIME}] into GLOBAL AUTOREPLIES DATABASE".format(HANDLER = handler, REPLY = reply, REPLYBOOL = replybool, DELETEBOOL = deletebool, DELETETIME = deletetime))
            return [False, False]

    def getGlobal(self, handler):
        try:
            if self.globalDoesExist(handler):
                handerData = db.table("GLOBAL").select("HANDLER", "REPLY", "REPLYBOOL", "DELETEBOOL", "DELETETIME").where("HANDLER").equals(handler).execute()

                for entry in handerData:
                    retReply = entry[1]

                    if entry[2] = 1:
                        retReplyBool = True
                    else:
                        retReplyBool = False

                    if entry[3] = 1:
                        retDeleteBool = True
                    else:
                        retDeleteBool = False

                    if entry[3] = 1:
                        retDeleteTime = entry[4]
                    else:
                        retDeleteTime = False

                    return [True, retReply, retReplyBool, retDeleteBool, retDeleteTime]
            else:
                return [False, False, False, False, False]


    def getLocal(self, serverID, handler):

        serverTable = S + serverID

        try:
            if self.localDoesExist(handler, serverTable):
                handerData = db.table(serverTable).select("HANDLER", "REPLY", "REPLYBOOL", "DELETEBOOL", "DELETETIME").where("HANDLER").equals(handler).execute()

                for entry in handerData:
                    retReply = entry[1]

                    if entry[2] = 1:
                        retReplyBool = True
                    else:
                        retReplyBool = False

                    if entry[3] = 1:
                        retDeleteBool = True
                    else:
                        retDeleteBool = False

                    if entry[3] = 1:
                        retDeleteTime = entry[4]
                    else:
                        retDeleteTime = False

                    return [True, retReply, retReplyBool, retDeleteBool, retDeleteTime]

            else:
                return [False, False, False, False, False]
