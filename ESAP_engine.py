from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto, unique
from typing import Dict, List, Tuple, Callable, Optional, Set, Union, TypeVar, Generic, Any
import copy
import random

import ESAP_minimax_math

# game configuration constants
CHESS_DIMENSION = 8  # 8x8 chess board... because duh lol
NULL_SQUARE = "--"   # representation of an empty square

# type definitions for improved code clarity
SquareContent = str  # a string representing piece on a square (like  wp for white pawn)
BoardMatrix = List[List[SquareContent]]  # 2d representation of the chess board

@unique
class ChessSide(Enum):
    """represents the sides in a chess game"""
    LIGHT = "w"  # white pieces
    DARK = "b"   # black pieces
    NONE = "-"   # used for empty squares
    
    @property
    def opponent(self) -> 'ChessSide':
        """returns the opposing side"""
        if self == ChessSide.LIGHT:
            return ChessSide.DARK
        elif self == ChessSide.DARK:
            return ChessSide.LIGHT
        return ChessSide.NONE

@unique
class ChessPieceCategory(Enum):
    """Defines the different types of chess pieces"""
    PAWN = "p"
    ROOK = "R"
    KNIGHT = "N"
    BISHOP = "B"
    QUEEN = "Q"
    KING = "K"
    NONE = "-"  # used for empty squares

# board coordinate system representation
@dataclass(frozen=True)
class BoardCoordinate:
    """Immutable class representing a position on the chess board
    
    Attributes:
        rank: int - The row on the board (0-7, 0 is the top row)
        file: int - The column on the board (0-7, 0 is the leftmost column)
    """
    rank: int  # chess terminology: rank = row
    file: int  # chess terminology: file = column
    

    # vectors???
    # is that a minions refernece???
    # with order and magnitiude

    def __add__(self, other: BoardCoordinate) -> BoardCoordinate:
        """Vector addition of coordinates"""
        return BoardCoordinate(self.rank + other.rank, self.file + other.file)
    
    def __mul__(self, scalar: int) -> BoardCoordinate:
        """Scalar multiplication of coordinates"""
        return BoardCoordinate(self.rank * scalar, self.file * scalar)
    
    def is_on_board(self) -> bool:
        """Check if the coordinate is within the bounds of the chess board"""
        return 0 <= self.rank < CHESS_DIMENSION and 0 <= self.file < CHESS_DIMENSION
        
    @classmethod
    def from_algebraic(cls, notation: str) -> BoardCoordinate:
        """Create a BoardCoordinate from algebraic chess notation (e.g., 'e4')
        
        Args:
            notation: A string in algebraic chess notation (e.g., 'e4')
            
        Returns:
            A BoardCoordinate object representing the position
            
        Raises:
            ValueError: If the notation is invalid
        """
        # mapping from algebraic notation to internal representation
        file_mapping = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
        rank_mapping = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
        
        if len(notation) != 2:
            raise ValueError(f"Invalid algebraic notation: {notation}")
        
        file_char, rank_char = notation[0].lower(), notation[1]
        if file_char not in file_mapping or rank_char not in rank_mapping:
            raise ValueError(f"Invalid algebraic notation: {notation}")
            
        return cls(rank_mapping[rank_char], file_mapping[file_char])
    
    def to_algebraic(self) -> str:
        """Convert the coordinate to algebraic chess notation (e.g., 'e4')
        
        Returns:
            A string in algebraic chess notation
        """
        file_mapping = {0: "a", 1: "b", 2: "c", 3: "d", 4: "e", 5: "f", 6: "g", 7: "h"}
        rank_mapping = {7: "1", 6: "2", 5: "3", 4: "4", 3: "5", 2: "6", 1: "7", 0: "8"}
        
        return file_mapping[self.file] + rank_mapping[self.rank]
        
    @property
    def row(self) -> int:
        return self.rank
        
    @property
    def col(self) -> int:
        return self.file
        
    from_chess_notation = from_algebraic
    to_chess_notation = to_algebraic

# chess piece representation system
class ChessPiece:
    """Base class for all chess pieces
    
    This abstract class defines the interface for all chess pieces and provides
    common functionality shared by all piece types.
    """
    def __init__(self, side: ChessSide, location: BoardCoordinate):
        """Initialize a new chess piece
        
        Args:
            side: The side (color) of the piece
            location: The current position of the piece on the board
        """
        self.side = side
        self.location = location
        self.movement_history = []  # Track piece movement for special rules like on crossant
        
    @property
    def has_moved(self) -> bool:
        """Whether the piece has moved from its starting position"""
        return len(self.movement_history) > 0
        
    @property
    def category(self) -> ChessPieceCategory:
        """The type/category of this chess piece"""
        raise NotImplementedError("Subclasses must implement the category property")
    
    @property
    def notation(self) -> str:
        """The two-character notation used in board representation (e.g., 'wp' for white pawn)"""
        return f"{self.side.value}{self.category.value}"
    
    def calculate_legal_moves(self, board: 'ChessMatrix') -> List['ChessAction']:
        """Calculate all legal moves for this piece without considering checks
        
        Args:
            board: The current state of the chess board
            
        Returns:
            A list of possible chess actions this piece can take
        """
        raise NotImplementedError("Subclasses must implement calculate_legal_moves")
        
    @property
    def color(self) -> ChessSide:
        return self.side
        
    @property
    def position(self) -> BoardCoordinate:
        return self.location
        
    @property
    def piece_type(self) -> ChessPieceCategory:
        return self.category
        
    get_possible_moves = calculate_legal_moves

@dataclass
class ChessAction:
    """Represents a chess move or action
    
    This class encapsulates all information about a chess move, including special moves
    like castling, en passant captures, and pawn promotions.
    """
    origin: BoardCoordinate
    destination: BoardCoordinate
    moving_piece: str
    captured_piece: str = NULL_SQUARE
    promotion: bool = False
    castling: bool = False
    en_passant: bool = False
    
    @property
    def unique_id(self) -> int:
        """Generate a unique identifier for this action
        
        Returns:
            An integer that uniquely identifies this move based on its coordinates
        """
        return (self.origin.rank * 1000 + self.origin.file * 100 + 
                self.destination.rank * 10 + self.destination.file)
    
    def __eq__(self, other) -> bool:
        """compare two chess actions for equality
        
        Args:
            other: Another object to compare with
            
        Returns:
            Trrue if the other object is a ChessAction with the same unique_id
        """
        if isinstance(other, ChessAction):
            return self.unique_id == other.unique_id
        return False
    
    def to_algebraic_notation(self) -> str:
        """Convert the action to algebraic chess notation (e.g., 'e2e4')
        
        Returns:
            A string representing the move in algebraic notation
        """
        return f"{self.origin.to_algebraic()}{self.destination.to_algebraic()}"
    
    def __str__(self) -> str:
        """generate a human-readable string representation of the action
        
        returns:
            a string representation in standard chess notation
        """
        # handle castling notation
        if self.castling:
            return "O-O" if self.destination.file == 6 else "O-O-O"
        
        # get the destination square in algebraic notation
        target_square = self.destination.to_algebraic()
        
        # for pawn moves
        if self.moving_piece[1] == 'p':
            if self.captured_piece != NULL_SQUARE:  # capture
                return f"{self.origin.to_algebraic()[0]}x{target_square}"
            return target_square
        
        # for piece moves
        piece_symbol = self.moving_piece[1]
        capture_symbol = "x" if self.captured_piece != NULL_SQUARE else ""
        
        return f"{piece_symbol}{capture_symbol}{target_square}"
        
    # for backward compatibility
    start_pos = property(lambda self: self.origin)
    end_pos = property(lambda self: self.destination)
    piece_moved = property(lambda self: self.moving_piece)
    piece_captured = property(lambda self: self.captured_piece)
    is_pawn_promotion = property(lambda self: self.promotion)
    is_castle_move = property(lambda self: self.castling)
    is_enpassant_move = property(lambda self: self.en_passant)
    move_id = unique_id
    get_chess_notation = to_algebraic_notation

