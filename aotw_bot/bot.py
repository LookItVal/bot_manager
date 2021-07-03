import os

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
COMMAND_PREFIX = os.getenv('AOTW_COMMAND')


class Bot:  # ToDo
    def __init__(self):
        self.discord_bot = commands.Bot(command_prefix=COMMAND_PREFIX)

        @self.discord_bot.event
        async def on_ready():
            print('Discord Bot Ready')

        @self.discord_bot.command()
        async def ping(ctx):
            await ctx.channel.send('dong')

        @self.discord_bot.command()
        async def set_raffle(ctx, arg):  # is this the propper naming convention?
            if 'artist' in arg:
                await ctx.channel.send('TYPE ERROR: Expected type Album, received type Artist')
                return
            if 'track' in arg:
                await ctx.channel.send('TYPE ERROR: Expected type Album, received type Track')
                return

    def run(self):
        self.discord_bot.run(TOKEN)
