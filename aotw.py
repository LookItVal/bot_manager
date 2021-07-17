import frame

import os

import spotipy
from discord.ext import commands
from dotenv import load_dotenv

TOKEN = os.getenv('DISCORD_TOKEN')


class AOTWBot(frame.Bot):
    TOKEN = os.getenv('DISCORD_TOKEN')

    def __init__(self):
        super().__init__()

        @self.discord_bot.command(  # ToDo Give a more exact description of what the raffle is here
            help='Give a spotify album url or uri to set as your raffle for the next Album of the Week.',
            brief='Sets your albums raffle'
        )
        async def set_raffle(ctx, args):
            await self.set_raffle(ctx, args)

    async def set_raffle(self, ctx, args):
        try:
            album = frame.Album(args)
        except:
            await ctx.send('Invalid Album Link')
            return
        user = User(ctx.author.id)
        await ctx.send(user.name)


# discord
class User(frame.User):
    def __init__(self, user):
        super().__init__(user)
