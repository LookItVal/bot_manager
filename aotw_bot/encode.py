import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from dotenv import load_dotenv

load_dotenv()
FILE = os.getenv('RSA_FILE')


class Encoder:
    def __init__(self) -> None:  # Why do i do this to myself ToDo TURN ALL OF THESE INTO ENV
        self.users_file  = '/aotw_bot/users.rsa'
        self.raffle_file = '/aotw_bot/raffle.rsa'
        self.aotw_file   = '/aotw_bot/aotw.rsa'
        self.albums_file = '/aotw_bot/albums.rsa'

    '''

    @property
    def users(self):
        pass

    @users.setter
    def users(self, user):
        pass

    @property
    def raffle(self):
        pass

    @raffle.setter
    def raffle(self, raffle):
        pass

    @property
    def aotw(self):
        pass

    @aotw.setter
    def aotw(self, aotw):
        pass

    @property
    def albums(self):
        pass

    @albums.setter
    def albums(self, albums):
        pass

    @property
    def artists(self):
        pass

    @artists.setter
    def artists(self, artists):
        pass

    @property
    def review(self):
        pass

    @review.setter
    def review(self, review):
        pass

    @property
    def enc(self):
        return self.load_key()
    
    '''

    def load_key(self):
        with open(FILE, 'rb') as pem_in:
            pemlines = pem_in.read()
        private_key = load_pem_private_key(pemlines, None, default_backend())
        return private_key

    @staticmethod
    def new_key():
        key = rsa.generate_private_key(
            public_exponent = 65537,
            key_size        = 2048,
            backend         = default_backend()
        )
        pem = key.private_bytes(
            encoding             = serialization.Encoding.PEM,
            format               = serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm = serialization.NoEncryption()
        )
        with open(FILE, 'wb') as pem_out:
            pem_out.write(pem)
