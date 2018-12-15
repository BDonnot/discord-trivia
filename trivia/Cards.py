import copy

A = 0
B = 1
C = 2
emojis = {A:"🇦", B: "🇧", C: "🇨"}

class Cards(object):
    pack_list_dict = {
        "title": "**Trivia** Card",
        "description": "Answer the question bellow:",
        "color": 14090240,
            "fields": [ {
        "name": "**__Question__**",
        "value": "{}",
                "inline": False
            }, {
        "name": "Answer {}",
        "value": "{}",
        "inline": False
            },
            {
        "name": "Answer {}",
        "value": "{}",
        "inline": False
            },
            {
        "name": "Answer {}",
        "value": "{}\n_ _",
        "inline": False
            }]
            }

    def __init__(self, id_player, question, ans_a, ans_b, ans_c, ans_correct):
        self.id_player = id_player
        self.question = question
        self.ans_a = ans_a
        self.ans_b = ans_b
        self.ans_c = ans_c
        self.ans_correct = ans_correct

    def from_dict(self, dict_mongo):
        self.id_player = dict_mongo["id_player"]
        self.question = dict_mongo["question"]
        self.ans_a = dict_mongo["ans_a"]
        self.ans_b = dict_mongo["ans_b"]
        self.ans_c = dict_mongo["ans_c"]
        self.season = int(dict_mongo["season"])
        self.difficulty = int(dict_mongo["difficulty"])

        
    def dict_embed(self):
        res = copy.deepcopy(self.pack_list_dict)
        res["fields"][0]["value"] = res["fields"][0]["value"].format(self.question)
        res["fields"][1]["value"] = res["fields"][1]["value"].format(self.ans_a)
        res["fields"][2]["value"] = res["fields"][2]["value"].format(self.ans_b)
        res["fields"][3]["value"] = res["fields"][3]["value"].format(self.ans_c)

        res["fields"][1]["name"] = res["fields"][1]["name"].format(emojis[A])
        res["fields"][2]["name"] = res["fields"][2]["name"].format(emojis[B])
        res["fields"][3]["name"] = res["fields"][3]["name"].format(emojis[C])

        return res