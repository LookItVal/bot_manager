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
            uri = url_to_uri(uri)
        self.uri:       str = uri
        self.directory = os.path.join(os.getcwd(), r'data/' + uri)
        if os.path.isdir(self.directory):
            pass
            # pull from this data
        else:
            spotify_info = sp.album(uri)
            self.name:     str = spotify_info['name']
            self.artists: list = spotify_info['artists']  # ToDo make this pull just the uri from each
            self.tracks:  list = spotify_info['tracks']  # ToDo make this pull just the uri from each
            self.data:    dict = {}

    def __call__(self) -> dict:
        data = self.__dict__ | self.data
        del data['data']
        return data

    def save(self):
        if not os.path.isdir(self.directory):
            print('trying')
            os.mkdir(self.directory)
        with open(self.directory + '/.json', 'w') as file:
            file.write(json.dumps(self(), sort_keys=True, indent=4))



class Track:  # ToDo
    def __init__(self, link) -> None:  # ToDo
        self.link = link
        self.name = None
        self.artist = None
        self.album = None


class Review:  # ToDo
    def __init__(self):
        pass


def url_to_uri(url) -> str:
    if 'https://' in url:
        split = url.split('/')
        uri = 'spotify:' + split[3] + ':' + split[4][:22]
        return uri
    else:
        raise TypeError('Please give Spotify Link')
