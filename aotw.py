import frame

import os
import random
from uuid import uuid4

import discord
import schedule


class AOTWBot(frame.Bot):
    TOKEN = os.getenv('DISCORD_TOKEN')

    def __init__(self) -> None:
        super().__init__()
        self.metadata = Meta()

        @self.discord_bot.command(  # ToDo Give a more exact description of what the raffle is here
            help='Give a spotify album url or uri to set as your raffle for the next Album of the Week.',
            brief='Sets your album raffle'
        )
        async def raffle(ctx, args):
            await self.raffle(ctx, args)

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
        metadata = Meta()
        metadata.uuid4_duplicate = False

    async def raffle(self, ctx, args: str) -> None:
        try:
            album = Album(args)
        except:
            await ctx.send('Invalid Album Link')
            return
        user = User(ctx.author)
        category = frame.Category(ctx.channel.category)
        user.raffle = {category.uri: album}
        await ctx.send('Raffle Set.')
        metadata = Meta()
        if metadata.uuid4_duplicate:
            await self.uuid4_collision(ctx)

    async def pick_raffle(self, category: uri) -> None:
        self.clear_aotw()
        aotw = None
        raffle_list = self.metadata.raffle_list
        while aotw is None:
            if not raffle_list:
                print('All Raffles Empty')
                break
            raffle = random.choice(raffle_list)
            raffle_list.remove(raffle)
            raffle = Raffle(raffle)
            aotw = raffle.album
        self.metadata.aotw = aotw
        if aotw:
            pass
            # Notify Raffle Change in async method here

    def clear_aotw(self) -> None:
        aotw = self.metadata.aotw
        if aotw is None:
            return
        if aotw:
            for user in aotw.raffles:
                user.raffle = None


# Spotify
class AlbumDict(dict):
    def __getitem__(self, key):
        return User(super().__getitem__(key))


class Album(frame.Album):
    def __init__(self, uri) -> None:
        super().__init__(uri)
        if 'raffles' in self.data:
            self.raffles = self.data.pop('raffles')
            for key, value in self.raffles.items():
                self.raffles[key] = RaffleDict(value)
        else:
            self.raffles = {}


# Discord
class UserDict(dict):
    def __getitem__(self, key):
        return User(super().__getitem__(key))


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
            return Raffle(self._raffle)
        else:
            return None

    @raffle.setter
    def raffle(self, album: None or dict) -> None:
        if not album:
            return
        key = next(iter(album.keys()))
        if not hasattr(self, '_raffle'):
            raffle = {
                'user': self,
                'album': None
            }
            raffle = Raffle(data=raffle)
            self._raffle = raffle.uri
        if isinstance(album[key], str):
            album = Album(album[key])
        self.raffle[key] = album[key]
        self.save()

    @property
    def raffles(self):  # ToDo cant add type hints here
        if self._raffle:
            return Raffle(self._raffle).albums
        else:
            return None

    @raffles.setter
    def raffles(self, album: dict) -> None:
        raise KeyError('If you want this to work you gotta build it yourself.')


# aotw
class Meta(frame.Meta):
    def __init__(self) -> None:
        uri = 'aotw:metadata'
        super().__init__(uri)
        if 'aotw' in self.data:
            self.aotw = self.data.pop('aotw')
        else:
            self.aotw = None

    @property
    def aotw(self) -> Album or None:
        if self._aotw:
            return Album(self._aotw)
        else:
            return None

    @aotw.setter
    def aotw(self, album: str or frame.Album) -> None:
        if isinstance(album, frame.Album):
            album = album.uri
        self._aotw = album
        self.save()

    @property
    def raffle_list(self):
        directories = os.listdir(os.path.join(os.getcwd(), r'data/'))
        raffles = []
        for dir in directories:
            if 'aotw:raffle:' in dir:
                raffles.append(dir)
        return raffles


class RaffleDict(dict):
    def __init__(self, val: None or dict):
        val = val or {}
        super().__init__(val)

    def __getitem__(self, key):
        return Album(super().__getitem__(key))


class Raffle(frame.Data):
    def __init__(self, uri: str = None, data: dict = None) -> None:
        if uri:
            super().__init__(uri)
            self.user:          str = self.data.pop('user')
            self._album: RaffleDict = RaffleDict(self.data.pop('album'))
            self.id:            str = self.data.pop('id')
        if data:
            self.id:            str = self.gen_id()
            self.uri:           str = 'aotw:raffle:' + self.id
            super().__init__(self.uri)
            self.user:          str = data.pop('user')
            self._album: RaffleDict = RaffleDict(data.pop('album'))
            self.data:         dict = data
            self.save()

    def __getitem__(self, key: str) -> Album:
        return self._album[key]

    def __setitem__(self, key: str or frame.Category, value: str or frame.Album) -> None:
        # key = category.uri
        if isinstance(key, frame.Category):
            key = key.uri
        # value = album.uri
        if isinstance(value, frame.Album):
            value = value.uri
        if 'https://' in value:
            value = frame.url_to_uri(value)
        if key in self._album:
            album: Album = self._album[key]
            del album.raffles[key][self.uri]
            album.save()
        self._album[key] = value
        album = self[key]
        if not hasattr(album.raffles, key):
            album.raffles[key] = {}
        album.raffles[key][self.uri] = self._user
        album.save()
        self.save()

    @property
    def albums(self) -> dict:
        return self._album

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

    def gen_id(self) -> str:
        metadata = Meta()
        return self.gen_id_rec(metadata)

    def gen_id_rec(self, metadata: frame.Meta) -> str:
        uuid = uuid4().hex
        if uuid in metadata.id_list:
            print('MOTHER FUCKER WE GOT A DUPLICATE ON UUID4')
            print('GENERATING NEW ID')
            metadata.uuid4_duplicate = True
            uuid = self.gen_id_rec(metadata)
        metadata.append_id(uuid)
        return uuid


class Review:  # ToDo
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
