# backend/app/services/ai/base_bot.py
from abc import ABC, abstractmethod
from typing import Tuple, List, Optional

# Assuming Board is defined in game_logic or imported appropriately
# from app.services.game_logic import Board as GameLogicBoard
GameLogicBoard = List[List[Optional[str]]]


class BaseBot(ABC):
    def __init__(self, player_piece: str):
        self.player_piece = player_piece  # 'X' or 'O'

    @abstractmethod
    def get_move(self, board: GameLogicBoard) -> Optional[Tuple[int, str]]:
        """
        Determines the AI's next move.
        Returns a tuple (row_index, side: 'L'|'R') or None if no valid move.
        """
        pass
