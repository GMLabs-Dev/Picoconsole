import config as cfg
import hal
from game_base import Game, EXIT

LIVES_START = 3
BRICK_ROWS = 5
ROW_STYLE = [
    (cfg.COLOR_RED, 2),
    (cfg.COLOR_MAGENTA, 2),
    (cfg.COLOR_YELLOW, 1),
    (cfg.COLOR_GREEN, 1),
    (cfg.COLOR_CYAN, 1),
]

PLAY_X0 = 20
PLAY_Y0 = 34
PLAY_W = 200
PLAY_H = 174
PLAY_X1 = PLAY_X0 + PLAY_W
PLAY_Y1 = PLAY_Y0 + PLAY_H

BRICK_W = 20
BRICK_H = 10
BRICK_GAP_TOP = 6
BRICK_COLS = PLAY_W // BRICK_W

PADDLE_W = 40
PADDLE_H = 6
PADDLE_Y = PLAY_Y1 - 14
PADDLE_SPEED = 0.22

BALL_SIZE = 5
TICK_MS = 30
BALL_VX0, BALL_VY0 = -2.0, -3.6
BALL_VX_MAX = 4.2


class BlockBreaker(Game):
    name = "Block Breaker"
    description = "Paddle, ball, bricks"

    def on_enter(self, display, buttons):
        self.buzzer = hal.get_buzzer()
        self._start_run()

    def _new_bricks(self):
        bricks = {}
        for row in range(BRICK_ROWS):
            color, hp = ROW_STYLE[row % len(ROW_STYLE)]
            by = PLAY_Y0 + BRICK_GAP_TOP + row * BRICK_H
            for col in range(BRICK_COLS):
                bx = PLAY_X0 + col * BRICK_W
                bricks[(bx, by)] = {"color": color, "hp": hp, "max_hp": hp}
        return bricks

    def _reset_ball(self):
        self.ball_x = float(self.paddle_x + PADDLE_W / 2)
        self.ball_y = float(PADDLE_Y - BALL_SIZE)
        self.ball_vx, self.ball_vy = BALL_VX0, BALL_VY0
        self.launched = False

    def _start_run(self):
        self.score = 0
        self.lives = LIVES_START
        self.level = 1
        self.won = False
        self.bricks = self._new_bricks()
        self.paddle_x = PLAY_X0 + (PLAY_W - PADDLE_W) // 2
        self._reset_ball()
        self._tick_accum = 0
        self.state = "play"

    def _draw(self, display):
        display.fill(cfg.COLOR_BG)
        display.text(f"Score:{self.score}  Lives:{self.lives}  Lvl:{self.level}",
                     8, 8, cfg.COLOR_CYAN)
        display.rect(PLAY_X0 - 1, PLAY_Y0 - 1, PLAY_W + 2, PLAY_H + 2, cfg.COLOR_GRAY)

        for (bx, by), brick in self.bricks.items():
            color = brick["color"] if brick["hp"] == brick["max_hp"] else cfg.COLOR_DARK_GRAY
            display.fill_rect(bx, by, BRICK_W - 2, BRICK_H - 2, color)

        display.fill_rect(self.paddle_x, PADDLE_Y, PADDLE_W, PADDLE_H, cfg.COLOR_WHITE)
        display.fill_rect(int(self.ball_x), int(self.ball_y), BALL_SIZE, BALL_SIZE,
                          cfg.COLOR_YELLOW)

        if not self.launched:
            display.text("A to launch", PLAY_X0, PLAY_Y1 + 6, cfg.COLOR_GRAY)
        display.text("LEFT/RIGHT move   MENU quit", 4, cfg.SCREEN_H - 16,
                     cfg.COLOR_DARK_GRAY)

    def _update_play(self, display, buttons, dt_ms):
        if buttons.pressed("MENU"):
            return EXIT

        if buttons.held("LEFT"):
            self.paddle_x = max(PLAY_X0, self.paddle_x - PADDLE_SPEED * dt_ms)
        elif buttons.held("RIGHT"):
            self.paddle_x = min(PLAY_X1 - PADDLE_W, self.paddle_x + PADDLE_SPEED * dt_ms)

        if not self.launched:
            if buttons.pressed("A"):
                self.launched = True
            self.ball_x = self.paddle_x + PADDLE_W / 2
            self.ball_y = PADDLE_Y - BALL_SIZE
        else:
            self._tick_accum += dt_ms
            while self._tick_accum >= TICK_MS:
                self._tick_accum -= TICK_MS
                self._physics_tick()
                if self.state != "play":
                    break

        self._draw(display)
        display.show()
        return None

    def _physics_tick(self):
        self.ball_x += self.ball_vx
        self.ball_y += self.ball_vy

        if self.ball_x <= PLAY_X0 or self.ball_x >= PLAY_X1 - BALL_SIZE:
            self.ball_vx = -self.ball_vx
            self.ball_x = max(PLAY_X0, min(PLAY_X1 - BALL_SIZE, self.ball_x))
        if self.ball_y <= PLAY_Y0:
            self.ball_vy = -self.ball_vy
            self.ball_y = PLAY_Y0

        bx_i, by_i = int(self.ball_x), int(self.ball_y)
        hit_key = None
        for (brx, bry) in self.bricks:
            if (bry <= by_i < bry + BRICK_H and
                    brx <= bx_i < brx + BRICK_W):
                hit_key = (brx, bry)
                break
        if hit_key:
            brick = self.bricks[hit_key]
            brick["hp"] -= 1
            if brick["hp"] <= 0:
                del self.bricks[hit_key]
                self.score += 10
                self.buzzer.beep(700, 30)
            else:
                self.score += 5
                self.buzzer.beep(500, 25)
            self.ball_vy = -self.ball_vy
            if not self.bricks:
                self.buzzer.beep(1000, 250)
                self.won = True
                self.state = "game_over"
                return

        if (PADDLE_Y <= by_i + BALL_SIZE and by_i <= PADDLE_Y + PADDLE_H and
                self.paddle_x <= bx_i < self.paddle_x + PADDLE_W and self.ball_vy > 0):
            self.ball_vy = -abs(self.ball_vy)
            offset = (bx_i - (self.paddle_x + PADDLE_W / 2)) / (PADDLE_W / 2)
            self.ball_vx = max(-BALL_VX_MAX, min(BALL_VX_MAX, offset * BALL_VX_MAX))
            self.ball_y = PADDLE_Y - BALL_SIZE
            self.buzzer.beep(350, 30)

        if self.ball_y >= PLAY_Y1 - BALL_SIZE:
            self.lives -= 1
            self.buzzer.beep(200, 200)
            if self.lives <= 0:
                self.won = False
                self.state = "game_over"
                return
            self._reset_ball()

    def _update_game_over(self, display, buttons):
        if buttons.pressed("MENU") or buttons.pressed("B"):
            return EXIT
        if buttons.pressed("A"):
            self._start_run()
            return None

        display.fill(cfg.COLOR_BG)
        display.rect(PLAY_X0 - 1, PLAY_Y0 - 1, PLAY_W + 2, PLAY_H + 2, cfg.COLOR_GRAY)
        title = "LEVEL CLEARED!" if self.won else "GAME OVER"
        color = cfg.COLOR_GREEN if self.won else cfg.COLOR_RED
        display.text(title, PLAY_X0 + (PLAY_W - len(title) * cfg.FONT_W) // 2,
                     PLAY_Y0 + PLAY_H // 2 - 16, color)
        line = f"Final score: {self.score}"
        display.text(line, PLAY_X0 + (PLAY_W - len(line) * cfg.FONT_W) // 2,
                     PLAY_Y0 + PLAY_H // 2, cfg.COLOR_WHITE)
        display.text("A Retry   B/MENU Menu", 8, cfg.SCREEN_H - 16, cfg.COLOR_DARK_GRAY)
        display.show()
        return None

    def update(self, display, buttons, dt_ms):
        if self.state == "play":
            return self._update_play(display, buttons, dt_ms)
        if self.state == "game_over":
            return self._update_game_over(display, buttons)
        return EXIT
