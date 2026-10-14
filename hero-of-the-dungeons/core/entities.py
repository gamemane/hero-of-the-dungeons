
from core.dungeon import Dungeon

class Player:
    def __init__(self, name, mode="normal"):
        self.name = name or "Hero"
        self.x, self.y = 0, 0
        self.hp, self.mana = 100, 30
        self.level, self.xp, self.xp_next = 1, 0, 20
        self.gold, self.tp = 30, 0
        self.weapon, self.armor = None, None
        self.inventory = {}
        self.learned = []
        self.cooldowns = {}
        self.passives = {}
        self.mode = mode
        self.mode_vision = {"normal": 8, "medium": 7, "hardcore": 6, "fog": 4}[mode]
        self.invisible = 0
        self.hasted = 0
        self.atk_bonus, self.def_bonus = 0, 0
        self.recompute()
    def recompute(self):
        def p(k):
            return self.passives.get(k, 0)
        max_hp = 100 + 15*p("vitality")
        max_mana = 30 + 10*p("clarity")
        self.max_hp, self.max_mana = max_hp, max_mana
        self.atk = 4 + 2*p("power") + self.atk_bonus
        self.defc = 1*p("toughness") + self.def_bonus
        self.crit = 5 + 5*p("precision")
        self.regen = p("regen")
        self.gold_mult = 1 + 0.2*p("fortune")
        self.base_vision = 8 + p("swiftness")
        self.vision = min(self.mode_vision, self.base_vision)
        self.hp = min(self.hp, self.max_hp)
        self.mana = min(self.mana, self.max_mana)
    def known_spells(self):
        return list(self.learned)
    def gain_xp(self, n):
        self.xp += n
        while self.xp >= self.xp_next:
            self.xp -= self.xp_next
            self.level += 1
            self.xp_next = int(self.xp_next * 1.5)
            self.tp += 1
            self.max_hp += 5
            self.hp += 5

class Enemy:
    def __init__(self, kind, x, y, hp, atk, defc, xp, gold, ranged=False, boss=False):
        self.kind, self.x, self.y = kind, x, y
        self.hp, self.max_hp, self.atk, self.defc = hp, hp, atk, defc
        self.xp, self.gold, self.ranged, self.boss = xp, gold, ranged, boss
        self.fx = {}
        self.slowed = 0
    def info(self):
        s = self.kind
        if self.boss: s += " (BOSS)"
        return s
