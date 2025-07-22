from typing import Dict, List, Tuple

# vals for the pieces
PIECE_VALUES = {
    'P': 100,   # Pawn
    'N': 320,   # Knight
    'B': 330,   # Bishop
    'R': 500,   # Rook
    'Q': 900,   # Queen
    'K': 20000  # King idk cuz for the funnies cuz they aint going anywhere lol
}

# for the reward for when the king is in the center of the board bc then bro controls more squares
KING_CENTRALIZATION = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 5, 5, 5, 5, 5, 5, 0],
    [0, 5, 10, 10, 10, 10, 5, 0],
    [0, 5, 10, 20, 20, 10, 5, 0],
    [0, 5, 10, 20, 20, 10, 5, 0],
    [0, 5, 10, 10, 10, 10, 5, 0],
    [0, 5, 5, 5, 5, 5, 5, 0],
    [0, 0, 0, 0, 0, 0, 0, 0]
]

# bonus for passed pawns (pawns with no opposing pawns in front of them)
PASSED_PAWN_BONUS = [0, 10, 20, 40, 60, 80, 100, 0] # per each square

# penalty for isolated pawns (pawns with no same colored pawns on adjacent files)
ISOLATED_PAWN_PENALTY = -15


class Evaluator:
    def __init__(self):
        pass
    
    def evaluate(self, board) -> int:
        """
        evaluate the current board position
        
        arguments to be passed in: board: the board to evaluate (nooo really??)
        returns: a score for the position (positive is good for white, negative is good for black)
        """
        # if game is over, return the score
        if board.is_checkmate():
            return -20000 if board.get_side_to_move() == 0 else 20000  # 0 for white, 1 for black
        
        if board.is_stalemate() or board.is_draw():
            return 0
        
        # init score
        score = 0
        
        # 1. Material counting
        score += self._evaluate_material(board)
        
        # 2. King activity (centralization in endgames)
        score += self._evaluate_king_position(board)
        
        # 3. Pawn structure
        score += self._evaluate_pawn_structure(board)
        
        # return final score (positive for white advantage, negative for black advantage)
        return score
    
    def _evaluate_material(self, board) -> int:
        """
        evaluate material balance
        
        arguments to be passed in: board: the board to evaluate
        returns: material score
        """
        white_material = 0
        black_material = 0
        
        # count material for each side
        pieces = board.get_pieces()
        for piece_type, positions in pieces.items():
            if piece_type.isupper():  # White piece
                white_material += PIECE_VALUES[piece_type.upper()] * len(positions)
            else:  # black piece
                black_material += PIECE_VALUES[piece_type.upper()] * len(positions)
        
        return white_material - black_material
    
    def _evaluate_king_position(self, board) -> int:
        """
        evaluate king positions - in endgames, centralized kings are better
        
        arguments to be passed in: board: the board to evaluate
        returns: king position score
        """
        score = 0
        
        # Only consider king centralization in endgames
        if self._is_endgame(board):
            white_king_pos = board.get_king_position(0)  # 0 for white
            black_king_pos = board.get_king_position(1)  # 1 for black
            
            if white_king_pos:
                rank, file = white_king_pos
                score += KING_CENTRALIZATION[rank][file]
            
            if black_king_pos:
                rank, file = black_king_pos
                score -= KING_CENTRALIZATION[rank][file]
        
        return score
    
    def _evaluate_pawn_structure(self, board) -> int:
        """
        evaluate pawn structure - passed pawns and isolated pawns
        
        arguments to be passed in: board: the board to evaluate
        returns: pawn structure score
        """
        score = 0
        
        # Get pawn positions
        white_pawns = board.get_piece_positions('P')
        black_pawns = board.get_piece_positions('p')
        
        # Evaluate passed pawns
        for rank, file in white_pawns:
            if self._is_passed_pawn(board, rank, file, 0):  # 0 for white
                score += PASSED_PAWN_BONUS[rank]  # Higher rank = more valuable passed pawn
        
        for rank, file in black_pawns:
            if self._is_passed_pawn(board, rank, file, 1):  # 1 for black
                score -= PASSED_PAWN_BONUS[7 - rank]  # Invert rank for black
        
        # Evaluate isolated pawns
        for rank, file in white_pawns:
            if self._is_isolated_pawn(board, rank, file, 0):  # 0 for white
                score += ISOLATED_PAWN_PENALTY
        
        for rank, file in black_pawns:
            if self._is_isolated_pawn(board, rank, file, 1):  # 1 for black
                score -= ISOLATED_PAWN_PENALTY
        
        return score
    
    """
    !!
    Probably dont need this method since its an endgame engine only
    !!
    """

    # def _is_endgame(self, board) -> bool:
    #     """
    #     determine if the position is an endgame
        
    #     arguments to be passed in: board: the board to evaluate
    #     returns: true if endgame, false otherwise
    #     """
    #     # Simple endgame detection: no queens or at most one minor piece per side
    #     pieces = board.get_pieces()
        
    #     white_queens = len(pieces.get('Q', []))
    #     black_queens = len(pieces.get('q', []))
        
    #     white_minors = len(pieces.get('N', [])) + len(pieces.get('B', []))
    #     black_minors = len(pieces.get('n', [])) + len(pieces.get('b', []))
        
    #     return (white_queens == 0 and black_queens == 0) or \
    #            (white_minors <= 1 and black_minors <= 1)


    """
    !!
    Probably dont need this method since its an endgame engine only
    !!
    """
    
    def _is_passed_pawn(self, board, rank, file, color) -> bool:
        """
        check if a pawn is passed (no opposing pawns in front of it)
        
        arguments to be passed in: board: the board to evaluate, rank: rank of the pawn, 
        file: file of the pawn, color: color of the pawn (0 for white, 1 for black)
        returns: true if passed pawn, false otherwise
        """
        if color == 0:  # white pawn
            # check if there are any black pawns in front of this pawn
            for r in range(rank - 1, -1, -1):  # look upward (decreasing rank)
                for f in range(max(0, file - 1), min(8, file + 2)):  # check file and adjacent files
                    if board.get_piece_at(r, f) == 'p':  # black pawn
                        return False
        else:  # black pawn
            # check if there are any white pawns in front of this pawn
            for r in range(rank + 1, 8):  # look downward (increasing rank)
                for f in range(max(0, file - 1), min(8, file + 2)):  # check file and adjacent files
                    if board.get_piece_at(r, f) == 'P':  # white pawn
                        return False
        
        return True
    
    def _is_isolated_pawn(self, board, rank, file, color) -> bool:
        """
        check if a pawn is isolated (no friendly pawns on adjacent files)
        
        arguments to be passed in: board: the board to evaluate, rank: rank of the pawn, 
        file: file of the pawn, color: color of the pawn (0 for white, 1 for black)
        returns: true if isolated pawn, false otherwise
        """
        pawn_char = 'P' if color == 0 else 'p'
        
        # Check left file
        if file > 0:
            for r in range(8):
                if board.get_piece_at(r, file - 1) == pawn_char:
                    return False
        
        # Check right file (no duh)
        if file < 7:
            for r in range(8):
                if board.get_piece_at(r, file + 1) == pawn_char:
                    return False
        
        return True