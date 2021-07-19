import os
import json
import inspect
from types import FunctionType, CoroutineType
from functools import wraps

import discord
import spotipy
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
auth_manager = spotipy.oauth2.SpotifyClientCredentials()
sp = spotipy.Spotify(auth_manager=auth_manager)

COMMAND_PREFIX = os.getenv('COMMAND_PREFIX')


def log(method) -> FunctionType or CoroutineType:
    if inspect.iscoroutinefunction(method):
        print('logging coroutine method: ' + method.__name__)

        @wraps(method)
        async def logged(*args, **kwargs):
            print()
            ctx = args[1]
            print('#' + ctx.author.discriminator + ctx.author.name + ' invoked the following command:')
            print(ctx.message.content)
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

    def run(self) -> None:
        self.discord_bot.run(self.TOKEN)


class Data:
    data = None
    directory = None

    def __init__(self) -> None:
        # Turn this into a superclass that will be the basis for all datatypes here
        pass

    def __call__(self) -> dict:
        data = self.__dict__ | self.data  # cause you can just do this ig
        del data['data']
        del data['directory']
        return data

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


class Album:
    def __init__(self, uri: str) -> None:
        if 'https://' in uri:
            uri = url_to_uri(uri)
        self.uri:       str = uri
        self.directory: str = os.path.join(os.getcwd(), r'data/' + uri)
        if os.path.isdir(self.directory):
            self.data:    dict = self.load()
            self.name:     str = self.data.pop('name')
            self.artists: list = self.data.pop('artists')
            self.tracks:  list = self.data.pop('tracks')
            self.uri:      str = self.data.pop('uri')  # this seems redundant, but removes key from self.data
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

    def __call__(self) -> dict:
        data = self.__dict__ | self.data  # cause you can just do this ig
        del data['data']
        del data['directory']
        return data

    def save(self) -> None:
        if not os.path.isdir(self.directory):
            os.mkdir(self.directory)
        with open(self.directory + '/.json', 'w') as file:
            file.write(json.dumps(self(), sort_keys=True, indent=4))

    def load(self) -> dict:
        with open(self.directory + '/.json', 'r') as file:
            return json.loads(file.read())

    # ToDo download image file of the album art and save to file


class Track:  # ToDo
    def __init__(self, link) -> None:  # ToDo
        self.link = link
        self.name = None
        self.artist = None
        self.album = None


# Discord
class User:  # ToDo
    def __init__(self, user: int or discord.User) -> None:
        if isinstance(user, int):  # if user is ID and not discord.user object
            self.directory: str = 'data/discord:member:' + str(user)
            self.data:         dict = self.load()
            self.id:            str = self.data.pop('id')  # do not pull id from local user, pop to remove from data
            self.name:          str = self.data.pop('name')
            self.discriminator: str = self.data.pop('discriminator')
            self.bot:          bool = self.data.pop('bot')
        else:
            self.directory:     str = 'data/discord:member:' + str(user.id)
            self.id:            int = user.id
            self.name:          str = user.name
            self.discriminator: str = user.discriminator
            self.bot:          bool = user.bot
            self.data:         dict = {}

    def __call__(self) -> dict:
        data = self.__dict__ | self.data
        del data['data']
        del data['directory']
        return data

    def save(self) -> None:
        if not os.path.isdir(self.directory):
            os.mkdir(self.directory)
        with open(self.directory + '/.json', 'w') as file:
            file.write(json.dumps(self(), sort_keys=True, indent=4))

    def load(self) -> dict:
        with open(self.directory + '/.json', 'r') as file:
            return json.loads(file.read())


class Category:  # no channel should be needed, the needed ID's should just be in here
    def __init__(self) -> None:  # ToDo
        pass


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
