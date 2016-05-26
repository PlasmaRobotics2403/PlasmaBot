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


    def createTable(self, table_name): # Need to work on before adding to bot.py
        c.execute('CREATE TABLE {tn} ({nf} {ft})'\
                .format(tn=table_name1, nf=new_field, ft=field_type))


    def __del__(self):
        self.connection.close()


