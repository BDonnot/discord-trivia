import copy
import pdb

A = 0
B = 1
C = 2
EMOJIS = {A: "🇦", B: "🇧", C: "🇨"}

EASY = 0
HARD = 1

ANSWERS = {val: key for key, val in EMOJIS.items()}


class Card(object):
    pack_list_dict = {
        "title": "**Trivia** Card",
        "description": "Answer the question bellow:",
        "color": 14090240,
            "fields": [ {
        "name": "Question",
        "value": "{}",
                "inline": False
            }, {
        "name": "Answers:",
        "value": "\t - {} \t {}\n\t - {} \t {}\n\t - {} \t {}",
        "inline": False
            }]
            }

    def __init__(self, id_player, question,
                 ans_a, ans_b, ans_c, ans_correct,
                 season, difficulty, category="from_game"):
        self.id_player = id_player
        self.question = question
        self.ans_a = ans_a
        self.ans_b = ans_b
        self.ans_c = ans_c
        self.ans_correct = self._correct_ans(ans_correct)
        self.season = season
        self.difficulty = difficulty
        self.category = category

    def get_ans_correct(self):
        res = "The correct answer is {} - {}"
        if self.ans_correct == A:
            res = res.format(EMOJIS[A], self.ans_a)
        elif self.ans_correct == B:
            res = res.format(EMOJIS[B], self.ans_b)
        elif self.ans_correct == C:
            res = res.format(EMOJIS[C], self.ans_c)
        else:
            raise RuntimeError("Unknown correct answer")
        return res

    @staticmethod
    def from_dict(dict_mongo):
        res = Card(id_player="", question="",
                 ans_a="", ans_b="", ans_c="", ans_correct=A,
                 season=0, difficulty=EASY, category="from_game")
        res.id_player = dict_mongo["id_player"]
        res.question = dict_mongo["question"]
        res.ans_a = dict_mongo["ans_a"]
        res.ans_b = dict_mongo["ans_b"]
        res.ans_c = dict_mongo["ans_c"]
        res.ans_correct = res._correct_ans(dict_mongo["ans_correct"])
        res.season = int(dict_mongo["season"])
        res.difficulty = int(dict_mongo["difficulty"])
        res.category = dict_mongo["category"]
        return res

    def to_dict(self):
        dict_mongo = {}
        dict_mongo["id_player"] = self.id_player
        dict_mongo["question"] = self.question
        dict_mongo["ans_a"] = self.ans_a
        dict_mongo["ans_b"] = self.ans_b
        dict_mongo["ans_c"] = self.ans_c
        dict_mongo["season"] = self.season
        dict_mongo["difficulty"] = self.difficulty
        dict_mongo["category"] = self.category
        dict_mongo["ans_correct"] = self.ans_correct
        return dict_mongo

    def _correct_ans(self, ans):
        if isinstance(ans, int):
            if ans in EMOJIS:
                return ans
            else:
                raise RuntimeError("Answer \"{}\" not valid. Please enter one of a, b or c".format(ans))
        elif ans == "a":
            return A
        elif ans == "b":
            return B
        elif ans == "c":
            return C
        elif ans == "A":
            return A
        elif ans == "B":
            return B
        elif ans == "C":
            return C
        else:
            raise RuntimeError("Answer \"{}\" not valid. Please enter one of a, b or c".format(ans))

    def dict_embed(self):
        res = copy.deepcopy(self.pack_list_dict)
        res["fields"][0]["value"] = res["fields"][0]["value"].format(self.question)
        tmp = res["fields"][1]["value"]
        res["fields"][1]["value"] = tmp.format(EMOJIS[A], self.ans_a,
                                               EMOJIS[B], self.ans_b,
                                               EMOJIS[C], self.ans_c)
        # res["fields"][1]["value"] = res["fields"][1]["value"].format(self.ans_a)
        # res["fields"][2]["value"] = res["fields"][2]["value"].format(self.ans_b)
        # res["fields"][3]["value"] = res["fields"][3]["value"].format(self.ans_c)
        #
        # res["fields"][1]["name"] = res["fields"][1]["name"].format(emojis[A])
        # res["fields"][2]["name"] = res["fields"][2]["name"].format(emojis[B])
        # res["fields"][3]["name"] = res["fields"][3]["name"].format(emojis[C])
        #
        return res

    def save_mongo(self, database):
        dict_mongo = self.to_dict()
        database.insert(dict_mongo)