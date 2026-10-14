
import pygame
from core.dungeon import MAP_W, MAP_H
from core.spells import SPELLS
from core import talents, craft as craft_mod
from core.items_data import ITEMS, SHOP

PANEL = 320

def soft_init():
    try:
        pygame.init()
        return True
    except Exception:
        return False

class UI:
    def __init__(self, w=1280, h=720):
        self.w, self.h = w, h
        self.screen = None
        self.panel = PANEL
        self.panel_scroll = 0
        self.offset = 0
        self.open_panel = None
        self.shop_tab = "buy"
        self.font = None
        self.small = None
        self.buttons = []
        try:
            pygame.font.init()
            self.font = pygame.font.SysFont("consolas", 15)
            self.small = pygame.font.SysFont("consolas", 13)
        except Exception:
            self.font = self.small = None
    def set_screen(self, screen):
        self.screen = screen
        self.w, self.h = screen.get_size()
    def draw_text(self, surf, text, x, y, color=(220,220,220), size=0):
        f = self.font if size == 0 else (self.small if size == 1 else self.font)
        if f is None: return
        surf.blit(f.render(text, True, color), (x, y))
    def button_row(self, game):
        self.buttons = []
        bw, bh, gap = 145, 34, 10
        x0 = self.w - self.panel + 15
        y0 = self.h * 0.33
        labels = [("spells", "Spells (%d)" % len(game.player.learned)),
                  ("talents", "Talents"),
                  ("items", "Items (%d)" % sum(game.player.inventory.values())),
                  ("craft", "Craft"),
                  ("shop", "Shop")]
        for i, (key, label) in enumerate(labels):
            row, col = i // 2, i % 2
            r = pygame.Rect(x0 + col * (bw + gap), y0 + row * (bh + gap), bw, bh)
            self.buttons.append((key, r))
        return self.buttons
    def draw_buttons(self, game, surf):
        for key, r in self.button_row(game):
            active = self.open_panel == key
            color = (60, 70, 110) if active else (40, 44, 60)
            pygame.draw.rect(surf, color, r, border_radius=6)
            label = dict(spells="Spells", talents="Talents", items="Items", craft="Craft", shop="Shop")[key]
            if key == "spells": label = "Spells (%d)" % len(game.player.learned)
            if key == "items": label = "Items (%d)" % sum(game.player.inventory.values())
            self.draw_text(surf, label, r.x + 12, r.y + 9, (235, 235, 245))
    def draw_info(self, game, surf):
        pygame.draw.rect(surf, (18, 18, 26), (self.w - self.panel, 0, self.panel, self.h))
        p = game.player
        self.draw_text(surf, "%s  Lv %d" % (p.name, p.level), self.w - self.panel + 15, 10, (240, 240, 250), 0)
        self.draw_text(surf, "HP %d/%d" % (p.hp, p.max_hp), self.w - self.panel + 15, 36, (230, 120, 120))
        self.draw_text(surf, "MP %d/%d" % (p.mana, p.max_mana), self.w - self.panel + 15, 54, (120, 150, 230))
        self.draw_text(surf, "ATK %d  DEF %d  CRIT %d%%" % (p.atk, p.defc, p.crit), self.w - self.panel + 15, 74)
        self.draw_text(surf, "Gold %d  TP %d" % (p.gold, p.tp), self.w - self.panel + 15, 92, (220, 190, 90))
        self.draw_text(surf, "Floor %d  Turn %d" % (game.floor, game.turn), self.w - self.panel + 15, 110)
        self.draw_buttons(game, surf)
        y = self.h * 0.33 + 90
        for line in ["1-9: cast spell", "Arrows/WASD: move", "Click cell: walk", "O/T/I/C/B: panels", "F5 save  F9 load", "R restart"]:
            self.draw_text(surf, line, self.w - self.panel + 15, y, (150, 150, 165), 1)
            y += 16
        y += 6
        for line in game.log[-10:]:
            self.draw_text(surf, line, self.w - self.panel + 15, y, (170, 175, 185), 1)
            y += 16
    def draw_map(self, game, surf):
        mw = self.w - self.panel
        tile = min(mw // MAP_W, self.h // MAP_H)
        ox = (mw - tile * MAP_W) // 2
        oy = (self.h - tile * MAP_H) // 2
        for (x, y) in game.known:
            if game.dungeon.is_wall(x, y):
                color = (28, 28, 38)
            else:
                color = (64, 64, 84)
            pygame.draw.rect(surf, color, (ox + x * tile, oy + y * tile, tile, tile))
        for e in game.enemies:
            if (e.x, e.y) in game.known:
                c = (200, 60, 60) if e.boss else (190, 120, 60)
                pygame.draw.rect(surf, c, (ox + e.x * tile, oy + e.y * tile, tile, tile))
        sx, sy = game.dungeon.stairs
        if (sx, sy) in game.known:
            pygame.draw.rect(surf, (120, 220, 120), (ox + sx * tile, oy + sy * tile, tile, tile))
        pygame.draw.rect(surf, (90, 200, 255), (ox + game.player.x * tile, oy + game.player.y * tile, tile, tile))
        self.tile, self.ox, self.oy = tile, ox, oy
    def draw_minimap(self, game, surf):
        cell = 3
        mw = self.w - self.panel
        for (x, y) in game.known:
            c = (28, 28, 38) if game.dungeon.is_wall(x, y) else (60, 60, 78)
            pygame.draw.rect(surf, c, (6 + x * cell, 6 + y * cell, cell, cell))
        sx, sy = game.dungeon.stairs
        if (sx, sy) in game.known:
            pygame.draw.rect(surf, (120, 220, 120), (6 + sx * cell, 6 + sy * cell, cell, cell))
        for e in game.enemies:
            if (e.x, e.y) in game.known:
                c = (200, 60, 60) if e.boss else (190, 120, 60)
                pygame.draw.rect(surf, c, (6 + e.x * cell, 6 + e.y * cell, cell, cell))
    def draw_panel_frame(self, surf, title):
        r = pygame.Rect(self.w - self.panel, 0, self.panel, self.h)
        pygame.draw.rect(surf, (24, 24, 34), r)
        self.draw_text(surf, title, r.x + 15, 10, (240, 240, 250), 0)
        self.draw_text(surf, "Esc to close, mouse wheel to scroll", r.x + 15, self.h - 24, (130, 130, 145), 1)
    def panel_lines(self, game):
        key = self.open_panel
        p = game.player
        lines = []
        if key == "talents":
            for tid, t in talents.PASSIVES.items():
                rank = p.passives.get(tid, 0)
                lines.append(("passive", tid, "%s  r%d/%d  gold %d" % (t["name"], rank, t["max"], t["cost"] * (rank + 1)), t["desc"]))
            for ab in talents.ABILITIES:
                owned = ab["spell"] in p.learned
                lines.append(("ability", ab["id"], "%s  gold %d %s" % (ab["name"], ab["cost"], "[owned]" if owned else ""), SPELLS[ab["spell"]]["desc"]))
        elif key == "spells":
            if not p.learned:
                lines.append(("none", None, "No spells yet - buy in Talents", ""))
            for sid in p.learned:
                sp = SPELLS[sid]
                cd = p.cooldowns.get(sid, 0)
                lines.append(("spell", sid, "%s  mana %d  cd %d%s" % (sp["name"], sp["mana"], sp["cd"], "  [CD %d]" % cd if cd else ""), sp["desc"]))
        elif key == "items":
            if p.weapon: lines.append(("equip", p.weapon, "%s [E]  %s" % (ITEMS[p.weapon]["name"], ITEMS[p.weapon]["desc"]), ""))
            if p.armor: lines.append(("equip", p.armor, "%s [E]  %s" % (ITEMS[p.armor]["name"], ITEMS[p.armor]["desc"]), ""))
            for iid, n in p.inventory.items():
                it = ITEMS.get(iid)
                if not it: continue
                lines.append(("item", iid, "%s x%d" % (it["name"], n), it["desc"]))
        elif key == "craft":
            for r in craft_mod.RECIPES:
                mats = ", ".join("%s %d/%d" % (m, p.inventory.get(m, 0), n) for m, n in r["mats"].items())
                can = all(p.inventory.get(m, 0) >= n for m, n in r["mats"].items())
                lines.append(("recipe", r["id"], "%s%s" % (r["name"], "  [OK]" if can else ""), mats))
        elif key == "shop":
            lines.append(("shoptab", "buy", "[BUY]", ""))
            lines.append(("shoptab", "sell", "[SELL materials]", ""))
            if self.shop_tab == "buy":
                for iid in SHOP:
                    it = ITEMS[iid]
                    lines.append(("buy", iid, "%s  %d gold" % (it["name"], it.get("price", 0)), it["desc"]))
            else:
                for iid in p.inventory:
                    it = ITEMS.get(iid)
                    if not it: continue
                    price = 4 if it["type"] == "material" else it.get("price", 10) // 2
                    lines.append(("sell", iid, "%s x%d  sell %d" % (it["name"], p.inventory[iid], price), ""))
        return lines
    def draw_panel(self, game, surf):
        self.draw_panel_frame(surf, self.open_panel.capitalize())
        lines = self.panel_lines(game)
        visible = (self.h - 60) // 22
        max_off = max(0, len(lines) - visible)
        self.offset = max(0, min(self.offset, max_off))
        r = pygame.Rect(self.w - self.panel, 0, self.panel, self.h)
        y = 40
        self.panel_rows = []
        for i in range(self.offset, min(len(lines), self.offset + visible)):
            kind, arg, text, desc = lines[i]
            rect = pygame.Rect(r.x + 10, y, r.width - 30, 22)
            self.panel_rows.append((rect, kind, arg))
            self.draw_text(surf, text, rect.x, y, (225, 225, 235), 1)
            if desc:
                self.draw_text(surf, desc, rect.x + 8, y + 13, (140, 140, 155), 1)
            y += 22
        if max_off > 0:
            sb = pygame.Rect(r.right - 8, 40, 5, self.h - 70)
            pygame.draw.rect(surf, (50, 50, 65), sb)
            frac = self.offset / max_off
            kh = max(30, int(sb.height * visible / len(lines)))
            ky = sb.y + int((sb.height - kh) * frac)
            pygame.draw.rect(surf, (120, 120, 150), (sb.x, ky, 5, kh))
    def draw(self, game, surf):
        surf.fill((12, 12, 18))
        self.draw_map(game, surf)
        self.draw_minimap(game, surf)
        if self.open_panel:
            self.draw_panel(game, surf)
        else:
            self.draw_info(game, surf)
    def cell_at(self, pos):
        if not hasattr(self, "tile") or self.tile is None:
            return None
        mw = self.w - self.panel
        tile = self.tile
        ox = (mw - tile * MAP_W) // 2
        oy = (self.h - tile * MAP_H) // 2
        x = (pos[0] - ox) // tile
        y = (pos[1] - oy) // tile
        if 0 <= x < MAP_W and 0 <= y < MAP_H:
            return (int(x), int(y))
        return None
    def click(self, game, pos):
        bx = self.w - self.panel
        if self.open_panel:
            for rect, kind, arg in getattr(self, "panel_rows", []):
                if rect.collidepoint(pos):
                    if kind == "passive": return game.buy_talent(arg)
                    if kind == "ability": return game.buy_talent(arg)
                    if kind == "spell":
                        sp = SPELLS[arg]
                        if sp["type"] == "self":
                            return game.cast(arg)
                        game.pending_spell = arg
                        return "Select target..."
                    if kind == "item": return game.use_item(arg)
                    if kind == "recipe": return game.craft_item(arg)
                    if kind == "buy": return game.shop_buy(arg)
                    if kind == "sell": return game.shop_sell(arg)
                    if kind == "shoptab":
                        self.shop_tab = "sell" if arg == "sell" else "buy"
                        return None
            return None
        for key, r in self.buttons:
            if r.collidepoint(pos):
                self.open_panel = None if self.open_panel == key else key
                self.offset = 0
                return None
        if pos[0] < bx:
            c = self.cell_at(pos)
            if c: game.click_move(*c)
        return None
    def scroll(self, dy):
        if self.open_panel:
            self.offset = max(0, self.offset + (1 if dy > 0 else -1))
    def draw_name_screen(self, surf, name):
        surf.fill((14, 14, 20))
        f = pygame.font.SysFont("consolas", 30)
        t = f.render("Enter your name:", True, (240, 240, 250))
        surf.blit(t, (surf.get_width() // 2 - t.get_width() // 2, surf.get_height() // 2 - 80))
        r = pygame.Rect(0, 0, 320, 44)
        r.center = (surf.get_width() // 2, surf.get_height() // 2)
        pygame.draw.rect(surf, (40, 44, 60), r, border_radius=6)
        if self.font:
            surf.blit(self.font.render(name + "_", True, (240, 240, 250)), (r.x + 12, r.y + 13))
        h = pygame.font.SysFont("consolas", 15)
        t2 = h.render("Press Enter to continue", True, (150, 150, 165))
        surf.blit(t2, (surf.get_width() // 2 - t2.get_width() // 2, surf.get_height() // 2 + 60))
    def draw_mode_screen(self, surf, idx):
        surf.fill((14, 14, 20))
        f = pygame.font.SysFont("consolas", 30)
        t = f.render("Choose difficulty:", True, (240, 240, 250))
        surf.blit(t, (surf.get_width() // 2 - t.get_width() // 2, surf.get_height() // 2 - 120))
        modes = ["normal", "medium", "hardcore", "fog"]
        s = pygame.font.SysFont("consolas", 22)
        for i, m in enumerate(modes):
            color = (120, 200, 255) if i == idx else (160, 160, 175)
            t2 = s.render(m.upper() + ("  <- harder enemies, more of them" if m in ("medium", "hardcore") else "  <- vision radius 4" if m == "fog" else ""), True, color)
            surf.blit(t2, (surf.get_width() // 2 - t2.get_width() // 2, surf.get_height() // 2 - 40 + i * 36))
    def draw_death(self, game, surf):
        surf.fill((20, 8, 8))
        f = pygame.font.SysFont("consolas", 40)
        t = f.render("YOU DIED", True, (230, 80, 80))
        surf.blit(t, (surf.get_width() // 2 - t.get_width() // 2, surf.get_height() // 2 - 60))
        s = pygame.font.SysFont("consolas", 20)
        for i, line in enumerate(["Floor %d, turn %d, level %d" % (game.floor, game.turn, game.player.level),
                                  "Press R to restart"]):
            t2 = s.render(line, True, (220, 220, 230))
            surf.blit(t2, (surf.get_width() // 2 - t2.get_width() // 2, surf.get_height() // 2 + 10 + i * 28))
