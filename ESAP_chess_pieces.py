from __future__ import annotations
from typing import List, Tuple, Dict, Set, Optional
from abc import ABC, abstractmethod

from ESAP_chess_core import BoardCoordinate, PieceColor, PieceType, NULL_SQUARE, ChessMatrix
from ESAP_chess_moves import Move

# direction constants
DIRECTIONS = {
    "straight": [(0, 1), (1, 0), (0, -1), (-1, 0)],  # rook directions
    "diagonal": [(1, 1), (1, -1), (-1, -1), (-1, 1)],  # bishop directions
    "knight": [(-2, -1), (-1, -2), (1, -2), (2, -1), (2, 1), (1, 2), (-1, 2), (-2, 1)],  # knight moves
    "king": [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (1, -1), (-1, 1)]  # king moves
}

# alphabet soup
# is yummy
# (it says ABC that was the joke) 

class PieceMovementStrategy(ABC):
    """abstract base class for piece movement strategies"""
    
    @abstractmethod
    def get_moves(self, position: Position, board: ChessBoard, pins: List, is_white_turn: bool) -> List[Move]:
        """get all possible moves for a piece at the given position"""
        pass

class PawnMovementStrategy(PieceMovementStrategy):
    def get_moves(self, position: Position, board: ChessBoard, pins: List, is_white_turn: bool, enpassant_target: Optional[Position] = None, white_king_position: Optional[Position] = None, black_king_position: Optional[Position] = None) -> List[Move]:
        """get all possible moves for a pawn"""
        moves = []
        r, c = position.row, position.col
        
        # check if pawn is pinned
        piece_pinned = False
        pin_direction = ()
        for i in range(len(pins) - 1, -1, -1):
            if pins[i][0] == r and pins[i][1] == c:
                piece_pinned = True
                pin_direction = (pins[i][2], pins[i][3])
                break
        
        # get king position for en passant checks
        if is_white_turn and white_king_position:
            king_row, king_col = white_king_position.row, white_king_position.col
        elif not is_white_turn and black_king_position:
            king_row, king_col = black_king_position.row, black_king_position.col
        else:
            # default values if king positions aren't provided
            king_row, king_col = (7, 4) if is_white_turn else (0, 4)
        
        if is_white_turn:  # white pawn moves
            # forward moves
            if board[r-1][c] == NULL_SQUARE:
                if not piece_pinned or pin_direction == (-1, 0):
                    moves.append(Move((r, c), (r-1, c), board))
                    if r == 6 and board[r-2][c] == NULL_SQUARE:
                        moves.append(Move((r, c), (r-2, c), board))
            
            # captures to the left (this is the simplest way i could implement this it looks awful but idc it works so DONT touch this code)
            if c-1 >= 0:
                if board[r-1][c-1][0] == "b":
                    if not piece_pinned or pin_direction == (-1, -1):
                        moves.append(Move((r, c), (r-1, c-1), board))
                elif enpassant_target and (r-1, c-1) == (enpassant_target.row, enpassant_target.col):
                    attacking_piece = blocking_piece = False
                    if king_row == r:
                        if king_col < c:
                            inside_range = range(king_col + 1, c-1)
                            outside_range = range(c+1, 8)
                        else:
                            inside_range = range(king_col - 1, c, -1)
                            outside_range = range(c-2, -1, -1)
                        for i in inside_range:
                            if board[r][i] != NULL_SQUARE:
                                blocking_piece = True
                        for i in outside_range:
                            square = board[r][i]
                            if square[0] == 'b' and (square[1] == 'R' or square[1] == 'Q'):
                                attacking_piece = True
                            elif square != NULL_SQUARE:
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move((r, c), (r-1, c-1), board, is_enpassant_move=True))
            
            # captures to the right
            if c+1 <= 7:
                if board[r-1][c+1][0] == "b":
                    if not piece_pinned or pin_direction == (-1, 1):
                        moves.append(Move((r, c), (r-1, c+1), board))
                elif enpassant_target and (r-1, c+1) == (enpassant_target.row, enpassant_target.col):
                    attacking_piece = blocking_piece = False
                    if king_row == r:
                        if king_col < c:
                            inside_range = range(king_col + 1, c)
                            outside_range = range(c+2, 8)
                        else:
                            inside_range = range(king_col - 1, c+1, -1)
                            outside_range = range(c-1, -1, -1)
                        for i in inside_range:
                            if board[r][i] != NULL_SQUARE:
                                blocking_piece = True
                        for i in outside_range:
                            square = board[r][i]
                            if square[0] == 'b' and (square[1] == 'R' or square[1] == 'Q'):
                                attacking_piece = True
                            elif square != NULL_SQUARE:
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move((r, c), (r-1, c+1), board, is_enpassant_move=True))
        else:  # black pawn moves
            # forward moves
            if board[r+1][c] == NULL_SQUARE:
                if not piece_pinned or pin_direction == (1, 0):
                    moves.append(Move((r, c), (r+1, c), board))
                    if r == 1 and board[r+2][c] == NULL_SQUARE:
                        moves.append(Move((r, c), (r+2, c), board))
            
            # captures to the left 
            # this is the simplest way i could implement this it looks awful but idc it works so DONT touch this code
            if c-1 >= 0:
                if board[r+1][c-1][0] == "w":
                    if not piece_pinned or pin_direction == (1, -1):
                        moves.append(Move((r, c), (r+1, c-1), board))
                elif enpassant_target and (r+1, c-1) == (enpassant_target.row, enpassant_target.col):
                    attacking_piece = blocking_piece = False
                    if king_row == r:
                        if king_col < c:
                            inside_range = range(king_col + 1, c-1)
                            outside_range = range(c+1, 8)
                        else:
                            inside_range = range(king_col - 1, c, -1)
                            outside_range = range(c-2, -1, -1)
                        for i in inside_range:
                            if board[r][i] != NULL_SQUARE:
                                blocking_piece = True
                        for i in outside_range:
                            square = board[r][i]
                            if square[0] == 'w' and (square[1] == 'R' or square[1] == 'Q'):
                                attacking_piece = True
                            elif square != NULL_SQUARE:
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move((r, c), (r+1, c-1), board, is_enpassant_move=True))
            
            # captures to the right
            if c+1 <= 7:
                if board[r+1][c+1][0] == "w":
                    if not piece_pinned or pin_direction == (1, 1):
                        moves.append(Move((r, c), (r+1, c+1), board))
                elif enpassant_target and (r+1, c+1) == (enpassant_target.row, enpassant_target.col):
                    attacking_piece = blocking_piece = False
                    if king_row == r:
                        if king_col < c:
                            inside_range = range(king_col + 1, c)
                            outside_range = range(c+2, 8)
                        else:
                            inside_range = range(king_col - 1, c+1, -1)
                            outside_range = range(c-1, -1, -1)
                        for i in inside_range:
                            if board[r][i] != NULL_SQUARE:
                                blocking_piece = True
                        for i in outside_range:
                            square = board[r][i]
                            if square[0] == 'w' and (square[1] == 'R' or square[1] == 'Q'):
                                attacking_piece = True
                            elif square != NULL_SQUARE:
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move((r, c), (r+1, c+1), board, is_enpassant_move=True))
        
        return moves

