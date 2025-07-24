from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, List, Dict, Optional

from ESAP_chess_core import Position, EMPTY_SQUARE

@dataclass
class CastleRights:
    """Class to track castling rights for both players"""
    wks: bool  # White king-side
    wqs: bool  # White queen-side
    bks: bool  # Black king-side
    bqs: bool  # Black queen-side
    
    def copy(self) -> 'CastleRights':
        """Create a copy of the castle rights"""
        return CastleRights(self.wks, self.wqs, self.bks, self.bqs)

class Move:
    """Represents a chess move with all relevant information"""
    # Mapping between ranks/files and board coordinates
    ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}
    files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    cols_to_files = {v: k for k, v in files_to_cols.items()}
    
    def __init__(self, start_sq, end_sq, board, 
                 is_enpassant_move: bool = False, is_castle_move: bool = False):
        # Start and end positions
        # Handle both Position objects and tuples
        if hasattr(start_sq, 'row') and hasattr(start_sq, 'col'):
            self.start_row = start_sq.row
            self.start_col = start_sq.col
        else:
            self.start_row = start_sq[0]
            self.start_col = start_sq[1]
            
        if hasattr(end_sq, 'row') and hasattr(end_sq, 'col'):
            self.end_row = end_sq.row
            self.end_col = end_sq.col
        else:
            self.end_row = end_sq[0]
            self.end_col = end_sq[1]
        
        # Piece information
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]
        
        # Special move flags
        self.is_pawn_promotion = (self.piece_moved == "wp" and self.end_row == 0) or \
                               (self.piece_moved == "bp" and self.end_row == 7)
        self.is_enpassant_move = is_enpassant_move
        if self.is_enpassant_move:
            self.piece_captured = "wp" if self.piece_moved == "bp" else "bp"
        
        self.is_castle_move = is_castle_move
        self.is_capture = (self.piece_captured != EMPTY_SQUARE)
        
        # Unique move ID for comparison
        self.move_id = self.start_col * 1000 + self.start_row * 100 + self.end_col * 10 + self.end_row
    
    def __eq__(self, other):
        """Compare moves based on their unique ID"""
        if isinstance(other, Move):
            return self.move_id == other.move_id
        return False
    
    def get_chess_notation(self) -> str:
        """Convert move to algebraic chess notation"""
        return self.get_file_rank(self.start_row, self.start_col) + self.get_file_rank(self.end_row, self.end_col)
    
    def get_file_rank(self, row: int, col: int) -> str:
        """Convert board coordinates to file and rank notation"""
        return self.cols_to_files[col] + self.rows_to_ranks[row]
    
    def __str__(self) -> str:
        """String representation of the move in chess notation"""
        # Castle move
        if self.is_castle_move:
            return "O-O" if self.end_col == 6 else "O-O-O"
        
        end_square = self.get_file_rank(self.end_row, self.end_col)
        
        # Pawn move
        if self.piece_moved[1] == 'p':
            if self.is_capture:
                return self.cols_to_files[self.start_col] + "x" + end_square
            else:
                return end_square
        
        # Piece move
        move_string = self.piece_moved[1]
        if self.is_capture:
            move_string += "x"
        return move_string + end_square

class MoveGenerator:
    """Utility class for generating and validating chess moves"""
    
    @staticmethod
    def get_castle_moves(row: int, col: int, moves: List[Move], board, 
                        is_white_turn: bool, castle_rights: CastleRights, in_check: bool,
                        check_function=None, white_king_pos=None, black_king_pos=None):
        """Generate castling moves if they are legal"""
        if in_check:
            return  # Can't castle while in check
        
        # Determine which castling rights to check based on whose turn it is
        if is_white_turn:
            kingside_rights = castle_rights.wks
            queenside_rights = castle_rights.wqs
            ally_color = 'w'
        else:
            kingside_rights = castle_rights.bks
            queenside_rights = castle_rights.bqs
            ally_color = 'b'
        
        # Check kingside castling
        if kingside_rights:
            MoveGenerator.get_kingside_castle_move(row, col, moves, board, ally_color, 
                                                  check_function, white_king_pos, black_king_pos)
        
        # Check queenside castling
        if queenside_rights:
            MoveGenerator.get_queenside_castle_move(row, col, moves, board, ally_color,
                                                   check_function, white_king_pos, black_king_pos)
    
    @staticmethod
    def get_kingside_castle_move(row: int, col: int, moves: List[Move], board, ally_color: str,
                               check_function=None, white_king_pos=None, black_king_pos=None):
        """Generate kingside castling move if legal"""
        # Check if squares between king and rook are empty
        if board[row][col+1] == EMPTY_SQUARE and board[row][col+2] == EMPTY_SQUARE:
            # If no check function provided, we can't verify safety
            if not check_function:
                moves.append(Move((row, col), (row, col+2), board, is_castle_move=True))
                return
                
            # Check if king passes through or ends up in check
            # Create temporary positions for checking
            temp_white_king_pos1 = Position(row, col+1) if ally_color == 'w' else white_king_pos
            temp_black_king_pos1 = Position(row, col+1) if ally_color == 'b' else black_king_pos
            
            # Check first square
            in_check1, _, _ = check_function(temp_white_king_pos1, temp_black_king_pos1)
            
            # Check destination square
            temp_white_king_pos2 = Position(row, col+2) if ally_color == 'w' else white_king_pos
            temp_black_king_pos2 = Position(row, col+2) if ally_color == 'b' else black_king_pos
            
            in_check2, _, _ = check_function(temp_white_king_pos2, temp_black_king_pos2)
            
            # If king doesn't pass through or end up in check, add the move
            if not in_check1 and not in_check2:
                moves.append(Move((row, col), (row, col+2), board, is_castle_move=True))
    
    @staticmethod
    def get_queenside_castle_move(row: int, col: int, moves: List[Move], board, ally_color: str,
                                check_function=None, white_king_pos=None, black_king_pos=None):
        """Generate queenside castling move if legal"""
        # Check if squares between king and rook are empty
        if board[row][col-1] == EMPTY_SQUARE and board[row][col-2] == EMPTY_SQUARE and board[row][col-3] == EMPTY_SQUARE:
            # If no check function provided, we can't verify safety
            if not check_function:
                moves.append(Move((row, col), (row, col-2), board, is_castle_move=True))
                return
                
            # Check if king passes through or ends up in check
            # Create temporary positions for checking
            temp_white_king_pos1 = Position(row, col-1) if ally_color == 'w' else white_king_pos
            temp_black_king_pos1 = Position(row, col-1) if ally_color == 'b' else black_king_pos
            
            # Check first square
            in_check1, _, _ = check_function(temp_white_king_pos1, temp_black_king_pos1)
            
            # Check destination square
            temp_white_king_pos2 = Position(row, col-2) if ally_color == 'w' else white_king_pos
            temp_black_king_pos2 = Position(row, col-2) if ally_color == 'b' else black_king_pos
            
            in_check2, _, _ = check_function(temp_white_king_pos2, temp_black_king_pos2)
            
            # If king doesn't pass through or end up in check, add the move
            if not in_check1 and not in_check2:
                moves.append(Move((row, col), (row, col-2), board, is_castle_move=True))
