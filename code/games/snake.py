import random
import config as cfg
import hal
from game_base import Game, EXIT
from widgets import Menu

START_LEN = 3
COLS = 20
ROWS = 18
CELL = 10
BOARD_W = COLS * CELL
BOARD_H = ROWS * CELL
BOARD_X0 = (cfg.SCREEN_W - BOARD_W) // 2
BOARD_Y0 = 30

DIFFICULTIES = {
    "Easy": {"start": 170, "min": 90, "step": 2},
    "Hard": {"start": 110, "min": 50, "step": 3}, 
}

DIR_UP = (-1, 0)
DIR_DOWN = (1, 0)
DIR_LEFT = (0, -1)
DIR_RIGHT = (0, 1)


class Snake(Game):
    name = "Snake"
    description = "Classic snake, don't hit yourself"

    def on_enter(self, display, buttons):
        self.buzzer = hal.get_buzzer()
        self.state = "difficulty_select"
        self.diff_menu = Menu(
            [("Easy"), ("Hard")],
            x=24, y=90, visible_rows=2,
            title="SNAKE",
            footer="A Select   B Back to launcher",
        )
        self.difficulty = "Hard"

    def _start_run(self):
        speed_cfg = DIFFICULTIES[self.difficulty]
        self.speed_start = speed_cfg["start"]
        self.speed_min = speed_cfg["min"]
        self.speed_step = speed_cfg["step"]

        self.snake = [(ROWS // 2, COLS // 2 - i) for i in range(START_LEN)]
        self.direction = DIR_RIGHT
        self.pending_dir = DIR_RIGHT
        self.score = 0
        self.speed = self.speed_start
        self.paused = False
        self._tick_accum = 0
        self.food = self._place_food()
        self.state = "play"

    def _place_food(self):
        while True:
            fr = random.randint(0, ROWS - 1)
            fc = random.randint(0, COLS - 1)
            if (fr, fc) not in self.snake:
                return (fr, fc)

    def _update_difficulty_select(self, display, buttons):
        result = self.diff_menu.update(buttons)
        display.fill(cfg.COLOR_BG)
        self.diff_menu.draw(display)
        display.show()
        if isinstance(result, int):
            self.difficulty = ("Easy", "Hard")[result]
            self._start_run()
        elif result == "back":
            return EXIT
        return None

    def _cell_rect(self, r, c):
        return (BOARD_X0 + c * CELL, BOARD_Y0 + r * CELL, CELL - 1, CELL - 1)

    def _draw_board(self, display):
        display.fill(cfg.COLOR_BG)
        display.text(f"Score: {self.score}   Len: {len(self.snake)}   [{self.difficulty}]",
                     12, 10, cfg.COLOR_CYAN)
        display.rect(BOARD_X0 - 1, BOARD_Y0 - 1, BOARD_W + 2, BOARD_H + 2,
                     cfg.COLOR_GRAY)

        fr, fc = self.food
        display.fill_rect(*self._cell_rect(fr, fc), cfg.COLOR_RED)

        for i, (sr, sc) in enumerate(self.snake):
            if i == 0:
                color = cfg.COLOR_YELLOW
            elif i % 2 == 0:
                color = cfg.COLOR_GREEN
            else:
                color = cfg.COLOR_CYAN
            display.fill_rect(*self._cell_rect(sr, sc), color)

        if self.paused:
            msg = "PAUSED - B to resume"
            display.fill_rect(BOARD_X0 + 10, BOARD_Y0 + BOARD_H // 2 - 10,
                              BOARD_W - 20, 20, cfg.COLOR_PANEL)
            display.text(msg, BOARD_X0 + (BOARD_W - len(msg) * cfg.FONT_W) // 2,
                         BOARD_Y0 + BOARD_H // 2 - 4, cfg.COLOR_HIGHLIGHT)

        display.text("D-pad move   B pause   MENU quit", 8,
                     cfg.SCREEN_H - 16, cfg.COLOR_DARK_GRAY)

    def _update_play(self, display, buttons, dt_ms):
        if buttons.pressed("MENU"):
            return EXIT
        if buttons.pressed("B"):
            self.paused = not self.paused

        if buttons.pressed("UP") and self.direction != DIR_DOWN:
            self.pending_dir = DIR_UP
        elif buttons.pressed("DOWN") and self.direction != DIR_UP:
            self.pending_dir = DIR_DOWN
        elif buttons.pressed("LEFT") and self.direction != DIR_RIGHT:
            self.pending_dir = DIR_LEFT
        elif buttons.pressed("RIGHT") and self.direction != DIR_LEFT:
            self.pending_dir = DIR_RIGHT

        if not self.paused:
            self._tick_accum += dt_ms
            if self._tick_accum >= self.speed:
                self._tick_accum = 0
                self._step()

        self._draw_board(display)
        display.show()
        return None

    def _step(self):
        self.direction = self.pending_dir
        hr, hc = self.snake[0]
        dr, dc = self.direction
        new_head = (hr + dr, hc + dc)

        if (new_head[0] < 0 or new_head[0] >= ROWS or
                new_head[1] < 0 or new_head[1] >= COLS or
                new_head in self.snake):
            self.buzzer.beep(180, 220)
            self.state = "game_over"
            return

        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.score += 10
            self.buzzer.beep(750, 40)
            self.food = self._place_food()
            self.speed = max(self.speed_min, self.speed - self.speed_step)
        else:
            self.snake.pop()

    def _update_game_over(self, display, buttons):
        if buttons.pressed("MENU"):
            return EXIT
        if buttons.pressed("A"):
            self._start_run()
            return None
        if buttons.pressed("B"):
            self.state = "difficulty_select"
            return None

        display.fill(cfg.COLOR_BG)
        display.rect(BOARD_X0 - 1, BOARD_Y0 - 1, BOARD_W + 2, BOARD_H + 2,
                     cfg.COLOR_GRAY)
        title = "GAME OVER"
        display.text(title, BOARD_X0 + (BOARD_W - len(title) * cfg.FONT_W) // 2,
                     BOARD_Y0 + BOARD_H // 2 - 24, cfg.COLOR_RED)
        line = f"Score: {self.score}  Len: {len(self.snake)}"
        display.text(line, BOARD_X0 + (BOARD_W - len(line) * cfg.FONT_W) // 2,
                     BOARD_Y0 + BOARD_H // 2 - 6, cfg.COLOR_WHITE)
        display.text("A Retry   B Difficulty   MENU Menu", 4,
                     cfg.SCREEN_H - 16, cfg.COLOR_DARK_GRAY)
        display.show()
        return None

    def update(self, display, buttons, dt_ms):
        if self.state == "difficulty_select":
            return self._update_difficulty_select(display, buttons)
        if self.state == "play":
            return self._update_play(display, buttons, dt_ms)
        if self.state == "game_over":
            return self._update_game_over(display, buttons)
        return EXIT
