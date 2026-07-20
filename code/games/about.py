import config as cfg
from game_base import Game, EXIT
from widgets import draw_wrapped


class About(Game):
    name = "About"
    description = "Credits & build info"

    def on_enter(self, display, buttons):
        self._blink = 0

    def update(self, display, buttons, dt_ms):
        if buttons.pressed("A") or buttons.pressed("B") or buttons.pressed("MENU"):
            return EXIT

        self._blink = (self._blink + dt_ms) % 1000

        display.fill(cfg.COLOR_BG)
        display.text("PICO CONSOLE", 16, 20, cfg.COLOR_HIGHLIGHT)
        display.hline(16, 34, cfg.SCREEN_W - 32, cfg.COLOR_DARK_GRAY)

        y = draw_wrapped(
            display,
            "A handheld built on a Raspberry Pi Pico", 
            16, 50, max_chars=(cfg.SCREEN_W - 32) // cfg.FONT_W,
            color=cfg.COLOR_WHITE,
        )
        y = draw_wrapped(display, "Made by Gustaw M.", 16, y + 10,
                        max_chars=(cfg.SCREEN_W - 32) // cfg.FONT_W,
                        color=cfg.COLOR_CYAN)

        if self._blink < 500:
            display.text("Press any button to go back", 16,
                         cfg.SCREEN_H - 30, cfg.COLOR_GRAY)

        display.show()
        return None
