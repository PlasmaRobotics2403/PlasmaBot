from plasmaBot.plugin import PBPlugin, PBPluginMeta, PBPluginConfig, Response
import discord

from plasmaBot import exceptions

from SQLiteHelper import SQLiteHelper as sq

import logging
log = logging.getLogger('discord')


class dbt_custom_commands_server_instance(object):
    def __init__(self):
        self.columns = ["COMMAND_KEY", "RESPONSE"]
        self.datatypes = ["TEXT PRIMARY KEY NOT NULL", "TEXT"]
        self.seed = []


class CustomCommands(PBPlugin):
    name = 'Custom Server Commands'
    globality = 'all'
    help_exclude = False

    def __init__(self, plasmaBot):
        super().__init__(plasmaBot)

        self.pl_config = PBPluginConfig(plasmaBot, 'custom_commands.ini', 'CUSTOM COMMANDS', {'Files':[['commands_db_location', 'The location of the Custom Commands database', 'data/custom_commands']]})

        self.commands_db = sq.Connect(self.pl_config.commands_db_location)
        self.commands_db_connection = self.commands_db.getConn()
        self.commands_db_cursor = self.commands_db_connection.cursor()

    async def cmd_custom(self, message, auth_perms, leftover_args):
        """
        Usage:
            {command_prefix}custom [modifier]

        List Custom Commands.  Moderators: Modify Server's Custom Commands
        """
        if message.server:
            server = message.server
        else:
            return Response('Custom Commands are not enabled in Direct Messages', reply=False, delete_after=120)

        if leftover_args:
            modifier = leftover_args[0]
            del leftover_args[0]
        else:
            modifier = None

        if not modifier:
            if not self.commands_db.table('server_{}'.format(server.id)).tableExists():
                return Response('{} does not have Custom Commands enabled'.format(server.name), reply=False, delete_after=30)
            else:
                commands_response = '**{}\'s Custom Commands:**\n```'.format(server.name)

                commands_return = self.commands_db.table('server_{}'.format(server.id)).select("COMMAND_KEY").execute()

                for custom_command in commands_return:
                    commands_response += ' • ' + self.bot.config.prefix + custom_command[0] + '\n'

                commands_response += '```'

                return Response(commands_response, reply=False, delete_after=60)

        elif modifier == 'add' or modifier == 'create':
            if auth_perms >= 35:
                possible_command_name = leftover_args[0].strip()

                raw_commands_return = self.bot.plugin_db.table('commands').select("PLUGIN_NAME").where("COMMAND_KEY").equals(possible_command_name.lower()).execute()

                does_exist = False

                for command in raw_commands_return:
                    does_exist = True

                if does_exist:
                    return Response('Bot Command `{prefix}{custom_command}` can not be overwriten by a Custom Command!'.format(prefix=self.bot.config.prefix, custom_command=possible_command_name.lower()), reply=True, delete_after=15)

                possible_command_response = message.content[len(self.bot.config.prefix + 'custom {} {} '.format(modifier, leftover_args[0])):].strip()

                if not self.commands_db.table('server_{}'.format(server.id)).tableExists():
                    initiation_glob = dbt_custom_commands_server_instance()
                    self.commands_db.table('server_{}'.format(server.id)).init(initiation_glob)

                raw_custom_commands_return = self.commands_db.table('server_{}'.format(server.id)).select("RESPONSE").where("COMMAND_KEY").equals(possible_command_name.lower()).execute()

                custom_does_exist = False

                for custom_command in raw_custom_commands_return:
                    custom_does_exist = True

                if custom_does_exist:
                    return Response('Custom Command `{prefix}{custom_command}` already exists!  Use `{prefix}custom edit {custom_command} (New_Response)` to modify it.'.format(prefix=self.bot.config.prefix, custom_command=possible_command_name), reply=True, delete_after=30)

                self.commands_db.table('server_{}'.format(server.id)).insert(possible_command_name.lower(), possible_command_response).into("COMMAND_KEY", "RESPONSE")

                return Response('Custom Command `{prefix}{custom_command}` Successfully Created!'.format(prefix=self.bot.config.prefix, custom_command=possible_command_name.lower()), reply=True, delete_after=30)

            else:
                return Response(permissions_error=True)

        elif modifier == 'edit' or modifier == 'update':
            if auth_perms >= 35:
                possible_command_name = leftover_args[0].strip()
                possible_command_response = message.content[len(self.bot.config.prefix + 'custom {} {} '.format(modifier, leftover_args[0])):].strip()

                if not self.commands_db.table('server_{}'.format(server.id)).tableExists():
                    return Response('{} does not have Custom Commands enabled.  Use `{}custom add {} (content)` to create this command'.format(server.name, self.bot.config.prefix, possible_command_name.lower()), reply=True, delete_after=30)

                raw_custom_commands_return = self.commands_db.table('server_{}'.format(server.id)).select("RESPONSE").where("COMMAND_KEY").equals(possible_command_name.lower()).execute()

                custom_does_exist = False

                for custom_command in raw_custom_commands_return:
                    custom_does_exist = True

                if custom_does_exist:

                    if possible_command_response == '':
                        return Response('Custom Command `{prefix}{command}` can not have an empty response.  Use `{prefix}custom edit {command} (content)` to edit this command'.format(prefix=self.bot.config.prefix, command=possible_command_name.lower()), reply=True, delete_after=30)

                    self.commands_db.table('server_{}'.format(server.id)).update("RESPONSE").setTo(possible_command_response).where("COMMAND_KEY").equals(possible_command_name.lower()).execute()
                    return Response('Response for `{prefix}{command}` updated!'.format(prefix=self.bot.config.prefix, command=possible_command_name.lower()), reply=True, delete_after=30)
                else:
                    return Response('Custom Command `{prefix}{command}` does not exist.  Use `{prefix}custom add {command} (content)` to create this command'.format(prefix=self.bot.config.prefix, command=possible_command_name.lower()), reply=True, delete_after=30)
            else:
                return Response(permissions_error=True)

        elif modifier == 'remove' or modifier == 'delete':
            if auth_perms >= 35:
                possible_command_name = leftover_args[0].strip()

                if not self.commands_db.table('server_{}'.format(server.id)).tableExists():
                    return Response('{} does not have Custom Commands enabled.'.format(server.name), reply=True, delete_after=30)

                raw_custom_commands_return = self.commands_db.table('server_{}'.format(server.id)).select("RESPONSE").where("COMMAND_KEY").equals(possible_command_name).execute()

                custom_does_exist = False

                for custom_command in raw_custom_commands_return:
                    custom_does_exist = True

                if not custom_does_exist:
                    return Response('Custom Command `{prefix}{command}` does not exist.'.format(prefix=self.bot.config.prefix, command=possible_command_name), reply=True, delete_after=30)

                all_custom_commands_return = self.commands_db.table('server_{}'.format(server.id)).select("COMMAND_KEY").execute()

                custom_commands_list = []

                for custom_command_all in all_custom_commands_return:
                    custom_commands_list += [custom_command[0]]

                if len(custom_commands_list) == 1:
                    self.commands_db_cursor.execute('DROP TABLE IF EXISTS server_{}'.format(server.id))
                    self.commands_db_connection.commit()
                    return Response('Custom Command `{prefix}{command}` has been removed and Custom Commands have been disabled.'.format(prefix=self.bot.config.prefix, command=possible_command_name), reply=True, delete_after=30)

                else:
                    self.commands_db.table('server_{}'.format(server.id)).delete().where("COMMAND_KEY").equals(possible_command_name).execute()
                return Response('Custom Command `{prefix}{command}` has been removed.'.format(prefix=self.bot.config.prefix, command=possible_command_name), reply=True, delete_after=30)
            else:
                return Response(permissions_error=True)

        else:
            return Response(send_help=True, help_message='Unrecognized Modifier \'{}\''.format(modifier))

    async def on_message(self, message, message_type, message_context):
        if not message.author.bot:
            if message.server and message.content.strip().startswith(self.bot.config.prefix):
                command, *args = message.content.strip().split()
                command = command[len(self.bot.config.prefix):].lower().strip()

                if self.commands_db.table('server_{}'.format(message.server.id)).tableExists():
                    custom_commands_return = self.commands_db.table('server_{}'.format(message.server.id)).select("RESPONSE").where("COMMAND_KEY").equals(command).execute()

                    custom_does_exist = False
                    custom_message = ''

                    for custom_command in custom_commands_return:
                        custom_does_exist = True
                        custom_message = custom_command[0]

                    if custom_does_exist:
                        try:
                            response = custom_message.format(args=args)
                        except IndexError:
                            if '{args[9]}' in custom_message:
                                arg_num = '10'
                            elif '{args[8]}' in custom_message:
                                arg_num = '9'
                            elif '{args[7]}' in custom_message:
                                arg_num = '8'
                            elif '{args[6]}' in custom_message:
                                arg_num = '7'
                            elif '{args[5]}' in custom_message:
                                arg_num = '6'
                            elif '{args[4]}' in custom_message:
                                arg_num = '5'
                            elif '{args[3]}' in custom_message:
                                arg_num = '4'
                            elif '{args[2]}' in custom_message:
                                arg_num = '3'
                            elif '{args[1]}' in custom_message:
                                arg_num = '2'
                            elif '{args[0]}' in custom_message:
                                arg_num = '1'
                            else:
                                arg_num = '11+'
                            response = '{} extra arguments required for Custom Command `{}{}`'.format(arg_num, self.bot.config.prefix, command)
                        await self.bot.safe_send_message(message.channel, response, expire_in=30)
                    else:
                        pass
            else:
                pass #Channel is a DM, where Custom Commands are not supported / Enabled.  Either that or the message just doesn't start with the command prefix
        else:
            pass #Custom Commands will not respond to bot users because of potential for automated custom-command spam sequences.
