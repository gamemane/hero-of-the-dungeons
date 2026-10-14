
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pygame
from core.game import Game
from core.ui import UI
from core import save as save_mod

def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
    pygame.display.set_caption("Hero of the Dungeons")
    ui = UI()
    ui.set_screen(screen)
    clock = pygame.time.Clock()
    state = "name"
    name = ""
    mode_idx = 0
    game = None
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); return
            elif ev.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(ev.size, pygame.RESIZABLE)
                ui.set_screen(screen)
            elif ev.type == pygame.KEYDOWN:
                if state == "name":
                    if ev.key == pygame.K_RETURN and name.strip():
                        state = "mode"
                    elif ev.key == pygame.K_BACKSPACE:
                        name = name[:-1]
                    elif ev.unicode.isprintable() and len(name) < 16:
                        name += ev.unicode
                elif state == "mode":
                    if ev.key in (pygame.K_UP, pygame.K_w): mode_idx = (mode_idx - 1) % 4
                    elif ev.key in (pygame.K_DOWN, pygame.K_s): mode_idx = (mode_idx + 1) % 4
                    elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                        game = Game(name, ["normal", "medium", "hardcore", "fog"][mode_idx])
                        state = "play"
                elif state == "play" and game:
                    if game.game_over:
                        if ev.key == pygame.K_r:
                            if game.mode == "hardcore":
                                save_mod.delete_saves()
                            game = None; state = "name"; name = ""
                    else:
                        if ev.key == pygame.K_ESCAPE:
                            ui.open_panel = None; ui.offset = 0
                        elif ev.key == pygame.K_o:
                            ui.open_panel = None if ui.open_panel == "spells" else "spells"; ui.offset = 0
                        elif ev.key == pygame.K_t:
                            ui.open_panel = None if ui.open_panel == "talents" else "talents"; ui.offset = 0
                        elif ev.key == pygame.K_i:
                            ui.open_panel = None if ui.open_panel == "items" else "items"; ui.offset = 0
                        elif ev.key == pygame.K_c:
                            ui.open_panel = None if ui.open_panel == "craft" else "craft"; ui.offset = 0
                        elif ev.key == pygame.K_b:
                            ui.open_panel = None if ui.open_panel == "shop" else "shop"; ui.offset = 0
                        elif ev.key == pygame.K_F5:
                            save_mod.save_game(game)
                            game.add_log("Game saved.")
                        elif ev.key == pygame.K_F9:
                            g2 = save_mod.load_game()
                            if g2: game = g2; game.add_log("Game loaded.")
                        elif ev.key in (pygame.K_UP, pygame.K_w): game.try_move(0, -1)
                        elif ev.key in (pygame.K_DOWN, pygame.K_s): game.try_move(0, 1)
                        elif ev.key in (pygame.K_LEFT, pygame.K_a): game.try_move(-1, 0)
                        elif ev.key in (pygame.K_RIGHT, pygame.K_d): game.try_move(1, 0)
                        elif pygame.K_1 <= ev.key <= pygame.K_9:
                            idx = ev.key - pygame.K_1
                            learned = game.player.learned
                            if idx < len(learned):
                                sp = learned[idx]
                                from core.spells import SPELLS
                                if SPELLS[sp]["type"] == "self":
                                    game.cast(sp)
                                else:
                                    game.pending_spell = sp
                                    game.add_log("Select target for %s." % SPELLS[sp]["name"])
            elif ev.type == pygame.MOUSEWHEEL and state == "play":
                ui.scroll(ev.y)
            elif ev.type == pygame.MOUSEBUTTONDOWN and state == "play" and ev.button == 1 and game:
                ui.click(game, ev.pos)
        if state == "name":
            ui.draw_name_screen(screen, name)
        elif state == "mode":
            ui.draw_mode_screen(screen, mode_idx)
        elif game:
            if game.game_over:
                ui.draw_death(game, screen)
            else:
                ui.draw(game, screen)
        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    main()
