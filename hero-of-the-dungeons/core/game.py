
import random
from core.dungeon import Dungeon, MAP_W, MAP_H, bfs_path
from core.entities import Player, Enemy
from core.spells import SPELLS
from core import talents
from core import craft as craft_mod
from core.items_data import ITEMS, SHOP

MODE_MULT = {"normal": (1.0, 1.0), "medium": (1.4, 1.35), "hardcore": (1.8, 1.6), "fog": (1.2, 1.0)}
ENEMY_TYPES = ["rat", "goblin", "orc", "skeleton", "dark_archer", "cultist_mage"]
E_STATS = {
    "rat": (8, 3, 0, 5, 2), "goblin": (14, 5, 1, 9, 4), "orc": (24, 8, 2, 16, 8),
    "skeleton": (18, 7, 1, 14, 7), "dark_archer": (14, 6, 0, 13, 8), "cultist_mage": (12, 9, 0, 15, 10),
}
MATERIALS = ["iron", "crystal", "herb", "coal", "shadow_essence", "hide"]

class Game:
    def __init__(self, name, mode="normal", floor=1):
        self.name = name or "Hero"
        self.mode = mode
        self.floor = floor
        self.turn = 0
        self.log = []
        self.dungeon = Dungeon(floor, mode)
        self.player = Player(self.name, mode)
        self.player.x, self.player.y = self.dungeon.start
        self.enemies = []
        self.items_on_map = {}
        self.traps = []
        self.known = set()
        self.pending_spell = None
        self.game_over = False
        self.spawn_all()
        self.reveal()
        self.add_log("You descend into the dungeon. Floor %d." % floor)
    def spawn_all(self):
        dm, cm = MODE_MULT[self.mode]
        n = int((10 + self.floor * 3) * cm)
        cells = [c for c in self.dungeon.free_cells()
                 if abs(c[0]-self.player.x) + abs(c[1]-self.player.y) > 8]
        random.shuffle(cells)
        boss = self.floor % 5 == 0
        for i in range(n):
            if not cells: break
            x, y = cells.pop()
            kind = random.choice(ENEMY_TYPES)
            hp, atk, dfc, xp, gold = E_STATS[kind]
            scale = 1 + (self.floor - 1) * 0.25
            hp, atk = int(hp * scale * dm), int(atk * scale * dm)
            self.enemies.append(Enemy(kind, x, y, hp, atk, dfc, int(xp*scale), int(gold*scale),
                                      ranged=(kind in ("dark_archer", "cultist_mage"))))
        if boss and cells:
            x, y = cells.pop()
            bhp = int(150 * dm * (1 + self.floor * 0.15))
            self.enemies.append(Enemy("dungeon_lord", x, y, bhp, int(12*dm), 5, 80, 120, boss=True))
        for _ in range(6):
            if cells:
                x, y = cells.pop()
                iid = random.choice(["potion_minor", "potion_health", "potion_mana", "iron_sword",
                                     "chain_mail", "leather_armor", "iron", "herb", "crystal", "coal",
                                     "shadow_essence", "hide", "gold_pile"])
                self.items_on_map[(x, y)] = iid
        for _ in range(3 + self.floor):
            if cells:
                x, y = cells.pop()
                self.traps.append((x, y, 5 + self.floor * 2))
    def reveal(self):
        for c in self.dungeon.reveal(self.player.x, self.player.y, self.player.vision):
            self.known.add(c)
    def add_log(self, msg):
        self.log.append(msg)
        if len(self.log) > 40: self.log.pop(0)
    def enemy_at(self, x, y):
        for e in self.enemies:
            if e.x == x and e.y == y: return e
        return None
    def dist(self, a, b):
        return max(abs(a[0]-b[0]), abs(a[1]-b[1]))
    def try_move(self, dx, dy):
        if self.game_over: return
        steps = 2 if self.player.hasted > 0 else 1
        for _ in range(steps):
            nx, ny = self.player.x + dx, self.player.y + dy
            if self.dungeon.is_wall(nx, ny): continue
            e = self.enemy_at(nx, ny)
            if e:
                self.attack(e); self.end_turn(); return
            self.player.x, self.player.y = nx, ny
            self.check_trap()
            self.check_pickup()
            if (self.player.x, self.player.y) == self.dungeon.stairs:
                self.descend(); return
        self.end_turn()
    def check_trap(self):
        x, y = self.player.x, self.player.y
        for t in self.traps[:]:
            if t[0] == x and t[1] == y:
                dmg = t[2]
                self.player.hp -= dmg
                self.add_log("Spikes! You take %d damage." % dmg)
                self.traps.remove(t)
                if self.player.hp <= 0: self.die()
    def check_pickup(self):
        key = (self.player.x, self.player.y)
        iid = self.items_on_map.pop(key, None)
        if not iid: return
        if iid == "gold_pile":
            g = random.randint(10, 30)
            self.player.gold += int(g * self.player.gold_mult)
            self.add_log("Picked up %d gold." % g)
        elif ITEMS[iid]["type"] == "potion":
            self.player.inventory[iid] = self.player.inventory.get(iid, 0) + 1
            self.add_log("Picked up %s." % ITEMS[iid]["name"])
        else:
            self.apply_item(iid)
    def apply_item(self, iid):
        it = ITEMS[iid]
        if it["type"] == "weapon":
            cur = self.player.weapon
            cur_atk = ITEMS[cur]["atk"] if cur else 0
            if it["atk"] > cur_atk:
                if cur: self.player.inventory[cur] = self.player.inventory.get(cur, 0) + 1
                self.player.weapon = iid
                self.player.atk_bonus = it["atk"]
                self.player.recompute()
                self.add_log("Equipped %s." % it["name"])
                return
            self.player.inventory[iid] = self.player.inventory.get(iid, 0) + 1
            self.add_log("Picked up %s." % it["name"])
        elif it["type"] == "armor":
            cur = self.player.armor
            cur_def = ITEMS[cur]["def"] if cur else 0
            if it["def"] > cur_def:
                if cur: self.player.inventory[cur] = self.player.inventory.get(cur, 0) + 1
                self.player.armor = iid
                self.player.def_bonus = it["def"]
                self.player.recompute()
                self.add_log("Equipped %s." % it["name"])
                return
            self.player.inventory[iid] = self.player.inventory.get(iid, 0) + 1
            self.add_log("Picked up %s." % it["name"])
        else:
            self.player.inventory[iid] = self.player.inventory.get(iid, 0) + 1
            self.add_log("Picked up %s." % it["name"])
    def attack(self, e):
        atk = self.player.atk
        crit = random.random() * 100 < self.player.crit
        dmg = atk * (2 if crit else 1) - e.defc
        dmg = max(1, dmg)
        e.hp -= dmg
        msg = "You hit %s for %d%s." % (e.info(), dmg, " (crit!)" if crit else "")
        self.add_log(msg)
        if e.hp <= 0:
            self.kill_enemy(e)
    def kill_enemy(self, e):
        self.enemies.remove(e)
        g = int(e.gold * self.player.gold_mult)
        self.player.gold += g
        self.player.gain_xp(e.xp)
        self.add_log("%s died! +%d XP, +%d gold." % (e.info(), e.xp, g))
        if e.boss:
            reward = random.choice(["rune_blade", "rune_armor", "dragon_mail", "warhammer"])
            self.items_on_map[(e.x, e.y)] = reward
            self.add_log("The boss dropped %s!" % ITEMS[reward]["name"])
    def ranged_attack(self, e):
        dmg = max(1, e.atk - self.player.defc)
        self.player.hp -= dmg
        self.add_log("%s shoots you for %d." % (e.info(), dmg))
        if self.player.hp <= 0: self.die()
    def enemy_turn(self):
        if self.game_over: return
        p = self.player
        for e in list(self.enemies):
            if self.game_over: return
            if e.slowed > 0:
                e.slowed -= 1
                if self.dist((e.x, e.y), (p.x, p.y)) <= 1:
                    continue
            if p.invisible > 0: continue
            d = self.dist((e.x, e.y), (p.x, p.y))
            if e.ranged and d <= 5:
                self.ranged_attack(e)
            elif d <= 1:
                dmg = max(1, e.atk - p.defc)
                p.hp -= dmg
                self.add_log("%s hits you for %d." % (e.info(), dmg))
                if p.hp <= 0: self.die()
            elif d <= 6:
                path = bfs_path(self.dungeon, (e.x, e.y), (p.x, p.y), self.known)
                if path and len(path) > 1:
                    e.x, e.y = path[1]
                elif path:
                    pass
    def end_turn(self, skip_cd=False):
        if self.game_over: return
        self.turn += 1
        p = self.player
        p.mana = min(p.max_mana, p.mana + 1 + p.regen)
        if p.regen: p.hp = min(p.max_hp, p.hp + p.regen)
        if p.invisible > 0: p.invisible -= 1
        if p.hasted > 0: p.hasted -= 1
        if not skip_cd:
            for k in list(p.cooldowns):
                if p.cooldowns[k] > 0: p.cooldowns[k] -= 1
        for e in self.enemies:
            fx = e.fx
            if fx.get("burn", 0) > 0:
                e.hp -= fx["burn"]; fx["burn"] -= 1
                if fx["burn"] == 0: del fx["burn"]
                if e.hp <= 0:
                    self.add_log("%s burned to death." % e.info()); self.kill_enemy(e); continue
            if fx.get("poison", 0) > 0:
                e.hp -= 3; fx["poison"] -= 1
                if fx["poison"] == 0: del fx["poison"]
                if e.hp <= 0:
                    self.add_log("%s died from poison." % e.info()); self.kill_enemy(e); continue
            if fx.get("curse", 0) > 0: fx["curse"] -= 1
        self.enemy_turn()
        self.reveal()
    def descend(self):
        self.floor += 1
        self.dungeon = Dungeon(self.floor, self.mode)
        self.player.x, self.player.y = self.dungeon.start
        self.known = set()
        self.enemies = []
        self.items_on_map = {}
        self.traps = []
        self.pending_spell = None
        self.spawn_all()
        self.reveal()
        self.add_log("You descend to floor %d." % self.floor)
    def die(self):
        self.player.hp = 0
        self.game_over = True
        self.add_log("You died on floor %d. Game over." % self.floor)
        if self.mode == "hardcore":
            self.add_log("Hardcore: saves are erased.")
    def cast(self, spell_id, tx=None, ty=None):
        p = self.player
        if spell_id not in p.learned:
            return "Cannot cast: not learned."
        if p.cooldowns.get(spell_id, 0) > 0:
            return "Cannot cast: cooldown %d." % p.cooldowns[spell_id]
        sp = SPELLS[spell_id]
        if p.mana < sp["mana"]:
            return "Not enough mana."
        p.mana -= sp["mana"]
        p.cooldowns[spell_id] = sp["cd"]
        if sp["type"] == "self":
            if sp.get("heal"): p.hp = min(p.max_hp, p.hp + sp["heal"])
            if sp.get("mana"): p.mana = min(p.max_mana, p.mana + sp["mana"])
            if sp.get("buff_def"): p.def_bonus += sp["buff_def"]; p.recompute()
            if sp.get("buff_atk"): p.atk_bonus += sp["buff_atk"]; p.recompute()
            if sp.get("invis"): p.invisible = sp["invis"]
            if sp.get("haste"): p.hasted = sp["haste"]
            self.add_log("You cast %s." % sp["name"])
            self.end_turn(skip_cd=True)
            return "Cast %s." % sp["name"]
        targets = []
        if sp["type"] == "target":
            e = self.enemy_at(tx, ty) if tx is not None else None
            if e is None: return "No target there."
            targets = [e]
        else:
            rng = 4
            for e in self.enemies:
                if self.dist((e.x, e.y), (p.x, p.y)) <= rng:
                    targets.append(e)
            if sp.get("targets"):
                targets = sorted(targets, key=lambda e: self.dist((e.x, e.y), (p.x, p.y)))[:sp["targets"]]
        if not targets: return "No enemies in range."
        for e in targets:
            dmg = max(1, sp["dmg"] - (0 if sp.get("pierce") else e.defc))
            e.hp -= dmg
            self.add_log("%s hits %s for %d." % (sp["name"], e.info(), dmg))
            if sp.get("burn"): e.fx["burn"] = e.fx.get("burn", 0) + sp["burn"]
            if sp.get("poison"): e.fx["poison"] = e.fx.get("poison", 0) + sp["poison"]
            if sp.get("slow"): e.slowed += sp["slow"]
            if sp.get("curse"): e.fx["curse"] = 3
            if sp.get("drain"):
                p.hp = min(p.max_hp, p.hp + dmg // 2)
            if e.hp <= 0: self.kill_enemy(e)
        self.end_turn(skip_cd=True)
        return "Cast %s." % sp["name"]
    def buy_talent(self, tid):
        p = self.player
        if tid in talents.PASSIVES:
            t = talents.PASSIVES[tid]
            rank = p.passives.get(tid, 0)
            if rank >= t["max"]: return "Already maxed."
            cost = t["cost"] * (rank + 1)
            if p.gold < cost: return "Not enough gold."
            if p.tp < 1: return "Not enough talent points."
            p.gold -= cost; p.tp -= 1
            p.passives[tid] = rank + 1
            p.recompute()
            self.add_log("Talent %s rank %d." % (t["name"], rank + 1))
            return "Learned %s rank %d." % (t["name"], rank + 1)
        for ab in talents.ABILITIES:
            if ab["id"] == tid:
                if ab["spell"] in p.learned: return "Already learned."
                if p.gold < ab["cost"]: return "Not enough gold."
                if p.tp < 1: return "Not enough talent points."
                p.gold -= ab["cost"]; p.tp -= 1
                p.learned.append(ab["spell"])
                self.add_log("You learned %s!" % SPELLS[ab["spell"]]["name"])
                return "Learned %s." % SPELLS[ab["spell"]]["name"]
        return "Unknown talent."
    def use_item(self, iid):
        p = self.player
        if p.inventory.get(iid, 0) <= 0: return "No such item."
        it = ITEMS[iid]
        if it["type"] == "potion":
            if it.get("heal"): p.hp = min(p.max_hp, p.hp + it["heal"])
            if it.get("mana"): p.mana = min(p.max_mana, p.mana + it["mana"])
            p.inventory[iid] -= 1
            if p.inventory[iid] == 0: del p.inventory[iid]
            self.add_log("Used %s." % it["name"])
            self.end_turn()
            return "Used %s." % it["name"]
        if it["type"] == "bomb":
            for e in list(self.enemies):
                if self.dist((e.x, e.y), (p.x, p.y)) <= 3:
                    e.hp -= it["dmg"]
                    e.fx["burn"] = e.fx.get("burn", 0) + 2
                    if e.hp <= 0: self.kill_enemy(e)
            p.inventory[iid] -= 1
            if p.inventory[iid] == 0: del p.inventory[iid]
            self.add_log("Fire Bomb explodes!")
            self.end_turn()
            return "Fire Bomb explodes!"
        if it["type"] == "weapon":
            cur = p.weapon
            if cur: p.inventory[cur] = p.inventory.get(cur, 0) + 1
            p.weapon = iid
            p.inventory[iid] -= 1
            if p.inventory[iid] == 0: del p.inventory[iid]
            p.atk_bonus = it["atk"]; p.recompute()
            self.add_log("Equipped %s." % it["name"])
            return "Equipped %s." % it["name"]
        if it["type"] == "armor":
            cur = p.armor
            if cur: p.inventory[cur] = p.inventory.get(cur, 0) + 1
            p.armor = iid
            p.inventory[iid] -= 1
            if p.inventory[iid] == 0: del p.inventory[iid]
            p.def_bonus = it["def"]; p.recompute()
            self.add_log("Equipped %s." % it["name"])
            return "Equipped %s." % it["name"]
        return "Cannot use."
    def craft_item(self, rid):
        for r in craft_mod.RECIPES:
            if r["id"] == rid:
                for m, n in r["mats"].items():
                    if self.player.inventory.get(m, 0) < n:
                        return "Not enough materials."
                for m, n in r["mats"].items():
                    self.player.inventory[m] -= n
                    if self.player.inventory[m] == 0: del self.player.inventory[m]
                out = r["out"]
                if out.startswith("learn:"):
                    sp = out.split(":")[1]
                    if sp in self.player.learned:
                        for m, n in r["mats"].items():
                            self.player.inventory[m] = self.player.inventory.get(m, 0) + n
                        return "Already learned."
                    self.player.learned.append(sp)
                    self.add_log("Crafted %s! Learned %s." % (r["name"], SPELLS[sp]["name"]))
                    return "Learned %s!" % SPELLS[sp]["name"]
                self.player.inventory[out] = self.player.inventory.get(out, 0) + 1
                self.add_log("Crafted %s." % r["name"])
                return "Crafted %s." % r["name"]
        return "Unknown recipe."
    def shop_buy(self, iid):
        it = ITEMS.get(iid)
        if not it or iid not in SHOP: return "Not sold here."
        if self.player.gold < it.get("price", 999): return "Not enough gold."
        self.player.gold -= it["price"]
        if it["type"] in ("weapon", "armor"):
            self.player.inventory[iid] = self.player.inventory.get(iid, 0) + 1
        else:
            self.player.inventory[iid] = self.player.inventory.get(iid, 0) + 1
        self.add_log("Bought %s." % it["name"])
        return "Bought %s." % it["name"]
    def shop_sell(self, iid):
        it = ITEMS.get(iid)
        if not it: return "No such item."
        if self.player.inventory.get(iid, 0) <= 0: return "Nothing to sell."
        if it["type"] == "material":
            price = 4
        else:
            price = it.get("price", 10) // 2
        self.player.inventory[iid] -= 1
        if self.player.inventory[iid] == 0: del self.player.inventory[iid]
        self.player.gold += price
        self.add_log("Sold %s for %d." % (it["name"], price))
        return "Sold %s for %d." % (it["name"], price)
    def click_move(self, tx, ty):
        if (tx, ty) not in self.known or self.dungeon.is_wall(tx, ty):
            return
        if self.pending_spell:
            res = self.cast(self.pending_spell, tx, ty)
            self.pending_spell = None
            if res and not res.startswith("Cast"):
                self.add_log(res)
            return
        path = bfs_path(self.dungeon, (self.player.x, self.player.y), (tx, ty), self.known)
        if path:
            for step in path[:-1]:
                self.player.x, self.player.y = step
                self.check_trap()
                self.check_pickup()
                if self.game_over: return
                if (self.player.x, self.player.y) == self.dungeon.stairs:
                    self.descend(); return
            self.end_turn()
