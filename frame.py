import os
import json
import inspect
from types import FunctionType, CoroutineType
from functools import wraps
from math import e
from decimal import *

import discord
import spotipy
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
auth_manager = spotipy.oauth2.SpotifyClientCredentials()
sp = spotipy.Spotify(auth_manager=auth_manager)

COMMAND_PREFIX = os.getenv('COMMAND_PREFIX')


def log(method: FunctionType or CoroutineType) -> FunctionType or CoroutineType:
    if inspect.iscoroutinefunction(method):
        print('logging coroutine method: ' + method.__name__)

        @wraps(method)
        async def logged(*args, **kwargs):
            print()
            if isinstance(args[1], discord.ext.commands.context.Context):
                ctx = args[1]
                print(ctx.author.name + '#' + ctx.author.discriminator + ' invoked the following command:')
                print(ctx.message.content)
            print('Triggering: ' + method.__name__)
            if isinstance(args[1], Category):
                print('In Category: ' + args[1].name)
            return await method(*args, **kwargs)
    else:
        print('logging method: ' + method.__name__)

        @wraps(method)
        def logged(*args, **kwargs):
            print()
            print(method.__name__ + ' called')
            return method(*args, **kwargs)
    return logged


class Bot:
    TOKEN = None
    CHANNEL_KEY = None

    def __new__(cls) -> object:  # i have no idea if this is the correct type but pycharm doesnt seem to care
        for name, method in inspect.getmembers(cls, inspect.isfunction):
            if name[:1] == '_':
                continue
            setattr(cls, name, log(method))
        return super(Bot, cls).__new__(cls)

    def __init__(self) -> None:
        self.discord_bot = commands.Bot(command_prefix=COMMAND_PREFIX)

        @self.discord_bot.event
        async def on_ready():
            print()
            print('Discord Bot Ready')

        @self.discord_bot.command(
            help="Returns pong if bot is properly connected to the server.",
            brief="Prints pong back to the channel."
        )
        async def ping(ctx):
            await self.ping(ctx)

    def __call__(self) -> None:
        self.run()

    async def ping(self, ctx) -> None:
        await ctx.send('pong')

    def channel(self, category: str or Category) -> discord.TextChannel:
        if isinstance(category, str):
            category = Category(category)
        channel_id = None
        if category.name == 'Dev Corner':
            channel_id = category.channels['bot-test-zone']
        else:
            channel_id = category.channels[self.CHANNEL_KEY]
        return self.discord_bot.get_channel(channel_id)

    def run(self) -> None:
        self.discord_bot.run(self.TOKEN)


class Data:
    def __init__(self, uri: str) -> None:
        self.data:     dict = None
        self.uri:       str = uri
        self.directory: str = os.path.join(os.getcwd(), r'data/' + uri)
        if os.path.isdir(self.directory):
            self.data: dict = self.load()
            self.uri:   str = self.data.pop('uri')  # feels redundant but is needed to remove the uri from self.data

    def __call__(self) -> dict:
        data = self.__dict__ | self.data  # cause you can just do this ig
        del data['data']
        del data['directory']
        final = {}
        for key in data.keys():
            if key[0] == '_':
                final[key[1:]] = data[key]
            else:
                final[key] = data[key]
        return final

    def save(self) -> None:
        if not os.path.isdir(self.directory):
            os.mkdir(self.directory)
        with open(self.directory + '/.json', 'w') as file:
            file.write(json.dumps(self(), sort_keys=True, indent=4))

    def load(self) -> dict:
        with open(self.directory + '/.json', 'r') as file:
            return json.loads(file.read())


# Spotify
class Artist:
    def __init__(self, link, data: dict = None) -> None:
        if data:
            self.uri:             str = data['uri']
            self.name:            str = data['name']
            self.genre:          list = data['genre']
            self.rated_releases: list = data['rated_releases']
            self.total_releases: list = data['total_releases']
        else:
            spotify_info = sp.artist(link)
            self.uri:             str = spotify_info['uri']
            self.name:            str = spotify_info['name']
            self.genre:          list = spotify_info['genre']
            self.rated_releases: list = []
            self.total_releases: list = self.releases

    @property
    def releases(self) -> list:
        releases = sp.artist_albums(self.uri)
        uris = []
        for release in releases:
            uris.append(release['uri'])
        return uris

    @classmethod
    def get_artist(cls, link):
        print('non functional')
'''seach for loaded copy
        load copy
            new thread with refreshing release
            give artist
        no copy
            run init'''


