import os
import json

import spotipy
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
auth_manager = spotipy.oauth2.SpotifyClientCredentials()
sp = spotipy.Spotify(auth_manager=auth_manager)

COMMAND_PREFIX = os.getenv('COMMAND_PREFIX')


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=COMMAND_PREFIX)

        @super().event
        async def on_ready():
            print('Discord Bot Ready')

        @super().command(
            help="Returns pong if bot is properly connected to the server.",
            brief="Prints pong back to the channel."
        )
        async def ping(ctx):
            await ctx.channel.send('pong')


# Nothing below here has been checked
class Artist:  # ToDo
    def __init__(self, link, data: dict = None) -> None:  # ToDo
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
        # seach for loaded copy
        # load copy
            #new thread with refreshing release
            #give artist
        #no copy
            # run init


class Album:  # ToDo
    def __init__(self, uri) -> None:  # ToDo
        if 'https://' in uri:
            split = uri.split('/')
            if not split[3] == 'album':
                raise ValueError('Link appears to not be a Spotify Album link')
            uri = 'spotify:' + split[3] + ':' + split[4][:22]
            print(uri)
        self.uri:       str = uri
        self.directory: str = '/data/' + uri
        if os.path.isdir(self.directory):
            pass
            # pull from this data
        else:
            spotify_info = sp.album(uri)
            self.name:     str = spotify_info['name']
            self.artists: list = spotify_info['artists']  # ToDo make this pull just the uri from each
            self.tracks:  list = spotify_info['tracks']  # ToDo make this pull just the uri from each
'''        if isinstance(data, dict):
            self.uri:      str = data.pop('uri')
            self.name:     str = data.pop('name')
            self.artists:  str = data.pop('artist')
            self.tracks:  list = data.pop('tracks')
            self.data:    dict = data
            # self.art we should turn this into a property to pull from a file'''
'''        spotify_info  = sp.album(uri)
        self.uri: str = spotify_info['uri']
        self.name     = spotify_info['name']
        self.artists  = None
        self.tracks   = []
        self.art      = None
        print(json.dumps(spotify_info, sort_keys=True, indent=4))'''


class Track:  # ToDo
    def __init__(self, link) -> None:  # ToDo
        self.link = link
        self.name = None
        self.artist = None
        self.album = None


class Review:  # ToDo
    def __init__(self):
        pass
