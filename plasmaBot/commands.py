import uuid
import inspect
from discord.ext import commands

class TerminalContext:
    """Custom Terminal Context"""
    def __init__(self, bot, message, *, prefix=None, command=None, args=None, raw_args=None, channel=None):
        self.bot = bot
        self.message = message
        self.prefix = prefix
        self.command = command
        self.args = args
        self.raw_args = raw_args
        self.channel = channel

class TerminalCommand:
    """Custom Terminal Command"""
    def __init__(self, callback, *, name=None, usage=None, description=None, aliases=None):
        self.callback = callback
        self.uuid = uuid.uuid4() if not hasattr(callback, 'terminal_command_id') else callback.terminal_command_id
        self.name = name if name else callback.__name__
        self.usage = inspect.cleandoc(usage) if usage else ''
        self.description = inspect.cleandoc(description) if description else inspect.cleandoc(callback.__doc__) if callback.__doc__ else ''
        self.aliases = aliases if aliases else []
    
    def get_uuid(self):
        """Returns the UUID of the command"""
        return self.uuid

    def get_args(self):
        """Returns the number of arguments the command requires"""
        return list(inspect.signature(self.callback).parameters)
    
    def get_arg_default(self, arg_name):
        """Returns the default value of the specified argument if it exists"""
        # Get the signature of the callback function
        signature = inspect.signature(self.callback)
        # Get the parameters from the signature
        parameters = signature.parameters
        # Check if the argument name is in the parameters
        if arg_name in parameters:
            # Get the parameter
            parameter = parameters[arg_name]
            # Check if it has a default value
            if parameter.default is not inspect.Parameter.empty:
                # Return the default value
                return parameter.default
        # Return inspect.Parameter.empty if there's no default value
        return inspect.Parameter.empty

    def get_name(self):
        """Returns the name of the command"""
        return self.name

    def get_description(self):
        """Returns the description of the command""" 
        return self.description
    
    def get_usage(self):
        """Returns the usage of the command"""
        return self.usage

    def get_aliases(self):
        """Returns the aliases of the command"""
        return self.aliases

    async def __call__(self, *args, **kwargs):
        """Calls the command callback with the given context and arguments"""
        return await self.callback(*args, **kwargs)
    
class ChatCommandMixin:
    """Mixin for Chat Commands"""
    pass


class ChatCommand(commands.HybridCommand, ChatCommandMixin):
    """Represents a Command accessible through Discord Chat"""
    pass


class ChatGroup(commands.HybridGroup, ChatCommandMixin):
    """Represents a Group of Commands accessible through Discord Chat"""
    pass


def chat_command(**kwargs):
    """Decorator for creating a chat command"""
    kwargs.setdefault('cls', ChatCommand)
    return commands.command(**kwargs)


def chat_group(**kwargs):
    """Decorator for creating a chat group"""
    kwargs.setdefault('cls', ChatGroup)
    return commands.group(**kwargs)