class RookMovementStrategy(PieceMovementStrategy):
    def get_moves(self, position: Position, board: ChessBoard, pins: List, is_white_turn: bool) -> List[Move]:
        """get all possible moves for a rook"""
        moves = []
        r, c = position.row, position.col
        
        # check if rook is pinned
        piece_pinned = False
        pin_direction = ()
        for i in range(len(pins) - 1, -1, -1):
            if pins[i][0] == r and pins[i][1] == c:
                piece_pinned = True
                pin_direction = (pins[i][2], pins[i][3])
                if board[r][c][1] != 'Q':  # Don't remove pin if it's a queen wahahahah :evil:
                    pins.remove(pins[i])
                break
        
        # determine enemy color
        enemy_color = 'b' if is_white_turn else 'w'
        
        # check moves in all four straight directions
        for d in DIRECTIONS["straight"]:
            for i in range(1, 8):
                end_row = r + d[0] * i
                end_col = c + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    if not piece_pinned or pin_direction == d or pin_direction == (-d[0], -d[1]):
                        end_piece = board[end_row][end_col]
                        if end_piece == NULL_SQUARE:
                            moves.append(Move((r, c), (end_row, end_col), board))
                        elif end_piece[0] == enemy_color:
                            moves.append(Move((r, c), (end_row, end_col), board))
                            break
                        else:  # friendly piece
                            break
                else:  # off board
                    break
        
        return moves

