import frame

import os
import random
import asyncio
from datetime import datetime

import discord
from discord.ext import tasks, commands, forms


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
        if 'reviews' in self.data:
            self.reviews = self.data.pop('reviews')
        else:
            self.reviews = {}


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
        if 'reviews' in self.data:
            self.reviews = self.data.pop('reviews')
        else:
            self.reviews = {}

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
            return []

    @raffles.setter
    def raffles(self, album: dict) -> None:
        raise KeyError('If you want this to work you gotta build it yourself.')

    def review(self, album, category, set: dict = None):
        if isinstance(album, frame.Album):
            album = album.uri
        if isinstance(category, frame.Category):
            category = category.uri
        if set:
            data = set
            if album in self.reviews:
                Review(self.reviews[album]).update(category, data)
            else:
                data['category'] = [category]
                data['user'] = self.uri
                data['album'] = album
                self.reviews[album] = Review(data=data).uri
                self.save()
        else:
            if album in self.reviews:
                return Review(self.reviews[album])
            else:
                return None

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
        if 'channel_key' in self.data:
            self.channel_key: str = self.data.pop('channel_key')
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
            if 'aotw.raffle.' in dir:
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


class Review(frame.Data):
    def __init__(self, uri: str = None, data: dict = None) -> None:
        if uri:
            super().__init__(uri)
            self.user:                 str = self.data.pop('user')
            self._album:               str = self.data.pop('album')
            self.category:            list = self.data.pop('category')
            self.id:                   str = self.data.pop('id')
            self.musical_ability:    float = self.data.pop('musical_ability')
            self.musical_creativity: float = self.data.pop('musical_creativity')
            self.vocal_ability:      float = self.data.pop('vocal_ability')
            self.lyrical_creativity: float = self.data.pop('lyrical_creativity')
            self.interconnectivity:  float = self.data.pop('interconnectivity')
            self.mix_master:         float = self.data.pop('mix_master')
            self.impression:         float = self.data.pop('impression')
            self.notes:                str = self.data.pop('notes')
        if data:
            self.id:                   str = self.gen_id()
            self.uri:                  str = 'aotw:review:' + self.id
            super().__init__(self.uri)
            self.user:                 str = data.pop('user')
            self._album:               str = data.pop('album')
            self.category:            list = data.pop('category')
            self.musical_ability:    float = data.pop('musical_ability')
            self.musical_creativity: float = data.pop('musical_creativity')
            self.vocal_ability:      float = data.pop('vocal_ability')
            self.lyrical_creativity: float = data.pop('lyrical_creativity')
            self.interconnectivity:  float = data.pop('interconnectivity')
            self.mix_master:         float = data.pop('mix_master')
            self.impression:         float = data.pop('impression')
            self.notes:        None or str = None
            self.data: dict = data
            album = self.album
            album.reviews[self.user] = self.uri
            album.save()
            self.save()

    @property
    def album(self):
        return Album(self._album)

    def update(self, category, data):
        if isinstance(category, frame.Category):
            category = category.uri
        if category not in self.category:
            self.category.append(category)
        for key, value in data.items():
            if key not in self.__dict__:
                raise KeyError('Update data must be already valued in Review class')
            self.__dict__[key] = value
        self.save()