# castling privileges management
@dataclass
class CastlingPrivileges:
    """tracks the castling rights for both players
    
    this class maintains the state of which castling moves are still legal for each player,
    based on whether the king or rooks have moved or been captured.
    """
    # using the original attribute names for compatibility
    wks: bool = True  # white kingside
    wqs: bool = True  # white queenside
    bks: bool = True  # black kingside
    bqs: bool = True  # black queenside
    
    # properties for more readable code
    @property
    def white_kingside(self) -> bool:
        return self.wks
        
    @property
    def white_queenside(self) -> bool:
        return self.wqs
        
    @property
    def black_kingside(self) -> bool:
        return self.bks
        
    @property
    def black_queenside(self) -> bool:
        return self.bqs

# chess board representation and management
class ChessMatrix:
    """represents the chess board and provides methods for manipulating pieces
    
    this class maintains the state of the chess board and provides methods for
    accessing and modifying the board state in a controlled manner.
    """
    def __init__(self):
        """init a new chess board with the standard starting position"""
        # init the board with the starting position using standard notation
        self.grid = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],  # Rank 8
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],  # Rank 7
            [NULL_SQUARE, NULL_SQUARE, NULL_SQUARE, NULL_SQUARE, NULL_SQUARE, NULL_SQUARE, NULL_SQUARE, NULL_SQUARE],  # Rank 6
            [NULL_SQUARE, NULL_SQUARE, NULL_SQUARE, NULL_SQUARE, NULL_SQUARE, NULL_SQUARE, NULL_SQUARE, NULL_SQUARE],  # Rank 5
            [NULL_SQUARE, NULL_SQUARE, NULL_SQUARE, NULL_SQUARE, NULL_SQUARE, NULL_SQUARE, NULL_SQUARE, NULL_SQUARE],  # Rank 4
            [NULL_SQUARE, NULL_SQUARE, NULL_SQUARE, NULL_SQUARE, NULL_SQUARE, NULL_SQUARE, NULL_SQUARE, NULL_SQUARE],  # Rank 3
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],  # Rank 2
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]   # Rank 1
        ]
        
        # track piece positions for faster access (optimization)
        self._piece_positions = {}
        self._initialize_piece_positions()
    
    def _initialize_piece_positions(self) -> None:
        """Initialize the piece position tracking dictionary"""
        for rank in range(CHESS_DIMENSION):
            for file in range(CHESS_DIMENSION):
                piece = self.grid[rank][file]
                if piece != NULL_SQUARE:
                    if piece not in self._piece_positions:
                        self._piece_positions[piece] = []
                    self._piece_positions[piece].append(BoardCoordinate(rank, file))
    
    def get_piece_at(self, location: BoardCoordinate) -> str:
        """Get the piece at the specified board location
        
        Args:
            location: The board coordinate to check
            
        Returns:
            The piece notation at the location, or NULL_SQUARE if invalid or empty
        """
        if not location.is_on_board():
            return NULL_SQUARE
        return self.grid[location.rank][location.file]
    
    def place_piece(self, location: BoardCoordinate, piece: str) -> None:
        """Place a piece at the specified board location
        
        Args:
            location: The board coordinate to place the piece
            piece: The piece notation to place
        """
        if location.is_on_board():
            self.grid[location.rank][location.file] = piece
            
            # update piece position tracking
            if piece != NULL_SQUARE:
                if piece not in self._piece_positions:
                    self._piece_positions[piece] = []
                self._piece_positions[piece].append(location)
    
    def is_square_empty(self, location: BoardCoordinate) -> bool:
        """Check if the specified board location is empty
        
        Args:
            location: The board coordinate to check
            
        Returns:
            True if the location is empty, False otherwise
        """
        return self.get_piece_at(location) == NULL_SQUARE
    
    def get_piece_side(self, location: BoardCoordinate) -> ChessSide:
        """Get the side (color) of the piece at the specified location
        
        Args:
            location: The board coordinate to check (obvi)
            
        Returns:
            The side of the piece, or ChessSide.NONE if empty
        """
        piece = self.get_piece_at(location)
        if piece == NULL_SQUARE:
            return ChessSide.NONE
        return ChessSide.LIGHT if piece[0] == 'w' else ChessSide.DARK
    
    def __getitem__(self, rank):
        """Make the ChessMatrix subscriptable with board[rank][file]
        
        Args:
        rank: The rank (row) index
            
        Returns:
            The row at the specified rank
        """
        return self.grid[rank]
    
    def __setitem__(self, rank, value):
        """Allow setting ranks with board[rank] = value
        
        Args:
            rank: The rank (row) index
            value: The new row value
        """
        self.grid[rank] = value
        
    @property
    def board(self):
        return self.grid
        
    get_piece = get_piece_at
    set_piece = place_piece
    is_empty = is_square_empty
    get_piece_color = get_piece_side

