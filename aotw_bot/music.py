import traceback

import spotipy
from dotenv import load_dotenv


load_dotenv()

auth_manager = spotipy.oauth2.SpotifyClientCredentials()
sp = spotipy.Spotify(auth_manager=auth_manager)


class Artist:  # ToDo
    def __init__(self, link) -> None:  # ToDo
        spotify_info = sp.artist(link)
        self.uri:             str = spotify_info['uri']
        self.name:            str = spotify_info['name']
        self.genre:          list = spotify_info['genre']
        self.rated_releases: list = []

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
    def __init__(self, link) -> None:  # ToDo
        spotify_info = sp.artist(link)
        self.uri: str = spotify_info['uri']
        self.name = spotify_info['name']
        self.artist = None
        self.tracks = []
        self.art = None


class Track:  # ToDo
    def __init__(self, link) -> None:  # ToDo
        self.link = link
        self.name = None
        self.artist = None
        self.album = None


class Review:  # ToDo
    def __init__(self):
        pass

