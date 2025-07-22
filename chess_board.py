from chess_piece import Piece, PieceType, Color
from chess_position import Position, Move

class Board:
    def __init__(self, fen=None):
        self.pieces = [[Piece() for _ in range(8)] for _ in range(8)]
        self.side_to_move = Color.WHITE
        self.white_can_castle_kingside = True
        self.white_can_castle_queenside = True
        self.black_can_castle_kingside = True
        self.black_can_castle_queenside = True
        self.en_passant_target = Position(-1, -1)
        self.half_move_clock = 0
        self.full_move_number = 1
        
        if fen:
            self._load_from_fen(fen)
        else:
            self._setup_initial_position()
    
    def _setup_initial_position(self):
        # Set up pawns
        for file in range(8):
            self.set_piece(Position(file, 1), Piece(PieceType.PAWN, Color.WHITE))
            self.set_piece(Position(file, 6), Piece(PieceType.PAWN, Color.BLACK))
        
        # Set up other pieces
        piece_order = [
            PieceType.ROOK, PieceType.KNIGHT, PieceType.BISHOP, PieceType.QUEEN,
            PieceType.KING, PieceType.BISHOP, PieceType.KNIGHT, PieceType.ROOK
        ]
        
        for file in range(8):
            self.set_piece(Position(file, 0), Piece(piece_order[file], Color.WHITE))
            self.set_piece(Position(file, 7), Piece(piece_order[file], Color.BLACK))
    
    def _load_from_fen(self, fen):
        parts = fen.split()
        if len(parts) < 6:
            raise ValueError("Invalid FEN string")
        
        # Parse board position
        ranks = parts[0].split('/')
        if len(ranks) != 8:
            raise ValueError("Invalid FEN: board position must have 8 ranks")
        
        for rank_idx, rank in enumerate(ranks):
            file_idx = 0
            for char in rank:
                if char.isdigit():
                    file_idx += int(char)
                else:
                    self.set_piece(Position(file_idx, 7 - rank_idx), Piece.from_char(char))
                    file_idx += 1
        
        # Parse side to move
        self.side_to_move = Color.WHITE if parts[1] == 'w' else Color.BLACK
        
        # Parse castling rights
        self.white_can_castle_kingside = 'K' in parts[2]
        self.white_can_castle_queenside = 'Q' in parts[2]
        self.black_can_castle_kingside = 'k' in parts[2]
        self.black_can_castle_queenside = 'q' in parts[2]
        
        # Parse en passant target
        if parts[3] != '-':
            self.en_passant_target = Position.from_algebraic(parts[3])
        
        # Parse half-move clock and full move number
        self.half_move_clock = int(parts[4])
        self.full_move_number = int(parts[5])
    
    def get_piece(self, pos):
        if not pos.is_valid():
            return Piece()
        return self.pieces[pos.rank][pos.file]
    
    def set_piece(self, pos, piece):
        if pos.is_valid():
            self.pieces[pos.rank][pos.file] = piece
    
    def get_side_to_move(self):
        return self.side_to_move
    
    def set_side_to_move(self, color):
        self.side_to_move = color
    
    def toggle_side_to_move(self):
        self.side_to_move = Color.BLACK if self.side_to_move == Color.WHITE else Color.WHITE
    
    def to_fen(self):
        fen = ""
        
        # Board position
        for rank in range(7, -1, -1):
            empty_count = 0
            for file in range(8):
                piece = self.get_piece(Position(file, rank))
                if piece.is_empty():
                    empty_count += 1
                else:
                    if empty_count > 0:
                        fen += str(empty_count)
                        empty_count = 0
                    fen += piece.to_char()
            
            if empty_count > 0:
                fen += str(empty_count)
            
            if rank > 0:
                fen += "/"
        
        # Side to move
        fen += " w" if self.side_to_move == Color.WHITE else " b"
        
        # Castling rights
        castling = ""
        if self.white_can_castle_kingside:
            castling += "K"
        if self.white_can_castle_queenside:
            castling += "Q"
        if self.black_can_castle_kingside:
            castling += "k"
        if self.black_can_castle_queenside:
            castling += "q"
        
        fen += " " + (castling if castling else "-")
        
        # En passant target
        fen += " " + (self.en_passant_target.to_algebraic() if self.en_passant_target.is_valid() else "-")
        
        # Half-move clock and full move number
        fen += f" {self.half_move_clock} {self.full_move_number}"
        
        return fen
    
    def print_board(self):
        print("  a b c d e f g h")
        print(" +-----------------+")
        for rank in range(7, -1, -1):
            print(f"{rank + 1}| ", end="")
            for file in range(8):
                piece = self.get_piece(Position(file, rank))
                print(piece.to_char() + " ", end="")
            print(f"|{rank + 1}")
        print(" +-----------------+")
        print("  a b c d e f g h")
        print(f"Side to move: {'White' if self.side_to_move == Color.WHITE else 'Black'}")
