import random
import config as cfg
import hal
from game_base import Game, EXIT
from widgets import Menu

TICK_MS = 30
MAX_STEP = 2.0

PLAY_X0 = 20
PLAY_Y0 = 34
PLAY_X1 = 220
PLAY_Y1 = 208
PLAY_W = PLAY_X1 - PLAY_X0
PLAY_H = PLAY_Y1 - PLAY_Y0

PADDLE_W = 6
PADDLE_H = 34
PADDLE_MARGIN = 6
LEFT_PADDLE_X = PLAY_X0 + PADDLE_MARGIN
RIGHT_PADDLE_X = PLAY_X1 - PADDLE_MARGIN - PADDLE_W
PLAYER_PADDLE_SPEED = 0.20

BALL_SIZE = 6
BALL_V0 = 2.2
BALL_SPEED_GROWTH = 1.05
BALL_SPEED_MAX = 5.0

WIN_SCORE = 5
SERVE_PAUSE_MS = 600

CPU_SETTINGS = {
    "Easy": {"speed": 0.09, "react_chance": 0.7},
    "Hard": {"speed": 0.17, "react_chance": 1.0},
}


class Pong(Game):
    name = "Pong"
    description = "Paddle vs paddle"

    def on_enter(self, display, buttons):
        self.buzzer = hal.get_buzzer()
        self.state = "mode_select"
        self.mode_menu = Menu(
            [("CPU: Easy"), ("CPU: Hard"),
             ("2P Local")],
            x=24, y=90, visible_rows=3,
            title="PONG",
            footer="A Select   B Back to launcher",
        )

    def _start_run(self, mode):
        self.mode = mode
        self.score_left = 0
        self.score_right = 0
        self.left_y = PLAY_Y0 + PLAY_H / 2 - PADDLE_H / 2
        self.right_y = PLAY_Y0 + PLAY_H / 2 - PADDLE_H / 2
        self._tick_accum = 0
        self._serve_ball(toward_left=random.choice([True, False]))
        self.state = "play"

    def _serve_ball(self, toward_left):
        self.ball_x = PLAY_X0 + PLAY_W / 2 - BALL_SIZE / 2
        self.ball_y = PLAY_Y0 + PLAY_H / 2 - BALL_SIZE / 2
        vx = -BALL_V0 if toward_left else BALL_V0
        vy = random.uniform(-1.6, 1.6)
        if abs(vy) < 0.5:
            vy = 0.5 if vy >= 0 else -0.5
        self.ball_vx, self.ball_vy = vx, vy
        self.serving = True
        self.serve_timer = 0

    def _draw(self, display, show_hint=True):
        display.fill(cfg.COLOR_BG)
        display.text(f"{self.score_left}   PONG   {self.score_right}", 80, 8,
                     cfg.COLOR_CYAN)

        mid_x = PLAY_X0 + PLAY_W // 2
        y = PLAY_Y0
        while y < PLAY_Y1:
            display.vline(mid_x, y, 6, cfg.COLOR_DARK_GRAY)
            y += 12
        display.rect(PLAY_X0, PLAY_Y0, PLAY_W, PLAY_H, cfg.COLOR_GRAY)

        display.fill_rect(LEFT_PADDLE_X, int(self.left_y), PADDLE_W, PADDLE_H,
                          cfg.COLOR_CYAN)
        right_color = cfg.COLOR_YELLOW if self.mode == "2P" else cfg.COLOR_RED
        display.fill_rect(RIGHT_PADDLE_X, int(self.right_y), PADDLE_W, PADDLE_H,
                          right_color)

        if not self.serving or self.serve_timer > 150:
            display.fill_rect(int(self.ball_x), int(self.ball_y),
                              BALL_SIZE, BALL_SIZE, cfg.COLOR_WHITE)

        if show_hint:
            if self.mode == "2P":
                hint = "P1 UP/DOWN  P2 LEFT/RIGHT  MENU quit"
            else:
                hint = f"D-pad move   CPU: {self.mode}   MENU quit"
            display.text(hint, 4, cfg.SCREEN_H - 16, cfg.COLOR_DARK_GRAY)

    def _update_mode_select(self, display, buttons):
        result = self.mode_menu.update(buttons)
        display.fill(cfg.COLOR_BG)
        self.mode_menu.draw(display)
        display.show()
        if result == 0:
            self._start_run("Easy")
        elif result == 1:
            self._start_run("Hard")
        elif result == 2:
            self._start_run("2P")
        elif result == "back":
            return EXIT
        return None

    def _move_paddles(self, buttons, dt_ms):
        if buttons.held("UP"):
            self.left_y = max(PLAY_Y0, self.left_y - PLAYER_PADDLE_SPEED * dt_ms)
        elif buttons.held("DOWN"):
            self.left_y = min(PLAY_Y1 - PADDLE_H, self.left_y + PLAYER_PADDLE_SPEED * dt_ms)

        if self.mode == "2P":
            if buttons.held("LEFT"):
                self.right_y = max(PLAY_Y0, self.right_y - PLAYER_PADDLE_SPEED * dt_ms)
            elif buttons.held("RIGHT"):
                self.right_y = min(PLAY_Y1 - PADDLE_H, self.right_y + PLAYER_PADDLE_SPEED * dt_ms)
        else:
            cfg_ai = CPU_SETTINGS[self.mode]
            if random.random() < cfg_ai["react_chance"]:
                target = self.ball_y + BALL_SIZE / 2 - PADDLE_H / 2
                speed = cfg_ai["speed"] * dt_ms
                if self.right_y < target:
                    self.right_y = min(target, self.right_y + speed)
                elif self.right_y > target:
                    self.right_y = max(target, self.right_y - speed)
                self.right_y = max(PLAY_Y0, min(PLAY_Y1 - PADDLE_H, self.right_y))

    def _update_play(self, display, buttons, dt_ms):
        if buttons.pressed("MENU"):
            return EXIT
        if buttons.pressed("B"):
            self.state = "mode_select"
            return None

        self._move_paddles(buttons, dt_ms)

        if self.serving:
            self.serve_timer += dt_ms
            if self.serve_timer >= SERVE_PAUSE_MS:
                self.serving = False
        else:
            self._tick_accum += dt_ms
            while self._tick_accum >= TICK_MS:
                self._tick_accum -= TICK_MS
                self._physics_tick()
                if self.state != "play":
                    self._draw(display)
                    display.show()
                    return None

        self._draw(display)
        display.show()
        return None

    @staticmethod
    def _overlap(ax0, ay0, ax1, ay1, bx0, by0, bx1, by1):
        return ax0 < bx1 and ax1 > bx0 and ay0 < by1 and ay1 > by0

    def _physics_tick(self):
        """Sub-stepped for the same tunneling-safety reason as Block
        Breaker (see that file's _physics_tick docstring)."""
        distance = max(abs(self.ball_vx), abs(self.ball_vy), 0.0001)
        steps = max(1, int(distance / MAX_STEP) + 1)
        for _ in range(steps):
            self._physics_substep(self.ball_vx / steps, self.ball_vy / steps)
            if self.state != "play":
                return

    def _physics_substep(self, vx, vy):
        self.ball_x += vx
        self.ball_y += vy

        if self.ball_y <= PLAY_Y0:
            self.ball_vy = abs(self.ball_vy)
            self.ball_y = PLAY_Y0
        elif self.ball_y >= PLAY_Y1 - BALL_SIZE:
            self.ball_vy = -abs(self.ball_vy)
            self.ball_y = PLAY_Y1 - BALL_SIZE

        bx0, by0 = self.ball_x, self.ball_y
        bx1, by1 = bx0 + BALL_SIZE, by0 + BALL_SIZE

        if (self.ball_vx < 0 and
                self._overlap(bx0, by0, bx1, by1, LEFT_PADDLE_X, self.left_y,
                              LEFT_PADDLE_X + PADDLE_W, self.left_y + PADDLE_H)):
            self._bounce_off_paddle(self.left_y, going_right=True)
        elif (self.ball_vx > 0 and
                self._overlap(bx0, by0, bx1, by1, RIGHT_PADDLE_X, self.right_y,
                              RIGHT_PADDLE_X + PADDLE_W, self.right_y + PADDLE_H)):
            self._bounce_off_paddle(self.right_y, going_right=False)

        if self.ball_x < PLAY_X0 - BALL_SIZE:
            self._score(right_scores=True)
        elif self.ball_x > PLAY_X1 + BALL_SIZE:
            self._score(right_scores=False)

    def _bounce_off_paddle(self, paddle_y, going_right):
        speed = min(BALL_SPEED_MAX, (self.ball_vx ** 2 + self.ball_vy ** 2) ** 0.5
                    * BALL_SPEED_GROWTH)
        offset = ((self.ball_y + BALL_SIZE / 2) - (paddle_y + PADDLE_H / 2)) / (PADDLE_H / 2)
        offset = max(-1.0, min(1.0, offset))
        angle_vy = offset * speed * 0.7
        angle_vx = (speed ** 2 - angle_vy ** 2) ** 0.5
        self.ball_vx = angle_vx if going_right else -angle_vx
        self.ball_vy = angle_vy
        self.ball_x = (LEFT_PADDLE_X + PADDLE_W) if going_right else (RIGHT_PADDLE_X - BALL_SIZE)
        self.buzzer.beep(400, 30)

    def _score(self, right_scores):
        if right_scores:
            self.score_right += 1
            self.buzzer.beep(300, 150)
        else:
            self.score_left += 1
            self.buzzer.beep(600, 150)

        if self.score_left >= WIN_SCORE or self.score_right >= WIN_SCORE:
            self.buzzer.beep(1000, 200)
            self.state = "round_end"
            return

        self._serve_ball(toward_left=right_scores)

    def _update_round_end(self, display, buttons):
        if buttons.pressed("MENU"):
            return EXIT
        if buttons.pressed("A"):
            self._start_run(self.mode)
            return None
        if buttons.pressed("B"):
            self.state = "mode_select"
            return None

        self._draw(display, show_hint=False)
        if self.mode == "2P":
            msg = "PLAYER 1 WINS!" if self.score_left > self.score_right else "PLAYER 2 WINS!"
        else:
            msg = "YOU WIN!" if self.score_left > self.score_right else "CPU WINS!"
        color = cfg.COLOR_GREEN if (self.score_left > self.score_right) else cfg.COLOR_RED
        msg_x = PLAY_X0 + max(0, (PLAY_W - len(msg) * cfg.FONT_W) // 2)
        box_y = PLAY_Y0 + PLAY_H // 2 - 10
        display.fill_rect(PLAY_X0, box_y - 4, PLAY_W, 26, cfg.COLOR_BG)
        display.text(msg, msg_x, box_y, color)
        display.text("A Rematch   B Mode   MENU Quit", 8,
                     cfg.SCREEN_H - 16, cfg.COLOR_DARK_GRAY)
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
