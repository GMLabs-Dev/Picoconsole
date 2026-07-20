import config as cfg
import hal
from game_base import Game, EXIT


class Settings(Game):
    name = "Settings"
    description = "Sound on/off"

    def on_enter(self, display, buttons):
        self.buzzer = hal.get_buzzer()

    def update(self, display, buttons, dt_ms):
        if buttons.pressed("MENU") or buttons.pressed("B"):
            return EXIT

        if buttons.pressed("A") or buttons.pressed("LEFT") or buttons.pressed("RIGHT"):
            now_muted = self.buzzer.toggle_mute()
            if not now_muted:
                self.buzzer.beep(700, 60)

        display.fill(cfg.COLOR_BG)
        display.text("SETTINGS", 16, 16, cfg.COLOR_CYAN)
        display.hline(16, 30, cfg.SCREEN_W - 32, cfg.COLOR_DARK_GRAY)

        state_label = "OFF" if self.buzzer.muted else "ON"
        state_color = cfg.COLOR_RED if self.buzzer.muted else cfg.COLOR_GREEN

        display.text("Sound", 16, 60, cfg.COLOR_WHITE)
        box_y = 76
        display.rect(16, box_y, 140, 28, cfg.COLOR_GRAY)
        display.text(state_label, 16 + (140 - len(state_label) * cfg.FONT_W) // 2,
                     box_y + 10, state_color)

        display.text("Resets to ON after a power cycle.", 16, 118, cfg.COLOR_DARK_GRAY)
        display.text("A/LEFT/RIGHT Toggle   B/MENU Back", 16,
                     cfg.SCREEN_H - 16, cfg.COLOR_DARK_GRAY)
        display.show()
        return None
