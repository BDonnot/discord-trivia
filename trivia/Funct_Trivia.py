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

from .Cards import Card, A, B, C, emojis, EASY, HARD
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
                       name_func=name_func, permission=permission)

        self.database = database

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

        # self._register_fun(prefix="search", fun=self._search,
        #                    desc="Search a speficic pack")
        #
        # self._register_fun_adminonly(prefix="new packs", fun=self._newpacks,
        #                    desc="Add new packs in one single csv (one pack per column)")
        # self._register_fun_adminonly(prefix="newpack", fun=self._newpack,
        #                    desc="Add a single pack, and broadcast it")

    async def _start(self, message, msg_str, cmd) -> None:

        pass
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

        for id_em in sorted(emojis.keys()):
            await self.discord_client.add_reaction(msg_check, emojis[id_em])

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

    # base functions
    async def _packlist(self, message, msg_str, cmd) -> None:

        _, ordering, modified, get_name = self._make_ordering_and_name(msg_str)

        keep = "k21"
        price = 99.99
        packs, exact = self.packHandler.retrieve_all(keep=keep, price=price)
        if not len(packs):
            await self.discord_client.send_message(message.channel, "No packs stored yet.")
            return

        emb_ = self._format_embed_list(packs, ordering=ordering, get_name=get_name, modified=modified)
        msg_check = await self.discord_client.send_message(message.channel, content=None, embed=emb_)
        msg_check = msg_check[0]

        emojis = ["🐉", "⚒", "🆙", "💰", "💬"]
        reset = "🗑"

        for emoji in emojis:
            await self.discord_client.add_reaction(msg_check, emoji)
        await self.discord_client.add_reaction(msg_check, reset)

        reactors = set()
        reactors.add(self.discord_client.user.id)
        res_pm = None
        added_val = {}
        for _ in range(120):
            msg_check = await self.discord_client.get_message(message.channel, msg_check.id)
            counts = {react.emoji: react for react in msg_check.reactions}
            to_remove = set()
            check_other = True
            added_new = False
            if reset in counts:
                react_ = counts[reset]
                if react_.count >= 2:
                    # reset everything
                    added_val = {}
                    await self._remove_all_emojis(msg_check)
                    for emoji in emojis:
                        await self.discord_client.add_reaction(msg_check, emoji)
                    await self.discord_client.add_reaction(msg_check, reset)
                    check_other = False
                    to_remove = set(emojis)
                    added_new = True

            if check_other and emojis[-1] in counts:
                react_ = counts[emojis[-1]]
                if react_.count >= 2:
                    users = await self.discord_client.get_reaction_users(react_)
                    for user in users:
                        if user.id not in reactors:
                            if res_pm is None:
                                res_pm = "```List of the {} packs stored```\n".format(len(packs))
                                packs = sorted(packs, key=PackHandler.key, reverse=True)
                                # for this to work packs must be sorted
                                bold_name = "**{}**"
                                name = ""
                                gold = 0
                                prices = []
                                prev_name_not_formatted = ""
                                for pack in packs:
                                    if pack.name != prev_name_not_formatted:
                                        # i encounter a new pack, i store in the results
                                        res_pm += self._join_res_pack(name, prices, gold)
                                        name = bold_name.format(pack.proper_name(pack.name))
                                        prices = ["${}".format(pack.price)]
                                        gold = pack.value_gold
                                        prev_name_not_formatted = pack.name
                                    else:
                                        # I update the pack the proper way
                                        tmp_ = pack.value_gold
                                        gold = tmp_ if tmp_ > gold else gold
                                        prices.append("${}".format(pack.price))
                                res_pm += self._join_res_pack(name, prices, gold)
                            reactors.add(user.id)
                            await self.discord_client.send_message(user, res_pm)

            for emoji in added_val:
                if check_other and emoji in counts:
                    react_ = counts[emoji]
                    if react_.count < 2:
                        # i remove the reaction
                        added_new = True
                        to_remove.add(emoji)

            for emoji in emojis[:-1]:
                if emoji in added_val:
                    continue
                if check_other and emoji in counts:
                    react_ = counts[emoji]
                    if react_.count >= 2:
                        added_new = True
                        if emoji == "🐉":
                            def tmp_fun(tmp_pack):
                                return tmp_pack.value_dragon
                        elif emoji == "⚒":
                            def tmp_fun(tmp_pack):
                                return tmp_pack.value_gear
                        elif emoji == "🆙":
                            def tmp_fun(tmp_pack):
                                return tmp_pack.value_enhancement
                        elif emoji == "💰":
                            def tmp_fun(tmp_pack):
                                return tmp_pack.value_coin
                        else:
                            def tmp_fun(tmp_pack):
                                return 0
                        added_val[emoji] = tmp_fun

            if added_new:
                added_val = {em: fun for em, fun in added_val.items() if not em in to_remove}
                emb_ = self._format_embed_list(packs, ordering=ordering, get_name=get_name,
                                               modified=modified, added_val=added_val)
                msg_check = await self.discord_client.edit_message(msg_check, new_content=None, embed=emb_)
                # print("I edited the msg")

            await asyncio.sleep(1)
        await self._remove_all_emojis(msg_check)

    def _join_res_pack(self, name, prices, gold):
        res = ""
        if name != "":
            prices = " | ".join(prices)
            name += " (up to {:,.0f} gold)\n".format(gold)
            res += name
            res += prices
            res += "\n"
        return res

    def _make_ordering_and_name(self, msg_str):
        # if re.match("\s+(by:.*)", msg_str) is not None:
        by_list = []
        for el in re.findall("by[:\s][a-zA-Z0-9]+\s*", msg_str):
            msg_str = re.sub(el, "", msg_str)
            tmp_ = re.sub("by[:\s]", "", el).rstrip().lstrip()
            for subel in tmp_.split():
                tmp = subel[:3]
                if not tmp in {"ks", "key", "fla", "tot", "gol", "foo", "woo", "iro", "ste", "sto", "liv", "lor"}:
                    ans = "You specify a specific ordering of the results \"{}\". It is not valid and should be one of"
                    ans += "keystone (or ks) flakes (and **not** gold flakes), total, gold, food, wood, stone, iron or steel, livestock or lore"
                    raise RuntimeError(ans.format(subel))
                by_list.append(tmp)

        def ordering(p, by_list=by_list):
            # res = (p.value_gold, )
            # res = (0, )
            if "gold" in p.values_type:
                gold = p.values_type["gold"]
            else:
                gold = 0
            res = (p.value_gold - gold,)
            price = 1
            for el in by_list[::-1]:
                cat = "buildings_mats"
                if el == "ks":
                    price = p._get_value(cat, "keystone", 1)
                    if cat in p.items:
                        if "keystone" in p.items[cat]:
                            res = (p.items[cat]["keystone"],) + res
                        else:
                            res = (0,) + res
                    else:
                        res = (0,) + res
                elif el == "key":
                    price = p._get_value(cat, "keystone", 1)
                    if cat in p.items:
                        if "keystone" in p.items[cat]:
                            res = (p.items[cat]["keystone"],) + res
                        else:
                            res = (0,) + res
                    else:
                        res = (0,) + res
                elif el == "fla":
                    cat = "research_mats"
                    price = p._get_value(cat, "red_gold_flake", 1)
                    if cat in p.items:
                        if "red_gold_flake" in p.items[cat]:
                            res = (p.items[cat]["red_gold_flake"],) + res
                        else:
                            res = (0,) + res
                    else:
                        res = (0,) + res
                elif el == "tot":
                    res = (p.value_gold - gold,) + res
                elif el == "gol":
                    if "gold" in p.values_type:
                        res = (0,) + res
                    else:
                        res = (0,) + res
                elif el == "foo":
                    price = p._get_value("food", "1", 1)
                    if "food" in p.total_amount:
                        res = (p.total_amount["food"],) + res
                    else:
                        res = (0,) + res
                elif el == "woo":
                    price = p._get_value("wood", "1", 1)
                    if "wood" in p.total_amount:
                        res = (p.total_amount["wood"],) + res
                    else:
                        res = (0,) + res
                elif el == "iro":
                    price = p._get_value("iron", "1", 1)
                    if "iron" in p.total_amount:
                        res = (p.total_amount["iron"],) + res
                    else:
                        res = (0,) + res
                elif el == "sto":
                    price = p._get_value("stone", "1", 1)
                    if "stone" in p.total_amount:
                        res = (p.total_amount["stone"],) + res
                    else:
                        res = (0,) + res
                elif el == "ste":
                    price = p._get_value("steel", "1", 1)
                    if "steel" in p.total_amount:
                        res = (p.total_amount["steel"],) + res
                    else:
                        res = (0,) + res
                elif el == "lor":
                    price = p._get_value("dragon", "dragon_lore", 1)
                    if "dragon" in p.items:
                        if "dragon_lore" in p.items["dragon"]:
                            res = (p.items["dragon"]["dragon_lore"],) + res
                        else:
                            res = (0,) + res
                    else:
                        res = (0,) + res
                elif el == "liv":
                    price = np.inf #p._get_calue("dragon", "livestock_orange", 1)
                    if "dragon" in p.items:
                        if "livestock_epic" in p.items["dragon"]:
                            res = (p.items["dragon"]["livestock_epic"],) + res
                        else:
                            res = (0,) + res
                    else:
                        res = (0,) + res

            head, *tail = res
            head += int(gold/price)
            return [head] + tail

        def get_name(p, by_list=by_list):
            res = (p.value_gold, "Total Store Value")
            if len(by_list):
                el = by_list[0]
                cat = "buildings_mats"
                if "gold" in p.values_type:
                    gold = p.values_type["gold"]
                else:
                    gold = 0
                res = (p.value_gold - gold, "Total Store Value")
                price = 1
                if el == "ks":
                    price = p._get_value(cat, "keystone", 1)
                    if cat in p.items:
                        if "keystone" in p.items[cat]:
                            res = p.items[cat]["keystone"], "Keystones"
                        else:
                            res = 0, "keystones"
                    else:
                        res = 0, "keystones"
                elif el == "key":
                    price = p._get_value(cat, "keystone", 1)
                    if cat in p.items:
                        if "keystone" in p.items[cat]:
                            res = p.items[cat]["keystone"], "Keystones"
                        else:
                            res = 0, "keystones"
                    else:
                        res = 0, "keystones"
                elif el == "fla":
                    cat = "research_mats"
                    price = p._get_value(cat, "red_gold_flake", 1)
                    if cat in p.items:
                        if "red_gold_flake" in p.items[cat]:
                            res = p.items[cat]["red_gold_flake"], "Red gold flakes"
                        else:
                            res = 0, "Red gold flakes"
                    else:
                        res = 0, "Red gold flakes"
                elif el == "tot":
                    res = (p.value_gold - gold, "Total Store Value")
                elif el == "gol":
                    if "gold" in p.values_type:
                        res = (0, "Gold")
                    else:
                        res = (0, "Gold")
                elif el == "foo":
                    price = p._get_value("food", "1", 1)
                    if "food" in p.total_amount:
                        res = (p.total_amount["food"], "Food")
                    else:
                        res = (0, "Food")
                elif el == "woo":
                    price = p._get_value("wood", "1", 1)
                    if "wood" in p.total_amount:
                        res = (p.total_amount["wood"], "Wood")
                    else:
                        res = (0, "Wood")
                elif el == "iro":
                    price = p._get_value("iron", "1", 1)
                    if "iron" in p.total_amount:
                        res = (p.total_amount["iron"], "Iron")
                    else:
                        res = (0, "Iron")
                elif el == "sto":
                    price = p._get_value("stone", "1", 1)
                    if "stone" in p.total_amount:
                        res = (p.total_amount["stone"], "Stone")
                    else:
                        res = (0, "Stone")
                elif el == "ste":
                    price = p._get_value("steel", "1", 1)
                    if "steel" in p.total_amount:
                        res = (p.total_amount["steel"], "Steel")
                    else:
                        res = (0, "Steel")
                elif el == "lor":
                    price = p._get_value("dragon", "dragon_lore", 1)
                    if "dragon" in p.items:
                        if "dragon_lore" in p.items["dragon"]:
                            res = (p.items['dragon']["dragon_lore"], "Dragon Lore")
                        else:
                            res = (0, "Dragon Lore")
                    else:
                        res = (0,) + res
                elif el == "liv":
                    price = np.inf  # p._get_calue("dragon", "livestock_orange", 1)
                    if "dragon" in p.items:
                        if "livestock_epic" in p.items["dragon"]:
                            res = (p.items["dragon"]["livestock_epic"],  "Dragon livestock (epic)")
                        else:
                            res = (0,  "Dragon livestock (epic)")
                    else:
                        res = (0,  "Dragon livestock (epic)")

                res = (res[0] + int(gold/price), res[1])
            return res

        return msg_str, ordering, len(by_list), get_name

    async def _search(self, message, cmd, msg_str):
        pack_name, ordering, modified_, get_name = self._make_ordering_and_name(msg_str)

        try:
            pack_name, _, _ = self._parse_pack(pack_name, default_values=False)
        except Exception as e:
            print(e)
            res = "Couldn't parse your querry.\n"
            res += "The error was: \n\"\"\"\n{}\n\"\"\""
            res += "\n please see the documentation for more information"
            res = res.format(e)
            await self.discord_client.send_message(message.channel, res)
            return
        keep = "k21"
        price = 99.99
        all_packs, exact = self.packHandler.pack_search(pack_name, keep=keep, price=price)
        # pdb.set_trace()
        all_packs = sorted(all_packs, key=ordering, reverse=True)

        if len(all_packs) == 0:
            ans = "No post matches \"{}\". Use `{} list` for the list of all posts."
            await self.discord_client.send_message(message.channel, ans.format(msg_str, self.func_cmd))  # point_up_2d
            await self.discord_client.add_reaction(message, "❌")  # point_up_2d
            return
        if len(all_packs) == 1:
            pack = all_packs[0]
            emb = self._format_pack_selected(msg_str, emoji="✅", pack=pack)
            msg_sent = await self.discord_client.send_message(message.channel, content=None, embed=emb)
            await self.discord_client.add_reaction(message, "✅")  # point_up_2d
            return

        links = {}
        li_emoji = ["\u0031\u20E3", "\u0032\u20E3", "\u0033\u20E3", "\u0034\u20E3",
                    "\u0035\u20E3", "\u0036\u20E3", "\u0037\u20E3", "\u0038\u20E3", "\u0039\u20E3"]
        num_max = len(li_emoji)
        back = "🔙"
        all_packs = all_packs[:num_max]
        res = []
        for i, pack in enumerate(all_packs):
            emoji = li_emoji[i]
            res.append((emoji, pack))
            links[emoji] = pack
        # res = "\n".join(res)
        # pdb.set_trace()
        emb_list = self._format_search_list(li=res, search_term=pack_name, ordering=ordering,
                                            get_name=get_name, modified=modified_)

        msg_sent = await self.discord_client.send_message(message.channel, content=None, embed=emb_list)

        msg_sent = msg_sent[0]
        # add reaction emoji
        for i in range(len(all_packs)):
            await self.discord_client.add_reaction(msg_sent, li_emoji[i])  # point_up_2d
        list_mode = True
        # state_list = True
        format_ = "**{}**\n{}"
        embs = {}
        for _ in range(120):
            msg = await self.discord_client.get_message(message.channel, msg_sent.id)
            counts = {react.emoji: react.count for react in msg.reactions}
            for vote, emoji in enumerate(sorted(counts.keys())):
                count = counts[emoji]
                if count >= 2:
                    if emoji == back:
                        msg_sent = await self.discord_client.edit_message(msg, new_content=None,
                                                                          embed=copy.deepcopy(emb_list))
                        # remove "back" reactions
                        await self._remove_all_emojis(msg_sent)

                        # add reactions to the packs
                        for i in range(len(all_packs[:num_max])):
                            await self.discord_client.add_reaction(msg_sent, li_emoji[i])  # point_up_2d
                        list_mode = True
                    elif emoji in links:
                        pack = links[emoji]
                        if not emoji in embs:
                            emb = self._format_pack_selected(search_term=msg_str, emoji=li_emoji[0], pack=pack)
                            embs[emoji] = emb
                        msg_sent = await self.discord_client.edit_message(msg, new_content=None,
                                                                          embed=copy.deepcopy(embs[emoji]))
                        await self._remove_all_emojis(msg_sent)
                        await self.discord_client.add_reaction(msg_sent, back)
                        list_mode = False
            await asyncio.sleep(1)

        # end of the playing stuff
        await self._remove_all_emojis(msg_sent)
        if list_mode:
            pack = links[li_emoji[0]]
            emb = self._format_pack_selected(search_term=msg_str, emoji=li_emoji[0], pack=pack)
        await self.discord_client.edit_message(msg_sent, new_content=None, embed=emb)

    # admin functions
    async def _modify(self, message, msg_str, cmd) -> None:
        """
        Rename a pack
        :param message:
        :param msg_str:
        :param cmd:
        :return:
        """
        pack_name = re.sub("^{}".format(cmd), "", message.content)
        pack_name = pack_name.rstrip().lstrip()
        pack_name, _, _ = self._parse_pack(pack_name, default_values=False)
        keep = "k21"
        price = 99.99
        raise NotImplementedError
        packs, exact = self.packHandler.retrieve_pack(pack_name, keep=keep, price=price)
        if len(packs) == 0:
            ans = "No pack matching \"{}\" are known. Please modify your querry"
            await self.discord_client.send_message(message.author, ans)
        elif len(packs) >= 2:
            ans = "Multiple packs matching your querry are known. Please be more specific"
            await self.discord_client.send_message(message.author, ans)
            await self._send_packs(init_message=message, packs=packs)
        else:
            # only one pack is found, i can modify it
            pack = packs[0]
            #TODO

    async def _newpack(self, message, msg_str, cmd) -> None:
        """
        Insert a new pack and give its value
        """
        ans = "Please fill the form attached, and send it back to us"
        await self.discord_client.send_message(message.author, ans)
        await self.discord_client.send_file(message.author, os.path.join(pkg_resources.resource_filename(__name__, 'data'),
                                                                   "packs_sample.csv"))
        msg = await self.discord_client.wait_for_message(author=message.author)
        if msg.attachments:
            # the player send the file, just need to check it, and update the pack
            for el in msg.attachments:
                try:
                    pack = await self.packHandler.handlefile(el, discordid=message.author.id)
                    pack_str = "{}".format(pack)
                    ans = "Name: **{}**\nContent: \n{}".format(pack.proper_name(pack.name), pack_str)
                    await self.discord_client.send_message(message.author, ans)

                    cmd_ = cmd.split()[0]
                    cmd_ += " search"

                    pack_val = ["Pack: __**{}**__ has been added".format(pack.proper_name(pack.name))]
                    pack_val += ["Total store value: **{:,.0f}**".format(pack.value_gold)]
                    pack_val += ["PM `{} {}` for more information".format(cmd_, pack.name)]

                    pack_str = "{}".format("\n".join(pack_val))

                    ans = "Does this seems legitimate ?"
                    await self.discord_client.send_message(message.author, ans)
                    while 1:
                        ok_ = await self._check_if_ok(orig_message=message)
                        if ok_ is not None:
                            break

                    if not ok_:
                        ans = "Discarding changes, the pack \"{}\" is not added"
                    else:
                        old_packs = self.packHandler.add_new_pack(pack)
                        ans = "{} old packs have been removed".format(len(old_packs))
                        await self.discord_client.send_message(message.author, ans)
                        ans = "Validate: the pack \"{}\" is added"
                        await self._braodcast_all_channels(pack_str, self.pack_channel)

                    await self.discord_client.send_message(message.author, ans.format(pack.name))

                except Exception as e:
                    res = "Couldn't Upload this pack.\n"
                    res += "The error was: \n\"\"\"\n{}\n\"\"\""
                    res = res.format(e)
                    await self.discord_client.send_message(message.author, res)
        else:
            ans = "There are nothing attached, please try again with the command \"{}\""
            await self.discord_client.send_message(message.author, ans.format(cmd))

    async def _newpacks(self, message, msg_str, cmd) -> None:
        """
        Add a new packs in the database, each column being a specific pack
        :param message:
        :param msg_str:
        :param cmd:
        :return:
        """
        nb = 0
        for el in message.attachments:
            try:
                nb = await self.packHandler.handle_multiple_packs(el, discordid=message.author.id)
                ans = "{} packs added."
                await self.discord_client.send_message(message.author, ans.format(nb))
            except Exception as e:
                print(e)
                res = "Couldn't Upload these packs.\n"
                res += "The error was: \n\"\"\"\n{}\n\"\"\""
                res = res.format(e)
                await self.discord_client.send_message(message.author, res)
        if not message.attachments:
            err = "_newpacks : Please attached a file and try again"
            raise RuntimeError(err)

    async def _deactivate(self, message, msg_str, cmd) -> None:
        pack_name, _, _ = self._parse_pack(msg_str, default_values=False)
        packs, exact = self.packHandler.retrieve_pack(pack_name, keep=None, price=None, activeonly=True)
        names = [p.name for p in packs]
        names = set(names)
        if len(names) == 0:
            err = "No pack matching \"{}\" found"
            raise RuntimeError(err.format(msg_str))
        emoji = "💔"
        timeout = 120

        format_timeout = "You have {}s to click on {} to deactivate a pack"
        msg_timer = await self.discord_client.send_message(message.author, format_timeout.format(timeout, emoji))
        msg_timer = msg_timer[0]

        messages = []
        format_ = "**{}** - ${} - keep {}"
        for p in packs:
            # self.packHandler.deactivate_pack(p)
            ans = format_.format(p.name, p.price, p.keep)
            msg = await self.discord_client.send_message(message.author, ans)
            msg = msg[0]
            await self.discord_client.add_reaction(msg, emoji)  # point_up_2d
            messages.append((msg, p, ans))

        for i in range(timeout):
            tmp = []
            for (msg_check, pack, ans) in messages:
                msg_check = await self.discord_client.get_message(msg_check.channel, msg_check.id)
                counts = {react.emoji: react for react in msg_check.reactions}
                if emoji in counts:
                    react_ = counts[emoji]
                    if react_.count >= 2:
                        self.packHandler.deactivate_pack(pack)
                        await self.discord_client.send_message(message.author, "Pack `{}` deleted".format(ans))
                        await self.discord_client.delete_message(msg_check)
                    else:
                        tmp.append((msg_check, pack, ans))
            messages = tmp
            await asyncio.sleep(1)
            await self.discord_client.edit_message(msg_timer, format_timeout.format(timeout-i, emoji))

        for (msg_check, pack, ans) in messages:
            msg_check = await self.discord_client.get_message(msg_check.channel, msg_check.id)
            counts = {react.emoji: react for react in msg_check.reactions}
            if emoji in counts:
                react_ = counts[emoji]
                await self.discord_client.remove_reaction(react_.message, emoji, self.discord_client.user)

    async def _clean_all_packs(self, message, msg_str, cmd) -> None:
        """
        Clean all the packs in the database, irreversible
        """
        ans = "Do you really want to clean all packs ?"
        await self.discord_client.send_message(message.author, ans)
        await self.discord_client.add_reaction(message, "✅")  # point_up_2d
        while 1:
            ok_ = await self._check_if_ok(orig_message=message)
            if ok_ is not None:
                break
        if ok_:
            self.packHandler.cleandb(message.author.id)
            ans = "All packs clean, i hope you were right :-/"
            await self.discord_client.send_message(message.author, ans)
        else:
            ans = "Cancelling the operation, nothing has been done"
            await self.discord_client.send_message(message.author, ans)


    async def _insert_packs(self, message, msg_str, cmd) -> None:
        """
        Admin ONLY : insert all the packs contain in a directory
        """
        ans = "Inserting all files in \"{}\"".format(msg_str)
        await self.discord_client.send_message(message.author, ans)
        nb_ = -1
        try:
            nb_ = self.packHandler.handledir(msg_str, discordid=message.author.id)
        except Exception as e:
            res = "Couldn't Upload these packs.\n"
            res += "The error was: \n\"\"\"\n{}\n\"\"\""
            res = res.format(e)
            await self.discord_client.send_message(message.channel, res)

        ans = "\"{}\" packs found and inserted".format(nb_)
        await self.discord_client.send_message(message.author, ans)
        #     return True
        # return False

    async def _packs_from_zip(self, message, msg_str, cmd) -> None:
        # cmd = self.func_prefix+"(\-|\s)"+"from\-zip"
        # if re.match(r'^{}'.format(cmd), message.content) is not None:
        self.permission._only_admin(message)
        res = []
        for attch in message.attachments:
            res+= await self.pack_from_img.parse_from_url(attch)

        for pack in res:
            await self.discord_client.send_message(message.channel, "{}".format(pack))
            # return True
        # return False

    # auxilliary functions
    def _parse_pack(self, message, default_values=True) -> (str, str):
        if default_values:
            keep = "k21"
            price = 99.99
        else:
            keep = None
            price = None
        packname = []
        li = message.split()
        # pdb.set_trace()
        if len(li) < 1:
            return "", keep, price
        for el in li:
            add_pack_name = True
            if not len(el):
                continue
            if re.match("^\s*\$", el) is not None:
                # this is the price
                try:
                    price = float(re.sub("\$", "", el))
                    if price - int(price) != 0.99:
                        price = float(int(price) + 0.99)
                except Exception as e:
                    print(e)
                    ans = "Couldn't convert \"{}\" into proper USD value. Please modify your querry"
                    raise RuntimeError(ans.format(el))
                # if not add_pack_name:
                #     # this means the player entered a keep, so i don't take into account default values for price
                #     keep = None
                # add_pack_name = False
            elif re.match("k[0-9]+", el) is not None:
                # this is the keep
                try:
                    keep = self.pack_from_img.format_keep(el)
                    # if not add_pack_name:
                    #     # this means the player entered a price, so i don't take into account default values for keep
                    #     price = None
                except Exception as e:
                    print(e)
                    ans = "Couldn't convert \"{}\" into proper keep value. Please modify your querry"
                    raise RuntimeError(ans.format(el))
                # add_pack_name = False
            else:
                packname.append(el)

        packname = " ".join(packname)
        packname = packname.rstrip().lstrip()
        return packname, keep, price

    async def _send_packs(self, init_message, packs, num=3):
        for p in packs[:num]:
            ans = ""
            ans += "{}".format(p)
            ans += "\n"
            await self.discord_client.send_message(init_message.channel, ans)

    def _format_embed_list(self, li_packs, ordering, get_name, modified, nmax=20, added_val={}):
        embed_list = copy.deepcopy(self.pack_list_dict)
        by_selected_name = get_name(li_packs[0])[1]
        add = "+".join(sorted(added_val.keys()))
        by_selected_name += add
        embed_list["description"] = embed_list["description"].format(by_selected_name)

        tmp = copy.deepcopy(embed_list["fields"][0])
        formatting = copy.deepcopy(tmp["value"])

        def pname(p):
            if not modified:
                res = Pack.proper_name(p.name)
            else:
                res = Pack.proper_name(p.name) + " ({:,.0f})".format(p.value_gold)
            return res

        # my_order = copy.deepcopy(ordering)
        def my_order(x):
            head, *tail = ordering(x)
            for el in added_val.values():
                head += el(x)
                # tmp_fun_ = copy.copy(my_order)
                # def tmp_fun_2(x):
            return [head] + tail

        lis_post = [formatting.format(my_order(p)[0], pname(p))
                    for p in sorted(li_packs, key=my_order, reverse=True)[:nmax]]
        tmp["value"] = "\n".join(lis_post)
        tmp["value"] += "\n_ _"
        tmp["value"] = re.sub("(g|G)ame (o|O)f (t|T)hrones{0,1} (c|C)onquest", "GOTC", tmp["value"])
        embed_list["fields"][0] = copy.deepcopy(tmp)
        del tmp, formatting
        embed_list = copy.deepcopy(self.embed_from_dict(dict_=embed_list))
        return embed_list

    def _format_search_list(self, search_term, li, ordering, get_name, modified):
        embed_list = copy.deepcopy(self.pack_search_list_dict)
        embed_list["description"] = embed_list["description"].format(search_term, get_name(li[0][1])[1])
        tmp = copy.deepcopy(embed_list["fields"][0])
        formatting = copy.deepcopy(tmp["value"])

        def pname(p):
            if not modified:
                res = Pack.proper_name(p.name)
            else:
                res = Pack.proper_name(p.name) + " ({:,.0f})".format(p.value_gold)
            return res

        lis_post = [formatting.format(emoji, get_name(p)[0], pname(p))
                    for emoji, p in sorted(li, key=lambda stuff : ordering(stuff[1]), reverse=True)]
        tmp["value"] = "\n".join(lis_post)
        tmp["value"] += "\n_ _"
        # tmp["value"] = re.sub("(g|G)ame (o|O)f (t|T)hrones{0,1} (c|C)onquest", "GOTC", tmp["value"])
        embed_list["fields"][0] = copy.deepcopy(tmp)
        del tmp, formatting
        embed_list = copy.deepcopy(self.embed_from_dict(dict_=embed_list))
        return embed_list

    def _format_pack_selected(self, search_term, emoji, pack):
        pack = copy.deepcopy(pack)
        embed_list = copy.deepcopy(self.pack_selected)
        p_name = Pack.proper_name(pack.name)
        embed_list["description"] = embed_list["description"].format(search_term, emoji,  pack.value_gold, p_name)
        tmp = copy.deepcopy(embed_list["fields"][0])
        tmp["name"] = tmp["name"].format(p_name)
        formatting = copy.deepcopy(tmp["value"])
        tmp["value"] = formatting.format(pack)
        tmp["value"] += "\n_ _"
        # tmp["value"] = re.sub("(g|G)ame (o|O)f (t|T)hrones{0,1} (c|C)onquest", "GOTC", tmp["value"])
        embed_list["fields"][0] = copy.deepcopy(tmp)
        del tmp, formatting
        embed_list = copy.deepcopy(self.embed_from_dict(dict_=embed_list))
        return embed_list