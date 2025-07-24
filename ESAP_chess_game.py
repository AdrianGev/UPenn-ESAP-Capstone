from __future__ import annotations
from typing import List, Tuple, Dict, Optional, Set
from copy import deepcopy

from ESAP_chess_core import BoardCoordinate, PieceColor, PieceType, NULL_SQUARE, ChessMatrix
from ESAP_chess_moves import Move, CastleRights, MoveGenerator
from ESAP_chess_pieces import PieceMovementFactory

class GameState:
    """Main class for managing the chess game state"""
    
    def __init__(self):
        # init the chess board
        self.board = ChessMatrix()
        
        # track whose turn it is
        self.white_to_move = True
        
        # move history
        self.move_log = []
        
        # track king positions
        self.white_king_position = BoardCoordinate(7, 4)
        self.black_king_position = BoardCoordinate(0, 4)
        
        # track check status
        self.in_check = False
        self.pins = []
        self.checks = []
        
        # en crossaint tracking
        self.enpassant_target = None
        
        # castling rights
        self.castle_rights = CastleRights(True, True, True, True)
        self.castle_rights_log = [CastleRights(True, True, True, True)]
        
        # position repetition tracking for draw detection
        self.position_history = {}
        self.threefold_repetition = False
        
        # insufficient material draw detection (cant checkmate)
        self.insufficient_material = False
        
        # map piece types to their move generation methods
        self.move_functions = {
            "p": self.get_pawn_moves,
            "R": self.get_rook_moves,
            "N": self.get_knight_moves,
            "B": self.get_bishop_moves,
            "Q": self.get_queen_moves,
            "K": self.get_king_moves
        }
    
    def make_move(self, move: Move) -> None:
        """Execute a move on the board"""
        # update the board
        self.board[move.start_row][move.start_col] = NULL_SQUARE
        self.board[move.end_row][move.end_col] = move.piece_moved
        
        # add move to log
        self.move_log.append(move)
        
        # switch turns
        self.white_to_move = not self.white_to_move
        
        # update king position if king moved
        if move.piece_moved == "wK":
            self.white_king_position = BoardCoordinate(move.end_row, move.end_col)
        elif move.piece_moved == "bK":
            self.black_king_position = BoardCoordinate(move.end_row, move.end_col)
        
        # handle pawn promotion
        if move.is_pawn_promotion:
            # default promotion to queen
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + "Q"
        
        # handle en passant capture
        if move.is_enpassant_move:
            # remove the captured pawn
            self.board[move.start_row][move.end_col] = NULL_SQUARE
        
        # update en crossaint target
        if move.piece_moved[1] == "p" and abs(move.start_row - move.end_row) == 2:
            # set en crossaint target to the square the pawn skipped over
            self.enpassant_target = BoardCoordinate((move.start_row + move.end_row) // 2, move.start_col)
        else:
            self.enpassant_target = None
        
        # handle castling move
        if move.is_castle_move:
            # Determine if kingside or queenside castle
            if move.end_col - move.start_col == 2:  # Kingside castle
                # Move the rook
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][move.end_col + 1]
                self.board[move.end_row][move.end_col + 1] = NULL_SQUARE
            else:  # Queenside castle
                # Move the rook
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 2]
                self.board[move.end_row][move.end_col - 2] = NULL_SQUARE
        
        # Update castling rights
        self.update_castle_rights(move)
        self.castle_rights_log.append(self.castle_rights.copy())
        
        # Track position for 3-move repetition rule
        position_key = self._get_position_key()
        self.position_history[position_key] = self.position_history.get(position_key, 0) + 1
        
        # Check for threefold repetition
        if self.position_history[position_key] >= 3:
            self.threefold_repetition = True
        
        # Update check status
        self.in_check, self.pins, self.checks = self.check_for_pins_and_checks()
    
    def undo_move(self) -> None:
        """undo the last move"""
        if not self.move_log:  # no moves to undo
            return
        
        # get the last move
        move = self.move_log.pop()
        
        # remove the position from history before undoing the move
        position_key = self._get_position_key()
        if position_key in self.position_history:
            self.position_history[position_key] -= 1
            if self.position_history[position_key] <= 0:
                del self.position_history[position_key]
        
        # reset threefold repetition flag
        self.threefold_repetition = False
        
        # restore the board
        self.board[move.start_row][move.start_col] = move.piece_moved
        self.board[move.end_row][move.end_col] = move.piece_captured
        
        # switch turns back
        self.white_to_move = not self.white_to_move
        
        # update king position if king moved
        if move.piece_moved == "wK":
            self.white_king_position = BoardCoordinate(move.start_row, move.start_col)
        elif move.piece_moved == "bK":
            self.black_king_position = BoardCoordinate(move.start_row, move.start_col)
        
        # handle en passant capture
        if move.is_enpassant_move:
            # restore the captured pawn
            self.board[move.end_row][move.end_col] = NULL_SQUARE
            self.board[move.start_row][move.end_col] = move.piece_captured
        
        # restore en passant target
        if len(self.move_log) > 0:
            prev_move = self.move_log[-1]
            if prev_move.piece_moved[1] == "p" and abs(prev_move.start_row - prev_move.end_row) == 2:
                self.enpassant_target = BoardCoordinate((prev_move.start_row + prev_move.end_row) // 2, prev_move.start_col)
            else:
                self.enpassant_target = None
        else:
            self.enpassant_target = None
        
        # handle castling move
        if move.is_castle_move:
            # determine if kingside or queenside castle
            if move.end_col - move.start_col == 2:  # kingside castle
                # restore the rook
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                self.board[move.end_row][move.end_col - 1] = NULL_SQUARE
            else:  # Queenside castle
                # restore the rook
                self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                self.board[move.end_row][move.end_col + 1] = NULL_SQUARE
        
        # restore castling rights
        self.castle_rights_log.pop()
        self.castle_rights = self.castle_rights_log[-1].copy()
        
        # update check status
        self.in_check, self.pins, self.checks = self.check_for_pins_and_checks()
    
    def update_castle_rights(self, move: Move) -> None:
        """update castling rights based on the move"""
        # if king moved, lose all castling rights for that color
        if move.piece_moved == "wK":
            self.castle_rights.wks = False
            self.castle_rights.wqs = False
        elif move.piece_moved == "bK":
            self.castle_rights.bks = False
            self.castle_rights.bqs = False
        
        # if rook moved, lose castling rights for that side
        elif move.piece_moved == "wR":
            if move.start_row == 7:
                if move.start_col == 0:  # queen's rook
                    self.castle_rights.wqs = False
                elif move.start_col == 7:  # king's rook
                    self.castle_rights.wks = False
        elif move.piece_moved == "bR":
            if move.start_row == 0:
                if move.start_col == 0:  # queen's rook
                    self.castle_rights.bqs = False
                elif move.start_col == 7:  # king's rook
                    self.castle_rights.bks = False
        
        # if rook is captured, lose castling rights for that side
        if move.piece_captured == "wR":
            if move.end_row == 7:
                if move.end_col == 0:
                    self.castle_rights.wqs = False
                elif move.end_col == 7:
                    self.castle_rights.wks = False
        elif move.piece_captured == "bR":
            if move.end_row == 0:
                if move.end_col == 0:
                    self.castle_rights.bqs = False
                elif move.end_col == 7:
                    self.castle_rights.bks = False
    
    def get_valid_moves(self) -> List[Move]:
        """Get all valid moves for the current player"""
        moves = []
        
        # check for pins and checks
        self.in_check, self.pins, self.checks = self.check_for_pins_and_checks()
        
        # get king position for the current player
        if self.white_to_move:
            king_row, king_col = self.white_king_position.row, self.white_king_position.col
        else:
            king_row, king_col = self.black_king_position.row, self.black_king_position.col
        
        # if in check, need to handle checks
        if self.in_check:
            # if there's only one check, either block or capture the checking piece
            if len(self.checks) == 1:
                check = self.checks[0]
                check_row, check_col = check[0], check[1]
                piece_checking = self.board[check_row][check_col]
                valid_squares = []  # squares that pieces can move to
                
                # if knight is checking, must capture the knight or move the king
                if piece_checking[1] == "N":
                    valid_squares = [(check_row, check_col)]
                else:
                    # for other pieces, can block the check
                    d_row, d_col = check[2], check[3]
                    for i in range(1, 8):
                        valid_square = (king_row + d_row * i, king_col + d_col * i)
                        valid_squares.append(valid_square)
                        if valid_square[0] == check_row and valid_square[1] == check_col:
                            break
                
                # get all possible moves
                self.get_all_possible_moves(moves)
                
                # filter moves that don't block or capture the checking piece
                i = len(moves) - 1
                while i >= 0:
                    move = moves[i]
                    if move.piece_moved[1] != "K":  # not a king move
                        # if the move doesn't block or capture the checking piece, remove it
                        if (move.end_row, move.end_col) not in valid_squares:
                            moves.pop(i)
                    i -= 1
            else:  # double check, king must move
                self.get_king_moves(king_row, king_col, moves)
        else:  # not in check, get all possible moves
            self.get_all_possible_moves(moves)
        
        # if no valid moves, it's either checkmate or stalemate
        if len(moves) == 0:
            if self.in_check:
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False
        
        return moves
    
    def get_all_possible_moves(self, moves: List[Move]) -> None:
        """Get all possible moves without considering checks"""
        # iterate through all squares on the board
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != NULL_SQUARE:  # if there's a piece on the square
                    piece_color = piece[0]
                    if (piece_color == "w" and self.white_to_move) or (piece_color == "b" and not self.white_to_move):
                        piece_type = piece[1]
                        # call the appropriate move function for the piece
                        self.move_functions[piece_type](row, col, moves)
    
    def check_for_pins_and_checks(self) -> Tuple[bool, List, List]:
        """Check for pins and checks on the current player's king"""
        pins = []  # squares pinned and the direction of the pin
        checks = []  # squares where enemy pieces are checking the king
        in_check = False
        
        # determine ally and enemy colors based on whose turn it is
        if self.white_to_move:
            ally_color = "w"
            enemy_color = "b"
            start_row, start_col = self.white_king_position.row, self.white_king_position.col
        else:
            ally_color = "b"
            enemy_color = "w"
            start_row, start_col = self.black_king_position.row, self.black_king_position.col
        
        # check all eight directions around the king
        directions = [(-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for i, direction in enumerate(directions):
            d_row, d_col = direction
            possible_pin = ()  # reset possible pin
            
            # check each square in this direction
            for j in range(1, 8):
                end_row = start_row + d_row * j
                end_col = start_col + d_col * j
                
                # check if the square is on the board
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    
                    # check if the piece is an ally piece (potential pin)
                    if end_piece[0] == ally_color and end_piece[1] != "K":
                        if possible_pin == ():  # First ally piece encountered
                            possible_pin = (end_row, end_col, d_row, d_col)
                        else:  # second ally piece, no pin or check possible
                            break
                    # check if the piece is an enemy piece
                    elif end_piece[0] == enemy_color:
                        piece_type = end_piece[1]
                        
                        # check if the piece can attack in this direction
                        if ((0 <= i <= 3 and piece_type == "R") or  # Rook checks horizontally/vertically
                            (4 <= i <= 7 and piece_type == "B") or  # Bishop checks diagonally
                            (j == 1 and piece_type == "p" and  # Pawn checks
                             ((enemy_color == "w" and 6 <= i <= 7) or  # White pawn checks diagonally down
                              (enemy_color == "b" and 4 <= i <= 5))) or  # Black pawn checks diagonally up
                            (piece_type == "Q") or  # Queen checks in all directions
                            (j == 1 and piece_type == "K")):  # King checks adjacent squares
                            
                            # No piece blocking, so check
                            if possible_pin == ():
                                in_check = True
                                checks.append((end_row, end_col, d_row, d_col))
                                break
                            # Piece blocking, so pin
                            else:
                                pins.append(possible_pin)
                                break
                        else:  # Enemy piece not applying check
                            break
                else:  # Off board
                    break
        
        # check for knight checks
        knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        for move in knight_moves:
            end_row = start_row + move[0]
            end_col = start_col + move[1]
            
            # check if the square is on the board
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                
                # check if the piece is an enemy knight
                if end_piece[0] == enemy_color and end_piece[1] == "N":
                    in_check = True
                    checks.append((end_row, end_col, move[0], move[1]))
        
        return in_check, pins, checks
    
    def get_pawn_moves(self, row: int, col: int, moves: List[Move]) -> None:
        """Get all possible pawn moves"""
        piece_pinned = False
        pin_direction = ()
        
        # check if the pawn is pinned
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                break
        
        # use the pawn movement strategy
        pawn_strategy = PieceMovementFactory.create_movement_strategy("p")
        pawn_moves = pawn_strategy.get_moves(
            BoardCoordinate(row, col), 
            self.board, 
            self.pins, 
            self.white_to_move, 
            self.enpassant_target,
            self.white_king_position,
            self.black_king_position
        )
        moves.extend(pawn_moves)
    
    def get_rook_moves(self, row: int, col: int, moves: List[Move]) -> None:
        """Get all possible rook moves"""
        # use the rook movement strategy
        rook_strategy = PieceMovementFactory.create_movement_strategy("R")
        rook_moves = rook_strategy.get_moves(
            BoardCoordinate(row, col), 
            self.board, 
            self.pins, 
            self.white_to_move
        )
        moves.extend(rook_moves)
    
    def get_knight_moves(self, row: int, col: int, moves: List[Move]) -> None:
        """Get all possible knight moves"""
        # use the knight movement strategy
        knight_strategy = PieceMovementFactory.create_movement_strategy("N")
        knight_moves = knight_strategy.get_moves(
            BoardCoordinate(row, col), 
            self.board, 
            self.pins, 
            self.white_to_move
        )
        moves.extend(knight_moves)
    
    def get_bishop_moves(self, row: int, col: int, moves: List[Move]) -> None:
        """Get all possible bishop moves"""
        # use the bishop movement strategy
        bishop_strategy = PieceMovementFactory.create_movement_strategy("B")
        bishop_moves = bishop_strategy.get_moves(
            BoardCoordinate(row, col), 
            self.board, 
            self.pins, 
            self.white_to_move
        )
        moves.extend(bishop_moves)
    
    def get_queen_moves(self, row: int, col: int, moves: List[Move]) -> None:
        """Get all possible queen moves"""
        # use the queen movement strategy
        queen_strategy = PieceMovementFactory.create_movement_strategy("Q")
        queen_moves = queen_strategy.get_moves(
            BoardCoordinate(row, col), 
            self.board, 
            self.pins, 
            self.white_to_move
        )
        moves.extend(queen_moves)
    
    def check_king_safety(self, white_king_pos: BoardCoordinate, black_king_pos: BoardCoordinate) -> Tuple[bool, List, List]:
        """Wrapper function for check_for_pins_and_checks that accepts king positions as parameters
        This allows us to simulate king moves without actually making them"""
        # save the current king positions
        original_white_king = self.white_king_position
        original_black_king = self.black_king_position
        
        # temporarily set the king positions to the provided positions
        self.white_king_position = white_king_pos
        self.black_king_position = black_king_pos
        
        # call the check method
        result = self.check_for_pins_and_checks()
        
        # restore the original king positions
        self.white_king_position = original_white_king
        self.black_king_position = original_black_king
        
        return result
        
    def get_king_moves(self, row: int, col: int, moves: List[Move]) -> None:
        """Get all possible king moves"""
        # use the king movement strategy for normal moves
        king_strategy = PieceMovementFactory.create_movement_strategy("K")
        king_moves = king_strategy.get_moves(
            BoardCoordinate(row, col), 
            self.board, 
            self.pins, 
            self.white_to_move,
            self.white_king_position,
            self.black_king_position,
            self.check_king_safety
        )
        moves.extend(king_moves)
        
        # check for castling moves
        MoveGenerator.get_castle_moves(
            row, col, moves, self.board, 
            self.white_to_move, self.castle_rights, self.in_check,
            self.check_king_safety, self.white_king_position, self.black_king_position
        )
    
    def is_game_over(self) -> bool:
        """Check if the game is over (checkmate, stalemate, threefold repetition, or insufficient material)"""
        # check for insufficient material
        self.check_insufficient_material()
        return hasattr(self, 'checkmate') and (self.checkmate or self.stalemate or self.threefold_repetition or self.insufficient_material)
    
    def get_game_state(self) -> str:
        """Get the current state of the game"""
        if hasattr(self, 'checkmate') and self.checkmate:
            return "Checkmate! " + ("Black" if self.white_to_move else "White") + " wins!"
        elif hasattr(self, 'stalemate') and self.stalemate:
            return "Stalemate!"
        elif self.threefold_repetition:
            return "Draw by threefold repetition!"
        elif self.insufficient_material:
            return "Draw by insufficient material!"
        else:
            return ("White" if self.white_to_move else "Black") + " to move"
    
    def print_board(self) -> None:
        """Print the current board state to the console"""
        print("  a b c d e f g h")
        print(" +-----------------+")
        for r in range(8):
            print(f"{8-r}|" + " ".join(self._get_piece_symbol(self.board[r][c]) for c in range(8)) + f"|{8-r}")
        print(" +-----------------+")
        print("  a b c d e f g h")
        print("")
        print(self.get_game_state())
    
    def _get_piece_symbol(self, piece: str) -> str:
        """Convert piece code to symbol for printing"""
        piece_symbols = {
            "wp": "P", "wR": "R", "wN": "N", "wB": "B", "wQ": "Q", "wK": "K",
            "bp": "p", "bR": "r", "bN": "n", "bB": "b", "bQ": "q", "bK": "k",
            NULL_SQUARE: "."
        }
        return piece_symbols.get(piece, "?")
        
    def check_insufficient_material(self) -> None:
        """Check if there is insufficient material to checkmate (draw condition)
        Insufficient material includes:
        - King vs King
        - King + Bishop vs King
        - King + Knight vs King
        - King + 2 Knights vs King (technically possible but extremely rare)
        """
        white_pieces = []
        black_pieces = []
        
        # count pieces for each side
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != NULL_SQUARE:
                    if piece[0] == 'w':
                        white_pieces.append(piece[1])
                    else:
                        black_pieces.append(piece[1])
        
        # remove kings from the count
        if 'K' in white_pieces:
            white_pieces.remove('K')
        if 'K' in black_pieces:
            black_pieces.remove('K')
        
        # check for insufficient material scenarios
        if len(white_pieces) == 0 and len(black_pieces) == 0:  # king vs king
            self.insufficient_material = True
        elif len(white_pieces) == 1 and len(black_pieces) == 0:  # king + minor piece vs king
            if white_pieces[0] == 'B' or white_pieces[0] == 'N':
                self.insufficient_material = True
        elif len(white_pieces) == 0 and len(black_pieces) == 1:  # king vs king + minor piece
            if black_pieces[0] == 'B' or black_pieces[0] == 'N':
                self.insufficient_material = True
        elif len(white_pieces) == 2 and len(black_pieces) == 0:  # king + 2 kknights vs king
            if white_pieces.count('N') == 2:
                self.insufficient_material = True
        elif len(white_pieces) == 0 and len(black_pieces) == 2:  # king vs king + 2 Knights
            if black_pieces.count('N') == 2:
                self.insufficient_material = True
        else:
            self.insufficient_material = False
    
    def _get_position_key(self) -> str:
        """Generate a unique key for the current board position for repetition detection
        The key includes the board state, castling rights, en passant square, and whose turn it is"""
        key_parts = []
        
        # add board state
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != NULL_SQUARE:
                    key_parts.append(f"{piece}@{row}{col}")
        
        # add castling rights
        key_parts.append(f"castle:{int(self.castle_rights.wks)}{int(self.castle_rights.wqs)}{int(self.castle_rights.bks)}{int(self.castle_rights.bqs)}")
        
        # add en passant target
        if self.enpassant_target:
            key_parts.append(f"ep:{self.enpassant_target.row}{self.enpassant_target.col}")
        
        # add whose turn it is
        key_parts.append(f"turn:{int(self.white_to_move)}")
        
        # Join all parts with a separator
        return "|".join(key_parts)
