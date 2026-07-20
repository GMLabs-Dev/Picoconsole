import time
import config as cfg

try:
    import machine 
    IS_HARDWARE = True
except ImportError:
    IS_HARDWARE = False


def _rgb_to_565(rgb):
    r, g, b = rgb
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

if IS_HARDWARE:
    from machine import Pin, SPI
    import framebuf
    import st7789py as st7789

    class Display:
        def __init__(self):
            spi = SPI(
                cfg.PIN_SPI_ID,
                baudrate=cfg.SPI_BAUDRATE,
                sck=Pin(cfg.PIN_SCK),
                mosi=Pin(cfg.PIN_MOSI),
            )
            self._panel = st7789.ST7789(
                spi,
                cfg.SCREEN_W,
                cfg.SCREEN_H,
                reset=Pin(cfg.PIN_RST, Pin.OUT),
                cs=Pin(cfg.PIN_CS, Pin.OUT),
                dc=Pin(cfg.PIN_DC, Pin.OUT),
                rotation=cfg.SCREEN_ROTATION,
            )
            if cfg.PIN_BL is not None:
                self._bl = Pin(cfg.PIN_BL, Pin.OUT)
                self._bl.value(1)
            self._panel.init()
            self.width = cfg.SCREEN_W
            self.height = cfg.SCREEN_H

        def fill(self, color):
            self._panel.fill(_rgb_to_565(color))

        def pixel(self, x, y, color):
            self._panel.pixel(x, y, _rgb_to_565(color))

        def hline(self, x, y, length, color):
            self._panel.hline(x, y, length, _rgb_to_565(color))

        def vline(self, x, y, length, color):
            self._panel.vline(x, y, length, _rgb_to_565(color))

        def rect(self, x, y, w, h, color):
            self._panel.rect(x, y, w, h, _rgb_to_565(color))

        def fill_rect(self, x, y, w, h, color):
            self._panel.fill_rect(x, y, w, h, _rgb_to_565(color))

        def text(self, string, x, y, color):
            self._panel.text(string, x, y, _rgb_to_565(color))

        def text_big(self, string, x, y, color, scale=None):
            if scale is None:
                scale = cfg.BIG_FONT_SCALE
            n = len(string)
            if n == 0:
                return
            w = 8 * n
            bytes_per_row = (w + 7) // 8
            buf = bytearray(bytes_per_row * 8)
            glyph = framebuf.FrameBuffer(buf, w, 8, framebuf.MONO_HLSB)
            glyph.text(string, 0, 0, 1)
            c565 = _rgb_to_565(color)
            for gy in range(8):
                gx = 0
                while gx < w:
                    if glyph.pixel(gx, gy):
                        run_start = gx
                        while gx < w and glyph.pixel(gx, gy):
                            gx += 1
                        dx0 = round(run_start * scale)
                        dx1 = round(gx * scale)
                        dy0 = round(gy * scale)
                        dy1 = round((gy + 1) * scale)
                        self._panel.fill_rect(
                            x + dx0, y + dy0, dx1 - dx0, max(1, dy1 - dy0), c565)
                    else:
                        gx += 1

        def show(self):
            pass

    class Buttons:
        def __init__(self):
            self._pins = {
                name: Pin(pin, Pin.IN, Pin.PULL_UP)
                for name, pin in cfg.BUTTON_PINS.items()
            }
            self._state = {name: False for name in self._pins}
            self._prev = {name: False for name in self._pins}
            self._held_since = {name: 0 for name in self._pins}
            self._last_repeat = {name: 0 for name in self._pins}

        def update(self):
            now = time.ticks_ms()
            for name, pin in self._pins.items():
                raw_pressed = pin.value() == 0 
                self._prev[name] = self._state[name]
                self._state[name] = raw_pressed
                if raw_pressed and self._held_since[name] == 0:
                    self._held_since[name] = now
                elif not raw_pressed:
                    self._held_since[name] = 0

        def pressed(self, name):
            return self._state[name] and not self._prev[name]

        def held(self, name):
            return self._state[name]

        def pressed_or_repeat(self, name):
            if self.pressed(name):
                self._last_repeat[name] = time.ticks_ms()
                return True
            if not self._state[name]:
                return False
            now = time.ticks_ms()
            held_for = time.ticks_diff(now, self._held_since[name])
            if held_for < cfg.REPEAT_DELAY_MS:
                return False
            if time.ticks_diff(now, self._last_repeat[name]) >= cfg.REPEAT_INTERVAL_MS:
                self._last_repeat[name] = now
                return True
            return False

    class Buzzer:

        def __init__(self):
            self._pwm = machine.PWM(Pin(cfg.PIN_BUZZER))
            self._pwm.duty_u16(0)
            self._off_at = 0
            self._active = False
            self.muted = False

        def beep(self, freq_hz=880, ms=80):
            if self.muted:
                return
            self._pwm.freq(int(freq_hz))
            self._pwm.duty_u16(32768)
            self._off_at = time.ticks_add(time.ticks_ms(), ms)
            self._active = True

        def update(self):
            if self._active and time.ticks_diff(self._off_at, time.ticks_ms()) <= 0:
                self._pwm.duty_u16(0)
                self._active = False

        def set_muted(self, muted):
            self.muted = muted
            if muted and self._active:
                self._pwm.duty_u16(0)
                self._active = False

        def toggle_mute(self):
            self.set_muted(not self.muted)
            return self.muted
