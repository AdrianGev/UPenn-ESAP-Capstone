from typing import List, Dict, Tuple, Optional, Any, Callable
from dataclasses import dataclass

@dataclass
class BoardCoordinate:
    """Represents a position on the chess board"""
    row: int
    col: int
    
    def __iter__(self):
        """Allow unpacking like a tuple"""
        yield self.row
        yield self.col
        
    def is_valid(self) -> bool:
        """Check if position is within board boundaries"""
        return 0 <= self.row < 8 and 0 <= self.col < 8


class GameState:
    """Represents the state of a chess game"""
    
    # board representation constants
    NULL_SQUARE = "--"
    
    # piece color constants
    WHITE = "w"
    BLACK = "b"
    
    # initial board setup
    INITIAL_BOARD = [
        ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
        ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
        ["--", "--", "--", "--", "--", "--", "--", "--"],
        ["--", "--", "--", "--", "--", "--", "--", "--"],
        ["--", "--", "--", "--", "--", "--", "--", "--"],
        ["--", "--", "--", "--", "--", "--", "--", "--"],
        ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
        ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
    ]
    
    def __init__(self):
        """Initialize a new chess game state"""
        # copy the initial board setup
        self.board: List[List[str]] = [
            row[:] for row in self.INITIAL_BOARD
        ]
        
        # map piece types to their move generation methods
        self.moveFunctions: Dict[str, Callable] = {
            'p': self.generate_pawn_moves,
            'R': self.generate_rook_moves,
            'N': self.generate_knight_moves,
            'B': self.generate_bishop_moves,
            'Q': self.generate_queen_moves,
            'K': self.generate_king_moves
        }
        
        # game state tracking
        self.white_to_move: bool = True  # white moves first
        self.move_log: List[Any] = []   # history of moves
        
        # track king positions for check detection
        self.white_king_location: Tuple[int, int] = (7, 4)
        self.black_king_location: Tuple[int, int] = (0, 4)
        
        # game ending states
        self.check_mate: bool = False
        self.stale_mate: bool = False
        
        # special move tracking
        self.enpassant_possible: Tuple[int, int] = ()  # empty tuple means no en passant possible

    def execute_move(self, move) -> None:
        """Execute a move on the board and update game state
        
        Args:
            move: The move to execute
        """
        # update the board by moving the piece
        self.board[move.startRow][move.startCol] = self.NULL_SQUARE
        self.board[move.endRow][move.endCol] = move.pieceMoved
        
        # record the move in the log
        self.move_log.append(move)
        
        # switch turns
        self.white_to_move = not self.white_to_move
        
        # update king position tracking if a king moved
        if move.pieceMoved == f"{self.white}K":
            self.white_king_location = (move.endRow, move.endCol)
        elif move.pieceMoved == f"{self.black}K":
            self.black_king_location = (move.endRow, move.endCol)

        # handle en passant capture
        if move.isEnpassantMove:
            print("En passant capture executed")
            self.board[move.startRow][move.endCol] = self.NULL_SQUARE  # Capture the pawn
            
        # update en passant possibility
        if move.pieceMoved[1] == 'p' and abs(move.startRow - move.endRow) == 2:
            # a pawn moved two squares, enabling en passant on the next move
            self.enpassant_possible = ((move.startRow + move.endRow) // 2, move.endCol)
        else:
            # reset en passant possibility
            self.enpassant_possible = ()

    def revert_move(self) -> bool:
        """Undo the last move and restore the previous game state
        
        Returns:
            bool: True if a move was undone, False if no moves to undo
        """
        # check if there are any moves to undo
        if not self.move_log:
            return False
            
        # get the last move from the log and remove it
        move = self.move_log.pop()
        
        # restore the board state
        self.board[move.start_row][move.start_col] = move.piece_moved
        self.board[move.end_row][move.end_col] = move.piece_captured
        
        # switch back to the previous player's turn
        self.white_to_move = not self.white_to_move
        
        # update king position tracking if a king was moved
        if move.piece_moved == f"{self.white}K":
            self.white_king_location = (move.start_row, move.start_col)
        elif move.piece_moved == f"{self.black}K":
            self.black_king_location = (move.start_row, move.start_col)

        # handle en passant move reversal
        if move.is_enpassant_move:
            # clear the destination square
            self.board[move.end_row][move.end_col] = self.empty_square
            # restore the captured pawn
            self.board[move.start_row][move.end_col] = move.piece_captured
            # set the en passant possible square
            self.enpassant_possible = (move.end_row, move.end_col)

        # reset en passant possibility for two-square pawn moves
        if move.piece_moved[1] == 'p' and abs(move.start_row - move.end_row) == 2:
            self.enpassant_possible = ()
            
        return True

    def fetch_legal_moves(self):
        """Get all valid moves for the current player, considering check rules
        
        Returns:
            list: list of valid Move objects
        """
        # save current en passant state
        temp_enpassant_possible = self.enpassant_possible
        
        # get all possible moves without considering check
        candidate_moves = self.get_all_possible_moves()
        
        # filter out moves that would leave the king in check
        # iterate backwards to safely remove items during iteration
        for i in range(len(candidate_moves)-1, -1, -1):
            # try the move
            self.make_move(candidate_moves[i])
            
            # switch perspective to opponent to check if they can capture our king
            self.white_to_move = not self.white_to_move
            
            # if this move leaves us in check, remove it from valid moves
            if self.is_in_check():
                candidate_moves.remove(candidate_moves[i])
                
            # undo the move and restore turn
            self.undo_move()
            self.white_to_move = not self.white_to_move
        
        # check for checkmate or stalemate
        if not candidate_moves:  # no valid moves left
            if self.is_in_check():
                self.check_mate = True
                print("Checkmate.")
            else:
                self.stale_mate = True
                print("Stalemate.")
        else:
            # reset game ending flags if moves are available
            self.check_mate = False
            self.stale_mate = False

        # restore the original en passant state
        self.enpassant_possible = temp_enpassant_possible
        return candidate_moves

    def is_in_check(self) -> bool:
        """Determine if the current player's king is in check
        
        Returns:
            bool: True if the current player is in check, False otherwise
        """
        # get the position of the current player's king
        king_position = self.white_king_location if self.white_to_move else self.black_king_location
        
        # check if the king's position is under attack by any opponent piece
        return self.is_square_under_attack(king_position[0], king_position[1])

    def is_square_under_attack(self, r: int, c: int) -> bool:
        """D etermine if a specific square is under attack by opponent pieces
        
        Args:
            r: Row of the square to check
            c: Column of the square to check
            
        Returns:
            bool: True if the square is under attack, False otherwise
        """
        # Temporarily switch turns to get opponent's perspective
        self.white_to_move = not self.white_to_move
        
        # Get all possible moves for the opponent
        opponent_moves = self.get_all_possible_moves()
        
        # Switch back to original player
        self.white_to_move = not self.white_to_move
        
        # Check if any opponent move targets the specified square
        for move in opponent_moves:
            if move.end_row == r and move.end_col == c:
                return True
                
        return False

    def get_all_possible_moves(self) -> list:
        """Generate all possible moves for the current player without considering check
        
        Returns:
            list: List of all possible Move objects
        """
        moves = []
        
        # iterate through all squares on the board
        for r in range(8):
            for c in range(8):
                # get the piece color at current square
                piece_color = self.board[r][c][0]
                
                # check if the piece belongs to the current player
                if ((piece_color == self.white and self.white_to_move) or 
                    (piece_color == self.black and not self.white_to_move)):
                    
                    # get the piece type (p, R, N, B, Q, K)
                    piece_type = self.board[r][c][1]
                    
                    # call the appropriate move generation function for this piece type
                    self.move_functions[piece_type](r, c, moves)
                    
        return moves

    def generate_pawn_moves(self, r: int, c: int, moves: list) -> None:
        """Generate all possible pawn moves from the given position
        
        Args:
            r: Row of the pawn
            c: Column of the pawn
            moves: List to append valid moves to
        """
        if self.white_to_move:  # white pawn moves (upward on the board)
            # forward move - one square
            if self.board[r-1][c] == self.empty_square:
                moves.append(Move((r, c), (r-1, c), self.board))
                # forward move - two squares from starting position
                if r == 6 and self.board[r-2][c] == self.empty_square:
                    moves.append(Move((r, c), (r-2, c), self.board))
                    
            # capture moves - diagonal left
            if c-1 >= 0:  # check left boundary
                if self.board[r-1][c-1][0] == self.black:  # regular capture
                    moves.append(Move((r, c), (r-1, c-1), self.board))
                elif (r-1, c-1) == self.enpassant_possible:  # en passant capture
                    moves.append(Move((r, c), (r-1, c-1), self.board, is_enpassant_move=True))
                    
            # capture moves - diagonal right
            if c+1 <= 7:  # check right boundary
                if self.board[r-1][c+1][0] == self.black:  # regular capture
                    moves.append(Move((r, c), (r-1, c+1), self.board))
                elif (r-1, c+1) == self.enpassant_possible:  # en passant capture
                    moves.append(Move((r, c), (r-1, c+1), self.board, is_enpassant_move=True))
        else:  # black pawn moves (downward on the board)
            # forward move - one square
            if self.board[r+1][c] == self.empty_square:
                moves.append(Move((r, c), (r+1, c), self.board))
                # forward move - two squares from starting position
                if r == 1 and self.board[r+2][c] == self.empty_square:
                    moves.append(Move((r, c), (r+2, c), self.board))
                    
            # capture moves - diagonal left
            if c-1 >= 0:  # check left boundary
                if self.board[r+1][c-1][0] == self.white:  # regular capture
                    moves.append(Move((r, c), (r+1, c-1), self.board))
                elif (r+1, c-1) == self.enpassant_possible:  # en passant capture
                    moves.append(Move((r, c), (r+1, c-1), self.board, is_enpassant_move=True))
                    
            # capture moves - diagonal right
            if c+1 <= 7:  # check right boundary
                if self.board[r+1][c+1][0] == self.white:  # regular capture
                    moves.append(Move((r, c), (r+1, c+1), self.board))
                elif (r+1, c+1) == self.enpassant_possible:  # en passant capture
                    moves.append(Move((r, c), (r+1, c+1), self.board, is_enpassant_move=True))

    def generate_rook_moves(self, r: int, c: int, moves: list) -> None:
        """Generate all possible rook moves from the given position
        
        Args:
            r: Row of the rook
            c: Column of the rook
            moves: List to append valid moves to
        """
        # rook moves in straight lines (horizontal and vertical)
        straight_directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # up, down, left, right
        enemy_color = self.BLACK if self.whiteToMove else self.WHITE
        
        # check each direction
        for direction in straight_directions:
            for distance in range(1, 8):  # maximum distance is 7 squares
                end_row = r + direction[0] * distance
                end_col = c + direction[1] * distance
                
                # check if the position is within board boundaries
                if not (0 <= end_row < 8 and 0 <= end_col < 8):
                    break
                    
                end_piece = self.board[end_row][end_col]
                
                if end_piece == self.EMPTY_SQUARE:  # empty square - valid move
                    moves.append(Move((r, c), (end_row, end_col), self.board))
                elif end_piece[0] == enemy_color:  # enemy piece - capture and stop
                    moves.append(Move((r, c), (end_row, end_col), self.board))
                    break
                else:  # friendly piece - stop looking in this direction (poorly phrased pls fix this)
                    break

    def generate_knight_moves(self, r: int, c: int, moves: list) -> None:
        """Generate all possible knight moves from the given position
        
        Args:
            r: Row of the knight
            c: Column of the knight
            moves: List to append valid moves to
        """
        # Knight moves in L-shape pattern
        knight_directions = [(-2, -1), (-1, -2), (1, -2), (2, -1), 
                            (2, 1), (1, 2), (-1, 2), (-2, 1)]
        ally_color = self.WHITE if self.whiteToMove else self.BLACK
        
        # Check each possible knight move
        for direction in knight_directions:
            end_row = r + direction[0]
            end_col = c + direction[1]
            
            # Check if the position is within board boundaries
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                # Valid move if square is empty or contains enemy piece
                if end_piece[0] != ally_color:  # Not an ally piece
                    moves.append(Move((r, c), (end_row, end_col), self.board))

    def generate_bishop_moves(self, r: int, c: int, moves: list) -> None:
        """Generate all possible bishop moves from the given position
        
        Args:
            r: Row of the bishop
            c: Column of the bishop
            moves: List to append valid moves to
        """
        # bishop moves in diagonal lines
        diagonal_directions = [(-1, -1), (1, 1), (1, -1), (-1, 1)]  # diagonals
        enemy_color = self.BLACK if self.whiteToMove else self.WHITE
        
        # check each direction
        for direction in diagonal_directions:
            for distance in range(1, 8):  # maximum distance is 7 squares
                end_row = r + direction[0] * distance
                end_col = c + direction[1] * distance
                
                # check if the position is within board boundaries
                if not (0 <= end_row < 8 and 0 <= end_col < 8):
                    break
                    
                end_piece = self.board[end_row][end_col]
                
                if end_piece == self.EMPTY_SQUARE:  # empty square - valid move
                    moves.append(Move((r, c), (end_row, end_col), self.board))
                elif end_piece[0] == enemy_color:  # enemy piece - capture and stop
                    moves.append(Move((r, c), (end_row, end_col), self.board))
                    break
                else:  # friendly piece - stop looking in this direction
                    break

    def generate_queen_moves(self, r: int, c: int, moves: list) -> None:
        """Generate all possible queen moves from the given position
        
        Args:
            r: Row of the queen
            c: Column of the queen
            moves: List to append valid moves to
        """
        # queen combines rook and bishop movement patterns
        self.generate_rook_moves(r, c, moves)    # horizontal and vertical moves
        self.generate_bishop_moves(r, c, moves)  # diagonal moves

    def generate_king_moves(self, r: int, c: int, moves: list) -> None:
        """Generate all possible king moves from the given position
        
        Args:
            r: Row of the king
            c: Column of the king
            moves: List to append valid moves to
        """
        # king moves one square in any direction
        king_directions = [(-1, 0), (1, 0), (0, -1), (0, 1),  # orthogonal
                          (-1, -1), (1, 1), (1, -1), (-1, 1)]  # diagonal
        ally_color = self.WHITE if self.whiteToMove else self.BLACK
        
        # check each possible king move
        for direction in king_directions:
            end_row = r + direction[0]
            end_col = c + direction[1]
            
            # check if the position is within board boundaries
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                # valid move if square is empty or contains enemy piece
                if end_piece[0] != ally_color:  # not an ally piece
                    moves.append(Move((r, c), (end_row, end_col), self.board))
