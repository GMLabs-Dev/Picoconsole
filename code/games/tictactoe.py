import random
import config as cfg
import hal
from game_base import Game, EXIT
from widgets import Menu

WIN_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
]

CPU_THINK_MS = 500
CELL = 46
GRID_W = CELL * 3
GRID_X0 = (cfg.SCREEN_W - GRID_W) // 2
GRID_Y0 = 62
MARK_PAD = 11


def winner_of(board):
    for a, b, c in WIN_LINES:
        if board[a] != " " and board[a] == board[b] == board[c]:
            return board[a], (a, b, c)
    if " " not in board:
        return "draw", None
    return None, None


def empty_cells(board):
    return [i for i in range(9) if board[i] == " "]


EASY_MISTAKE_CHANCE = 0.3


def _heuristic_move(board):
    me, opp = "O", "X"
    for i in empty_cells(board):
        board[i] = me
        if winner_of(board)[0] == me:
            board[i] = " "
            return i
        board[i] = " "
    for i in empty_cells(board):
        board[i] = opp
        if winner_of(board)[0] == opp:
            board[i] = " "
            return i
        board[i] = " "
    if board[4] == " ":
        return 4
    corners = [i for i in (0, 2, 6, 8) if board[i] == " "]
    if corners:
        return random.choice(corners)
    return random.choice(empty_cells(board))


def _minimax(board, player, alpha=-2, beta=2):
    winner, _ = winner_of(board)
    if winner == "O":
        return 1, None
    if winner == "X":
        return -1, None
    if winner == "draw":
        return 0, None

    best_move = None
    if player == "O":
        best_score = -2
        for i in empty_cells(board):
            board[i] = "O"
            score, _ = _minimax(board, "X", alpha, beta)
            board[i] = " "
            if score > best_score:
                best_score, best_move = score, i
            alpha = max(alpha, best_score)
            if alpha >= beta:
                break
        return best_score, best_move
    else:
        best_score = 2
        for i in empty_cells(board):
            board[i] = "X"
            score, _ = _minimax(board, "O", alpha, beta)
            board[i] = " "
            if score < best_score:
                best_score, best_move = score, i
            beta = min(beta, best_score)
            if alpha >= beta:
                break
        return best_score, best_move


def cpu_move(board, difficulty="hard"):
    if difficulty == "easy":
        if random.random() < EASY_MISTAKE_CHANCE:
            return random.choice(empty_cells(board))
        return _heuristic_move(board)

    _, best_move = _minimax(board, "O")
    return best_move


def _line(display, x0, y0, x1, y1, color):
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(steps + 1):
        x = x0 + (x1 - x0) * i // steps
        y = y0 + (y1 - y0) * i // steps
        display.pixel(x, y, color)
        display.pixel(x + 1, y, color)
        display.pixel(x, y + 1, color)


def draw_x(display, cx, cy, half, color):
    _line(display, cx - half, cy - half, cx + half, cy + half, color)
    _line(display, cx + half, cy - half, cx - half, cy + half, color)


def draw_o(display, cx, cy, radius, color):
    for r in (radius, radius - 1):
        x, y, err = r, 0, 0
        while x >= y:
            for dx, dy in ((x, y), (y, x), (-x, y), (-y, x),
                           (-x, -y), (-y, -x), (x, -y), (y, -x)):
                display.pixel(cx + dx, cy + dy, color)
            y += 1
            if err <= 0:
                err += 2 * y + 1
            if err > 0:
                x -= 1
                err -= 2 * x + 1


