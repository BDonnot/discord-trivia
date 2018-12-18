import re
import os
import pkg_resources
import copy
import asyncio
import numpy as np
from karadoc import Funct
import json

import aiohttp
from io import BytesIO, StringIO, TextIOWrapper

from .Cards import Card, A, B, C, EMOJIS, EASY, HARD
from .Game import Game
# from .DiscordHelper import DiscordHelper

# from .Packs import PackHandler, Pack
# from .test_ocr import PackFromIMG

import pdb

class FunctTrivia(Funct):
    pack_list_dict = {
        "title": "**GOTCTips** Pack List",
        "description": "Below you can find a list of all active $99.99 packs stored by us.\nThe list is sorted by \"**{}**\".\nFor more information please read `!gt-pack help`.",
        "color": 14090240,
            "fields": [ {
        "name": "Current Packs ",
        "value": "*{:,.0f}* -{}",
                "inline": False
            }, {
        "name": "Join us on Discord",
        "value": "[GOTCTips Discord Server](https://discord.gg/gCVq9nW)",
        "inline": True
            },
            {
        "name": "Visit our Blog",
        "value": "[GOTCTips Blog](https://gotctips.com)",
        "inline":True
            }],
            "thumbnail": {
        "url": "http://gotctips.com/wp-content/uploads/2018/10/gotctips-discord-pack2.png"
            },
            "footer": {
        "icon_url": "http://gotctips.com/wp-content/uploads/2018/06/favicon.png",
        "text": "GOTCTips - Your best source for tips, news and guides about Game of Thrones Conquest!"
            }
            }

    def __init__(self, discord_client, database, bot_prefix, name_func, permission):
        Funct.__init__(self, discord_client=discord_client, bot_prefix=bot_prefix,
                       name_func=name_func, permission=permission, link="")

        self.database = database
        self.dict_game = {}
        # self.helper = DiscordHelper(discord_client=self.discord_client)
        # self.packHandler = PackHandler(stored_info=self.database,
        #                                game_data=self.game_data,
        #                                permission=permission)
        # self.pack_from_img = PackFromIMG(game_data=self.game_data, packs_database=self.database.packs)
        self.pack_channel = "trivia"

        # self._set_only_vip()
        self._register_fun(prefix="test", fun=self._display,
                           desc="Just display a test")
        self._register_fun(prefix="add", fun=self._newcard,
                           desc="Add a new card, by answering question")
        self._register_fun(prefix="fileadd", fun=self._from_file,
                           desc="Add a new card, by providing a file")

        self._register_fun(prefix="start", fun=self._start,
                           desc="Start a nex game")
        self._register_fun(prefix="join", fun=self._register,
                           desc="Join a game already started")
        self._register_fun(prefix="next", fun=self._next,
                           desc="Start the next round")
        # self._register_fun(prefix="search", fun=self._search,
        #                    desc="Search a speficic pack")
        #
        # self._register_fun_adminonly(prefix="new packs", fun=self._newpacks,
        #                    desc="Add new packs in one single csv (one pack per column)")
        # self._register_fun_adminonly(prefix="newpack", fun=self._newpack,
        #                    desc="Add a single pack, and broadcast it")

    async def _start(self, message, msg_str, cmd) -> None:
        if message.channel.id in self.dict_game:
            await self.discord_client.send_message(message.channel, "And game has already started in this channel. Type `!trivia join` to join it.")
        else:
            game = Game(self.database)
            await game.start_game(self.discord_client, message.channel)
            self.dict_game[message.channel.id] = game

    async def _register(self, message, msg_str, cmd) -> None:
        if message.channel.id in self.dict_game:
            self.dict_game[message.channel.id].add_player(message.author.id)
        else:
            await self.discord_client.send_message(message.channel, "No game has started on this channel. Type `!trivia start` to start one.")

    async def _next(self, message, msg_str, cmd) -> None:
        if message.channel.id in self.dict_game:
            await self.dict_game[message.channel.id].start_round(self.discord_client, message.channel)
        else:
            await self.discord_client.send_message(message.channel, "No game has started on this channel. Type `!trivia start` to start one, and  `!trivia join` to join it.")

    async def _display(self, message, msg_str, cmd) -> None:
        card = Card(message.author.id,
                      "Where is test ?",
                      "Not here",
                      "Here",
                      "Not there",
                      ans_correct=B,
                      difficulty=EASY,
                      season=0)
        emb = self.embed_from_dict(card.dict_embed())
        msg_check = await self.discord_client.send_message(message.channel, embed=emb)
        msg_check = msg_check[-1]

        for id_em in sorted(EMOJIS.keys()):
            await self.discord_client.add_reaction(msg_check, EMOJIS[id_em])

    async def _from_file(self, message, msg_str, cmd) -> None:
        file_ = {}
        if message.attachments:
            # there is a json already attached to it
            file_ = message.attachments[0]
        else:
            await self.discord_client.send_message(message.channel, "You ask to enter a new card, please check your dm")
            await self.discord_client.send_file(message.author, os.path.join(pkg_resources.resource_filename(__name__, 'data'),
                                                                   "card_example.json"))
            await self.discord_client.send_message(message.author, "Please modify the file \"card_example.json\", and send it back to us")
            as_attach = False
            while not as_attach:
                ans = await self.discord_client.wait_for_message(author=message.author)
                if ans.attachments:
                    as_attach = True
                    file_ = ans.attachments[0]
                else:
                    await self.discord_client.send_message(message.channel,
                                                           "Please modify the file \"card_example.json\", and send it back to us")

        async with aiohttp.ClientSession() as session:
            # note that it is often preferable to create a single session to use multiple times later - see below for this.
            async with session.get(file_['url']) as resp:
                buffer = BytesIO(await resp.read())
        # pdb.set_trace()
        # with open(buffer, "r") as f:
        #     dict_ = json.load(f)
        dict_ = json.load(TextIOWrapper(buffer, encoding='utf-8'))
        dict_["id_player"] = message.author.id
        dict_["category"] = "from_game"
        card = Card(**dict_)
        await self.__confirm_card(card, message)

    async def _newcard(self, message, msg_str, cmd) -> None:
        await self.discord_client.send_message(message.channel, "You ask to enter a new card, please check your dm")
        await self.discord_client.send_message(message.author, "Please provide the question")
        question = await self.discord_client.wait_for_message(author=message.author)
        await self.discord_client.send_message(message.author, "Please provide the possible answer a")
        ans_a = await self.discord_client.wait_for_message(author=message.author)
        await self.discord_client.send_message(message.author, "Please provide the possible answer b")
        ans_b = await self.discord_client.wait_for_message(author=message.author)
        await self.discord_client.send_message(message.author, "Please provide the possible answer c")
        ans_c = await self.discord_client.wait_for_message(author=message.author)
        await self.discord_client.send_message(message.author, "What is the correct answer (a, b or c)")
        ans_correct = await self.discord_client.wait_for_message(author=message.author)

        season_set = False
        season = 0
        while not season_set:
            await self.discord_client.send_message(message.author, "What is the season?")
            season = await self.discord_client.wait_for_message(author=message.author)
            try:
                season = int(season.content)
                season_set = True
            except Exception as e:
                print(e)
                await self.discord_client.send_message(message.author, "Please enter a valid integer")

        difficulty_set = False
        difficulty = EASY
        while not difficulty_set:
            await self.discord_client.send_message(message.author, "What is the difficulty (easy / hard)?")
            difficulty = await self.discord_client.wait_for_message(author=message.author)
            difficulty = difficulty.content
            if difficulty[:2] == "ea":
                difficulty_set = True
                difficulty = EASY
            elif difficulty[:2] == "ha":
                difficulty_set = True
                difficulty = HARD
            else:
                await self.discord_client.send_message(message.author, "Please enter easy/hard")

        card = Card(id_player=message.author.id,
                    question=question.content,
                    ans_a=ans_a.content,
                    ans_b=ans_b.content,
                    ans_c=ans_c.content,
                    ans_correct=ans_correct.content,
                    season=season,
                    difficulty=difficulty)
        await self.__confirm_card(card, message)

    async def __confirm_card(self, card: Card, message):
        ans_correct = card.get_ans_correct()
        emb = self.embed_from_dict(card.dict_embed())
        message_card = await self.discord_client.send_message(message.author, embed=emb)
        message_card = message_card[-1]
        await self.discord_client.send_message(message.author, "{}".format(ans_correct))
        await self.discord_client.send_message(message.author, "Is this card correct?")
        while 1:
            ok_ = await self._check_if_ok(orig_message=message)
            if ok_ is not None:
                break
        if ok_:
            card.save_mongo(database=self.database.cards)
            await self.discord_client.send_message(message.author, "Sucessfully added the card")
            await self.discord_client.add_reaction(message_card, "✅")  # point_up_2d
        else:
            await self.discord_client.send_message(message.author, "Card removed")
            await self.discord_client.add_reaction(message_card, "❌")  # point_up_2d
        # await self.discord_client.add_reaction(message, "❌")  # point_up_2d