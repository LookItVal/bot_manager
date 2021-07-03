import os

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
COMMAND_PREFIX = os.getenv('AOTW_COMMAND')


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=COMMAND_PREFIX)

    @super().event
    async def on_ready():
        print('Discord Bot Ready')

    @super().command()
    async def ping(self, ctx):
        await ctx.channel.send('pong')