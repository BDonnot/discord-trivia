import copy
import asyncio
import datetime
import discord

import numpy as np

from discord.ext import commands

from karadoc import Funct
from .Cards import Card, EMOJIS, ANSWERS


class Player(object):
    one_sec = datetime.timedelta(seconds=1)
    timeout = 120
    def __init__(self, id_discord):
        self.id_discord = id_discord
        self.user = discord.User(id=id_discord)
        self.emoji = "✅"
        self.format_timeout = "React on the emoji to choose an answer. When you are sure validate with ✅"
        self.format_timeout += "{} s left to play"
        self.total_point = 0

        # game related (should be reset after each round)
        self.msg_check = None
        self.beginning_ts = None
        self.answer = None
        self.time_end = None

    @staticmethod
    def from_dict(dict_mongo):
        res = Player(id_discord=None)
        res.id_discord = dict_mongo["id_discord"]
        res.total_point = dict_mongo["total_point"]
        res.user = discord.User(id=res.id_discord)
        return res

    def to_dict(self):
        res = {}
        res["id_discord"] = self.id_discord
        res["total_point"] = self.total_point
        return res

    def set_point(self, correct_answer):
        if self.answer == correct_answer:
            self.total_point += 1

        self.msg_check = None
        self.beginning_ts = None
        self.answer = None
        self.time_end = None

    async def send_cards(self, discord_client, cards_emb):
        message = await discord_client.send_message(self.user,
                                                    content=self.format_timeout.format(self.timeout),
                                                    embed=cards_emb)
        self.msg_check = message[-1]

        for id_em in sorted(EMOJIS.keys()):
            await discord_client.add_reaction(self.msg_check, EMOJIS[id_em])
        await discord_client.add_reaction(self.msg_check, self.emoji)
        self.beginning_ts = datetime.datetime.now()
        self.time_end = self.beginning_ts + self.timeout * self.one_sec

    async def check_react(self, discord_client, cards_emb):
        if self.answer is not None:
            # I already answered the question, so i need to pass
            return

        # another_one = True
        #
        # next_time = self.beginning_ts + one_sec
        nb_sec = 1
        # while another_one and nb_sec <= self.timeout:
        #     self.msg_check = await discord_client.get_message(self.msg_check.channel, self.msg_check.id)
        #     counts = {react.emoji: react for react in self.msg_check.reactions}
        #     if self.emoji in counts:
        #         react_ = counts[self.emoji]
        #         if react_.count >= 2:
        #             need_break = False
        #             # await discord_client.delete_message(msg_check)
        #             for em in EMOJIS.values():
        #                 if em in counts:
        #                     if counts[em].count >= 2:
        #                         if self.answer is None:
        #                             self.answer = ANSWERS[em]
        #                             need_break = True
        #                         else:
        #                             need_break = False
        #                             self.answer = None
        #                             await discord_client.send_message(self.user,
        #                                                               content="Please choose only one anwser")
        #             if self.answer is None:
        #                 await discord_client.send_message(self.user,
        #                                                   content="Please choose at least one anwser")
        #             if need_break:
        #                 break
        #     self.msg_check = await discord_client.edit_message(self.msg_check,
        #                                                        self.format_timeout.format(self.timeout-nb_sec, self.emoji),
        #                                                        embed=cards_emb)
        #
        #     curr_time = datetime.datetime.now()
        #     while self.beginning_ts + nb_sec*one_sec <= curr_time:
        #         nb_sec += 1
        #     next_time = self.beginning_ts + nb_sec * one_sec
        #     tmp_ = next_time - curr_time
        #     await asyncio.sleep(tmp_.total_seconds())

        self.msg_check = await discord_client.get_message(self.msg_check.channel, self.msg_check.id)
        counts = {react.emoji: react for react in self.msg_check.reactions}
        if self.emoji in counts:
            react_ = counts[self.emoji]
            if react_.count >= 2:
                # await discord_client.delete_message(msg_check)
                for em in EMOJIS.values():
                    if em in counts:
                        if counts[em].count >= 2:
                            if self.answer is None:
                                self.answer = ANSWERS[em]
                            else:
                                self.answer = None
                                await discord_client.send_message(self.user,
                                                                  content="Please choose only one anwser")
                if self.answer is None:
                    await discord_client.send_message(self.user,
                                                      content="Please choose at least one anwser")
        curr_time = datetime.datetime.now()
        while self.beginning_ts + nb_sec*self.one_sec <= curr_time:
            nb_sec += 1
        self.msg_check = await discord_client.edit_message(self.msg_check,
                                                           self.format_timeout.format(self.timeout-nb_sec, self.emoji),
                                                           embed=cards_emb)

        if self.answer is not None:
            await discord_client.send_message(self.user,
                                              content="You choose anwser {}".format(EMOJIS[self.answer]))
            msg = await discord_client.get_message(self.msg_check.channel, self.msg_check.id)
            for react in msg.reactions:
                emoji = react.emoji
                users = await discord_client.get_reaction_users(react)
                for user in users:
                    try:
                        await discord_client.remove_reaction(react.message, emoji, user)
                    except Exception as e:
                        print("_remove_all_emojis")
                        print(e)
                        print("Probably a permission issue")
        elif curr_time > self.time_end:
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
        self.player_tmp = []
        self.all_ids = set()
        self.cards_criteria = {}  # used to choose the cards to play, note that reloading a game would probably change
        self.id_mongo = None
        # the cards in the deck
        self.deck = []
        self.init = False

        # game related stuff
        self.current_card_id = None
        self.message_game = None
        self.main_message_text = None
        self.embed_card = None
        self.lock = False

    def add_player(self, player_id):
        if player_id in self.all_ids:
            return False
        tmp = Player(id_discord=player_id)
        self.player_tmp.append(tmp)
        self.all_ids.add(player_id)
        self.save()
        return True

    def _integrate_new_players(self):
        self.players += self.player_tmp
        self.player_tmp = []
        self.lock = True

    def save(self):
        dict_ = self.to_dict()
        if self.id_mongo is None:
            tmp = self.database.games.insert(dict_)
            self.id_mongo = tmp
        else:
            self.database.games.update_one({'_id': self.id_mongo}, {"$set": dict_})

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
        self.all_ids = {el.id_discord for el in self.players}

    def is_locked(self):
        return self.lock

    async def start_game(self, discord_client, channel):
        self.init_me()
        np.random.shuffle(self.deck)
        self.current_card_id = 0
        # await self.start_round(discord_client, channel)

    async def end_game(self, discord_client, channel):
        # count results and winners of the game
        content_ = "Global results are: "
        tmp = ["\t - <@!{}>: {} point(s)".format(el.id_discord, el.total_point) for el in
               sorted(self.players, key=lambda p: p.total_point, reverse=True)]
        content_ += '\n{}'.format("\n".join(tmp))
        self.save()
        # self.players = []
        # self.player_tmp = []
        await discord_client.send_message(channel,
                                          content=content_)

    async def start_round(self, discord_client, channel):
        if self.lock:
            raise RuntimeError("Impossible to start a new round while a round is still in progress.")
        # start welcoming message
        self._integrate_new_players()

        content_ = "A round is about to start with {} players:".format(len(self.players))
        tmp = ["\t - <@!{}>".format(el.id_discord) for el in self.players]
        content_ += '\n{}'.format("\n".join(tmp))
        self.main_message_text = content_
        self.message_game = await discord_client.send_message(channel,
                                                              content=self.main_message_text)
        self.message_game = self.message_game[-1]

        # choose a card from the deck
        card = Card.from_dict(self.deck[self.current_card_id])
        self.embed_card = Funct.embed_from_dict(card.dict_embed())

        # set send it to the main channel
        self.message_game = await discord_client.get_message(self.message_game.channel, self.message_game.id)
        self.message_game = await discord_client.edit_message(self.message_game,
                                                              self.main_message_text,
                                                              embed=self.embed_card)

        # send it in pm to each player
        sends_async = []
        for player in self.players:
            sends_async.append(player.send_cards(discord_client, self.embed_card))
        for s in sends_async:
            await s
        self.round_beg = np.max([p.beginning_ts for p in self.players])

        # update message in main when people played
        another_one = True
        one_sec = Player.one_sec
        timeout = Player.timeout
        nb_sec = 1
        while another_one and nb_sec <= timeout:
            checked_p = [p for p in self.players if p.answer is None]
            if not checked_p:
                break
            sends_async = [p.check_react(discord_client, self.embed_card) for p in checked_p]
            for s in sends_async:
                await s

            content_ = "Round has started and counts {} players:".format(len(self.players))
            tmp = ["\t - <@!{}>: {}".format(el.id_discord, "⌛" if el.answer is None else "🤫") for el in self.players]
            content_ += '\n{}'.format("\n".join(tmp))
            self.main_message_text = content_
            self.message_game = await discord_client.edit_message(self.message_game,
                                                                  self.main_message_text,
                                                                  embed=self.embed_card)

            curr_time = datetime.datetime.now()
            while self.round_beg + nb_sec*one_sec <= curr_time:
                nb_sec += 1
            next_time = self.round_beg + nb_sec * one_sec
            tmp_ = next_time - curr_time
            await asyncio.sleep(tmp_.total_seconds())

        # display winner of rounds
        content_ = "Round has ended. Results are: "
        tmp = ["\t - <@!{}> {}: {}".format(el.id_discord, EMOJIS[el.answer], "😀" if el.answer == card.ans_correct else "😔") for el in self.players]
        content_ += '\n{}'.format("\n".join(tmp))
        await discord_client.edit_message(self.message_game,
                                          content_,
                                          embed=self.embed_card)

        # count results and winners of the game
        for p in self.players:
            p.set_point(card.ans_correct)

        content_ = "Global results are: "
        tmp = ["\t - <@!{}>: {}".format(el.id_discord, el.total_point) for el in self.players]
        content_ += '\n{}'.format("\n".join(tmp))
        await discord_client.send_message(self.message_game.channel,
                                          content=content_)
        self.current_card_id += 1

        self.main_message_text = None
        self.message_game = None
        self.lock = False





