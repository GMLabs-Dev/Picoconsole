import config as cfg
from game_base import Game, EXIT
from widgets import draw_wrapped


def make_coming_soon(title, description=""):
    class ComingSoon(Game):
        def update(self, display, buttons, dt_ms):
            if buttons.pressed("A") or buttons.pressed("B") or buttons.pressed("MENU"):
                return EXIT
            display.fill(cfg.COLOR_BG)
            display.text(self.name, 16, 90, cfg.COLOR_HIGHLIGHT)
            draw_wrapped(display, "Coming soon - not ported yet.", 16, 116,
                        max_chars=(cfg.SCREEN_W - 32) // cfg.FONT_W,
                        color=cfg.COLOR_GRAY)
            display.text("Press any button to go back", 16,
                         cfg.SCREEN_H - 30, cfg.COLOR_DARK_GRAY)
            display.show()
            return None

    ComingSoon.name = title
    ComingSoon.description = description or "Not yet"
    return ComingSoon
