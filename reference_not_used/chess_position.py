class Position:
    def __init__(self, file=0, rank=0):
        self.file = file  # 0-7 (a-h)
        self.rank = rank  # 0-7 (1-8)
    
    def is_valid(self):
        return 0 <= self.file < 8 and 0 <= self.rank < 8
    
    def to_algebraic(self):
        if not self.is_valid():
            return "invalid"
        return f"{chr(self.file + ord('a'))}{self.rank + 1}"
    
    @staticmethod
    def from_algebraic(algebraic):
        if len(algebraic) != 2:
            return Position(-1, -1)  # invalid position
        
        file = ord(algebraic[0]) - ord('a')
        rank = int(algebraic[1]) - 1
        
        if not (0 <= file < 8 and 0 <= rank < 8):
            return Position(-1, -1)  # invalid position
        
        return Position(file, rank)
    
    def __eq__(self, other):
        if not isinstance(other, Position):
            return False
        return self.file == other.file and self.rank == other.rank
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __repr__(self):
        return self.to_algebraic()


class Move:
    def __init__(self, from_pos=None, to_pos=None, promotion=None):
        self.from_pos = from_pos if from_pos is not None else Position(-1, -1)
        self.to_pos = to_pos if to_pos is not None else Position(-1, -1)
        self.promotion = promotion  # PieceType for pawn promotion
    
    def to_algebraic(self):
        if not self.from_pos.is_valid() or not self.to_pos.is_valid():
            return "invalid"
        
        move_str = f"{self.from_pos.to_algebraic()}{self.to_pos.to_algebraic()}"
        
        if self.promotion:
            promotion_chars = {
                'QUEEN': 'q', 'ROOK': 'r', 'BISHOP': 'b', 'KNIGHT': 'n'
            }
            move_str += promotion_chars.get(self.promotion.name, '')
        
        return move_str
    
    @staticmethod
    def from_algebraic(algebraic):
        if len(algebraic) < 4:
            return Move()  # Invalid move
        
        from_pos = Position.from_algebraic(algebraic[0:2])
        to_pos = Position.from_algebraic(algebraic[2:4])
        
        promotion = None
        if len(algebraic) > 4:
            from chess_piece import PieceType
            promotion_map = {
                'q': PieceType.QUEEN,
                'r': PieceType.ROOK,
                'b': PieceType.BISHOP,
                'n': PieceType.KNIGHT
            }
            promotion = promotion_map.get(algebraic[4].lower())
        
        return Move(from_pos, to_pos, promotion)
    
    def __repr__(self):
        return self.to_algebraic()
