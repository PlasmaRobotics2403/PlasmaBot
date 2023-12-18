import peewee

database = None

def setup_database(host:str,port:str,user:str,password:str,db:str):
    global database
    database = peewee.MySQLDatabase(
        host=host,
        port=port,
        user=user,
        password=password,
        database=db,
        charset='utf8mb4'
    )

    class BaseModel(peewee.Model):
        class Meta:
            database = database

    database.base_model = BaseModel

    database.connect()

    return database