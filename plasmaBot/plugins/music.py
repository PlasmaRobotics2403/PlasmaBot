import shlex
import traceback
import asyncio
import discord

from collections import defaultdict
from io import BytesIO
from textwrap import dedent

from plasmaBot.plugins import command
from plasmaBot.structures import Response
from plasmaBot.playlist import Playlist
from plasmaBot.player import MusicPlayer
from plasmaBot.config import Config, ConfigDefaults
from plasmaBot.permissions import Permissions, PermissionsDefaults
from plasmaBot.utils import load_file, write_file, sane_round_int
from plasmaBot.exceptions import PlasmaBotException, CommandError, ExtractionError, WrongEntryTypeError, PermissionsError, HelpfulError

@command("test1234")
async def cmd_id(self, author, user_mentions):
    """
    Usage:
        {command_prefix}id [@user]
    Tells the user their id or the id of another user.
    """
    if not user_mentions:
        return Response('your id is `%s`' % author.id, reply=True, delete_after=35)
    else:
        usr = user_mentions[0]
        return Response("%s's id is `%s`" % (usr.name, usr.id), reply=True, delete_after=35)
