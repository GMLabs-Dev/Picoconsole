import random
import config as cfg
import hal
from game_base import Game, EXIT
from widgets import Menu

DIFFICULTIES = [
    ("Easy", 9, 9, 10),
    ("Medium", 12, 12, 24),
    ("Hard", 16, 16, 45),
]

NUMBER_COLORS = {
    1: cfg.COLOR_CYAN, 2: cfg.COLOR_GREEN, 3: cfg.COLOR_RED,
    4: cfg.COLOR_MAGENTA, 5: cfg.COLOR_ORANGE, 6: cfg.COLOR_YELLOW,
    7: cfg.COLOR_WHITE, 8: cfg.COLOR_GRAY,
}

BOARD_Y0 = 36
BOARD_BOTTOM_LIMIT = 220
BOARD_MAX_W = cfg.SCREEN_W - 20


class MinesweeperLogic:

    def __init__(self, rows, cols, mines):
        self.rows = rows
        self.cols = cols
        self.mine_count = mines
        self.grid = [[0] * cols for _ in range(rows)]
        self.revealed = [[False] * cols for _ in range(rows)]
        self.flagged = [[False] * cols for _ in range(rows)]
        self.mines_placed = False
        self.game_over = False
        self.won = False
        self.moves = 0

    def place_mines(self, safe_r, safe_c):
        forbidden = {(safe_r + dr, safe_c + dc)
                     for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
        cells = [(r, c) for r in range(self.rows) for c in range(self.cols)
                 if (r, c) not in forbidden]
        mine_cells = random.sample(cells, min(self.mine_count, len(cells)))
        for r, c in mine_cells:
            self.grid[r][c] = -1
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == -1:
                    continue
                count = 0
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols and self.grid[nr][nc] == -1:
                            count += 1
                self.grid[r][c] = count
        self.mines_placed = True

    def neighbors(self, r, c):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    yield nr, nc

    def flood_reveal(self, r, c):
        stack = [(r, c)]
        while stack:
            cr, cc = stack.pop()
            if self.revealed[cr][cc] or self.flagged[cr][cc]:
                continue
            self.revealed[cr][cc] = True
            if self.grid[cr][cc] == 0:
                for nr, nc in self.neighbors(cr, cc):
                    if not self.revealed[nr][nc]:
                        stack.append((nr, nc))

    def reveal(self, r, c):
        if self.flagged[r][c] or self.revealed[r][c]:
            return
        if not self.mines_placed:
            self.place_mines(r, c)
        self.moves += 1
        if self.grid[r][c] == -1:
            self.revealed[r][c] = True
            self.game_over = True
            return
        self.flood_reveal(r, c)
        self.check_win()

    def toggle_flag(self, r, c):
        if self.revealed[r][c]:
            return
        self.flagged[r][c] = not self.flagged[r][c]

    def check_win(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] != -1 and not self.revealed[r][c]:
                    return
        self.won = True
        self.game_over = True

    def flags_used(self):
        return sum(row.count(True) for row in self.flagged)

    def reveal_all_mines(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == -1:
                    self.revealed[r][c] = True


class Minesweeper(Game):
    name = "Minesweeper"
    description = "Clear the board, avoid mines"

    def on_enter(self, display, buttons):
        self.buzzer = hal.get_buzzer()
        self.state = "difficulty_select"
        self.diff_menu = Menu(
            [(name, f"{r}x{c}, {m} mines") for name, r, c, m in DIFFICULTIES],
            x=24, y=90, visible_rows=3,
            title="MINESWEEPER",
            footer="A Select   B Back to launcher",
        )

    def _start_run(self, diff_index):
        self.diff_index = diff_index
        name, rows, cols, mines = DIFFICULTIES[diff_index]
        self.game = MinesweeperLogic(rows, cols, mines)
        self.cursor = [rows // 2, cols // 2]
        self.start_ticks = None
        self.elapsed_s = 0

        cell = min(BOARD_MAX_W // cols, (BOARD_BOTTOM_LIMIT - BOARD_Y0) // rows)
        self.cell = max(6, cell)
        self.board_w = cols * self.cell
        self.board_h = rows * self.cell
        self.board_x0 = (cfg.SCREEN_W - self.board_w) // 2
        self.board_y0 = BOARD_Y0 + ((BOARD_BOTTOM_LIMIT - BOARD_Y0 - self.board_h) // 2)
        self.state = "play"

    def _cell_xy(self, r, c):
        return self.board_x0 + c * self.cell, self.board_y0 + r * self.cell

    def _draw_cell(self, display, r, c, is_cursor):
        x, y = self._cell_xy(r, c)
        size = self.cell - 1
        g = self.game

        if g.flagged[r][c]:
            display.fill_rect(x, y, size, size, cfg.COLOR_ORANGE)
        elif not g.revealed[r][c]:
            display.fill_rect(x, y, size, size, cfg.COLOR_PANEL)
        elif g.grid[r][c] == -1:
            display.fill_rect(x, y, size, size, cfg.COLOR_RED)
        else:
            display.fill_rect(x, y, size, size, cfg.COLOR_DARK_GRAY)
            n = g.grid[r][c]
            if n > 0 and self.cell >= 10:
                color = NUMBER_COLORS.get(n, cfg.COLOR_WHITE)
                display.text(str(n), x + (size - cfg.FONT_W) // 2,
                             y + (size - cfg.FONT_H) // 2, color)

        if is_cursor:
            display.rect(x - 1, y - 1, size + 2, size + 2, cfg.COLOR_HIGHLIGHT)

    def _draw_board(self, display, cursor_visible):
        g = self.game
        display.fill(cfg.COLOR_BG)
        name = DIFFICULTIES[self.diff_index][0]
        display.text(f"MINESWEEPER - {name}", 10, 8, cfg.COLOR_CYAN)
        status = f"Mines:{g.mine_count} Flags:{g.flags_used()} Time:{self.elapsed_s}s"
        display.text(status, 10, 20, cfg.COLOR_GRAY)

        display.rect(self.board_x0 - 1, self.board_y0 - 1,
                     self.board_w + 2, self.board_h + 2, cfg.COLOR_GRAY)
        cr, cc = self.cursor
        for r in range(g.rows):
            for c in range(g.cols):
                is_cursor = cursor_visible and (r, c) == (cr, cc)
                self._draw_cell(display, r, c, is_cursor)

        display.text("D-pad move  A reveal  B flag  MENU quit", 4,
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

        g = self.game
        r, c = self.cursor
        if buttons.pressed_or_repeat("UP"):
            self.cursor[0] = max(0, r - 1)
        elif buttons.pressed_or_repeat("DOWN"):
            self.cursor[0] = min(g.rows - 1, r + 1)
        elif buttons.pressed_or_repeat("LEFT"):
            self.cursor[1] = max(0, c - 1)
        elif buttons.pressed_or_repeat("RIGHT"):
            self.cursor[1] = min(g.cols - 1, c + 1)
        elif buttons.pressed("A"):
            was_placed = g.mines_placed
            g.reveal(r, c)
            if not was_placed and g.mines_placed:
                self.start_ticks = hal.ticks_ms()
            if g.game_over and not g.won:
                self.buzzer.beep(150, 300)
            elif g.game_over and g.won:
                self.buzzer.beep(1000, 200)
            else:
                self.buzzer.beep(500, 25)
        elif buttons.pressed("B"):
            g.toggle_flag(r, c)
            self.buzzer.beep(650, 30)

        if self.start_ticks is not None and not g.game_over:
            self.elapsed_s = hal.ticks_diff(hal.ticks_ms(), self.start_ticks) // 1000

        if g.game_over:
            g.reveal_all_mines()
            self.state = "round_end"

        self._draw_board(display, cursor_visible=True)
        display.show()
        return None

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
        if self.game.won:
            msg, color = "YOU CLEARED THE FIELD!", cfg.COLOR_GREEN
        else:
            msg, color = "BOOM! YOU HIT A MINE.", cfg.COLOR_RED
        box_y = self.board_y0 + self.board_h // 2 - 14
        display.fill_rect(self.board_x0, box_y - 4, self.board_w, 30, cfg.COLOR_BG)
        text = msg[:self.board_w // cfg.FONT_W]
        text_x = self.board_x0 + max(0, (self.board_w - len(text) * cfg.FONT_W) // 2)
        display.text(text, text_x, box_y, color)
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