class KnightMovementStrategy(PieceMovementStrategy):
    def get_moves(self, position: Position, board: ChessBoard, pins: List, is_white_turn: bool) -> List[Move]:
        """get all possible moves for a knight"""
        moves = []
        r, c = position.row, position.col
        
        # check if knight is pinned
        piece_pinned = False
        for i in range(len(pins) - 1, -1, -1):
            if pins[i][0] == r and pins[i][1] == c:
                piece_pinned = True
                pins.remove(pins[i])
                break
        
        # Knights can't move if pinned (no WAyayayay)
        if piece_pinned:
            return moves
        
        # determine ally color
        ally_color = 'w' if is_white_turn else 'b'
        
        # check all possible knight moves
        for d in DIRECTIONS["knight"]:
            end_row = r + d[0]
            end_col = c + d[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = board[end_row][end_col]
                if end_piece[0] != ally_color:  # Empty or enemy piece
                    moves.append(Move((r, c), (end_row, end_col), board))
        
        return moves

class BishopMovementStrategy(PieceMovementStrategy):
    def get_moves(self, position: Position, board: ChessBoard, pins: List, is_white_turn: bool) -> List[Move]:
        """get all possible moves for a bishop"""
        moves = []
        r, c = position.row, position.col
        
        # check if bishop is pinned
        piece_pinned = False
        pin_direction = ()
        for i in range(len(pins) - 1, -1, -1):
            if pins[i][0] == r and pins[i][1] == c:
                piece_pinned = True
                pin_direction = (pins[i][2], pins[i][3])
                pins.remove(pins[i])
                break
        
        # determine enemy color
        enemy_color = 'b' if is_white_turn else 'w'
        
        # check moves in all four diagonal directions
        for d in DIRECTIONS["diagonal"]:
            for i in range(1, 8):
                end_row = r + d[0] * i
                end_col = c + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    if not piece_pinned or pin_direction == d or pin_direction == (-d[0], -d[1]):
                        end_piece = board[end_row][end_col]
                        if end_piece == NULL_SQUARE:
                            moves.append(Move((r, c), (end_row, end_col), board))
                        elif end_piece[0] == enemy_color:
                            moves.append(Move((r, c), (end_row, end_col), board))
                            break
                        else:  # friendly piece
                            break
                else:  # off board
                    break
        
        return moves

class QueenMovementStrategy(PieceMovementStrategy):
    def get_moves(self, position: Position, board: ChessBoard, pins: List, is_white_turn: bool) -> List[Move]:
        """get all possible moves for a queen (combines rook and bishop moves)"""
        moves = []
        
        # use rook and bishop strategies to get queen moves
        rook_strategy = RookMovementStrategy()
        bishop_strategy = BishopMovementStrategy()
        
        moves.extend(rook_strategy.get_moves(position, board, pins, is_white_turn))
        moves.extend(bishop_strategy.get_moves(position, board, pins, is_white_turn))
        
        return moves

class KingMovementStrategy(PieceMovementStrategy):
    def get_moves(self, position: Position, board: ChessBoard, pins: List, is_white_turn: bool, 
                  white_king_position: Optional[Position] = None, black_king_position: Optional[Position] = None,
                  check_for_checks_func=None) -> List[Move]:
        """get all possible moves for a king"""
        moves = []
        r, c = position.row, position.col
        
        # determine ally color
        ally_color = 'w' if is_white_turn else 'b'
        
        # check all eight directions
        for d in DIRECTIONS["king"]:
            end_row = r + d[0]
            end_col = c + d[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = board[end_row][end_col]
                if end_piece[0] != ally_color:  # empty or enemy piece
                    # if we have the check function, use it to verify move safety
                    if check_for_checks_func:
                        # create temporary positions for checking
                        temp_white_king_pos = BoardCoordinate(end_row, end_col) if is_white_turn else white_king_position
                        temp_black_king_pos = BoardCoordinate(end_row, end_col) if not is_white_turn else black_king_position
                        
                        # check if the move puts the king in check
                        in_check, _, _ = check_for_checks_func(temp_white_king_pos, temp_black_king_pos)
                    
                        # add move if it doesn't put the king in check
                        if not in_check:
                            moves.append(Move((r, c), (end_row, end_col), board))
                    else:
                        # if we don't have the check function, just add the move
                        # (the game state will filter unsafe moves later)
                        moves.append(Move((r, c), (end_row, end_col), board))
        
        return moves

# factory to create the appropriate movement strategy for each piece type
# named it this cuz i heard theres a game called factorio and its 1am so why not
class PieceMovementFactory:
    @staticmethod
    def create_movement_strategy(piece_type: str) -> PieceMovementStrategy:
        if piece_type == 'p':
            return PawnMovementStrategy()
        elif piece_type == 'R':
            return RookMovementStrategy()
        elif piece_type == 'N':
            return KnightMovementStrategy()
        elif piece_type == 'B':
            return BishopMovementStrategy()
        elif piece_type == 'Q':
            return QueenMovementStrategy()
        elif piece_type == 'K':
            return KingMovementStrategy()
        else:
            raise ValueError(f"Unknown piece type: {piece_type}")
