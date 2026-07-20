SCREEN_W = 240
SCREEN_H = 240
SCREEN_ROTATION = 0        # 0/1/2/3, adjust once you see the physical orientation
SCREEN_ROW_OFFSET = 0      # try 80 if the picture is shifted down
SCREEN_COL_OFFSET = 0
PIN_SPI_ID   = 1
PIN_SCK      = 14   # labelled "SCL" on the board silkscreen
PIN_MOSI     = 15   # labelled "SDA" on the board silkscreen
PIN_DC       = 18
PIN_RST      = 19
PIN_CS       = 17
PIN_BL       = 16
SPI_BAUDRATE = 40_000_000
PIN_BUZZER = 12
BUTTON_PINS = {
    "UP":     11,
    "DOWN":   9,
    "LEFT":   8,
    "RIGHT":  10,
    "A":      7,
    "B":      6,
    "MENU":   5,
}

DEBOUNCE_MS = 30            # ignore repeat presses inside this window
REPEAT_DELAY_MS = 400       # how long a button must be held before auto-repeat starts
REPEAT_INTERVAL_MS = 120    # auto-repeat interval once held (used by NumberPicker)
COLOR_BLACK      = (0, 0, 0)
COLOR_WHITE      = (255, 255, 255)
COLOR_GREEN      = (80, 220, 100)
COLOR_RED        = (230, 70, 70)
COLOR_YELLOW     = (240, 200, 60)
COLOR_ORANGE     = (240, 140, 50)
COLOR_BLUE       = (80, 150, 240)
COLOR_CYAN       = (90, 220, 220)
COLOR_MAGENTA    = (210, 100, 220)
COLOR_GRAY       = (110, 110, 110)
COLOR_DARK_GRAY  = (40, 40, 40)
COLOR_BG         = (10, 10, 20)      # default screen background
COLOR_PANEL      = (25, 25, 40)      # panel / card background
COLOR_HIGHLIGHT  = (255, 220, 90)    # selected menu item
FONT_W = 8
FONT_H = 8
BIG_FONT_W = 12
BIG_FONT_H = 12
BIG_FONT_SCALE = BIG_FONT_W / FONT_W
TARGET_FPS = 30
FRAME_MS = int(1000 / TARGET_FPS)
