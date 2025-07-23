from enum import Enum, auto

class PieceType(Enum):
    EMPTY = 0
    PAWN = 1
    KNIGHT = 2
    BISHOP = 3
    ROOK = 4
    QUEEN = 5
    KING = 6

class Color(Enum):
    WHITE = 0
    BLACK = 1

class Piece:
    def __init__(self, piece_type=PieceType.EMPTY, color=None):
        self.piece_type = piece_type
        self.color = color
    
    def is_empty(self):
        return self.piece_type == PieceType.EMPTY
    
    def to_char(self):
        if self.is_empty():
            return '.'
        
        char_map = {
            PieceType.PAWN: 'p',
            PieceType.KNIGHT: 'n',
            PieceType.BISHOP: 'b',
            PieceType.ROOK: 'r',
            PieceType.QUEEN: 'q',
            PieceType.KING: 'k'
        }
        
        char = char_map[self.piece_type]
        return char.upper() if self.color == Color.WHITE else char
    
    @staticmethod
    def from_char(char):
        if char == '.':
            return Piece()
        
        color = Color.WHITE if char.isupper() else Color.BLACK
        char = char.lower()
        
        type_map = {
            'p': PieceType.PAWN,
            'n': PieceType.KNIGHT,
            'b': PieceType.BISHOP,
            'r': PieceType.ROOK,
            'q': PieceType.QUEEN,
            'k': PieceType.KING
        }
        
        return Piece(type_map.get(char, PieceType.EMPTY), color)
