import config as cfg

def wrap_text(text, max_chars):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        candidate = (cur + " " + w).strip()
        if len(candidate) > max_chars:
            if cur:
                lines.append(cur)
            cur = w
        else:
            cur = candidate
    if cur:
        lines.append(cur)
    return lines or [""]


def draw_wrapped(display, text, x, y, max_chars, color, line_h=None):
    line_h = line_h or (cfg.FONT_H + 2)
    for i, line in enumerate(wrap_text(text, max_chars)):
        display.text(line, x, y + i * line_h, color)
    lines = wrap_text(text, max_chars)
    return y + len(lines) * line_h


def draw_panel(display, x, y, w, h, border_color=cfg.COLOR_GRAY,
               fill_color=cfg.COLOR_PANEL):
    if fill_color is not None:
        display.fill_rect(x, y, w, h, fill_color)
    display.rect(x, y, w, h, border_color)

class Menu:

    def __init__(self, items, x=10, y=40, w=None, visible_rows=6,
                 title=None, footer="UP/DOWN  A Select  B Back"):
        self.items = items
        self.x = x
        self.y = y
        self.w = w or (cfg.SCREEN_W - x * 2)
        self.visible_rows = visible_rows
        self.title = title
        self.footer = footer
        self.index = 0
        self.scroll = 0
        label_line_h = cfg.BIG_FONT_H + 4
        subtitle_line_h = cfg.FONT_H + 4
        self.row_h = label_line_h + subtitle_line_h + 6

    def _label(self, item):
        return item[0] if isinstance(item, tuple) else item

    def _subtitle(self, item):
        return item[1] if isinstance(item, tuple) else None

    def update(self, buttons):
        n = len(self.items)
        if n == 0:
            return None
        if buttons.pressed_or_repeat("UP"):
            self.index = (self.index - 1) % n
        elif buttons.pressed_or_repeat("DOWN"):
            self.index = (self.index + 1) % n

        if self.index < self.scroll:
            self.scroll = self.index
        elif self.index >= self.scroll + self.visible_rows:
            self.scroll = self.index - self.visible_rows + 1

        if buttons.pressed("A"):
            return self.index
        if buttons.pressed("B") or buttons.pressed("MENU"):
            return "back"
        return None

    def draw(self, display):
        y = self.y
        if self.title:
            display.text_big(self.title, self.x, y, cfg.COLOR_WHITE)
            y += cfg.BIG_FONT_H + 8
            display.hline(self.x, y, self.w, cfg.COLOR_DARK_GRAY)
            y += 6

        visible = self.items[self.scroll:self.scroll + self.visible_rows]
        for row, item in enumerate(visible):
            real_i = self.scroll + row
            iy = y + row * self.row_h
            selected = (real_i == self.index)
            label = self._label(item)
            subtitle = self._subtitle(item)

            if selected:
                display.fill_rect(self.x - 4, iy - 4, self.w, self.row_h - 4,
                                   cfg.COLOR_HIGHLIGHT)
                text_color = cfg.COLOR_BLACK
            else:
                text_color = cfg.COLOR_WHITE

            prefix = "> " if selected else "  "
            display.text_big(prefix + label, self.x, iy, text_color)
            if subtitle:
                sub_color = cfg.COLOR_BLACK if selected else cfg.COLOR_GRAY
                display.text("  " + subtitle, self.x, iy + cfg.BIG_FONT_H + 4, sub_color)

        if self.scroll > 0:
            display.text("^", self.x + self.w - 10, self.y + 14, cfg.COLOR_GRAY)
        if self.scroll + self.visible_rows < len(self.items):
            bottom_y = y + self.visible_rows * self.row_h
            display.text("v", self.x + self.w - 10, bottom_y - 6, cfg.COLOR_GRAY)

        if self.footer:
            display.text(self.footer, self.x,
                         cfg.SCREEN_H - cfg.FONT_H - 8, cfg.COLOR_DARK_GRAY)

