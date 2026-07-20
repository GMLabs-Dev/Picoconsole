import config as cfg
from hal import get_display, get_buttons, get_buzzer, sleep_ms, ticks_ms, ticks_diff
from widgets import Menu, Toast
from games import GAMES
from game_base import EXIT

STATE_MENU = "menu"
STATE_GAME = "game"


def build_menu(selected_index=0):
    items = [(g.name, g.description) for g in GAMES]
    menu = Menu(
        items,
        x=14, y=34, visible_rows=4,
        title="PICO CONSOLE",
        footer="UP/DOWN Navigate   A Play",
    )
    menu.index = selected_index
    return menu


def main():
    display = get_display()
    buttons = get_buttons()
    buzzer = get_buzzer()

    state = STATE_MENU
    menu = build_menu()
    current_game = None
    last_tick = ticks_ms()
    toast = None

    while True:
        now = ticks_ms()
        dt_ms = ticks_diff(now, last_tick)
        last_tick = now

        buttons.update()
        buzzer.update()

        if state == STATE_MENU:
            result = menu.update(buttons)
            display.fill(cfg.COLOR_BG)
            menu.draw(display)
            counter = f"{menu.index + 1}/{len(GAMES)}"
            display.text(counter, cfg.SCREEN_W - len(counter) * cfg.FONT_W - 12,
                         12, cfg.COLOR_GRAY)

            if isinstance(result, int):
                current_game = GAMES[result]
                current_game.on_enter(display, buttons)
                buzzer.beep(660, 60)
                state = STATE_GAME
            elif result == "back":
                toast = Toast("Already at the home menu")

            if toast is not None:
                if toast.update():
                    toast.draw(display)
                else:
                    toast = None

            display.show()

        elif state == STATE_GAME:
            outcome = current_game.update(display, buttons, dt_ms)
            if outcome == EXIT:
                current_game.on_exit()
                menu = build_menu(selected_index=GAMES.index(current_game))
                current_game = None
                state = STATE_MENU

        elapsed = ticks_diff(ticks_ms(), now)
        remaining = cfg.FRAME_MS - elapsed
        if remaining > 0:
            sleep_ms(remaining)


if __name__ == "__main__":
    main()