# chess game state management
class ChessGameState:
    """manages the state of a chess game
    
    this class is responsible for tracking the current state of a chess game,
    including the board position, whose turn it is, and special conditions like
    check, checkmate, and castling rights.
    """
    def __init__(self):
        """Initialize a new chess game with the standard starting position"""
        # core game state
        self.board = ChessMatrix()
        self.active_side = ChessSide.LIGHT  # white moves first
        self.action_history = []  # record of all moves made
        
        # king positions (critical for check detection)
        self.light_king_location = BoardCoordinate(7, 4)  # e1
        self.dark_king_location = BoardCoordinate(0, 4)   # e8
        
        # game status flags
        self.check_status = False
        self.checkmate_status = False
        self.stalemate_status = False
        
        # special move tracking
        self.en_passant_square = ()
        self.en_passant_history = [self.en_passant_square]
        
        # check detection helpers
        self.pinned_pieces = []
        self.checking_pieces = []
        
        # map piece types to their move generation methods
        self.move_generators = {
            'p': self.calculate_pawn_moves,
            'R': self.calculate_rook_moves,
            'N': self.calculate_knight_moves,
            'B': self.calculate_bishop_moves,
            'Q': self.calculate_queen_moves,
            'K': self.calculate_king_moves
        }
        
        # castling rights tracking
        self.castling_rights = CastlingPrivileges(True, True, True, True)
        self.castling_rights_history = [CastlingPrivileges(
            self.castling_rights.wks,
            self.castling_rights.wqs,
            self.castling_rights.bks,
            self.castling_rights.bqs
        )]
        
        # position repetition tracking for threefold repetition rule
        self.position_history = {}
        self.current_position_key = self.generate_position_key()
        self.position_history[self.current_position_key] = 1
        
    def generate_position_key(self) -> str:
        """Generate a unique key for the current board position
        
        Returns:
            A string representing the current board state for repetition detection
        """
        key_parts = []
        
        # add board state
        for rank in range(CHESS_DIMENSION):
            for file in range(CHESS_DIMENSION):
                piece = self.board[rank][file]
                if piece != NULL_SQUARE:
                    key_parts.append(f"{piece}{rank}{file}")
        
        # add whose turn it is
        key_parts.append(f"turn:{self.active_side.value}")
        
        # add castling rights
        key_parts.append(f"castle:{int(self.castling_rights.wks)}{int(self.castling_rights.wqs)}{int(self.castling_rights.bks)}{int(self.castling_rights.bqs)}")
        
        # add en passant target if any
        if self.en_passant_square:
            key_parts.append(f"ep:{self.en_passant_square[0]}{self.en_passant_square[1]}")
            
        return "|".join(key_parts)
        
    @property # this is a decorator, it looks cool, i cannot be stopped.
    def white_to_move(self) -> bool:
        return self.active_side == ChessSide.LIGHT
        
    @property
    def move_log(self) -> list:
        return self.action_history
        
    @property
    def white_king_position(self) -> BoardCoordinate:
        return self.light_king_location
        
    @property
    def black_king_position(self) -> BoardCoordinate:
        return self.dark_king_location
        
    @property
    def in_check(self) -> bool:
        return self.check_status
        
    @property
    def checkmate(self) -> bool:
        return self.checkmate_status
        
    @property
    def stalemate(self) -> bool:
        return self.stalemate_status
        
    @property
    def enpassant_target(self):
        return self.en_passant_square
        
    @property
    def enpassant_log(self) -> list:
        return self.en_passant_history
        
    @property
    def pins(self) -> list:
        return self.pinned_pieces
        
    @property
    def checks(self) -> list:
        return self.checking_pieces
        
    @property
    def moveFunctions(self) -> dict:
        return self.move_generators


    def execute_move(self, action):
        """Execute a chess move on the board
        
        This method updates the board state and all relevant game state variables
        when a move is executed.
        
        Args:
            action: the chess movee to execute
        """
        # update the board by moving the piece
        self.board[action.origin.rank][action.origin.file] = NULL_SQUARE
        self.board[action.destination.rank][action.destination.file] = action.moving_piece
        
        # record the move in the game history
        self.action_history.append(action)
        
        # switch active player
        self.active_side = ChessSide.DARK if self.active_side == ChessSide.LIGHT else ChessSide.LIGHT
        
        # update king position tracking if a king was moved
        if action.moving_piece == "wK":
            self.light_king_location = action.destination
        elif action.moving_piece == "bK":
            self.dark_king_location = action.destination

        # handle pawn promotion
        if action.promotion:
            # promote to queen by default
            self.board[action.destination.rank][action.destination.file] = action.moving_piece[0] + "Q"

        # handle en passant capture
        if action.en_passant:
            # remove the captured pawn
            self.board[action.origin.rank][action.destination.file] = NULL_SQUARE

        # update en passant target square
        if action.moving_piece[1] == 'p' and abs(action.origin.rank - action.destination.rank) == 2:
            # set en passant target on two-square pawn advance
            middle_rank = (action.origin.rank + action.destination.rank) // 2
            self.en_passant_square = (middle_rank, action.origin.file)
        else:
            # clear en passant target
            self.en_passant_square = ()

        # record en passant state in history
        self.en_passant_history.append(self.en_passant_square)

        # Handle castling
        if action.castling:
            if action.destination.file - action.origin.file == 2:  # Kingside castle
                # move the rook from h-file to f-file
                rook_origin_file = action.destination.file + 1
                rook_destination_file = action.destination.file - 1
                self.board[action.destination.rank][rook_destination_file] = self.board[action.destination.rank][rook_origin_file]
                self.board[action.destination.rank][rook_origin_file] = NULL_SQUARE
            else:  # queenside castle
                # move the rook from a-file to d-file
                rook_origin_file = action.destination.file - 2
                rook_destination_file = action.destination.file + 1
                self.board[action.destination.rank][rook_destination_file] = self.board[action.destination.rank][rook_origin_file]
                self.board[action.destination.rank][rook_origin_file] = NULL_SQUARE

        # update castling rights
        self.update_castling_privileges(action)
        
        # update position history for threefold repetition detection
        self.current_position_key = self.generate_position_key()
        self.position_history[self.current_position_key] = self.position_history.get(self.current_position_key, 0) + 1
        
    makeMove = execute_move

    def revert_last_move(self):
        """Revert the last move made on the board
        
        This method undoes the last move, restoring the board to its previous state
        and updating all relevant game state variables.
        
        Returns:
            bool: True if a move was successfully undone, False otherwise
        """
        # check if there are any moves to undo
        if not self.action_history:
            return False
            
        # get the last move from the history
        last_action = self.action_history.pop()
        
        # restore the pieces to their original positions
        self.board[last_action.origin.rank][last_action.origin.file] = last_action.moving_piece
        self.board[last_action.destination.rank][last_action.destination.file] = last_action.captured_piece
        
        # switch back to the previous player
        self.active_side = ChessSide.DARK if self.active_side == ChessSide.LIGHT else ChessSide.LIGHT
        
        # update king position tracking if a king was moved
        if last_action.moving_piece == "wK":
            self.light_king_location = last_action.origin
        elif last_action.moving_piece == "bK":
            self.dark_king_location = last_action.origin
            
        # handle en passant move reversal
        if last_action.en_passant:
            # clear the destination square
            self.board[last_action.destination.rank][last_action.destination.file] = NULL_SQUARE
            # restore the captured pawn
            self.board[last_action.origin.rank][last_action.destination.file] = last_action.captured_piece
            
        # restore previous en passant target to proceed in reverting the move
        self.en_passant_history.pop()
        self.en_passant_square = self.en_passant_history[-1]
        
        # restore previous castling rights to proceed
        self.castling_rights_history.pop()
        previous_rights = self.castling_rights_history[-1]
        self.castling_rights = CastlingPrivileges(
            previous_rights.wks,
            previous_rights.wqs,
            previous_rights.bks,
            previous_rights.bqs
        )
        
        # handle castle move reversal
        if last_action.castling:
            if last_action.destination.file - last_action.origin.file == 2:  # Kingside
                # move the rook back from f-file to h-file
                rook_current_file = last_action.destination.file - 1
                rook_original_file = last_action.destination.file + 1
                self.board[last_action.destination.rank][rook_original_file] = self.board[last_action.destination.rank][rook_current_file]
                self.board[last_action.destination.rank][rook_current_file] = NULL_SQUARE
            else:  # queenside
                # move the rook back from d-file to a-file
                rook_current_file = last_action.destination.file + 1
                rook_original_file = last_action.destination.file - 2
                self.board[last_action.destination.rank][rook_original_file] = self.board[last_action.destination.rank][rook_current_file]
                self.board[last_action.destination.rank][rook_current_file] = NULL_SQUARE
                
        # reset game ending flags
        self.checkmate_status = False
        self.stalemate_status = False
        
        # update position history for threefold repetition detection
        if self.current_position_key in self.position_history:
            self.position_history[self.current_position_key] -= 1
            if self.position_history[self.current_position_key] == 0:
                del self.position_history[self.current_position_key]
        
        # generate the new current position key
        self.current_position_key = self.generate_position_key()
        
        return True
        
    undoMove = revert_last_move

    def update_castling_privileges(self, action):
        """Update castling rights based on the executed move
        
        This method updates the castling rights whenever a king or rook moves,
        or when a rook is captured.
         
        Args:
                   action: the chess move that was executed
        """
        # king movement invalidates all castling rights for that side
        if action.moving_piece == "wK":
            self.castling_rights.wks = False  # white kingside
            self.castling_rights.wqs = False  # white queenside
        elif action.moving_piece == "bK":
            self.castling_rights.bks = False  # black kingside
            self.castling_rights.bqs = False  # black queenside
            
        # rook movement invalidates castling on that side :nerd:
        elif action.moving_piece == "wR":
            if action.origin.rank == 7:  # white's back rank
                if action.origin.file == 0:  # queen's rook (a1)
                    self.castling_rights.wqs = False
                elif action.origin.file == 7:  # king's rook (h1)
                    self.castling_rights.wks = False
        elif action.moving_piece == "bR":
            if action.origin.rank == 0:  # black's back rank
                if action.origin.file == 0:  # queen's rook (a8)
                    self.castling_rights.bqs = False
                elif action.origin.file == 7:  # king's rook (h8)
                    self.castling_rights.bks = False

        # rook capture invalidates castling with that rook
        if action.captured_piece == "wR":
            if action.destination.rank == 7:  # white's back rank
                if action.destination.file == 0:  # queen's rook (a1)
                    self.castling_rights.wqs = False
                elif action.destination.file == 7:  # king's rook (h1)
                    self.castling_rights.wks = False
        elif action.captured_piece == "bR":
            if action.destination.rank == 0:  # black's back rank
                if action.destination.file == 0:  # queen's rook (a8)
                    self.castling_rights.bqs = False
                elif action.destination.file == 7:  # king's rook (h8)
                    self.castling_rights.bks = False
                    
        # record the updated castling rights in the history
        self.castling_rights_history.append(CastlingPrivileges(
            self.castling_rights.wks,
            self.castling_rights.wqs,
            self.castling_rights.bks,
            self.castling_rights.bqs
        ))
        
    updateCastleRight = update_castling_privileges
            


    def get_legal_moves(self):
        """Calculate all legal moves in the current position
        
        This method determines all legal moves considering checks, pins, and other
        chess rules. It handles different scenarios based on whether the king is in check.
        
        Returns:
            list: A list of all legal moves in the current position
        """
        # init an empty list to store legal moves
        legal_moves = []
        
        # check if the king is in check and identify pins and checking pieces
        self.check_status, self.pinned_pieces, self.checking_pieces = self.check_for_pins_and_checks()
        
        # get the current king's position based on whose turn it is
        if self.active_side == ChessSide.LIGHT:
            king_rank = self.light_king_location.rank
            king_file = self.light_king_location.file
        else:
            king_rank = self.dark_king_location.rank
            king_file = self.dark_king_location.file

        # handle different scenarios based on check status
        if self.check_status:
            # single check: can block, capture the checking piece, or move the king
            if len(self.checking_pieces) == 1:
                # get all candidate moves
                legal_moves = self.generate_candidate_moves()
                
                # extract information about the checking piece
                check = self.checking_pieces[0]
                check_rank, check_file = check[0], check[1]
                checking_piece = self.board[check_rank][check_file]
                
                # determine valid squares to block or capture
                valid_target_squares = []
                
                # knights can only be captured, not blocked
                if checking_piece[1] == 'N':
                    valid_target_squares = [(check_rank, check_file)]
                else:
                    # for sliding pieces (bishop, rook, queen), can block along the attack line
                    for i in range(1, CHESS_DIMENSION):
                        # calculate squares along the attack ray
                        blocking_square = (king_rank + check[2] * i, king_file + check[3] * i)
                        valid_target_squares.append(blocking_square)
                        
                        # stop once we reach the checking piece
                        if blocking_square[0] == check_rank and blocking_square[1] == check_file:
                            break
                
                # filter moves: only keep king moves and moves that block/capture the checking piece
                for i in range(len(legal_moves) - 1, -1, -1):
                    if legal_moves[i].moving_piece[1] != 'K':
                        if (legal_moves[i].destination.rank, legal_moves[i].destination.file) not in valid_target_squares:
                            legal_moves.remove(legal_moves[i])
            
            # double check: only king moves are legal
            else:
                # only the king can move in double check
                self.calculate_king_moves(king_rank, king_file, legal_moves)
        
        # no check: all moves are potentially legal (subject to pins)
        else:
            legal_moves = self.generate_candidate_moves()

        # Check for checkmate or stalemate
        if not legal_moves:
            if self.check_status:
                self.checkmate_status = True  # Checkmate
            else:
                self.stalemate_status = True  # Stalemate
                
        # Check for threefold repetition
        if self.current_position_key in self.position_history and self.position_history[self.current_position_key] >= 3:
            self.stalemate_status = True  # Draw by threefold repetition
            
        # Check for insufficient material
        if self.has_insufficient_material():
            self.stalemate_status = True  # Draw by insufficient material

        return legal_moves
        
    # For backward compatibility
    getValidMoves = get_legal_moves


    def generate_candidate_moves(self):
        """Generate all possible moves without considering checks
        
        This method iterates through the board and generates all possible moves for
        each piece of the active player, without considering whether they would leave
        the king in check.
        
        Returns:
            list: A list of all candidate moves in the current position
        """
        # Initialize an empty list to store candidate moves
        candidate_moves = []
        
        # Iterate through the entire board
        for rank in range(CHESS_DIMENSION):
            for file in range(CHESS_DIMENSION):
                # Get the piece color at the current square
                piece_color = self.board[rank][file][0]
                
                # Check if the piece belongs to the active player
                is_active_player_piece = (
                    (piece_color == ChessSide.LIGHT.value and self.active_side == ChessSide.LIGHT) or
                    (piece_color == ChessSide.DARK.value and self.active_side == ChessSide.DARK)
                )
                
                # If the piece belongs to the active player, generate its moves
                if is_active_player_piece:
                    # Get the piece type
                    piece_type = self.board[rank][file][1]
                    
                    # Call the appropriate move generation function for this piece type
                    self.move_generators[piece_type](rank, file, candidate_moves)
                    
        return candidate_moves
        
    # For backward compatibility
    getAllPossibleMoves = generate_candidate_moves

    def calculate_pawn_moves(self, rank, file, moves):
        """Calculate all possible pawn moves from the given position
        
        This method handles all pawn movement logic, including normal moves,
        captures, en passant captures, and initial two-square advances.
        
        Args:
            rank: The rank (row) of the pawn
            file: The file (column) of the pawn
            moves: List to append valid moves to
        """
        # Check if the pawn is pinned and determine the pin direction
        is_pinned = False
        pin_direction = ()
        
        # Check if this pawn is in the pins list
        for i in range(len(self.pinned_pieces) - 1, -1, -1):
            if self.pinned_pieces[i][0] == rank and self.pinned_pieces[i][1] == file:
                is_pinned = True
                pin_direction = (self.pinned_pieces[i][2], self.pinned_pieces[i][3])
                self.pinned_pieces.remove(self.pinned_pieces[i])
                break
        
        # get king position for en passant safety checks
        if self.active_side == ChessSide.LIGHT:
            king_rank = self.light_king_location.rank
            king_file = self.light_king_location.file
        else:
            king_rank = self.dark_king_location.rank
            king_file = self.dark_king_location.file
            
        # handle white pawn moves
        if self.active_side == ChessSide.LIGHT:
            # forward move (one square)
            if self.board[rank-1][file] == NULL_SQUARE:
                # check if move is allowed by pin
                if not is_pinned or pin_direction == (-1, 0):
                    moves.append(ChessAction(
                        BoardCoordinate(rank, file),
                        BoardCoordinate(rank-1, file),
                        self.board[rank][file],
                        NULL_SQUARE
                    ))
                    # two-square advance
                    if rank == 6 and self.board[4][file] == NULL_SQUARE:
                        moves.append(ChessAction(
                            BoardCoordinate(rank, file),
                            BoardCoordinate(4, file),
                            self.board[rank][file],
                            NULL_SQUARE
                        ))
            
            # captures to the left diagonal
            if file-1 >= 0:
                # normal capture
                if self.board[rank-1][file-1][0] == ChessSide.DARK.value:
                    if not is_pinned or pin_direction == (-1, -1):
                        moves.append(ChessAction(
                            BoardCoordinate(rank, file),
                            BoardCoordinate(rank-1, file-1),
                            self.board[rank][file],
                            self.board[rank-1][file-1]
                        ))
                # en passant capture
                elif (rank-1, file-1) == self.en_passant_square:
                    # special case: check for horizontal pins when capturing en passant
                    is_safe = True
                    if king_rank == rank:
                        # check for horizontal pin or discovered check
                        if king_file < file:
                            # king is to the left of the pawn
                            inside_range = range(king_file + 1, file-1)
                            outside_range = range(file+1, CHESS_DIMENSION)
                        else:
                            # king is to the right of the pawn
                            inside_range = range(king_file - 1, file, -1)
                            outside_range = range(file-2, -1, -1)
                            
                        # check for blocking pieces between king and pawn
                        for i in inside_range:
                            if self.board[rank][i] != NULL_SQUARE:
                                is_safe = False
                                break
                                
                        # check for attacking pieces beyond the pawn
                        for i in outside_range:
                            square = self.board[rank][i]
                            if square[0] == ChessSide.DARK.value and (square[1] == 'R' or square[1] == 'Q'):
                                is_safe = False
                                break
                            elif square != NULL_SQUARE:
                                # any other piece blocks the attack
                                is_safe = True
                                break
                                
                    if is_safe:
                        moves.append(ChessAction(
                            BoardCoordinate(rank, file),
                            BoardCoordinate(rank-1, file-1),
                            self.board[rank][file],
                            self.board[rank][file-1],
                            en_passant=True
                        ))
            
            # captures to the right diagonal
            if file+1 < CHESS_DIMENSION:
                # normal capture
                if self.board[rank-1][file+1][0] == ChessSide.DARK.value:
                    if not is_pinned or pin_direction == (-1, 1):
                        moves.append(ChessAction(
                            BoardCoordinate(rank, file),
                            BoardCoordinate(rank-1, file+1),
                            self.board[rank][file],
                            self.board[rank-1][file+1]
                        ))
                # en passant capture
                elif (rank-1, file+1) == self.en_passant_square:
                    # special case: check for horizontal pins when capturing en passant
                    is_safe = True
                    if king_rank == rank:
                        # check for horizontal pin or discovered check
                        if king_file < file:
                            # king is to the left of the pawn
                            inside_range = range(king_file + 1, file)
                            outside_range = range(file+2, CHESS_DIMENSION)
                        else:
                            # king is to the right of the pawn
                            inside_range = range(king_file - 1, file+1, -1)
                            outside_range = range(file-1, -1, -1)
                            
                        # Check for blocking pieces between king and pawn
                        for i in inside_range:
                            if self.board[rank][i] != NULL_SQUARE:
                                is_safe = False
                                break
                                
                        # check for attacking pieces beyond the pawn
                        for i in outside_range:
                            square = self.board[rank][i]
                            if square[0] == ChessSide.DARK.value and (square[1] == 'R' or square[1] == 'Q'):
                                is_safe = False
                                break
                            elif square != NULL_SQUARE:
                                # any other piece blocks the attack
                                is_safe = True
                                break
                                
                    if is_safe:
                        moves.append(ChessAction(
                            BoardCoordinate(rank, file),
                            BoardCoordinate(rank-1, file+1),
                            self.board[rank][file],
                            self.board[rank][file+1],
                            en_passant=True
                        ))
        
        # handle black pawn moves
        else:
            # forward move (one square)
            if self.board[rank+1][file] == NULL_SQUARE:
                # check if move is allowed by pin
                if not is_pinned or pin_direction == (1, 0):
                    moves.append(ChessAction(
                        BoardCoordinate(rank, file),
                        BoardCoordinate(rank+1, file),
                        self.board[rank][file],
                        NULL_SQUARE
                    ))
                    # two-square advance on first move
                    if rank == 1 and self.board[3][file] == NULL_SQUARE:
                        moves.append(ChessAction(
                            BoardCoordinate(rank, file),
                            BoardCoordinate(3, file),
                            self.board[rank][file],
                            NULL_SQUARE
                        ))
            
            # captures to the left diagonal
            if file-1 >= 0:
                # normal capture
                if self.board[rank+1][file-1][0] == ChessSide.LIGHT.value:
                    if not is_pinned or pin_direction == (1, -1):
                        moves.append(ChessAction(
                            BoardCoordinate(rank, file),
                            BoardCoordinate(rank+1, file-1),
                            self.board[rank][file],
                            self.board[rank+1][file-1]
                        ))
                # en passant capture
                elif (rank+1, file-1) == self.en_passant_square:
                    # special case: check for horizontal pins when capturing en passant
                    is_safe = True
                    if king_rank == rank:
                        # check for horizontal pin or discovered check
                        if king_file < file:
                            # king is to the left of the pawn
                            inside_range = range(king_file + 1, file-1)
                            outside_range = range(file+1, CHESS_DIMENSION)
                        else:
                            # king is to the right of the pawn
                            inside_range = range(king_file - 1, file, -1)
                            outside_range = range(file-2, -1, -1)
                            
                        # check for blocking pieces between king and pawn
                        for i in inside_range:
                            if self.board[rank][i] != NULL_SQUARE:
                                is_safe = False
                                break
                                
                        # Check for attacking pieces beyond the pawn
                        for i in outside_range:
                            square = self.board[rank][i]
                            if square[0] == ChessSide.LIGHT.value and (square[1] == 'R' or square[1] == 'Q'):
                                is_safe = False
                                break
                            elif square != NULL_SQUARE:
                                # Any other piece blocks the attack
                                is_safe = True
                                break
                                
                    if is_safe:
                        moves.append(ChessAction(
                            BoardCoordinate(rank, file),
                            BoardCoordinate(rank+1, file-1),
                            self.board[rank][file],
                            self.board[rank][file-1],
                            en_passant=True
                        ))
            
            # Captures to the right diagonal
            if file+1 < CHESS_DIMENSION:
                # Normal capture
                if self.board[rank+1][file+1][0] == ChessSide.LIGHT.value:
                    if not is_pinned or pin_direction == (1, 1):
                        moves.append(ChessAction(
                            BoardCoordinate(rank, file),
                            BoardCoordinate(rank+1, file+1),
                            self.board[rank][file],
                            self.board[rank+1][file+1]
                        ))
                # En passant capture
                elif (rank+1, file+1) == self.en_passant_square:
                    # Special case: check for horizontal pins when capturing en passant
                    is_safe = True
                    if king_rank == rank:
                        # Check for horizontal pin or discovered check
                        if king_file < file:
                            # King is to the left of the pawn
                            inside_range = range(king_file + 1, file)
                            outside_range = range(file+2, CHESS_DIMENSION)
                        else:
                            # King is to the right of the pawn
                            inside_range = range(king_file - 1, file+1, -1)
                            outside_range = range(file-1, -1, -1)
                            
                        # check for blocking pieces between king and pawn
                        for i in inside_range:
                            if self.board[rank][i] != NULL_SQUARE:
                                is_safe = False
                                break
                                
                        # check for attacking pieces beyond the pawn
                        for i in outside_range:
                            square = self.board[rank][i]
                            if square[0] == ChessSide.LIGHT.value and (square[1] == 'R' or square[1] == 'Q'):
                                is_safe = False
                                break
                            elif square != NULL_SQUARE:
                                # any other piece blocks the attack
                                is_safe = True
                                break
                                
                    if is_safe:
                        moves.append(ChessAction(
                            BoardCoordinate(rank, file),
                            BoardCoordinate(rank+1, file+1),
                            self.board[rank][file],
                            self.board[rank][file+1],
                            en_passant=True
                        ))
                        
    getPawnMoves = calculate_pawn_moves

    def calculate_rook_moves(self, rank, file, moves):
        """Calculate all possible rook moves from the given position
        
        This method handles all rook movement logic, including straight line moves
        and captures, while respecting pins and board boundaries.
        
        Args:
            rank: The rank (row) of the rook
            file: The file (column) of the rook
            moves: List to append valid moves to
        """
        # check if the rook is pinned and determine the pin direction
        is_pinned = False
        pin_direction = ()
        
        # check if this rook is in the pins list
        for i in range(len(self.pinned_pieces) - 1, -1, -1):
            if self.pinned_pieces[i][0] == rank and self.pinned_pieces[i][1] == file:
                is_pinned = True
                pin_direction = (self.pinned_pieces[i][2], self.pinned_pieces[i][3])
                # don't remove the pin if this is a queen (which also moves like a rook)
                if self.board[rank][file][1] != 'Q':
                    self.pinned_pieces.remove(self.pinned_pieces[i])
                break

        # define the four orthogonal directions a rook can move
        orthogonal_directions = [
            (-1, 0),  # North
            (1, 0),   # South
            (0, -1),  # West
            (0, 1)    # East
        ]
        
        # determine the opponent's color
        opponent_color = ChessSide.DARK.value if self.active_side == ChessSide.LIGHT else ChessSide.LIGHT.value
        
        # check moves in each direction
        for direction in orthogonal_directions:
            for distance in range(1, CHESS_DIMENSION):
                # calculate the target square
                target_rank = rank + direction[0] * distance
                target_file = file + direction[1] * distance
                
                # check if the target square is on the board
                if not (0 <= target_rank < CHESS_DIMENSION and 0 <= target_file < CHESS_DIMENSION):
                    break
                    
                # if the piece is pinned, it can only move along the pin direction
                if is_pinned and not (pin_direction == direction or pin_direction == (-direction[0], -direction[1])):
                    break
                    
                # get the piece at the target square
                target_piece = self.board[target_rank][target_file]
                
                # empty square - valid move
                if target_piece == NULL_SQUARE:
                    moves.append(ChessAction(
                        BoardCoordinate(rank, file),
                        BoardCoordinate(target_rank, target_file),
                        self.board[rank][file],
                        NULL_SQUARE
                    ))
                # Opponent's piece - valid capture, then stop
                elif target_piece[0] == opponent_color:
                    moves.append(ChessAction(
                        BoardCoordinate(rank, file),
                        BoardCoordinate(target_rank, target_file),
                        self.board[rank][file],
                        target_piece
                    ))
                    break
                # Own piece - blocked, stop looking in this direction
                else:
                    break
                    
    # For backward compatibility
    getRookMoves = calculate_rook_moves

    def calculate_knight_moves(self, rank, file, moves):
        """Calculate all possible knight moves from the given position
        
        This method handles all knight movement logic, including L-shaped moves
        and captures, while respecting pins and board boundaries.
        
        Args:
            rank: The rank (row) of the knight
            file: The file (column) of the knight
            moves: List to append valid moves to
        """
        # check if the knight is pinned
        is_pinned = False
        
        # check if this knight is in the pins list
        for i in range(len(self.pinned_pieces) - 1, -1, -1):
            if self.pinned_pieces[i][0] == rank and self.pinned_pieces[i][1] == file:
                # A pinned knight cannot move at all
                is_pinned = True
                self.pinned_pieces.remove(self.pinned_pieces[i])
                break
                
        # if the knight is pinned, it cannot move
        if is_pinned:
            return
            
        # define the eight L-shaped directions a knight can move
        knight_moves = [
            (-2, -1),  # 2 up, 1 left
            (-2, 1),   # 2 up, 1 right
            (-1, -2),  # 1 up, 2 left
            (-1, 2),   # 1 up, 2 right
            (1, -2),   # 1 down, 2 left
            (1, 2),    # 1 down, 2 right
            (2, -1),   # 2 down, 1 left
            (2, 1)     # 2 down, 1 right
        ]
        
        # determine the player's color
        player_color = ChessSide.LIGHT.value if self.active_side == ChessSide.LIGHT else ChessSide.DARK.value
        
        # check each possible knight move
        for move_offset in knight_moves:
            # calculate the target square
            target_rank = rank + move_offset[0]
            target_file = file + move_offset[1]
            
            # check if the target square is on the board
            if 0 <= target_rank < CHESS_DIMENSION and 0 <= target_file < CHESS_DIMENSION:
                # get the piece at the target square
                target_piece = self.board[target_rank][target_file]
                
                # knight can move if the target square is empty or contains an enemy piece
                if target_piece[0] != player_color:  # either empty or enemy piece
                    moves.append(ChessAction(
                        BoardCoordinate(rank, file),
                        BoardCoordinate(target_rank, target_file),
                        self.board[rank][file],
                        target_piece
                    ))
                    
    getKnightMoves = calculate_knight_moves

    def calculate_bishop_moves(self, rank, file, moves):
        """Calculate all possible bishop moves from the given position
        
        This method handles all bishop movement logic, including diagonal moves
        and captures, while respecting pins and board boundaries.
        
        Args:
            rank: The rank (row) of the bishop
            file: The file (column) of the bishop
            moves: List to append valid moves to
        """
        # check if the bishop is pinned and determine the pin direction
        is_pinned = False
        pin_direction = ()
        
        # check if this bishop is in the pins list
        for i in range(len(self.pinned_pieces) - 1, -1, -1):
            if self.pinned_pieces[i][0] == rank and self.pinned_pieces[i][1] == file:
                is_pinned = True
                pin_direction = (self.pinned_pieces[i][2], self.pinned_pieces[i][3])
                # don't remove the pin if this is a queen (which also moves like a bishop)
                if self.board[rank][file][1] != 'Q':
                    self.pinned_pieces.remove(self.pinned_pieces[i])
                break

        # Define the four diagonal directions a bishop can move
        diagonal_directions = [
            (-1, -1),  # Northwest
            (-1, 1),   # Northeast
            (1, -1),   # Southwest
            (1, 1)     # Southeast
        ]
        
        # determine the opponent's color
        opponent_color = ChessSide.DARK.value if self.active_side == ChessSide.LIGHT else ChessSide.LIGHT.value
        
        # check moves in each direction
        for direction in diagonal_directions:
            for distance in range(1, CHESS_DIMENSION):
                # calculate the target square
                target_rank = rank + direction[0] * distance
                target_file = file + direction[1] * distance
                
                # check if the target square is on the board
                if not (0 <= target_rank < CHESS_DIMENSION and 0 <= target_file < CHESS_DIMENSION):
                    break
                    
                # if the piece is pinned, it can only move along the pin direction
                if is_pinned and not (pin_direction == direction or pin_direction == (-direction[0], -direction[1])):
                    break
                    
                # get the piece at the target square
                target_piece = self.board[target_rank][target_file]
                
                # empty square - valid move
                if target_piece == NULL_SQUARE:
                    moves.append(ChessAction(
                        BoardCoordinate(rank, file),
                        BoardCoordinate(target_rank, target_file),
                        self.board[rank][file],
                        NULL_SQUARE
                    ))
                # opponent's piece - valid capture, then stop
                elif target_piece[0] == opponent_color:
                    moves.append(ChessAction(
                        BoardCoordinate(rank, file),
                        BoardCoordinate(target_rank, target_file),
                        self.board[rank][file],
                        target_piece
                    ))
                    break
                # Own piece - blocked, stop looking in this direction!!
                else:
                    break
                    
    getBishopMoves = calculate_bishop_moves

    def calculate_queen_moves(self, rank, file, moves):
        """Calculate all possible queen moves from the given position
        
        The queen combines the movement of a rook and bishop, so this method
        delegates to those piece movement methods.
        
        Args:
            rank: The rank (row) of the queen
            file: The file (column) of the queen
            moves: List to append valid moves to
        """
        # queen moves like a rook and bishop combined
        self.calculate_rook_moves(rank, file, moves)
        self.calculate_bishop_moves(rank, file, moves)
        
    getQueenMoves = calculate_queen_moves

    def calculate_king_moves(self, rank, file, moves):
        """Calculate all possible king moves from the given position
        
        This method handles all king movement logic, including one-square moves
        in all directions and castling, while ensuring the king doesn't move into check.
        
        Args:
            rank: The rank (row) of the king
            file: The file (column) of the king
            moves: List to append valid moves to
        """
        # Define the eight directions a king can move (one square in any direction)
        king_directions = [
            (-1, 0),   # North
            (1, 0),    # South
            (0, -1),   # West
            (0, 1),    # East
            (-1, -1),  # Northwestern university
            (-1, 1),   # Northeastern university
            (1, -1),   # Southwest airlinessssss
            (1, 1)     # Southeast
        ]
        
        # determine the player's color
        player_color = ChessSide.LIGHT.value if self.active_side == ChessSide.LIGHT else ChessSide.DARK.value
        
        # check each possible king move
        for direction in king_directions:
            # calculate the target square
            target_rank = rank + direction[0]
            target_file = file + direction[1]
            
            # check if the target square is on the board
            if 0 <= target_rank < CHESS_DIMENSION and 0 <= target_file < CHESS_DIMENSION:
                # get the piece at the target square
                target_piece = self.board[target_rank][target_file]
                
                # king can move if the target square doesn't contain a friendly piece
                if target_piece[0] != player_color:  # either empty or enemy piece
                    # temporarily move the king to check if the move would be into check
                    if player_color == ChessSide.LIGHT.value:
                        # save original position
                        original_position = self.white_king_position
                        # temporarily move king to new position
                        self.white_king_position = BoardCoordinate(target_rank, target_file)
                    else:
                        # save original position
                        original_position = self.black_king_position
                        # temporarily move king to new position
                        self.black_king_position = BoardCoordinate(target_rank, target_file)
                    
                    # check if the king would be in check after the move
                    in_check, pins, checks = self.check_for_pins_and_checks()
                    
                    # if the move doesn't put the king in check, it's valid
                    if not in_check:
                        moves.append(ChessAction(
                            BoardCoordinate(rank, file),
                            BoardCoordinate(target_rank, target_file),
                            self.board[rank][file],
                            target_piece
                        ))
                    
                    # restore the king's position
                    if player_color == ChessSide.LIGHT.value:
                        self.white_king_position = original_position
                    else:
                        self.black_king_position = original_position
        
        # check for castling moves
        self.calculate_castle_moves(rank, file, moves, player_color)
    
    getKingMoves = calculate_king_moves

    def check_for_pins_and_checks(self):
        """Analyze the board to detect pins and checks against the current player's king
        
        This method scans the board from the king's position outward in all directions
        to identify pieces that are pinned (can't move without exposing the king to check cuz then u can capture the king and thats bad)
        and pieces that are currently checking the king.
        
        Returns:
            tuple: (is_in_check, pinned_pieces, checking_pieces)
                - is_in_check: Boolean indicating if the king is in check
                - pinned_pieces: List of pieces that are pinned to the king
                - checking_pieces: List of enemy pieces that are checking the king
        """
        # initialize lists to track pinned pieces and checking pieces
        pinned_pieces = []
        checking_pieces = []
        is_in_check = False
        
        # determine the current player's color and king position
        if self.active_side == ChessSide.LIGHT:
            opponent_color = ChessSide.DARK.value
            player_color = ChessSide.LIGHT.value
            king_rank = self.white_king_position.row
            king_file = self.white_king_position.col
        else:
            opponent_color = ChessSide.LIGHT.value
            player_color = ChessSide.DARK.value
            king_rank = self.black_king_position.row
            king_file = self.black_king_position.col

        # Define all eight directions (orthogonal and diagonal)
        # The first four are orthogonal (rook directions)
        # The last four are diagonal (bishop directions)
        directions = [
            (-1, 0),   # North
            (1, 0),    # South
            (0, -1),   # West
            (0, 1),    # East
            (-1, -1),  # Northwest
            (-1, 1),   # Northeast
            (1, 1),    # Southeast
            (1, -1)    # Southwest airlines
        ]
        
        # check each direction from the king's position
        for direction_index, direction in enumerate(directions):
            # track potential pins (friendly pieces that might be pinned)
            potential_pin = None
            
            # look outward from the king in this direction
            for distance in range(1, CHESS_DIMENSION):
                # calculate the target square
                target_rank = king_rank + direction[0] * distance
                target_file = king_file + direction[1] * distance
                
                # check if the target square is on the board
                if not (0 <= target_rank < CHESS_DIMENSION and 0 <= target_file < CHESS_DIMENSION):
                    break
                    
                # get the piece at the target square
                target_piece = self.board[target_rank][target_file]
                
                # if the square contains a friendly piece (not the king)
                if target_piece[0] == player_color and target_piece[1] != 'K':
                    # if we haven't found a potential pin yet, this could be a pinned piece
                    if potential_pin is None:
                        potential_pin = (target_rank, target_file, direction[0], direction[1])
                    # if we've already found a potential pin, this second piece blocks any pin
                    else:
                        break
                        
                # if the square contains an enemy piece
                elif target_piece[0] == opponent_color:
                    piece_type = target_piece[1]
                    
                    # check if this enemy piece can attack the king in this direction
                    is_attacker = False
                    
                    # rook can attack in orthogonal directions (updown sideside)(0-3)
                    if 0 <= direction_index <= 3 and piece_type == 'R':
                        is_attacker = True
                    # bishop can attack in diagonal directions (4-7)
                    elif 4 <= direction_index <= 7 and piece_type == 'B':
                        is_attacker = True
                    # pawn can attack diagonally forward one square
                    elif (distance == 1 and piece_type == 'p' and 
                          ((opponent_color == ChessSide.DARK.value and 4 <= direction_index <= 5) or 
                           (opponent_color == ChessSide.LIGHT.value and 6 <= direction_index <= 7))):
                        is_attacker = True
                    # queen can attack in any direction (we have to nerf this in the next update)
                    elif piece_type == 'Q':
                        is_attacker = True
                    # King can attack one square in any direction
                    elif distance == 1 and piece_type == 'K':
                        is_attacker = True
                        
                    # if this piece can attack the king
                    if is_attacker:
                        # if there's no piece in between, it's a check
                        if potential_pin is None:
                            is_in_check = True
                            checking_pieces.append((target_rank, target_file, direction[0], direction[1]))
                            break
                        # if there is a piece in between, it's pinned
                        else:
                            pinned_pieces.append(potential_pin)
                            break
                    # if this piece can't attack the king, we can stop looking in this direction
                    else:
                        break
                        
        # check for knight checks (knights can jump over pieces wowowoowowowow)
        knight_moves = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        
        for move in knight_moves:
            target_rank = king_rank + move[0]
            target_file = king_file + move[1]
            
            # check if the target square is on the board
            if 0 <= target_rank < CHESS_DIMENSION and 0 <= target_file < CHESS_DIMENSION:
                target_piece = self.board[target_rank][target_file]
                
                # if there's an enemy knight, it's a check
                if target_piece[0] == opponent_color and target_piece[1] == 'N':
                    is_in_check = True
                    checking_pieces.append((target_rank, target_file, move[0], move[1]))
                    break

        return is_in_check, pinned_pieces, checking_pieces
        
    # for backward compatibility
    checkForPinsAndChecks = check_for_pins_and_checks

    def calculate_castle_moves(self, rank, file, moves, player_color=""):
        """Calculate castling moves for the king
        
        This method checks if castling is legal (kingside and/or queenside)
        and adds the corresponding moves to the list if they are.
        
        Args:
            rank: The rank (row) of the king
            file: The file (column) of the king
            moves: List to append valid moves to
            player_color: The color of the player ('w' or 'b')
        """
        # can't castle while in check
        if self.in_check:
            return
            
        # check kingside castling rights
        if ((self.active_side == ChessSide.LIGHT and self.castle_rights.wks) or 
            (self.active_side == ChessSide.DARK and self.castle_rights.bks)):
            self.calculate_kingside_castle_move(rank, file, moves, player_color)
            
        # check queenside castling rights
        if ((self.active_side == ChessSide.LIGHT and self.castle_rights.wqs) or 
            (self.active_side == ChessSide.DARK and self.castle_rights.bqs)):
            self.calculate_queenside_castle_move(rank, file, moves, player_color)
            
    getCastleMoves = calculate_castle_moves

    def calculate_kingside_castle_move(self, rank, file, moves, player_color=""):
        """Calculate kingside castling move for the king
        
        This method checks if kingside castling is legal by verifying that:
        1. The squares between the king and rook are empty
        2. The king doesn't move through or into check
        
        Args:
            rank: The rank (row) of the king
            file: The file (column) of the king
            moves: List to append valid moves to
            player_color: The color of the player ('w' or 'b')
        """
        # check if the squares between the king and rook are empty
        if self.board[rank][file+1] == NULL_SQUARE and self.board[rank][file+2] == NULL_SQUARE:
            # temporarily move the king to the first square it passes through
            if player_color == ChessSide.LIGHT.value:
                # save original position
                original_position = self.white_king_position
                # move king to first square
                self.white_king_position = BoardCoordinate(rank, file+1)
            else:
                # save original position
                original_position = self.black_king_position
                # move king to first square
                self.black_king_position = BoardCoordinate(rank, file+1)
                
            # check if the king would be in check at the intermediate position
            in_check1, pins, checks = self.check_for_pins_and_checks()
            
            # temporarily move the king to the final castling position
            if player_color == ChessSide.LIGHT.value:
                self.white_king_position = BoardCoordinate(rank, file+2)
            else:
                self.black_king_position = BoardCoordinate(rank, file+2)
                
            # check if the king would be in check at the final position
            in_check2, pins, checks = self.check_for_pins_and_checks()
            
            # Restore the king's original position
            if player_color == ChessSide.LIGHT.value:
                self.white_king_position = original_position
            else:
                self.black_king_position = original_position

            # if the king doesn't move through or into check, castling is legal
            if not in_check1 and not in_check2:
                moves.append(ChessAction(
                    BoardCoordinate(rank, file),
                    BoardCoordinate(rank, file+2),
                    self.board[rank][file],
                    NULL_SQUARE,
                    is_castle_move=True
                ))
                
    # For backward compatibility
    getKingsideCastleMove = calculate_kingside_castle_move

    def calculate_queenside_castle_move(self, rank, file, moves, player_color=""):
        """Calculate queenside castling move for the king
        
        This method checks if queenside castling is legal by verifying that:
        1. The squares between the king and rook are empty
        2. The king doesn't move through or into check
        3. The rook is in the correct position
        
        Args:
            rank: The rank (row) of the king
            file: The file (column) of the king
            moves: List to append valid moves to
            player_color: The color of the player ('w' or 'b')
        """
        # check if the squares between the king and rook are empty
        if (self.board[rank][file-1] == NULL_SQUARE and 
            self.board[rank][file-2] == NULL_SQUARE and 
            self.board[rank][file-3] == NULL_SQUARE):
            
            # save original position
            if player_color == ChessSide.LIGHT.value:
                original_position = self.white_king_position
            else:
                original_position = self.black_king_position
                
            # check first intermediate square (king moves one square left)
            if player_color == ChessSide.LIGHT.value:
                self.white_king_position = BoardCoordinate(rank, file-1)
            else:
                self.black_king_position = BoardCoordinate(rank, file-1)
                
            in_check1, pins, checks = self.check_for_pins_and_checks()
            
            # check second intermediate square (king's final position, two squares left)
            if player_color == ChessSide.LIGHT.value:
                self.white_king_position = BoardCoordinate(rank, file-2)
            else:
                self.black_king_position = BoardCoordinate(rank, file-2)
                
            in_check2, pins, checks = self.check_for_pins_and_checks()
            
            # check third intermediate square (not used by king but must be safe)
            if player_color == ChessSide.LIGHT.value:
                self.white_king_position = BoardCoordinate(rank, file-3)
            else:
                self.black_king_position = BoardCoordinate(rank, file-3)
                
            in_check3, pins, checks = self.check_for_pins_and_checks()
            
            # restore the king's original position
            #back tracking for searching
            if player_color == ChessSide.LIGHT.value:
                self.white_king_position = original_position
            else:
                self.black_king_position = original_position

            # if the king doesn't move through or into check, castling is legal
            # chess 101 fr
            if not in_check1 and not in_check2 and not in_check3:
                moves.append(ChessAction(
                    BoardCoordinate(rank, file),
                    BoardCoordinate(rank, file-2),
                    self.board[rank][file],
                    NULL_SQUARE,
                    is_castle_move=True
                ))
                
    # For backward compatibility
    getQueensideCastleMove = calculate_queenside_castle_move

