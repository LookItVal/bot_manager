import frame

import os
import random
import asyncio
from datetime import datetime
from uuid import uuid4

import discord
from discord.ext import tasks, commands


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
                self.raffles[key] = AlbumDict(value)
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
            self._raffle = None

    @property
    def raffle(self):  # ToDo cant add type hints here
        if self._raffle:
            return Raffle(self._raffle)
        else:
            return None

    @raffle.setter
    def raffle(self, album: None or dict) -> None:
        if album is None:
            return
        key = next(iter(album.keys()))
        if not self._raffle:
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

    def is_winner(self, category: str or frame.Category):
        if isinstance(category, frame.Category):
            category = category.uri
        raffle = self.raffle
        aotw = Meta()[category]
        if raffle is None or aotw is None:
            return False
        if raffle.uri in aotw.raffles[category]:
            return True
        else:
            return False


# aotw
class Meta(frame.Meta):
    def __init__(self, uri: None or str = None) -> None:
        if uri is None:
            uri = 'aotw:metadata'
        super().__init__(uri)
        if 'schedule' in self.data:
            self._schedule: dict = self.data.pop('schedule')
        else:
            self._schedule = {}
        if 'aotw' in self.data:
            self._aotw: dict = self.data.pop('aotw')
        else:
            self._aotw: dict = {}
        if not hasattr(self, 'channel_key'):
            self.channel_key = 'album-of-the-week'

    def __getitem__(self, key):
        if key in self._aotw:
            if self._aotw[key]:
                return Album(self._aotw[key])
            else:
                return None
        else:
            return None

    def __setitem__(self, key: str or frame.Category, value: str or frame.Album):
        if isinstance(key, frame.Category):
            key = key.uri
        if isinstance(value, frame.Album):
            value = value.uri
        self._aotw[key] = value
        self.save()

    @property
    def schedule(self):
        return self._schedule

    @schedule.setter
    def schedule(self, date: list):
        category = date[0]
        if isinstance(category, frame.Category):
            category = category.uri
        date = date[1].lower()
        if ' ' in date:
            date = date.split(' ')
            if ':' in date[1]:
                date = [date[0]] + date[1].split(':')
            else:
                raise ValueError('date must be Day, 24hr Time, or Both.')
        elif ':' in date:
            date = [None] + date.split(':')
        elif 'day' in date:
            date = [date, None, None]
        else:
            raise ValueError('date must be Day, 24hr Time, or Both.')
        if date[0] is not None and not date[0].upper() in frame.DAYS:
            raise ValueError('date must be Day, 24hr Time, or Both.')
        if date[1] is not None and not 0 <= int(date[1]) < 24:
            raise ValueError('date must be Day, 24hr Time, or Both.')
        if date[2] is not None and not 0 <= int(date[2]) < 60:
            raise ValueError('date must be Day, 24hr Time, or Both.')
        if date[0] is not None:
            date[0] = date[0][0].upper() + date[0][1:]
        if date[1] is not None and 0 <= int(date[1]) < 10:
            date[1] = '0' + str(int(date[1]))
        if date[2] is not None and 0 <= int(date[2]) < 10:
            date[2] = '0' + str(int(date[2]))
        if category not in self._schedule:
            self._schedule[category] = [None, None, None]
        for key, value in enumerate(date):
            if value is not None:
                self._schedule[category][key] = value
        self.save()

    @property
    def aotw(self):
        return self._aotw

    @property
    def scheduled_categories(self):
        categories = []
        for item in self._schedule.keys():
            categories.append(item)
        return categories

    def is_date(self, category):
        now = datetime.now()
        if not self.schedule[category][0].upper() == frame.DAYS[now.weekday()]:
            return False
        elif not int(self.schedule[category][1]) == now.hour:
            return False
        elif not int(self.schedule[category][2]) == now.minute:
            return False
        else:
            return True

    def raffle_list(self, category: str = None) -> list:
        directories = os.listdir(os.path.join(os.getcwd(), r'data/'))
        raffles = []
        for dir in directories:
            if 'aotw:raffle:' in dir:
                raffles.append(dir)
        if category is None:
            return raffles
        final = []
        for raffle in raffles:
            raffle = Raffle(raffle)
            if category in raffle.albums:
                if raffle[category] is not None:
                    final.append(raffle[category])
        return final


class RaffleDict(dict):
    def __init__(self, val: None or dict):
        val = val or {}
        super().__init__(val)

    def __getitem__(self, key):
        uri = super().__getitem__(key)
        if uri is None:
            return None
        else:
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
        if isinstance(value, str):
            if 'https://' in value:
                value = AOTW.url_to_uri(value)
        if key in self._album and self._album[key] is not None:
            album: Album = self._album[key]
            del album.raffles[key][self.uri]
            album.save()
        self._album[key] = value
        if self[key] is None:
            self.save()
            return
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