class TicTacToe(Game):
    name = "Tic-Tac-Toe"
    description = "1P vs CPU or 2P"

    def on_enter(self, display, buttons):
        self.buzzer = hal.get_buzzer()
        self.state = "mode_select"
        self.mode_menu = Menu(
            [("CPU: Easy"), ("CPU: Hard"),
             ("2P Local")],
            x=24, y=90, visible_rows=3,
            title="TIC-TAC-TOE",
            footer="A Select   B Back to launcher",
        )
        self.wins = {"X": 0, "O": 0, "draws": 0}
        self.vs_cpu = True
        self.cpu_difficulty = "hard"

    def _start_round(self):
        self.board = [" "] * 9
        self.turn = "X"
        self.cursor = [1, 1]
        self.win_line = None
        self.result = None
        self.cpu_timer = 0
        self.state = "play"

    def _draw_header(self, display):
        display.text("TIC-TAC-TOE", 16, 12, cfg.COLOR_CYAN)
        score = f"X:{self.wins['X']}  O:{self.wins['O']}  Draws:{self.wins['draws']}"
        display.text(score, 16, 26, cfg.COLOR_GRAY)

    def _draw_grid(self, display):
        for i in range(4):
            x = GRID_X0 + i * CELL
            display.vline(x, GRID_Y0, GRID_W, cfg.COLOR_GRAY)
        for i in range(4):
            y = GRID_Y0 + i * CELL
            display.hline(GRID_X0, y, GRID_W, cfg.COLOR_GRAY)

        cursor_i = self.cursor[0] * 3 + self.cursor[1]
        for i in range(9):
            r, c = divmod(i, 3)
            cx = GRID_X0 + c * CELL + CELL // 2
            cy = GRID_Y0 + r * CELL + CELL // 2

            if self.win_line and i in self.win_line:
                display.fill_rect(GRID_X0 + c * CELL + 2, GRID_Y0 + r * CELL + 2,
                                  CELL - 4, CELL - 4, cfg.COLOR_DARK_GRAY)

            val = self.board[i]
            if val == "X":
                draw_x(display, cx, cy, CELL // 2 - MARK_PAD, cfg.COLOR_YELLOW)
            elif val == "O":
                draw_o(display, cx, cy, CELL // 2 - MARK_PAD, cfg.COLOR_CYAN)

            if (self.state == "play" and i == cursor_i
                    and not (self.vs_cpu and self.turn == "O")):
                cursor_color = cfg.COLOR_HIGHLIGHT if val == " " else cfg.COLOR_ORANGE
                display.rect(GRID_X0 + c * CELL + 3, GRID_Y0 + r * CELL + 3,
                             CELL - 6, CELL - 6, cursor_color)

    def _draw_turn_label(self, display):
        if self.vs_cpu and self.turn == "O":
            label = f"CPU ({self.cpu_difficulty}) thinking..."
            color = cfg.COLOR_CYAN
        elif self.vs_cpu:
            label, color = "Your move (X)", cfg.COLOR_YELLOW
        else:
            label = f"Player {self.turn}'s move"
            color = cfg.COLOR_YELLOW if self.turn == "X" else cfg.COLOR_CYAN
        display.text(label, 16, 44, color)

    def _update_mode_select(self, display, buttons):
        result = self.mode_menu.update(buttons)
        display.fill(cfg.COLOR_BG)
        self.mode_menu.draw(display)
        display.show()
        if result == 0:
            self.vs_cpu = True
            self.cpu_difficulty = "easy"
            self._start_round()
        elif result == 1:
            self.vs_cpu = True
            self.cpu_difficulty = "hard"
            self._start_round()
        elif result == 2:
            self.vs_cpu = False
            self._start_round()
        elif result == "back":
            return EXIT
        return None

    def _update_play(self, display, buttons, dt_ms):
        if buttons.pressed("MENU"):
            return EXIT

        cpu_turn = self.vs_cpu and self.turn == "O"

        if cpu_turn:
            self.cpu_timer += dt_ms
            if self.cpu_timer >= CPU_THINK_MS:
                move = cpu_move(self.board, self.cpu_difficulty)
                self.board[move] = "O"
                self.buzzer.beep(500, 30)
                self.result, self.win_line = winner_of(self.board)
                self.turn = "X"
                self.cpu_timer = 0
        else:
            r, c = self.cursor
            if buttons.pressed("UP"):
                self.cursor[0] = (r - 1) % 3
            elif buttons.pressed("DOWN"):
                self.cursor[0] = (r + 1) % 3
            elif buttons.pressed("LEFT"):
                self.cursor[1] = (c - 1) % 3
            elif buttons.pressed("RIGHT"):
                self.cursor[1] = (c + 1) % 3
            elif buttons.pressed("A"):
                i = r * 3 + c
                if self.board[i] == " ":
                    self.board[i] = self.turn
                    self.buzzer.beep(600, 40)
                    self.result, self.win_line = winner_of(self.board)
                    self.turn = "O" if self.turn == "X" else "X"
            elif buttons.pressed("B"):
                self.state = "mode_select"
                return None

        if self.result is not None:
            if self.result == "draw":
                self.wins["draws"] += 1
                self.buzzer.beep(400, 180)
            else:
                self.wins[self.result] += 1
                self.buzzer.beep(900, 150)
            self.state = "round_end"

        display.fill(cfg.COLOR_BG)
        self._draw_header(display)
        self._draw_turn_label(display)
        self._draw_grid(display)
        display.text("A place   B back   MENU quit", 8,
                     cfg.SCREEN_H - 16, cfg.COLOR_DARK_GRAY)
        display.show()
        return None

    def _update_round_end(self, display, buttons):
        if buttons.pressed("MENU"):
            return EXIT
        if buttons.pressed("A"):
            self._start_round()
            return None
        if buttons.pressed("B"):
            self.state = "mode_select"
            return None

        if self.result == "draw":
            msg, color = "IT'S A DRAW!", cfg.COLOR_YELLOW
        elif self.vs_cpu:
            msg = "YOU WIN!" if self.result == "X" else "CPU WINS!"
            color = cfg.COLOR_GREEN if self.result == "X" else cfg.COLOR_RED
        else:
            msg, color = f"PLAYER {self.result} WINS!", cfg.COLOR_GREEN

        display.fill(cfg.COLOR_BG)
        self._draw_header(display)
        self._draw_grid(display)
        display.text(msg, (cfg.SCREEN_W - len(msg) * cfg.FONT_W) // 2,
                     GRID_Y0 + GRID_W + 12, color)
        display.text("A play again   B menu", 16,
                     cfg.SCREEN_H - 16, cfg.COLOR_GRAY)
        display.show()
        return None

    def update(self, display, buttons, dt_ms):
        if self.state == "mode_select":
            return self._update_mode_select(display, buttons)
        if self.state == "play":
            return self._update_play(display, buttons, dt_ms)
        if self.state == "round_end":
            return self._update_round_end(display, buttons)
        return EXIT
