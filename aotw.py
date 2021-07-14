import bot_frame

import os

import spotipy
from discord.ext import commands
from dotenv import load_dotenv

TOKEN = os.getenv('DISCORD_TOKEN')


class AOTWBot(bot_frame.Bot):
    TOKEN = os.getenv('DISCORD_TOKEN')

    def __init__(self):
        super().__init__()

        @super().command(  # ToDo Give a more exact description of what the raffle is here
            help='Give a spotify album url or uri to set as your raffle for the next Album of the Week.',
            brief='Sets your albums raffle'
        )
        async def set_raffle(ctx, args):
            try:
                album = bot_frame.Album(args)
            except:
                await ctx.send('Invalid Album Link')
                return
            user = User(ctx.author.id)
            await ctx.send(user.name)

    def run(self):
        super().run(self.TOKEN)


# discord
class User(bot_frame.User):
    def __init__(self, user):
        super().__init__(user)