class Album(Data):
    def __init__(self, uri: str) -> None:
        if 'https://' in uri:
            uri = url_to_uri(uri)
        super().__init__(uri)
        if self.data:
            self.name:     str = self.data.pop('name')
            self.artists: list = self.data.pop('artists')
            self.tracks:  list = self.data.pop('tracks')
        else:
            spotify_info: dict = sp.album(uri)
            self.name:     str = spotify_info['name']
            self.artists: list = spotify_info['artists']
            for i, artist in enumerate(self.artists):
                self.artists[i]: str = artist['uri']
            self.tracks:  list = spotify_info['tracks']
            tracks = []
            for track in self.tracks['items']:
                tracks.append(track['uri'])
            self.tracks:  list = tracks
            self.data:    dict = {}
    # ToDo download image file of the album art and save to file


class Track:  # ToDo
    def __init__(self, link) -> None:  # ToDo
        self.link = link
        self.name = None
        self.artist = None
        self.album = None


# Discord
class User(Data):  # ToDo
    def __init__(self, user: str or int or discord.User) -> None:
        if isinstance(user, str):
            super().__init__(user)
            if self.data:
                self.id: str = self.data.pop('id')
                self.name: str = self.data.pop('name')
                self.discriminator: str = self.data.pop('discriminator')
                self.bot: bool = self.data.pop('bot')
            else:
                raise TypeError('Given id as User attribute with no user on file')
        elif isinstance(user, int):
            uri: str = 'discord:member:' + str(user)
            super().__init__(uri)
            if self.data:
                self.id: str = self.data.pop('id')  # do not pull id from local user, pop to remove from data
                self.name: str = self.data.pop('name')
                self.discriminator: str = self.data.pop('discriminator')
                self.bot: bool = self.data.pop('bot')
            else:
                raise TypeError('Given id as User attribute with no user on file')
        elif isinstance(user, discord.member.Member) or isinstance(user, discord.user.User):
            uri: str = 'discord:member:' + str(user.id)
            super().__init__(uri)
            if self.data:
                self.id: str = self.data.pop('id')  # do not pull id from local user, pop to remove from data
                self.name: str = self.data.pop('name')
                self.discriminator: str = self.data.pop('discriminator')
                self.bot: bool = self.data.pop('bot')
            else:
                self.id: int = user.id
                self.name: str = user.name
                self.discriminator: str = user.discriminator
                self.bot: bool = user.bot
                self.data: dict = {}
        else:
            raise TypeError('User object given unknown type')


class Category(Data):
    def __init__(self, category: str or int or discord.CategoryChannel) -> None:  # ToDo
        uri = None
        if isinstance(category, str):
            uri = category
        if isinstance(category, int):
            uri = 'discord:category:' + str(category)
        if isinstance(category, discord.CategoryChannel):
            uri = 'discord:category:' + str(category.id)
        super().__init__(uri)
        if self.data:
            self.id: int = self.data.pop('id')
            self.name: str = self.data.pop('name')
            self.channels: dict = self.data.pop('channels')
        elif isinstance(category, discord.CategoryChannel):
            self.id: int = category.id
            self.name: str = category.name
            self.channels: dict = {}
            for channel in category.channels:
                self.channels[channel.name]: int = int(channel.id)
            self.data = {}
            self.save()


class Meta(Data):
    def __init__(self, uri: str = None) -> None:
        uri = uri or 'coda:metadata'
        super().__init__(uri)
        if self.data:
            self.id_list:         list = self.data.pop('id_list')
            self.uuid4_duplicate: bool = self.data.pop('uuid4_duplicate')
        else:
            self.id_list: list = []
            self.uuid4_duplicate: bool = False
            self.data: dict = {}

    def append_id(self, arg: str) -> None:
        self.id_list.append(arg)
        self.save()

'''    def collision_chance(self):
        getcontext().prec = 128
        n = (Decimal(-e) ** (Decimal(10) ** Decimal(2)) * (Decimal(2) ** Decimal(-123))) + Decimal(1)
        print(n)
        d = Decimal(os.getenv('COLLISION_CONSTANT'))
        print(d)
        print((n/d) + Decimal(1))'''


def url_to_uri(url: str) -> str:
    if 'https://' in url:
        split = url.split('/')
        uri = 'spotify:' + split[3] + ':' + split[4][:22]
        return uri
    else:
        raise TypeError('Please give Spotify Link')


def pretty_print(data: dict) -> str:
    data = json.dumps(data, sort_keys=True, indent=4)
    print(data)
    return data
