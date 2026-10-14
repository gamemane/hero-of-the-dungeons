
import json, os
SAVE_DIR = "dungeons"

def save_game(game):
    os.makedirs(SAVE_DIR, exist_ok=True)
    g = game
    data = {
        "name": g.player.name, "mode": g.mode, "floor": g.floor, "turn": g.turn,
        "player": {
            "x": g.player.x, "y": g.player.y, "hp": g.player.hp, "mana": g.player.mana,
            "level": g.player.level, "xp": g.player.xp, "xp_next": g.player.xp_next,
            "gold": g.player.gold, "tp": g.player.tp,
            "weapon": g.player.weapon, "armor": g.player.armor,
            "inventory": g.player.inventory, "learned": g.player.learned,
            "cooldowns": g.player.cooldowns, "passives": g.player.passives,
            "invisible": g.player.invisible, "hasted": g.player.hasted,
            "atk_bonus": g.player.atk_bonus, "def_bonus": g.player.def_bonus,
        },
        "known": [list(c) for c in g.known],
        "items_on_map": [[x, y, iid] for (x, y), iid in g.items_on_map.items()],
        "traps": [list(t) for t in g.traps],
        "enemies": [{"kind": e.kind, "x": e.x, "y": e.y, "hp": e.hp, "atk": e.atk, "defc": e.defc,
                     "xp": e.xp, "gold": e.gold, "ranged": e.ranged, "boss": e.boss, "fx": e.fx} for e in g.enemies],
        "log": g.log,
    }
    path = os.path.join(SAVE_DIR, "%s_save.json" % g.player.name.replace(" ", "_"))
    with open(path, "w") as f:
        json.dump(data, f)
    return path

def load_game():
    if not os.path.isdir(SAVE_DIR): return None
    saves = [f for f in os.listdir(SAVE_DIR) if f.endswith(".json")]
    if not saves: return None
    path = os.path.join(SAVE_DIR, sorted(saves)[-1])
    with open(path) as f:
        d = json.load(f)
    from core.game import Game
    g = Game(d["name"], d["mode"], d["floor"])
    p = d["player"]
    pl = g.player
    pl.x, pl.y = p["x"], p["y"]
    pl.hp, pl.mana = p["hp"], p["mana"]
    pl.level, pl.xp, pl.xp_next = p["level"], p["xp"], p["xp_next"]
    pl.gold, pl.tp = p["gold"], p["tp"]
    pl.weapon, pl.armor = p["weapon"], p["armor"]
    pl.inventory = p["inventory"]; pl.learned = p["learned"]
    pl.cooldowns = p["cooldowns"]; pl.passives = p["passives"]
    pl.invisible = p.get("invisible", 0); pl.hasted = p.get("hasted", 0)
    pl.atk_bonus = p.get("atk_bonus", 0); pl.def_bonus = p.get("def_bonus", 0)
    pl.recompute()
    g.known = set((c[0], c[1]) for c in d["known"])
    g.items_on_map = {(i[0], i[1]): i[2] for i in d["items_on_map"]}
    g.traps = [tuple(t) for t in d["traps"]]
    g.enemies = []
    from core.entities import Enemy
    for e in d["enemies"]:
        en = Enemy(e["kind"], e["x"], e["y"], e["hp"], e["atk"], e["defc"], e["xp"], e["gold"],
                   ranged=e.get("ranged", False), boss=e.get("boss", False))
        en.fx = e.get("fx", {}) or {}
        g.enemies.append(en)
    g.turn = d.get("turn", 0)
    g.log = d.get("log", [])
    return g

def delete_saves():
    if os.path.isdir(SAVE_DIR):
        for f in os.listdir(SAVE_DIR):
            if f.endswith(".json"):
                os.remove(os.path.join(SAVE_DIR, f))
