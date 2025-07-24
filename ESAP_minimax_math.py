from typing import Dict, List, Tuple, Optional, Any
import random
import time
from dataclasses import dataclass

CHECKMATE_VALUE = 100000
STALEMATE_VALUE = 0
SEARCH_DEPTH = 0 # Very important value! Makes the bot stronger or weaker
# Depth of 4-5 recommended for strongest results, depth of 2-3 recommended for fast (still good) games
best_move_found = None # By increasing or decreasing how far it sees ahead
positions_evaluated = 0

@dataclass # This will appear throughout this code base. I saw this once in a python tutorial and I thought it looked cool, so it is here now
class PositionalValues:
    """Stores positional values for different chess pieces on the board"""
    # Base material values for each piece type
    material_values: Dict[str, int] = None
    
    # Positional bonus tables
    knight_table: List[List[int]] = None
    bishop_table: List[List[int]] = None
    queen_table: List[List[int]] = None
    rook_table: List[List[int]] = None
    white_pawn_table: List[List[int]] = None # differentiate because of promotion logic
    black_pawn_table: List[List[int]] = None # so a black pawn and white pawn need to handle differently
    
    def __post_init__(self):
        if self.material_values is None:
            self.material_values = {
                "K": 0,    # king's value is infinite! (handled separately)
                "Q": 90,   # queen
                "R": 50,   # rook
                "B": 35,   # bhop
                "N": 30,   # k night
                "p": 10    # pawn
            }
        

        # the following just enourages having good piece activity (num points linked with the square on the board)

        # knight positional values (knights are better in the center and worse at the edges)
        # pro tip: a knight on the rim, is dim -- is a good rule of thumb
        if self.knight_table is None:
            self.knight_table = [
                [1, 1, 1, 1, 1, 1, 1, 1],
                [1, 2, 2, 2, 2, 2, 2, 1],
                [1, 2, 3, 3, 3, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 3, 3, 3, 2, 1],
                [1, 2, 2, 2, 2, 2, 2, 1],
                [1, 1, 1, 1, 1, 1, 1, 1]
            ]
        
        # bishop positional values (bhops are better on diags)
        if self.bishop_table is None:
            self.bishop_table = [
                [4, 3, 2, 1, 1, 2, 3, 4],
                [3, 4, 3, 2, 2, 3, 4, 3],
                [2, 3, 4, 3, 3, 4, 3, 2],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [2, 3, 4, 3, 3, 4, 3, 2],
                [3, 4, 3, 2, 2, 3, 4, 3],
                [4, 3, 2, 1, 1, 2, 3, 4]
            ]
        
        # queen positional values
        if self.queen_table is None:
            self.queen_table = [
                [1, 1, 1, 3, 1, 1, 1, 1],
                [1, 2, 3, 3, 3, 1, 1, 1],
                [1, 4, 3, 3, 3, 4, 2, 1],
                [1, 2, 3, 3, 3, 2, 2, 1],
                [1, 2, 3, 3, 3, 2, 2, 1],
                [1, 4, 3, 3, 3, 4, 2, 1],
                [1, 2, 3, 3, 3, 1, 1, 1],
                [1, 1, 1, 3, 1, 1, 1, 1]
            ]
        
        # rook positional values - rooks are better on open files and 7th/8th ranks
        # there's even a whole puzzle catagory on chesscom called 'rooks on the 7th'
        if self.rook_table is None:
            self.rook_table = [
                [4, 3, 4, 4, 4, 4, 3, 4],
                [4, 4, 4, 4, 4, 4, 4, 4],
                [1, 1, 2, 3, 3, 2, 1, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 1, 2, 3, 3, 2, 1, 1],
                [4, 4, 4, 4, 4, 4, 4, 4],
                [4, 3, 4, 4, 4, 4, 3, 4]
            ]
        
        # white pawn positional values - pawns are better when advanced
        if self.white_pawn_table is None:
            self.white_pawn_table = [
                [8, 8, 8, 8, 8, 8, 8, 8],  # Promotion rank
                [8, 8, 8, 8, 8, 8, 8, 8],
                [5, 6, 6, 7, 7, 6, 6, 5],
                [2, 3, 3, 5, 5, 3, 3, 2],
                [1, 2, 3, 4, 4, 2, 2, 1], #lower for F file cuz its bad to push F pawn
                [1, 2, 3, 3, 3, 2, 2, 1],
                [1, 1, 1, 0, 0, 1, 1, 1],  # Starting rank
                [0, 0, 0, 0, 0, 0, 0, 0]
            ]
        
        # black pawn positional values - mirror of white pawn values
        if self.black_pawn_table is None:
            self.black_pawn_table = [
                [0, 0, 0, 0, 0, 0, 0, 0],
                [1, 1, 1, 0, 0, 1, 1, 1],
                [1, 2, 3, 3, 3, 2, 2, 1], #same f file logic as white
                [1, 2, 3, 4, 4, 2, 2, 1],
                [2, 3, 3, 5, 5, 3, 3, 2],
                [5, 6, 6, 7, 7, 6, 6, 5],
                [8, 8, 8, 8, 8, 8, 8, 8],
                [8, 8, 8, 8, 8, 8, 8, 8]
            ]

# initialize the positional values (what we just described above)
position_values = PositionalValues()

# create a mapping for piece type to position table
position_tables = {
    'N': position_values.knight_table,
    'B': position_values.bishop_table,
    'Q': position_values.queen_table,
    'R': position_values.rook_table,
    "wp": position_values.white_pawn_table,
    "bp": position_values.black_pawn_table
}

# All of the methods should be commented just like this one below
# This is the capstone so I figured it should look professional

