# Picoconsole

A handheld game console built on a Raspberry Pi Pico, running MicroPython on a 240×240 ST7789 display with a 7 button layout. Includes a full game library and a desktop simulator so you can develop and playtest without hardware.

## Games

- Lemonade Stand
- Snake
- Tic-Tac-Toe
- Minesweeper
- Memory Match
- Block Breaker
- Pong

Plus a Settings screen (mute toggle, etc.) and an About screen.

## Features

- Simple menu-driven home screen with live game count and selection memory
- Hardware abstraction layer (hal.py) the exact same game code runs on real Pico hardware or in a Pygame-based desktop simulator, auto-detected at runtime
- Reusable UI widgets (widgets.py): scrolling menu, toasts, number pickers, confirm dialogs, progress bars, wrapped text
- Simple Game base class (game_base.py) so new games just implement on_enter / update / on_exit
- Buzzer support with mute, and button auto-repeat for held D-pad input

## Hardware

- Raspberry Pi Pico (or Pico W)
- 240×240 SPI ST7789 display
- 7 buttons wired to GPIO (Up / Down / Left / Right / A / B / Menu)
- Passive buzzer (PWM)

Pin mappings and display settings live in config.py, edit these to match your wiring.

## Running

### On hardware 
1. Copy the project files to the Pico (e.g. with mpremote or Thonny)
2. Run main.py. Requires the st7789py [MicroPython driver](/code/st7789py.py) on the device.

## On desktop (simulator)

```python
pip install pygame
python main.py
```
Simulator controls: Arrow keys = D-pad, Z = A, X = B, C = Menu.

## Project Structure

```text
main.py             # app entry point
config.py           # display, pins, colors, timing constants
hal.py              # hardware abstraction layer
game_base.py        # Game base class + EXIT sentinel
widgets.py          # reusable UI components
games/              # one module per game, registered in games/__init__.py
```

## Adding a Game

1. Create games/your_game.py with a class that subclasses Game and implements on_enter, update, and on_exit.
2. Import it and add an instance to the [games list](code/games/__init__.py)

It will automatically appear in the home menu.

## Attribution

This project bundles the [st7789py.py](https://github.com/russhughes/st7789py_mpy) driver by Russ Hughes, licensed under the [MIT License](/third_party/MIT_LICENSE).

## Disclosure

This project was developed with AI assistance. All generated code was reviewed and edited by me.

---

Made by Gustaw M.
