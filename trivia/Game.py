import copy
import asyncio

import discord
from discord.ext import commands

from .Cards import Card, EMOJIS, ANSWERS
import datetime

class Player(object):
    def __init__(self, id_discord):
        self.id_discord = None
        self.user = None

    @staticmethod
    def from_dict(dict_mongo):
        res = Player(id_discord=None)
        res.id_discord = dict_mongo["id_discord"]
        res.user = discord.User(id=res.id_discord)
        return res

    def to_dict(self):
        res = {}
        res["id_discord"] = self.id_discord
        return res

    async def send_cards(self, discord_client, cards_emb):
        format_timeout = "React on the emoji to choose an answer. When you are sure validate with ✅"
        format_timeout += "{} s left to play"
        timeout = 120
        message = await discord_client.send_message(self.user,
                                                    content=format_timeout.format(timeout),
                                                    embed=cards_emb)
        msg_check = message[-1]
        emoji = "✅"
        for id_em in sorted(EMOJIS.keys()):
            await discord_client.add_reaction(msg_check, EMOJIS[id_em])
        await discord_client.add_reaction(msg_check, emoji)
        beginning_ts = datetime.datetime.now()
        # for i in range(timeout):
        another_one = True
        one_sec = datetime.timedelta(seconds=1)
        next_time = beginning_ts + one_sec
        nb_sec = 1
        answer = None
        while another_one and nb_sec <= timeout:
            msg_check = await discord_client.get_message(msg_check.channel, msg_check.id)
            counts = {react.emoji: react for react in msg_check.reactions}
            if emoji in counts:
                react_ = counts[emoji]
                if react_.count >= 2:
                    need_break = False
                    # await discord_client.delete_message(msg_check)
                    for em in EMOJIS.values():
                        if em in counts:
                            if counts[em].count >= 2:
                                if answer is None:
                                    answer = ANSWERS[em]
                                    need_break = True
                                else:
                                    need_break = False
                                    await discord_client.send_message(self.user,
                                                                      content="Please choose only one anwser")
                    if answer is None:
                        await discord_client.send_message(self.user,
                                                          content="Please choose at least one anwser")
                    if need_break:
                        break
            await discord_client.edit_message(msg_check,
                                              format_timeout.format(timeout-nb_sec, emoji),
                                              embed=cards_emb)

            curr_time = datetime.datetime.now()
            while beginning_ts + nb_sec*one_sec <= curr_time:
                nb_sec += 1
            next_time = beginning_ts + one_sec
            tmp_ = beginning_ts + nb_sec*one_sec - curr_time
            await asyncio.sleep(tmp_.total_seconds())
        if answer is not None:
            await discord_client.send_message(self.user,
                                              content="You choose anwser {}".format(EMOJIS[answer]))
        else:
            await discord_client.send_message(self.user,
                                              content="Timeout, you didn't choose any answer :-/")


class Game(object):
    def __init__(self, database):
        """
        create a new game, and register it in the database
        :param database:
        """
        self.database = database
        self.players = []
        self.cards_criteria = {}  # used to choose the cards to play, note that reloading a game would probably change
        self.id_mongo = None
        # the cards in the deck
        self.deck = []
        self.init = False

    def add_player(self, player_id):
        tmp = Player(id_discord=player_id)
        self.players.append(tmp)
        self.save()

    def save(self):
        dict_ = self.to_dict()
        if self.id_mongo is None:
            tmp = self.database.insert(dict_)
            self.id_mongo = tmp.id
        else:
            self.database.update_one({'_id': self.id_mongo}, {"$set": dict_})

    def init_me(self):
        self.deck = list(self.database.cards.find(self.cards_criteria))
        self.init = True

    def to_dict(self):
        res = {}
        res["players"] = [el.to_dict() for el in self.players]
        res["cards_criteria"] = self.cards_criteria
        if self.id_mongo is not None:
            res["_id"] = self.id_mongo
        return res

    def from_dict(self, dict_mongo):
        self.players = [Player.from_dict(el) for el in dict_mongo["players"]]
        self.cards_criteria = dict_mongo["cards_criteria"]
        self.id_mongo = dict_mongo["_id"]
        self.init = False
        self.init_me()

    def start_round(self):