class AOTW(frame.Frame, Meta):
    TOKEN = os.getenv('DISCORD_TOKEN')
    CHANNEL_KEY = 'album-of-the-week'

    def __init__(self) -> None:
        super().__init__('aotw:metadata')
        self.bot.add_cog(AOTWCog(self))

    async def uuid4_collision(self, ctx) -> None:
        # TODO ADD BACK THE @EVERYONE ONCE THIS HAS BEEN TESTED
        await ctx.send('THE IMPOSSIBLE HAS HAPPENED!\n' +
                       '<@!' + str(ctx.author.id) + '> Generated a DUPLICATE ID based on pythons UUID4!\n' +
                       'The number of random version-4 UUIDs which need to be generated in order to have a 50%' +
                       ' probability of at least one collision is 2.71 QUINTILLION.\n' +
                       'This number is equivalent to generating 1 billion UUIDs per second for about 85 years.\n' +
                       'The probability to find a duplicate within 103 trillion version-4 UUIDs is one in a ' +
                       'billion.\n')
        embed = discord.Embed(description='[Universally Unique Identifier](https://en.wikipedia.org/wiki/Universally' +
                                          '_unique_identifier#:~:text=This%20number%20is%20equivalent%20to,would%20be' +
                                          '%20about%2045%20exabytes.&text=Thus%2C%20the%20probability%20to%20find,is%' +
                                          '20one%20in%20a%20billion.)')
        await ctx.send(embed=embed)
        print('uuid4 Duplicate detected, and regenerated.')
        metadata = Meta()
        metadata.uuid4_duplicate = False

    async def raffle(self, ctx, arg: str) -> None:
        user = User(ctx.author)
        category = frame.Category(ctx.channel.category)
        if user.is_winner(category):
            await ctx.send('Cannot change raffle while your album has been picked.')
            return
        try:
            album = Album(arg)
        except:
            await ctx.send('Invalid Album Link')
            return
        user.raffle = {category.uri: album}
        await ctx.send('Raffle Set.')
        metadata = Meta()
        if metadata.uuid4_duplicate:
            await self.uuid4_collision(ctx)

    async def picker(self, category):  # ToDo HERE HERE HERE
        while True:
            while not self.is_date(category):
                await asyncio.sleep(30)
            await self.pick_raffle(category)
            await asyncio.sleep(60)

    async def pick(self, ctx):
        category = frame.Category(ctx.channel.category)
        await self.pick_raffle(category)

    async def set_schedule(self, ctx, *args):
        category = frame.Category(ctx.channel.category).uri
        self.schedule = [category, args[0]]
        if len(args) >= 2:
            self.schedule = [category, args[1]]
        await ctx.send('Schedule set for ' + self.schedule[category][0] + ' at ' +
                       self.schedule[category][1] + ':' + self.schedule[category][2])

    async def pick_raffle(self, category: str or frame.Category) -> None:
        if isinstance(category, frame.Category):
            category = category.uri
        self.clear_aotw(category)
        raffle_list = self.raffle_list(category)
        if raffle_list:
            album: Album = random.choice(raffle_list)
            self[category] = album
        else:
            self[category] = None
        await self.notify_raffle(category)
        # Notify Raffle Change in async method here

    def clear_aotw(self, category: str) -> None:
        if category in self.aotw and self[category] is not None:
            current_winners = self[category].raffles[category]
            for key, value in current_winners.items():
                user = User(value)
                user.raffle = {category: None}
            self[category] = None

    async def notify_raffle(self, category: str) -> None:
        channel = self.channel(category)
        if self[category]:
            winners = []
            for user in self[category].raffles[category]:
                winners.append(user)
            await channel.send('A new album has been chosen for the week:\n' +
                               'The Album for this week is ' + self[category].name)
        else:
            await channel.send('No Raffles set for this category. There will be no Album for this week.')


class AOTWCog(commands.Cog):
    def __init__(self, bot: AOTW) -> None:
        self.bot = bot
        self.picker.start()

    @commands.command(  # ToDo Give a more exact description of what the raffle is here
        help='Give a spotify album url or uri to set as your raffle for the next Album of the Week.',
        brief='Sets your album raffle'
    )
    async def raffle(self, ctx, *args):
        await self.bot.raffle(ctx, args[0])

    @commands.command(
        help='From a list of every raffle set by the Members of this channel, pick an album at random to be the ' +
             'album of the week',
        brief='Picks an album as the aotw'
    )
    @commands.has_any_role('Moderator', 'Administrator')
    async def pick(self, ctx):
        await self.bot.pick(ctx)

    @commands.command(
        help='Sets the schedule for when the Album of the Week is picked each week. Argument 1 must be the ' +
             'Day of the week, and argument 2 must be the Time of day in the form of a 24 hour clock.\n' +
             'example: "!schedule Monday 17:00" would set the Album of the Week to set every Monday at 5pm',
        brief='Chooses when to set the Album of the Week'
    )
    @commands.has_any_role('Moderator', 'Administrator')
    async def schedule(self, ctx, *args):
        await self.bot.set_schedule(ctx, *args)

    @tasks.loop(count=1)
    async def picker(self):
        categories = self.bot.scheduled_categories
        pickers = await asyncio.gather(*(self.bot.picker(category) for category in categories))
        loop = asyncio.get_event_loop()
        asyncio.ensure_future(pickers)
        try:
            loop.run_forever()
        finally:
            loop.close()

    @picker.before_loop
    async def before_picker(self):
        print('pickers waiting for bot to initialize')
        await self.bot.bot.wait_until_ready()
