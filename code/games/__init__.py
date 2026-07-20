from games.coming_soon import make_coming_soon
from games.about import About
from games.tictactoe import TicTacToe
from games.lemonade_stand import LemonadeStand
from games.settings import Settings
from games.snake import Snake
from games.minesweeper import Minesweeper
from games.memory_game import MemoryMatch
from games.block_breaker import BlockBreaker
from games.pong import Pong

GAMES = [
    LemonadeStand(),
    Snake(),
    TicTacToe(),
    Minesweeper(),
    MemoryMatch(),
    BlockBreaker(),
    Pong(),
    Settings(),
    About(), 
]