def select_random_move(valid_moves: List[Any]) -> Optional[Any]:
    """Select a random move from the list of valid moves.
    
    Args:
        valid_moves: List of valid moves to choose from
        
    Returns:
        A randomly selected move or None if no valid moves
    """
    if not valid_moves:
        return None
    return random.choice(valid_moves)


def find_best_move(game_state: Any, valid_moves: List[Any]) -> Any:
    """Find the best move using minimax algorithm with alpha-beta pruning.
    
    Args:
        game_state: Current state of the chess game
        valid_moves: List of valid moves to evaluate
        
    Returns:
        The best move found by the minimax algorithm
    """
    global best_move_found, positions_evaluated
    
    # Reset global variables
    best_move_found = None
    positions_evaluated = 0
    
    # Initialize alpha-beta bounds so that they are the most neutral and ready to be revaluated after starting position
    alpha = -CHECKMATE_VALUE
    beta = CHECKMATE_VALUE
    
    # Start timing for the data section
    start_time = time.time()
    
    # Run minimax search
    minimax_search(game_state, valid_moves, SEARCH_DEPTH, alpha, beta, game_state.white_to_move)
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    # Debug statistics (commented out for cleaner output)
    # print(f"elapsed_time:{elapsed_time}[sec]")
    # print(positions_evaluated)
    #Not necessary but you can us e this if you want to (imo my output is cleaner)
    
    return best_move_found

# For more about minimax refer to our write-up

def minimax_search(game_state: Any, valid_moves: List[Any], depth: int, alpha: int, beta: int, is_white_turn: bool) -> int:
    """Recursive minimax search with alpha-beta pruning.
    
    Args:
        game_state: Current state of the chess game
        valid_moves: List of valid moves to evaluate
        depth: Current search depth
        alpha: Alpha value for pruning
        beta: Beta value for pruning
        is_white_turn: True if it's white's turn, False otherwise
        
    Returns:
        The evaluation score of the best move
    """
    global best_move_found, positions_evaluated
    positions_evaluated += 1
    
    # Base case: reached leaf node or terminal state (last one in the tree)
    if depth == 0 or game_state.checkmate or game_state.stalemate:
        return evaluate_position(game_state)
    
    # Randomize move order for better pruning
    random.shuffle(valid_moves)
    
    if is_white_turn:
        # maximizing player (white)
        best_score = -CHECKMATE_VALUE
        
        for move in valid_moves:
            # make the move
            game_state.make_move(move)
            next_moves = game_state.get_valid_moves()
            
            # recursive evaluation
            score = minimax_search(game_state, next_moves, depth - 1, alpha, beta, False)
            
            # undo the move
            game_state.undo_move()
            
            # update best score and move
            if score > best_score:
                best_score = score
                if depth == SEARCH_DEPTH:
                    best_move_found = move
            
            # alpha-beta pruning
            alpha = max(alpha, score)
            if beta <= alpha:
                break
                
        return best_score
    else:
        # minimizing player (black)
        best_score = CHECKMATE_VALUE
        
        for move in valid_moves:
            # make the move
            game_state.make_move(move)
            next_moves = game_state.get_valid_moves()
            
            # recursive evaluation!! this is the project requirement right here !!
            score = minimax_search(game_state, next_moves, depth - 1, alpha, beta, True)
            
            game_state.undo_move()
            
            # update best score and move
            if score < best_score:
                best_score = score
                if depth == SEARCH_DEPTH:
                    best_move_found = move
            
            # alpha-beta pruning 
            # we 'prune' away obviously bad lines that are so bad they arent
            # worth checking, saving us time and resources and optimizing the bot :nerd:
            beta = min(beta, score)
            if beta <= alpha:
                break
                
        return best_score


def evaluate_position(game_state: Any) -> int:
    """Evaluate the current board position.
    
    Args:
        game_state: current state of the chess game
        
    Returns:
        numerical evaluation of the position (positive favors white, negative favors black)
    """
    # check for checkmate or stalemate
    if game_state.checkmate:
        if game_state.white_to_move:
            return -CHECKMATE_VALUE  #  black wins
        else:
            return CHECKMATE_VALUE   # w hite wins
    elif game_state.stalemate:
        return STALEMATE_VALUE
    
    # material and positional evaluation
    total_score = 0
    
    # iterate through the board (no duh)
    for row in range(8):
        for col in range(8):
            square = game_state.board[row][col]
            
            # skip empty squares
            if square == "--":
                continue
                
            # calculate positional bonus
            positional_bonus = 0
            piece_type = square[1]
            color = square[0]
            
            # skip kings for positional evaluation cuz theyre always there
            if piece_type != "K":
                # handle pawns specially cuz they have different tables
                if piece_type == "p":
                    positional_bonus = position_tables[square][row][col]
                else:
                    positional_bonus = position_tables[piece_type][row][col]
            
            # add material and positioning value based on piece color
            if color == 'w':
                total_score += position_values.material_values[piece_type] + positional_bonus
            elif color == 'b':
                total_score -= position_values.material_values[piece_type] + positional_bonus
    
    return total_score

def findRandomMove(valid_moves):
    return select_random_move(valid_moves)

def findBestMoveMinimax(game_state, valid_moves):
    return find_best_move(game_state, valid_moves)

def findMoveMinimax(game_state, valid_moves, depth, alpha, beta, white_to_move):
    return minimax_search(game_state, valid_moves, depth, alpha, beta, white_to_move)

def scoreBoard(game_state):
    return evaluate_position(game_state)

# init global variables for compatibility
nextMove = None
nodes = 0