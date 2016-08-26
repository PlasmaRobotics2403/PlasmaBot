class dbt_plugins(object):
    def __init__(self):
        self.columns = ["PLUGIN_NAME", "FANCY_NAME", "GLOBALITY", "SPECIAL_SERVERS", "PLUGIN_HELP_EXCLUDE"]
        self.datatypes = ["TEXT PRIMARY KEY NOT NULL", "TEXT", "TEXT", "TEXT", "TEXT"]
        self.seed = []

class dbt_commands(object):
    def __init__(self):
        self.columns = ["COMMAND_KEY", "PLUGIN_NAME", "COMMAND_USAGE", "COMMAND_DESCRIPTION", "HELP_EXCLUDE"]
        self.datatypes = ["TEXT PRIMARY KEY NOT NULL", "TEXT", "TEXT", "TEXT", "TEXT"]
        self.seed = [["shutdown", "BASE", "{command_prefix}shutdown", "Shutdown Bot", "YES"],
                     ["restart", "BASE", "{command_prefix}restart", "Restart Bot", "YES"]]

class dbt_toggles(object):
    def __init__(self):
        self.columns = ["TOGGLE_NAME", "PLUGIN_NAME"]
        self.datatypes = ["TEXT PRIMARY KEY NOT NULL", "TEXT"]
        self.seed = []

class dbt_server(object):
    def __init__(self):
        self.columns = ["SERVER_ID"]
        self.datatypes = ["TEXT PRIMARY KEY NOT NULL"]
        self.seed = []

class dbt_glob_perms(object):
    def __init__(self):
        self.columns = ["USER_ID", "PERMISSIONS_LEVEL"]
        self.datatypes = ["TEXT PRIMARY KEY NOT NULL", "TEXT"]
        self.seed = [["180094452860321793", "100"]]

class dbt_server_perms(object):
    def __init__(self):
        self.columns = ["SERVER_ID", "OWNER_ID", "ADMINISTRATOR_ROLE_ID", "MODERATOR_ROLE_ID", "HELPER_ROLE_ID", "BLACKLISTED_ROLE_ID"]
        self.datatypes = ["TEXT PRIMARY KEY NOT NULL", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT"]
        self.seed = []