class CastlingRights:
    """Class representing the castling rights for both player colrs
    
    This class stores whether each player can castle kingside or queenside.
    
    Attributes:
    wks: White kingside castling right
    wqs: White queenside castling right
        bks: Black kingside castling right
        bqs: Black queenside castling right
    """
    def __init__(self, white_kingside=True, white_queenside=True, black_kingside=True, black_queenside=True):
        """Initialize castling rights
        
        Args:
            white_kingside: Whether white can castle kingside
            white_queenside: Whether white can castle queenside
            black_kingside: Whether black can castle kingside
            black_queenside: Whether black can castle queenside
        """
        # keep attribute names as wks, wqs, bks, bqs - adrian
        self.wks = white_kingside
        self.wqs = white_queenside
        self.bks = black_kingside
        self.bqs = black_queenside
        
    def copy(self):
        """Create a deep copy of the castling rights
        
        Returns:
            A new CastlingRights object with the same values
        """
        return CastlingRights(self.wks, self.wqs, self.bks, self.bqs)
        
# for backward compatibility
castleRight = CastlingRights


# calling it chess action because it sounded more complicated than it is
# bc this is too simple and we gotta spice it up!
class ChessAction:
    """Class representing a chess move
    
    This class stores all information about a chess move, including start and end positions,
    the piece being moved, any piece being captured, and special move flags.
    
    Attributes:
        start_position: The starting position of the piece
        end_position: The ending position of the piece
        piece_moved: The piece being moved
        piece_captured: The piece being captured (if any)
        is_pawn_promotion: Whether this move is a pawn promotion
        is_en_passant_move: Whether this move is an en passant capture
        is_castle_move: Whether this move is a castling move
        is_capture: Whether this move captures a piece
        move_id: A unique identifier for the move
    """
    # mappings between chess notation and array indices
    RANK_TO_ROW = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    ROW_TO_RANK = {v: k for k, v in RANK_TO_ROW.items()}
    FILE_TO_COL = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    COL_TO_FILE = {v: k for k, v in FILE_TO_COL.items()}

    def __init__(self, start_square, end_square, piece_moved, piece_captured=NULL_SQUARE, 
                 is_en_passant_move=False, is_castle_move=False):
        """init a chess move (might need those LMAO)
        
        Args:
            start_square: The starting position (BoardCoordinate or tuple)
            end_square: The ending position (BoardCoordinate or tuple)
            piece_moved: The piece being moved
            piece_captured: The piece being captured (if any)
            is_en_passant_move: Whether this move is an en passant capture
            is_castle_move: Whether this move is a castling move
        """
        # handle both BoardCoordinate objects and tuples for compatibility :thumbs-up:
        if hasattr(start_square, 'row') and hasattr(start_square, 'col'):
            self.start_row = start_square.row
            self.start_col = start_square.col
        else:
            self.start_row = start_square[0]
            self.start_col = start_square[1]
            
        if hasattr(end_square, 'row') and hasattr(end_square, 'col'):
            self.end_row = end_square.row
            self.end_col = end_square.col
        else:
            self.end_row = end_square[0]
            self.end_col = end_square[1]
        
        self.piece_moved = piece_moved
        self.piece_captured = piece_captured
        
        # special move flags
        # wow vertical code for readability (thanks adrian)
        self.is_pawn_promotion = (
            (self.piece_moved == WHITE_PAWN and self.end_row == 0) or 
            (self.piece_moved == BLACK_PAWN and self.end_row == 7)
        )
        
        self.is_en_passant_move = is_en_passant_move
        if self.is_en_passant_move:
            self.piece_captured = WHITE_PAWN if self.piece_moved == BLACK_PAWN else BLACK_PAWN
            
        self.is_castle_move = is_castle_move
        self.is_capture = (self.piece_captured != NULL_SQUARE)
        
        # create a unique Id for the move (for comparison) :nerd:
        self.move_id = self.start_col * 1000 + self.start_row * 100 + self.end_col * 10 + self.end_row

    def __eq__(self, other):
        """Check if two moves are equal
        Args:
            other: Another move to compare with
            
        Returns:
            True if the moves are equal, False otherwise
        """
        if isinstance(other, ChessAction):
            return self.move_id == other.move_id
        return False

    def get_chess_notation(self):
        """Get the chess notation for this move (e.g., 'e2e4')
        
        Returns  :
            The move in chess notation (omg no way holy guacacow)
        """
        return self.get_square_notation(self.start_row, self.start_col) + \
               self.get_square_notation(self.end_row, self.end_col)
               
    def get_square_notation(self, row, col):
        """Convert a row and column to chess notation
        
        Args:
        row: The row index
            col: The column index
            
        Returns:
            The square in chess notation
        """
        return self.COL_TO_FILE[col] + self.ROW_TO_RANK[row]

    def __str__(self):
        """Get a string representation of the move in algebraic notation
        
        Returns:
            The move in algebraic notation
        """
        # handle castling moves bc they are special
        if self.is_castle_move:
            return "O-O" if self.end_col == 6 else "O-O-O"
            
        end_square = self.get_square_notation(self.end_row, self.end_col)
        
        # handle pawn moves bc they are specialer
        if self.piece_moved.endswith('p'):
            if self.is_capture:
                return self.COL_TO_FILE[self.start_col] + "x" + end_square
            else:
                return end_square

        # handle piece moves
        move_string = self.piece_moved[1]  # get the piece letter (R, N, B, Q, K)
        if self.is_capture:
            move_string += "x"
            
        return move_string + end_square
        
Move = ChessAction
