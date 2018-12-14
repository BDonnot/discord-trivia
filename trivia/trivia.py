from builtins import Exception

matplotlib.use('Agg')

import datetime
import time
import re
import numpy as np
import os
import pkg_resources
import asyncio
import json

from karadoc import Funct, BotBase, BaseDataBase

class TriviaDB(BaseDataBase):
    def __init__(self, app_name="got_trivia", readyness_level="test"):
        BaseDataBase.__init__(self, app_name=app_name)

        # players
        self.cards_collection = self.client["{}_{}_cards".format(app_name, readyness_level)]  # self.player_database is a collection
        self.cards = self.players_collection["cards"]  # self.players is a database


class Trivia(BotBase):
    def __init__(self, bot_token, channel_name="got-trivia", readyness_level="test",
                 reboot_message=None, last_message_posted=None,
                 bot_prefix="!gt", loop=None):

        kwargs = {"channel_name": channel_name}
        BotBase.__init__(self, bot_token=bot_token, readyness_level=readyness_level,
                         reboot_message=reboot_message, last_message_posted=last_message_posted,
                         loop=loop, bot_prefix=bot_prefix, kwargs_funct=kwargs,
                         DatabaseClass=TriviaDB)

    def _init_functionnalities(self, **kwargs):
        channel_name = kwargs["channel_name"]
        auth_twitter = kwargs["auth_twitter"]
        self.channel_name = channel_name
        self.game_data = GameData(path=pkg_resources.resource_filename(__name__, 'data'))

        self.twitter = Twitter(discord_client=self.discord_client,
                               name_func="twitter",
                               permission=self.permission,
                               bot_prefix=self.bot_prefix,
                               auth_twitter=auth_twitter,
                               database=self.database)
        self._attach_func(self.twitter, req_permanent_lookup=True)