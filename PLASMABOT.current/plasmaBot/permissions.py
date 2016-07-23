import os
import sys
import asyncio
import discord
import traceback

from . import exceptions

from plasmaBot.defaults.database_tables import dbt_glob_perms, dbt_server_perms

from SQLiteHelper import SQLiteHelper as sq

class Permissions:
    def __init__(self, perm_db_path, plasmaBot):
        self.perm_db = sq.Connect(perm_db_path)

        if not self.perm_db.table('global').tableExists():
            initiation_glob = dbt_glob_perms()
            self.perm_db.table('global').init(initiation_glob)
        if not self.perm_db.table('servers').tableExists():
            initiation_serv = dbt_server_perms()
            self.perm_db.table('servers').init(initiation_serv)

        self.bot = plasmaBot

    #def set_server_permissions(self, server, admin_role_id, mod_role_id, helper_role_id, black_role_id):
    #    current_server_return = self.perm_db.table('servers').select("OWNER_ID", "ADMINISTRATOR_ROLE_ID", "MODERATOR_ROLE_ID", "HELPER_ROLE_ID").where("SERVER_ID").equals(server.id).execute()
    #    if len(current_server_return.fetchall()) >= 1:
    #        if current_server_return.fetchall()[0][0] == server.id:
    #    else:

    async def check_permissions(self, user, channel, server=None):
        # 0 = Blacklisted
        # 5 = Standard User / No Server Features Enabled
        # 10 = Standard User
        # 25 = Server's Helper Role
        # 35 = Server's Moderator Role
        # 45 = Server's Administrator Role
        # 50 = Server Owner & Adminstrator Permission Holders
        # 100 = Bot Owner
        permission_level = 0

        user_glob_permissions_return = self.perm_db.table('global').select('PERMISSIONS_LEVEL').where("USER_ID").equals(user.id).execute()

        for row in user_glob_permissions_return:
            permission_level = min(int(row[0]), 100)
            return permission_level

        if user.id == self.bot.config.owner_id or user.id == self.bot.config.debug_id:
            permission_level = 100
            return permission_level

        if server:
            server_permissions_return = self.perm_db.table('servers').select("OWNER_ID", "ADMINISTRATOR_ROLE_ID", "MODERATOR_ROLE_ID", "HELPER_ROLE_ID").where("SERVER_ID").equals(server.id).execute()

            s_owner = ''
            s_admin = ''
            s_moderator = ''
            s_helper = ''
            s_blacklist = ''

            for row in server_permissions_return:
                s_owner = row[0]
                s_admin = row[1]
                s_moderator = row[2]
                s_helper = row[3]
                s_blacklist = row[4]

            if s_owner == '':
                await self.bot.safe_send_message(server.owner, '{}, you should probably set up permissions roles for your server _**{}**_'.format(server.owner.name, server.name))
                return

            if user.id == s_owner:
                permission_level = 50
                return permission_level

            if user.permissions_for(channel).administrator:
                permission_level = 50
                return permission_level

            for role in user.roles:
                if role.id == s_admin:
                    permission_level = 45
                    return permission_level
                if role.id == s_moderator:
                    permission_level = 35
                    return permission_level
                if role.id == s_helper:
                    permission_level = 25
                    return permission_level
                if role.id == s_blacklist:
                    permission_level = 0
                    return permission_level

            permission_level = 10
            return permission_level

        else:
            permission_level = 5
            return permission_level