class NumberPicker:

    def __init__(self, label, value=0, min_val=0, max_val=999, step=1,
                 big_step=10, x=20, y=100, unit="", prefix=""):
        self.label = label
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.big_step = big_step
        self.x = x
        self.y = y
        self.unit = unit
        self.prefix = prefix

    def _clamp(self):
        self.value = max(self.min_val, min(self.max_val, self.value))

    def update(self, buttons):
        if buttons.pressed_or_repeat("LEFT"):
            self.value -= self.step
            self._clamp()
        elif buttons.pressed_or_repeat("RIGHT"):
            self.value += self.step
            self._clamp()
        elif buttons.pressed_or_repeat("UP"):
            self.value += self.big_step
            self._clamp()
        elif buttons.pressed_or_repeat("DOWN"):
            self.value -= self.big_step
            self._clamp()

        if buttons.pressed("A"):
            return True
        if buttons.pressed("B") or buttons.pressed("MENU"):
            return False
        return None

    def draw(self, display):
        display.text(self.label, self.x, self.y, cfg.COLOR_WHITE)
        val_str = f"{self.prefix}{self.value}{self.unit}"
        box_y = self.y + cfg.FONT_H + 10
        draw_panel(display, self.x, box_y, 120, 26)
        display.text("<", self.x + 6, box_y + 9, cfg.COLOR_GRAY)
        display.text(val_str, self.x + 44 - (len(val_str) * 4), box_y + 9,
                     cfg.COLOR_HIGHLIGHT)
        display.text(">", self.x + 106, box_y + 9, cfg.COLOR_GRAY)
        display.text("LEFT/RIGHT +-1  UP/DOWN +-10", self.x,
                     box_y + 34, cfg.COLOR_DARK_GRAY)

class ConfirmDialog:

    def __init__(self, message, x=16, y=90, yes_label="Yes", no_label="No"):
        self.message = message
        self._menu = Menu([yes_label, no_label], x=x, y=y + 30,
                           visible_rows=2, footer="A Confirm  B Cancel")
        self.x = x
        self.y = y

    def update(self, buttons):
        result = self._menu.update(buttons)
        if result == "back":
            return False
        if result == 0:
            return True
        if result == 1:
            return False
        return None

    def draw(self, display):
        draw_wrapped(display, self.message, self.x, self.y,
                     max_chars=(cfg.SCREEN_W - self.x * 2) // cfg.FONT_W,
                     color=cfg.COLOR_WHITE)
        self._menu.draw(display)

class ProgressBar:
    def __init__(self, x, y, w, h=12, fg=cfg.COLOR_GREEN, bg=cfg.COLOR_DARK_GRAY):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.fg, self.bg = fg, bg

    def draw(self, display, value, max_value, label=None):
        display.fill_rect(self.x, self.y, self.w, self.h, self.bg)
        if max_value > 0:
            fill_w = int(self.w * max(0, min(1, value / max_value)))
            if fill_w > 0:
                display.fill_rect(self.x, self.y, fill_w, self.h, self.fg)
        display.rect(self.x, self.y, self.w, self.h, cfg.COLOR_WHITE)
        if label:
            display.text(label, self.x, self.y - cfg.FONT_H - 4, cfg.COLOR_WHITE)

class Toast:

    def __init__(self, text, frames=45, color=cfg.COLOR_YELLOW):
        self.text = text
        self.frames_left = frames
        self.color = color

    def update(self):
        self.frames_left -= 1
        return self.frames_left > 0

    def draw(self, display):
        w = min(cfg.SCREEN_W - 20, len(self.text) * cfg.FONT_W + 20)
        x = (cfg.SCREEN_W - w) // 2
        y = cfg.SCREEN_H - 40
        draw_panel(display, x, y, w, 24, border_color=self.color)
        display.text(self.text, x + 10, y + 8, self.color)
