import frame

import os
from uuid import uuid4

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
        except commands.errors.MissingRequiredArgument:
            await ctx.send('Missing Argument: Please send a link to the album you would like to set as your raffle')
            return
        except:
            await ctx.send('Invalid Album Link')
            return
        user = User(ctx.author)
        await ctx.send(user.name)
        await ctx.send(album.name)
        user.save()
        album.save()
        #TODO SOMEWHER IN HERE WE NEED TO CHECK frame.Meta.uuid4_duplicate TO SEE IF THERE IS ANY DUPLICATES


# Spotify
class Album(frame.Album):
    def __init__(self, uri):
        super().__init__(uri)
        try:
            self.raffle = self.data.pop('raffle')
        except KeyError:
            self.raffle = None  # Todo something here im not really sure tbh


# Discord
class User(frame.User):
    def __init__(self, user):
        super().__init__(user)
        try:
            self.raffle = self.data.pop('raffle')
        except KeyError:
            self.raffle = None

    @property
    def raffle(self):
        if self._raffle:
            return Raffle(self._raffle)
        else:
            return None

    @raffle.setter
    def raffle(self, album):
        if album:
            if isinstance(album, str):
                album = Album(album)
                raffle = {
                    'user' : self,
                    'album': album,
                }
                raffle = Raffle(raffle)
                self._raffle = raffle.uri
            if isinstance(album, Album):
                raffle = {
                    'user' : self,
                    'album': album,
                }
                raffle = Raffle(raffle)
                self._raffle = raffle.uri
        else:
            self._raffle = None
        self.save()


# aotw
class Raffle(frame.Data):
    def __init__(self, uri: str = None, data: dict = None) -> None:
        if uri:
            super().__init__(uri)
            self.user:  str = self.data.pop('user')
            self.album: str = self.data.pop('album')
            self.id:    str = self.data.pop('id')
        if data:
            self.id:    str = self.gen_id()
            self.uri:   str = 'aotw:raffle:' + self.id
            super().__init__(self.uri)
            self.user:  str = data['user']
            self.album: str = data['album']
            self.data: dict = {}
            self.save()

    def __setattr__(self, key, value):
        if key == 'album':
            album = Album(self.album)
            del album.raffle[self.uri]
            album = Album(value)
            album.raffle[self.uri] = self.user

# TODO add raffle to the album class

    def gen_id(self) -> str:
        coda = frame.Meta()
        return self.gen_id_rec(coda)

    def gen_id_rec(self, coda: frame.Meta):
        uuid = uuid4().hex
        if uuid in coda.id_list:
            print('MOTHER FUCKER WE GOT A DUPLICATE ON UUID4')
            print('GENERATING NEW ID')
            uuid = self.gen_id_rec(coda)
        coda.id_list.append(uuid)
        return uuid


class Review:
    def __init__(self, uri):
        pass


def is_album_url(url):
    if 'https://open.spotify.com/album/' in url:
        return True
    else:
        return False

def is_album_uri(uri):
    if 'spotify:album:' in uri:
        return True
    else:
        return False