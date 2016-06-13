all_commands = {}

def command(name):
    def decorate(f):
        if name in all_commands:
            raise Exception("Error with Plugin Import:  Command has been duplicated")

        all_commands[name] = f
        return f
    return decorate

# import plasmaBot.plugins.meta
# import plasmaBot.plugins.moderation
import plasmaBot.plugins.music
# import plasmaBot.plugins.server
