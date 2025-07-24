from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Tuple, Callable, Optional, Set, Union

BOARD_SIZE = 8
EMPTY_SQUARE = "--"

class PieceColor(Enum):
    WHITE = "w"
    BLACK = "b"
    EMPTY = "-"
    
    @property
    def opposite(self) -> 'PieceColor':
        if self == PieceColor.WHITE:
            return PieceColor.BLACK
        elif self == PieceColor.BLACK:
            return PieceColor.WHITE
        return PieceColor.EMPTY

class PieceType(Enum):
    PAWN = "p"
    ROOK = "R"
    KNIGHT = "N"
    BISHOP = "B"
    QUEEN = "Q"
    KING = "K"
    EMPTY = "-"

# Position class for better coordinate handling
@dataclass(frozen=True)
class Position:
    row: int
    col: int
    
    def __add__(self, other: Position) -> Position:
        return Position(self.row + other.row, self.col + other.col)
    
    def __mul__(self, scalar: int) -> Position:
        return Position(self.row * scalar, self.col * scalar)
    
    def is_valid(self) -> bool:
        return 0 <= self.row < BOARD_SIZE and 0 <= self.col < BOARD_SIZE
        
    @classmethod
    def from_chess_notation(cls, notation: str) -> Position:
        """Convert chess notation (e.g., 'e4') to a Position object"""
        file_to_col = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
        rank_to_row = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
        
        if len(notation) != 2:
            raise ValueError(f"Invalid chess notation: {notation}")
        
        file, rank = notation[0].lower(), notation[1]
        if file not in file_to_col or rank not in rank_to_row:
            raise ValueError(f"Invalid chess notation: {notation}")
            
        return cls(rank_to_row[rank], file_to_col[file])
    
    def to_chess_notation(self) -> str:
        """Convert Position to chess notation (e.g., 'e4')"""
        col_to_file = {0: "a", 1: "b", 2: "c", 3: "d", 4: "e", 5: "f", 6: "g", 7: "h"}
        row_to_rank = {7: "1", 6: "2", 5: "3", 4: "4", 3: "5", 2: "6", 1: "7", 0: "8"}
        
        return col_to_file[self.col] + row_to_rank[self.row]

# Main chess board class
class ChessBoard:
    def __init__(self):
        # Initialize the board with the starting position
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            [EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE],
            [EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE],
            [EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE],
            [EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]
        
    def get_piece(self, pos: Position) -> str:
        """Get the piece at the specified position"""
        if not pos.is_valid():
            return EMPTY_SQUARE
        return self.board[pos.row][pos.col]
    
    def set_piece(self, pos: Position, piece: str) -> None:
        """Set the piece at the specified position"""
        if pos.is_valid():
            self.board[pos.row][pos.col] = piece
    
    def is_empty(self, pos: Position) -> bool:
        """Check if the position is empty"""
        return self.get_piece(pos) == EMPTY_SQUARE
    
    def get_piece_color(self, pos: Position) -> PieceColor:
        """Get the color of the piece at the specified position"""
        piece = self.get_piece(pos)
        if piece == EMPTY_SQUARE:
            return PieceColor.EMPTY
        return PieceColor.WHITE if piece[0] == PieceColor.WHITE.value else PieceColor.BLACK
            
    def __getitem__(self, row):
        """Make the ChessBoard subscriptable with board[row][col]"""
        return self.board[row]
        
    def __setitem__(self, row, value):
        """Allow setting rows with board[row] = value"""
        self.board[row] = value