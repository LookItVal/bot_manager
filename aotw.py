import aotw
import frame

import os
from uuid import uuid4

import discord


class AOTWBot(frame.Bot):
    TOKEN = os.getenv('DISCORD_TOKEN')

    def __init__(self) -> None:
        super().__init__()

        @self.discord_bot.command(  # ToDo Give a more exact description of what the raffle is here
            help='Give a spotify album url or uri to set as your raffle for the next Album of the Week.',
            brief='Sets your albums raffle'
        )
        async def set_raffle(ctx, args):
            await self.set_raffle(ctx, args)
            print(type(ctx))
            # await self.uuid4_collision(ctx)

    async def uuid4_collision(self, ctx) -> None:
        await ctx.send('@everyone THE IMPOSSIBLE HAS HAPPENED!')
        # await ctx.send('THE IMPOSSIBLE HAS HAPPENED!')
        await ctx.send('<@!' + str(ctx.author.id) + '> Generated a DUPLICATE ID based on pythons UUID4!')
        await ctx.send('The number of random version-4 UUIDs which need to be generated in order to have a 50%' +
                       ' probability of at least one collision is 2.71 QUINTILLION.')
        await ctx.send('This number is equivalent to generating 1 billion UUIDs per second for about 85 years.')
        await ctx.send('The probability to find a duplicate within 103 trillion version-4 UUIDs is one in a billion.')
        embed = discord.Embed(description='[Universally Uniquie Identifier](https://en.wikipedia.org/wiki/Universally' +
                                          '_unique_identifier#:~:text=This%20number%20is%20equivalent%20to,would%20be' +
                                          '%20about%2045%20exabytes.&text=Thus%2C%20the%20probability%20to%20find,is%' +
                                          '20one%20in%20a%20billion.)')
        await ctx.send(embed=embed)
        print('uuid4 Duplicate detected, and regenerated.')
        coda = frame.Meta()
        coda.uuid4_duplicate = False

    async def set_raffle(self, ctx, args: str) -> None:
        try:
            album = Album(args)
        except:
            await ctx.send('Invalid Album Link')
            return
        user = User(ctx.author)
        user.raffle = album
        await ctx.send('Raffle Set.')
        coda = frame.Meta()
        if coda.uuid4_duplicate:
            await self.uuid4_collision(ctx)


# Spotify
class RaffleDict(dict):
    def __getitem__(self, key):
        return User(super().__getitem__(key))


class Album(frame.Album):
    def __init__(self, uri) -> None:
        super().__init__(uri)
        if 'raffles' in self.data:
            self.raffles = self.data.pop('raffles')
        else:
            self.raffles = {}


# Discord
class User(frame.User):
    def __init__(self, user) -> None:
        super().__init__(user)
        if 'raffle' in self.data:
            self._raffle = self.data.pop('raffle')
        else:
            self.raffle = None

    @property
    def raffle(self):  # ToDo cant add type hints here
        if self._raffle:
            return Raffle(uri=self._raffle)
        else:
            return None

    @raffle.setter
    def raffle(self, album: str or frame.Album) -> None:
        if hasattr(self, '_raffle'):
            if album:
                if isinstance(album, str):
                    album = Album(album)
                self.raffle.album = album
            else:
                self.raffle.album = None
        else:
            if album:
                if isinstance(album, str):
                    album = Album(album)
                raffle = {
                    'user': self,
                    'album': album,
                }
                raffle = Raffle(data=raffle)
                self._raffle = raffle.uri
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
            self.user:  str = data.pop('user')
            self.album: str = data.pop('album')
            self.data: dict = data
            self.save()

    @property
    def user(self) -> User:
        return User(self._user)

    @user.setter
    def user(self, value: str or frame.User) -> None:
        if isinstance(value, frame.User):
            self._user = value.uri
        elif isinstance(value, str):
            self._user = value
        else:
            raise TypeError('User must be string uri, frame.User, or its subclasses.')

    @property
    def album(self) -> Album:
        return Album(self._album)

    @album.setter
    def album(self, value: str or frame.Album) -> None:
        save = False
        if hasattr(self, '_album'):
            album = self.album
            del album.raffles[self.uri]
            album.save()
            save = True
        if isinstance(value, frame.Album):
            self._album = value.uri
        elif isinstance(value, str):
            if 'https://' in value:
                value = frame.url_to_uri(value)
            self._album = value
        else:
            raise TypeError('Album must be string uri or url, or an instance of frame.Album or its subclasses.')
        album = self.album
        album.raffles[self.uri] = self._user
        album.save()
        if save:
            self.save()

    def gen_id(self) -> str:
        coda = frame.Meta()
        return self.gen_id_rec(coda)

    def gen_id_rec(self, coda: frame.Meta) -> str:
        uuid = uuid4().hex
        if uuid in coda.id_list:
            print('MOTHER FUCKER WE GOT A DUPLICATE ON UUID4')
            print('GENERATING NEW ID')
            coda.uuid4_duplicate = True
            uuid = self.gen_id_rec(coda)
        coda.append_id(uuid)
        return uuid


class Review: # ToDo
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
