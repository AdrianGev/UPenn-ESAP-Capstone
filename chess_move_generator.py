from chess_piece import Piece, PieceType, Color
from chess_position import Position, Move

class MoveGenerator:
    def __init__(self, board):
        self.board = board
    
    def generate_legal_moves(self):
        # generate all legal moves for the current side to move
        pseudo_legal_moves = self.generate_pseudo_legal_moves()
        legal_moves = []
        
        for move in pseudo_legal_moves:
            if self.is_legal_move(move):
                legal_moves.append(move)
        
        return legal_moves
    
    def generate_pseudo_legal_moves(self):
        # generate all pseudlegal moves for the current side to move
        moves = []
        side_to_move = self.board.get_side_to_move()
        
        for rank in range(8):
            for file in range(8):
                pos = Position(file, rank)
                piece = self.board.get_piece(pos)
                
                if not piece.is_empty() and piece.color == side_to_move:
                    piece_moves = self.generate_piece_moves(pos)
                    moves.extend(piece_moves)
        
        return moves
    
    def generate_piece_moves(self, pos):
        # generate all pseudolegal moves for a specific piece
        piece = self.board.get_piece(pos)
        
        if piece.is_empty():
            return []
        
        if piece.piece_type == PieceType.PAWN:
            return self.generate_pawn_moves(pos)
        elif piece.piece_type == PieceType.KNIGHT:
            return self.generate_knight_moves(pos)
        elif piece.piece_type == PieceType.BISHOP:
            return self.generate_bishop_moves(pos)
        elif piece.piece_type == PieceType.ROOK:
            return self.generate_rook_moves(pos)
        elif piece.piece_type == PieceType.QUEEN:
            return self.generate_queen_moves(pos)
        elif piece.piece_type == PieceType.KING:
            return self.generate_king_moves(pos)
        
        return []
    
    def generate_pawn_moves(self, pos):
        # generate all pseudolegal pawn moves
        moves = []
        piece = self.board.get_piece(pos)
        
        if piece.is_empty() or piece.piece_type != PieceType.PAWN:
            return moves
        
        # direction of movement (1 for white, -1 for black)
        direction = 1 if piece.color == Color.WHITE else -1 # wow so compact
        
        # single step forward
        new_pos = Position(pos.file, pos.rank + direction)
        if new_pos.is_valid() and self.board.get_piece(new_pos).is_empty():
            # check for promotion
            if (piece.color == Color.WHITE and new_pos.rank == 7) or \
               (piece.color == Color.BLACK and new_pos.rank == 0):
                for promotion in [PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT]:
                    moves.append(Move(pos, new_pos, promotion))
            else:
                moves.append(Move(pos, new_pos))
            
            # double step from starting position
            if (piece.color == Color.WHITE and pos.rank == 1) or \
               (piece.color == Color.BLACK and pos.rank == 6):
                new_pos = Position(pos.file, pos.rank + 2 * direction)
                if new_pos.is_valid() and self.board.get_piece(new_pos).is_empty():
                    moves.append(Move(pos, new_pos))
        
        # captures
        for file_offset in [-1, 1]:
            new_pos = Position(pos.file + file_offset, pos.rank + direction)
            if new_pos.is_valid():
                target_piece = self.board.get_piece(new_pos)
                
                # normal capture
                if not target_piece.is_empty() and target_piece.color != piece.color:
                    # check for promotion
                    if (piece.color == Color.WHITE and new_pos.rank == 7) or \
                       (piece.color == Color.BLACK and new_pos.rank == 0):
                        for promotion in [PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT]:
                            moves.append(Move(pos, new_pos, promotion))
                    else:
                        moves.append(Move(pos, new_pos))
                
                # en passant capture
                elif new_pos == self.board.en_passant_target:
                    moves.append(Move(pos, new_pos))
        
        return moves
    
    def generate_knight_moves(self, pos):
        # generate all pseudolegal knight moves
        moves = []
        piece = self.board.get_piece(pos)
        
        if piece.is_empty() or piece.piece_type != PieceType.KNIGHT:
            return moves
        
        # knight move offsets
        offsets = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        
        for offset in offsets:
            new_pos = Position(pos.file + offset[0], pos.rank + offset[1])
            if new_pos.is_valid():
                target_piece = self.board.get_piece(new_pos)
                if target_piece.is_empty() or target_piece.color != piece.color:
                    moves.append(Move(pos, new_pos))
        
        return moves
    
    def generate_sliding_moves(self, pos, directions):
        # generate sliding moves (bishop, rook, queen)
        moves = []
        piece = self.board.get_piece(pos)
        
        if piece.is_empty():
            return moves
        
        for direction in directions:
            file_dir, rank_dir = direction
            current_pos = Position(pos.file + file_dir, pos.rank + rank_dir)
            
            while current_pos.is_valid():
                target_piece = self.board.get_piece(current_pos)
                
                if target_piece.is_empty():
                    # empty square, add move and continue
                    moves.append(Move(pos, current_pos))
                elif target_piece.color != piece.color:
                    # enemy piece, add capture and stop
                    moves.append(Move(pos, current_pos))
                    break
                else:
                    # Friendly piece, stop
                    break
                
                current_pos = Position(current_pos.file + file_dir, current_pos.rank + rank_dir)
        
        return moves
    
    def generate_bishop_moves(self, pos):
        # generate all pseudolegal bishop moves
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        return self.generate_sliding_moves(pos, directions)
    
    def generate_rook_moves(self, pos):
        # generate all pseudolegal rook moves
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        return self.generate_sliding_moves(pos, directions)
    
    def generate_queen_moves(self, pos):
        # generate all pseudolegal queen moves
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 1),
            (1, -1), (1, 0), (1, 1)
        ]
        return self.generate_sliding_moves(pos, directions)
    
    def generate_king_moves(self, pos):
        # generate all pseudolegal king moves
        moves = []
        piece = self.board.get_piece(pos)
        
        if piece.is_empty() or piece.piece_type != PieceType.KING:
            return moves
        
        # regular king moves
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 1),
            (1, -1), (1, 0), (1, 1)
        ]
        
        for direction in directions:
            new_pos = Position(pos.file + direction[0], pos.rank + direction[1])
            if new_pos.is_valid():
                target_piece = self.board.get_piece(new_pos)
                if target_piece.is_empty() or target_piece.color != piece.color:
                    moves.append(Move(pos, new_pos))
        
        # castling
        if piece.color == Color.WHITE:
            # kingside castling
            if self.board.white_can_castle_kingside:
                if (self.board.get_piece(Position(5, 0)).is_empty() and
                    self.board.get_piece(Position(6, 0)).is_empty() and
                    not self.is_square_attacked(Position(4, 0), Color.BLACK) and
                    not self.is_square_attacked(Position(5, 0), Color.BLACK) and
                    not self.is_square_attacked(Position(6, 0), Color.BLACK)):
                    moves.append(Move(pos, Position(6, 0)))
            
            # Queenside castling
            if self.board.white_can_castle_queenside:
                if (self.board.get_piece(Position(1, 0)).is_empty() and
                    self.board.get_piece(Position(2, 0)).is_empty() and
                    self.board.get_piece(Position(3, 0)).is_empty() and
                    not self.is_square_attacked(Position(2, 0), Color.BLACK) and
                    not self.is_square_attacked(Position(3, 0), Color.BLACK) and
                    not self.is_square_attacked(Position(4, 0), Color.BLACK)):
                    moves.append(Move(pos, Position(2, 0)))
        else:
            # Kingside castling
            if self.board.black_can_castle_kingside:
                if (self.board.get_piece(Position(5, 7)).is_empty() and
                    self.board.get_piece(Position(6, 7)).is_empty() and
                    not self.is_square_attacked(Position(4, 7), Color.WHITE) and
                    not self.is_square_attacked(Position(5, 7), Color.WHITE) and
                    not self.is_square_attacked(Position(6, 7), Color.WHITE)):
                    moves.append(Move(pos, Position(6, 7)))
            
            # Queenside castling
            if self.board.black_can_castle_queenside:
                if (self.board.get_piece(Position(1, 7)).is_empty() and
                    self.board.get_piece(Position(2, 7)).is_empty() and
                    self.board.get_piece(Position(3, 7)).is_empty() and
                    not self.is_square_attacked(Position(2, 7), Color.WHITE) and
                    not self.is_square_attacked(Position(3, 7), Color.WHITE) and
                    not self.is_square_attacked(Position(4, 7), Color.WHITE)):
                    moves.append(Move(pos, Position(2, 7)))
        
        return moves
    
    def is_square_attacked(self, pos, attacking_color):
        # check if a square is attacked by a specific color
        # check pawn attacks
        direction = -1 if attacking_color == Color.WHITE else 1
        for file_offset in [-1, 1]:
            attacker_pos = Position(pos.file + file_offset, pos.rank + direction)
            if attacker_pos.is_valid():
                attacker = self.board.get_piece(attacker_pos)
                if (not attacker.is_empty() and 
                    attacker.color == attacking_color and 
                    attacker.piece_type == PieceType.PAWN):
                    return True
        
        # check knight attacks
        knight_offsets = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        for offset in knight_offsets:
            attacker_pos = Position(pos.file + offset[0], pos.rank + offset[1])
            if attacker_pos.is_valid():
                attacker = self.board.get_piece(attacker_pos)
                if (not attacker.is_empty() and 
                    attacker.color == attacking_color and 
                    attacker.piece_type == PieceType.KNIGHT):
                    return True
        
        # check sliding piece attacks (bishop, rook, queen)
        bishop_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        rook_directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        # check bishop and queen attacks
        for direction in bishop_directions:
            file_dir, rank_dir = direction
            current_pos = Position(pos.file + file_dir, pos.rank + rank_dir)
            
            while current_pos.is_valid():
                attacker = self.board.get_piece(current_pos)
                if not attacker.is_empty():
                    if (attacker.color == attacking_color and 
                        (attacker.piece_type == PieceType.BISHOP or 
                         attacker.piece_type == PieceType.QUEEN)):
                        return True
                    break
                
                current_pos = Position(current_pos.file + file_dir, current_pos.rank + rank_dir)
        
        # check rook and queen attacks
        for direction in rook_directions:
            file_dir, rank_dir = direction
            current_pos = Position(pos.file + file_dir, pos.rank + rank_dir)
            
            while current_pos.is_valid():
                attacker = self.board.get_piece(current_pos)
                if not attacker.is_empty():
                    if (attacker.color == attacking_color and 
                        (attacker.piece_type == PieceType.ROOK or 
                         attacker.piece_type == PieceType.QUEEN)):
                        return True
                    break
                
                current_pos = Position(current_pos.file + file_dir, current_pos.rank + rank_dir)
        
        # check king attacks
        king_directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 1),
            (1, -1), (1, 0), (1, 1)
        ]
        for direction in king_directions:
            attacker_pos = Position(pos.file + direction[0], pos.rank + direction[1])
            if attacker_pos.is_valid():
                attacker = self.board.get_piece(attacker_pos)
                if (not attacker.is_empty() and 
                    attacker.color == attacking_color and 
                    attacker.piece_type == PieceType.KING):
                    return True
        
        return False
    
    def is_in_check(self, color=None):
        # check if the specified color (or current side to move) is in check
        if color is None:
            color = self.board.get_side_to_move()
        
        # find the king
        king_pos = None
        for rank in range(8):
            for file in range(8):
                pos = Position(file, rank)
                piece = self.board.get_piece(pos)
                if (not piece.is_empty() and 
                    piece.color == color and 
                    piece.piece_type == PieceType.KING):
                    king_pos = pos
                    break
            if king_pos:
                break
        
        if not king_pos:
            return False  # No king found (shouldn't happen in a valid game)
        
        # check if the king is under attack
        opposing_color = Color.BLACK if color == Color.WHITE else Color.WHITE
        return self.is_square_attacked(king_pos, opposing_color)
    
    def is_legal_move(self, move):
        # check if a move is legal (doesn't leave the king in check)
        # make a copy of the board
        from copy import deepcopy
        test_board = deepcopy(self.board)
        
        # make the move on the copy
        self.make_move_on_board(test_board, move)
        
        # check if the king is in check after the move
        test_generator = MoveGenerator(test_board)
        return not test_generator.is_in_check(self.board.get_side_to_move())
    
    def make_move_on_board(self, board, move):
        # make a move on the board without checking legality
        if not move.from_pos.is_valid() or not move.to_pos.is_valid():
            return False
        
        piece = board.get_piece(move.from_pos)
        target = board.get_piece(move.to_pos)
        
        # update half-move clock
        if piece.piece_type == PieceType.PAWN or not target.is_empty():
            board.half_move_clock = 0
        else:
            board.half_move_clock += 1
        
        # update full move number
        if board.side_to_move == Color.BLACK:
            board.full_move_number += 1
        
        # handle castling
        if piece.piece_type == PieceType.KING:
            if piece.color == Color.WHITE:
                board.white_can_castle_kingside = False
                board.white_can_castle_queenside = False
                
                # Kingside castling
                if move.from_pos.file == 4 and move.from_pos.rank == 0 and move.to_pos.file == 6 and move.to_pos.rank == 0:
                    # Move the rook
                    rook = board.get_piece(Position(7, 0))
                    board.set_piece(Position(7, 0), Piece())
                    board.set_piece(Position(5, 0), rook)
                
                # Queenside castling
                elif move.from_pos.file == 4 and move.from_pos.rank == 0 and move.to_pos.file == 2 and move.to_pos.rank == 0:
                    # Move the rook
                    rook = board.get_piece(Position(0, 0))
                    board.set_piece(Position(0, 0), Piece())
                    board.set_piece(Position(3, 0), rook)
            else:
                board.black_can_castle_kingside = False
                board.black_can_castle_queenside = False
                
                # Kingside castling
                if move.from_pos.file == 4 and move.from_pos.rank == 7 and move.to_pos.file == 6 and move.to_pos.rank == 7:
                    # Move the rook
                    rook = board.get_piece(Position(7, 7))
                    board.set_piece(Position(7, 7), Piece())
                    board.set_piece(Position(5, 7), rook)
                
                # Queenside castling
                elif move.from_pos.file == 4 and move.from_pos.rank == 7 and move.to_pos.file == 2 and move.to_pos.rank == 7:
                    # Move the rook
                    rook = board.get_piece(Position(0, 7))
                    board.set_piece(Position(0, 7), Piece())
                    board.set_piece(Position(3, 7), rook)
        
        # handle rook moves (update castling rights)
        elif piece.piece_type == PieceType.ROOK:
            if piece.color == Color.WHITE:
                if move.from_pos.file == 0 and move.from_pos.rank == 0:
                    board.white_can_castle_queenside = False
                elif move.from_pos.file == 7 and move.from_pos.rank == 0:
                    board.white_can_castle_kingside = False
            else:
                if move.from_pos.file == 0 and move.from_pos.rank == 7:
                    board.black_can_castle_queenside = False
                elif move.from_pos.file == 7 and move.from_pos.rank == 7:
                    board.black_can_castle_kingside = False
        
        # handle pawn moves
        if piece.piece_type == PieceType.PAWN:
            # double pawn move (set en passant target)
            if abs(move.to_pos.rank - move.from_pos.rank) == 2:
                en_passant_rank = (move.from_pos.rank + move.to_pos.rank) // 2
                board.en_passant_target = Position(move.from_pos.file, en_passant_rank)
            else:
                board.en_passant_target = Position(-1, -1)
            
            # en passant capture
            if move.to_pos == board.en_passant_target:
                # remove the captured pawn
                capture_rank = move.from_pos.rank
                board.set_piece(Position(move.to_pos.file, capture_rank), Piece())
            
            # promotion
            if move.promotion and ((piece.color == Color.WHITE and move.to_pos.rank == 7) or
                                   (piece.color == Color.BLACK and move.to_pos.rank == 0)):
                piece = Piece(move.promotion, piece.color)
        else:
            # reset en passant target for non-pawn moves
            board.en_passant_target = Position(-1, -1)
        
        # move the piece
        board.set_piece(move.to_pos, piece)
        board.set_piece(move.from_pos, Piece())
        
        # toggle side to move
        board.toggle_side_to_move()
        
        return True