class AOTW(frame.Frame, Meta):
    TOKEN = os.getenv('DISCORD_TOKEN')

    def __init__(self) -> None:
        super().__init__('aotw:metadata')
        self.bot.add_cog(AOTWCog(self))

    async def uuid4_collision(self, ctx) -> None:
        await ctx.send('@everyone THE IMPOSSIBLE HAS HAPPENED!\n' +
                       '<@!' + str(ctx.author.id) + '> Generated a DUPLICATE ID based on pythons UUID4!\n' +
                       'The number of random version-4 UUIDs which need to be generated in order to have a 50% ' +
                       'probability of at least one collision is 2.71 QUINTILLION.\n' +
                       'This number is equivalent to generating 1 billion UUIDs per second for about 85 years.\n' +
                       'The probability to find a duplicate within 103 trillion version-4 UUIDs is one in a ' +
                       'billion.\n' +
                       f'In this app we have {len(self.id_list)}.')
        embed = discord.Embed(description='[Universally Unique Identifier](https://en.wikipedia.org/wiki/Universally' +
                                          '_unique_identifier#:~:text=This%20number%20is%20equivalent%20to,would%20be' +
                                          '%20about%2045%20exabytes.&text=Thus%2C%20the%20probability%20to%20find,is%' +
                                          '20one%20in%20a%20billion.)')
        await ctx.send(embed=embed)
        print('uuid4 Duplicate detected, and regenerated.')
        metadata = Meta()
        metadata.uuid4_duplicate = False

    async def get_raffle(self, ctx):
        user = User(ctx.author)
        category = frame.Category(ctx.channel.category).uri
        raffles = user.raffles
        if category in raffles and user.raffle[category] is not None:
            album = user.raffle[category]
            await ctx.send('Your current raffle for this category is: ' + album.name)
            embed = discord.Embed(
                description='[' + album.name + '](' + album.link + ')')
            await ctx.send(embed=embed)
        else:
            await ctx.send('You currently have no chosen raffle. To set your raffle send "!raffle" followed by a ' +
                           'spotify link to the album you would like to pick.')

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
        metadata = frame.Meta()
        if metadata.uuid4_duplicate:
            await self.uuid4_collision(ctx)

    async def set_schedule(self, ctx, *args):
        category = frame.Category(ctx.channel.category).uri
        self.schedule = [category, args[0]]
        if len(args) >= 2:
            self.schedule = [category, args[1]]
        await ctx.send('Schedule set for ' + self.schedule[category][0] + ' at ' +
                       self.schedule[category][1] + ':' + self.schedule[category][2])

    async def picker(self, category):
        while True:
            while not self.is_date(category):
                await asyncio.sleep(30)
            await self.pick_raffle(category)
            await asyncio.sleep(60)

    async def pick(self, ctx):
        category = frame.Category(ctx.channel.category)
        await self.pick_raffle(category)

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
            await channel.send('A new album has been chosen for the week:\n' +
                               'The Album for this week is: ' + self[category].name + ', which was chosen by:')
            for user in self[category].raffles[category].values():
                await channel.send('<@!' + str(User(user).id) + '>')
            embed = discord.Embed(
                description='[' + self[category].name + '](' + self[category].link + ')')
            await channel.send(embed=embed)
        else:
            await channel.send('No Raffles set for this category. There will be no Album for this week.')

    async def review(self, ctx, album: frame.Album):
        form = forms.Form(ctx, album.name, cleanup=True)
        form.add_question('Musical Ability\n' +
                          'On a scale from 1-10 how would you rate the Musical Ability displayed in this album?',
                          'musical_ability',
                          [self.review_validator])
        form.add_question('Musical Creativity\n' +
                          'On a scale from 1-10 how would you rate the Musical Creativity displayed in this album?',
                          'musical_creativity',
                          [self.review_validator])
        form.add_question('Vocal Ability\n' +
                          'On a scale from 1-10 how would you rate the Vocal Ability displayed in this album?',
                          'vocal_ability',
                          [self.review_validator])
        form.add_question('Lyrical Creativity\n' +
                          'On a scale from 1-10 how would you rate the Lyrical Creativity displayed in this album?',
                          'lyrical_creativity',
                          [self.review_validator])
        form.add_question('Album Interconnectivity\n' +
                          'On a scale from 1-10 how well connected were each song to the album as a whole?',
                          'interconnectivity',
                          [self.review_validator])
        form.add_question('Mix and Master\n' +
                          'On a scale from 1-10 how would you rate the Mix and Master of this album?',
                          'mix_master',
                          [self.review_validator])
        form.add_question('Overall Impression\n' +
                          'On a scale from 1-10 how much did you like this album?',
                          'impression',
                          [self.review_validator])
        form.edit_and_delete(True)
        form.set_timeout(60)
        result = await form.start()
        user = User(ctx.author.id)
        user.review(album.uri, ctx.channel.category.id, set=result.__dict__)
        await self.notify_review(ctx, album)

    async def review_validator(self, ctx, message):
        try:
            number = float(message.content)
            if 1 <= number <= 10:
                return number
            return False
        except:
            return False

    async def notify_review(self, ctx, album):
        user = User(ctx.author.id)
        category = frame.Category(ctx.channel.category.id)
        review = user.review(album.uri, category)
        description = (f'Musical Ability: {review.musical_ability}\n' +
                       f'Musical Creativity: {review.musical_creativity}\n' +
                       f'Vocal Ability: {review.vocal_ability}\n' +
                       f'Lyrical Creativity: {review.lyrical_creativity}\n' +
                       f'Album Interconnectivity: {review.interconnectivity}\n' +
                       f'Mix and Master: {review.mix_master}\n' +
                       f'Overall Impression: {review.impression}\n')
        if review.notes is not None:
            description = description + f'Notes:: {review.notes}\n'
        embed = discord.Embed(title=f"@{ctx.author.name}'s Review of {album.name}", description=description)
        await ctx.send(embed=embed)


class AOTWCog(commands.Cog):
    def __init__(self, bot: AOTW) -> None:
        self.bot = bot
        self.picker.start()

    @commands.command(
        help='Give a spotify album url or uri to set as your raffle for the next Album of the Week. Informs you of ' +
             'your current raffle if no album send.',
        brief='Sets your album raffle'
    )
    async def raffle(self, ctx, *args):
        if not args:
            await self.bot.get_raffle(ctx)
        else:
            await self.bot.raffle(ctx, args[0])

    @commands.command(
        help='Review an album. Send "!review" with no parameters to review the current album of the week, or add a ' +
             'spotify album link to review that album. Just follow the prompts to set your rating.',
        brief='Reviews an album'
    )
    async def review(self, ctx, *args):
        if args:
            if self.bot.is_album_url(args[0]) or self.bot.is_album_uri(args[0]):
                album = Album(args[0])
                await self.bot.review(ctx, album)
            else:
                await ctx.send('Invalid Album link')
        else:
            category = frame.Category(ctx.channel.category).uri
            album = None
            if category in self.bot.aotw and self.bot.aotw[category] is not None:
                album = Album(self.bot.aotw[category])
            if album is None:
                await ctx.send('There is no album of the week right now to review. If you would like to review a ' +
                               'different album please add a link to the album on spotify after "!review"')
            else:
                await self.bot.review(ctx, album)
        # TODO this should eventually have the ability to do "!review note {add notes here}" or something similar

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
        if not categories:
            return
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
