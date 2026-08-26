"""
★ MATHPAL ★  —  Learn Math. Level Up.
======================================
Entry point for the Mathpal desktop application.

Run with:
    python main.py
"""

import sys
import os

# Ensure the project root is on sys.path so imports work when launched
# from any working directory.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.game import Game
from scenes.menu_scene import MenuScene


def main():
    game = Game()
    game.change_state(MenuScene(game))
    game.run()          # Blocks until the player quits


if __name__ == "__main__":
    main()
