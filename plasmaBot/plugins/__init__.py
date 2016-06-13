import os

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
# import plasmaBot.plugins.music
# import plasmaBot.plugins.server

for name in os.listdir("plasmaBot.plugins"):
    if name.endswith(".py"):
          #strip the extension
         module = name[:-3]
         # set the module name in the current global name space:
         globals()[module] = __import__(os.path.join("plugins", name)
