import random
import config as cfg
import hal
from game_base import Game, EXIT
from widgets import Menu

DIFFICULTIES = [
    ("Easy", 4, 4),
    ("Medium", 4, 6),
    ("Hard", 6, 6),
]

SYMBOLS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
SYMBOL_COLORS = [
    cfg.COLOR_MAGENTA, cfg.COLOR_RED, cfg.COLOR_GREEN,
    cfg.COLOR_YELLOW, cfg.COLOR_CYAN, cfg.COLOR_BLUE,
    cfg.COLOR_ORANGE, cfg.COLOR_WHITE,
]

CHECK_PAUSE_MS = 700
BOARD_Y0 = 46
BOARD_BOTTOM_LIMIT = 220
BOARD_MAX_W = cfg.SCREEN_W - 20


class MemoryMatch(Game):
    name = "Memory Match"
    description = "Find the matching pairs"

    def on_enter(self, display, buttons):
        self.buzzer = hal.get_buzzer()
        self.state = "difficulty_select"
        self.diff_menu = Menu(
            [(name, f"{r}x{c}, {r * c // 2} pairs") for name, r, c in DIFFICULTIES],
            x=24, y=90, visible_rows=3,
            title="MEMORY MATCH",
            footer="A Select   B Back to launcher",
        )

    def _start_run(self, diff_index):
        self.diff_index = diff_index
        name, rows, cols = DIFFICULTIES[diff_index]
        self.rows, self.cols = rows, cols
        n = rows * cols
        pairs_needed = n // 2
        symbols = SYMBOLS[:pairs_needed] * 2
        random.shuffle(symbols)
        self.cards = symbols
        self.symbol_color_map = {
            sym: SYMBOL_COLORS[i % len(SYMBOL_COLORS)]
            for i, sym in enumerate(sorted(set(symbols)))
        }
        self.matched = [False] * n
        self.moves = 0
        self.cursor = [0, 0]
        self.revealed = []
        self.checking = False
        self.check_timer = 0
        self.last_match = None

        cell = min(BOARD_MAX_W // cols, (BOARD_BOTTOM_LIMIT - BOARD_Y0) // rows)
        self.cell = max(20, cell)
        self.board_w = cols * self.cell
        self.board_h = rows * self.cell
        self.board_x0 = (cfg.SCREEN_W - self.board_w) // 2
        self.board_y0 = BOARD_Y0 + ((BOARD_BOTTOM_LIMIT - BOARD_Y0 - self.board_h) // 2)
        self.state = "play"

    def _pairs_found(self):
        return sum(self.matched) // 2

    def _total_pairs(self):
        return len(self.cards) // 2

    def _card_xy(self, r, c):
        return self.board_x0 + c * self.cell, self.board_y0 + r * self.cell

    def _draw_card(self, display, r, c, is_cursor):
        i = r * self.cols + c
        x, y = self._card_xy(r, c)
        size = self.cell - 3

        if self.matched[i]:
            display.fill_rect(x, y, size, size, cfg.COLOR_DARK_GRAY)
            color = self.symbol_color_map[self.cards[i]]
            display.text_big(self.cards[i], x + (size - cfg.BIG_FONT_W) // 2,
                             y + (size - cfg.BIG_FONT_H) // 2, color)
        elif i in self.revealed:
            display.fill_rect(x, y, size, size, cfg.COLOR_PANEL)
            color = self.symbol_color_map[self.cards[i]]
            display.text_big(self.cards[i], x + (size - cfg.BIG_FONT_W) // 2,
                             y + (size - cfg.BIG_FONT_H) // 2, color)
        else:
            display.fill_rect(x, y, size, size, cfg.COLOR_PANEL)
            display.text_big("?", x + (size - cfg.BIG_FONT_W) // 2,
                             y + (size - cfg.BIG_FONT_H) // 2, cfg.COLOR_GRAY)

        if is_cursor:
            display.rect(x - 1, y - 1, size + 2, size + 2, cfg.COLOR_HIGHLIGHT)

    def _draw_board(self, display, cursor_visible):
        display.fill(cfg.COLOR_BG)
        name = DIFFICULTIES[self.diff_index][0]
        display.text(f"MEMORY MATCH - {name}", 10, 8, cfg.COLOR_CYAN)
        status = f"Moves:{self.moves}  Pairs:{self._pairs_found()}/{self._total_pairs()}"
        display.text(status, 10, 22, cfg.COLOR_GRAY)

        cr, cc = self.cursor
        for r in range(self.rows):
            for c in range(self.cols):
                is_cursor = cursor_visible and (r, c) == (cr, cc)
                self._draw_card(display, r, c, is_cursor)

        if self.checking and self.last_match is not None:
            msg = "MATCH!" if self.last_match else "No match"
            color = cfg.COLOR_GREEN if self.last_match else cfg.COLOR_RED
            text_x = self.board_x0 + (self.board_w - len(msg) * cfg.FONT_W) // 2
            display.fill_rect(self.board_x0, self.board_y0 - 16, self.board_w, 14,
                              cfg.COLOR_BG)
            display.text(msg, text_x, self.board_y0 - 16, color)

        display.text("D-pad move  A flip  B menu  MENU quit", 4,
                     cfg.SCREEN_H - 16, cfg.COLOR_DARK_GRAY)

    def _update_difficulty_select(self, display, buttons):
        result = self.diff_menu.update(buttons)
        display.fill(cfg.COLOR_BG)
        self.diff_menu.draw(display)
        display.show()
        if isinstance(result, int):
            self._start_run(result)
        elif result == "back":
            return EXIT
        return None

    def _update_play(self, display, buttons, dt_ms):
        if buttons.pressed("MENU"):
            return EXIT

        if self.checking:
            self.check_timer -= dt_ms
            if self.check_timer <= 0:
                self._resolve_check()
        else:
            if buttons.pressed("B"):
                self.state = "difficulty_select"
                return None

            r, c = self.cursor
            if buttons.pressed_or_repeat("UP"):
                self.cursor[0] = (r - 1) % self.rows
            elif buttons.pressed_or_repeat("DOWN"):
                self.cursor[0] = (r + 1) % self.rows
            elif buttons.pressed_or_repeat("LEFT"):
                self.cursor[1] = (c - 1) % self.cols
            elif buttons.pressed_or_repeat("RIGHT"):
                self.cursor[1] = (c + 1) % self.cols
            elif buttons.pressed("A"):
                i = r * self.cols + c
                if not self.matched[i] and i not in self.revealed:
                    self.revealed.append(i)
                    self.buzzer.beep(550, 30)
                    if len(self.revealed) == 2:
                        self.moves += 1
                        self.checking = True
                        self.check_timer = CHECK_PAUSE_MS
                        a, b = self.revealed
                        self.last_match = self.cards[a] == self.cards[b]

        self._draw_board(display, cursor_visible=True)
        display.show()
        return None

    def _resolve_check(self):
        a, b = self.revealed
        if self.last_match:
            self.matched[a] = True
            self.matched[b] = True
            self.buzzer.beep(900, 120)
        else:
            self.buzzer.beep(220, 150)
        self.revealed = []
        self.checking = False
        self.last_match = None

        if all(self.matched):
            self.buzzer.beep(1000, 250)
            self.state = "round_end"

    def _update_round_end(self, display, buttons):
        if buttons.pressed("MENU"):
            return EXIT
        if buttons.pressed("A"):
            self._start_run(self.diff_index)
            return None
        if buttons.pressed("B"):
            self.state = "difficulty_select"
            return None

        self._draw_board(display, cursor_visible=False)
        msg = "ALL PAIRS FOUND!"
        text_x = self.board_x0 + (self.board_w - len(msg) * cfg.FONT_W) // 2
        display.fill_rect(self.board_x0, self.board_y0 - 16, self.board_w, 14,
                          cfg.COLOR_BG)
        display.text(msg, text_x, self.board_y0 - 16, cfg.COLOR_GREEN)
        display.text("A Retry   B Difficulty   MENU Quit", 4,
                     cfg.SCREEN_H - 16, cfg.COLOR_DARK_GRAY)
        display.show()
        return None

    def update(self, display, buttons, dt_ms):
        if self.state == "difficulty_select":
            return self._update_difficulty_select(display, buttons)
        if self.state == "play":
            return self._update_play(display, buttons, dt_ms)
        if self.state == "round_end":
            return self._update_round_end(display, buttons)
        return EXIT