else:
    import pygame

    _SCALE = 2

    _KEYMAP = {
        "UP": [pygame.K_UP],
        "DOWN": [pygame.K_DOWN],
        "LEFT": [pygame.K_LEFT],
        "RIGHT": [pygame.K_RIGHT],
        "A": [pygame.K_z],
        "B": [pygame.K_x],
        "MENU": [pygame.K_c],
    }

    class Display:
        def __init__(self):
            pygame.init()
            pygame.display.set_caption(
                "Pico Console Simulator  [arrows=dpad  Z=A  X=B  C=Menu]"
            )
            self.width = cfg.SCREEN_W
            self.height = cfg.SCREEN_H
            self._surface = pygame.Surface((self.width, self.height))
            self._window = pygame.display.set_mode(
                (self.width * _SCALE, self.height * _SCALE)
            )
            self._font = pygame.font.Font(None, 14)
            self._font_big = pygame.font.Font(None, 18)

        def fill(self, color):
            self._surface.fill(color)

        def pixel(self, x, y, color):
            self._surface.set_at((x, y), color)

        def hline(self, x, y, length, color):
            pygame.draw.line(self._surface, color, (x, y), (x + length - 1, y))

        def vline(self, x, y, length, color):
            pygame.draw.line(self._surface, color, (x, y), (x, y + length - 1))

        def rect(self, x, y, w, h, color):
            pygame.draw.rect(self._surface, color, (x, y, w, h), 1)

        def fill_rect(self, x, y, w, h, color):
            pygame.draw.rect(self._surface, color, (x, y, w, h))

        def text(self, string, x, y, color):
            img = self._font.render(string, False, color)
            self._surface.blit(img, (x, y))

        def text_big(self, string, x, y, color, scale=2):
            img = self._font_big.render(string, False, color)
            self._surface.blit(img, (x, y))

        def show(self):
            pygame.event.pump()
            scaled = pygame.transform.scale(
                self._surface, (self.width * _SCALE, self.height * _SCALE)
            )
            self._window.blit(scaled, (0, 0))
            pygame.display.flip()

    class Buttons:
        def __init__(self):
            self._state = {name: False for name in _KEYMAP}
            self._prev = {name: False for name in _KEYMAP}
            self._held_since = {name: 0 for name in _KEYMAP}
            self._last_repeat = {name: 0 for name in _KEYMAP}

        def update(self):
            pygame.event.pump()
            keys = pygame.key.get_pressed()
            now = pygame.time.get_ticks()
            for name, key_list in _KEYMAP.items():
                raw_pressed = any(keys[k] for k in key_list)
                self._prev[name] = self._state[name]
                self._state[name] = raw_pressed
                if raw_pressed and self._held_since[name] == 0:
                    self._held_since[name] = now
                elif not raw_pressed:
                    self._held_since[name] = 0
            for event in pygame.event.get(pygame.QUIT):
                raise SystemExit

        def pressed(self, name):
            return self._state[name] and not self._prev[name]

        def held(self, name):
            return self._state[name]

        def pressed_or_repeat(self, name):
            if self.pressed(name):
                self._last_repeat[name] = pygame.time.get_ticks()
                return True
            if not self._state[name]:
                return False
            now = pygame.time.get_ticks()
            held_for = now - self._held_since[name]
            if held_for < cfg.REPEAT_DELAY_MS:
                return False
            if now - self._last_repeat[name] >= cfg.REPEAT_INTERVAL_MS:
                self._last_repeat[name] = now
                return True
            return False

    class Buzzer:

        def __init__(self):
            self.muted = False

        def beep(self, freq_hz=880, ms=80):
            pass

        def update(self):
            pass

        def set_muted(self, muted):
            self.muted = muted

        def toggle_mute(self):
            self.muted = not self.muted
            return self.muted

_display = None
_buttons = None
_buzzer = None


def get_display():
    global _display
    if _display is None:
        _display = Display()
    return _display


def get_buttons():
    global _buttons
    if _buttons is None:
        _buttons = Buttons()
    return _buttons


def get_buzzer():
    global _buzzer
    if _buzzer is None:
        _buzzer = Buzzer()
    return _buzzer


def sleep_ms(ms):
    if IS_HARDWARE:
        time.sleep_ms(ms)
    else:
        pygame.time.wait(ms)


def ticks_ms():
    if IS_HARDWARE:
        return time.ticks_ms()
    else:
        return pygame.time.get_ticks()


def ticks_diff(a, b):
    if IS_HARDWARE:
        return time.ticks_diff(a, b)
    else:
        return a - b
