import pygame
import time
import sys
import os
from Esap_Board import Board
# from chess_gui import ChessGUI
from esap_piece import *
from chess_utils import blocked_from, get_blocked_directions
from chess_check_utils import is_in_check, filter_moves_for_check, is_square_attacked
from python_engine import Engine, Color
from python_evaluator import Evaluator
import copy


WIDTH, HEIGHT = 640, 640  # window size
ROWS, COLS = 8, 8

# Game state variables
game_active = True  # Whether the game is ongoing or ended
game_result = None  # None, 'checkmate_white_wins', 'checkmate_black_wins', 'stalemate', 'fifty_move_rule'
move_counter = 0    # Counter for the 50-move rule
last_capture_or_pawn_move = 0  # Last move where a capture was made or a pawn was moved

# Colors
WHITE = (232, 235, 239)
BLUE = (125, 135, 150)
GREEN = (100, 200, 100)  # For highlighting legal moves
RED = (200, 100, 100)    # For check indicator
GOLD = (212, 175, 55)    # For promotion selection

# pieces
kingBlack = Piece(pygame.image.load("pieces/black-king.png"), 0, 4, "k")
kingWhite = Piece(pygame.image.load("pieces/white-king.png"), 7, 4, "K")

bishopBlack = Piece(pygame.image.load("pieces/black-bishop.png"), 1, 2, "b")
bishopWhite = Piece(pygame.image.load("pieces/white-bishop.png"), 6, 5, "B")

pawnBlack = Piece(pygame.image.load("pieces/black-pawn.png"), 1, 6, "p")
pawnWhite = Piece(pygame.image.load("pieces/white-pawn.png"), 6, 1, "P")

rookBlack = Piece(pygame.image.load("pieces/black-rook.png"), 0, 0, "r")
rookWhite = Piece(pygame.image.load("pieces/white-rook.png"), 7, 7, "R")

# list of pieces we're using
pieces = [kingBlack, kingWhite, bishopBlack, bishopWhite, pawnBlack, pawnWhite, rookBlack, rookWhite]

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess Board")
clock = pygame.time.Clock()

# board function draw
def draw_board():
    screen.fill(WHITE)
    for row in range(ROWS):
        for col in range(COLS):
            color = BLUE if (row + col) % 2 else WHITE
            pygame.draw.rect(screen, color, (col * 80, row * 80, 80, 80))

def draw_pieces():
    for piece in pieces:
        piece.draw(screen)

# Variables to store the selected piece and its valid moves
selected_piece = None
valid_moves = []

# Variables to track check status
# Define UI colors with transparency
check_indicator_color = (255, 0, 0, 128)  # Red with 50% transparency
promotion_bg_color = (0, 0, 0, 180)       # Dark background for promotion selection

# Define promotion pieces and their images
promotion_pieces = {
    'white': {
        'Q': pygame.image.load("pieces/white-queen.png"),
        'R': pygame.image.load("pieces/white-rook.png"),
        'B': pygame.image.load("pieces/white-bishop.png"),
        'N': pygame.image.load("pieces/white-knight.png")
    },
    'black': {
        'q': pygame.image.load("pieces/black-queen.png"),
        'r': pygame.image.load("pieces/black-rook.png"),
        'b': pygame.image.load("pieces/black-bishop.png"),
        'n': pygame.image.load("pieces/black-knight.png")
    }
}

# Game state control
waiting_for_promotion = False
promotion_pawn = None
promotion_square = None

# Initialize chess engine for black moves
engine = Engine(max_depth=3)  # Adjust depth as needed for performance vs strength

# Function to convert our board representation to the format expected by the engine
def convert_board_for_engine():
    # Create a board object that the engine can understand
    class EngineBoard:
        def __init__(self):
            self.board = [[None for _ in range(8)] for _ in range(8)]
            # Map our pieces to the board
            for piece in pieces:
                self.board[piece.row][piece.col] = piece.name
        
        def get_side_to_move(self):
            return Color.BLACK  # We want the engine to move as Black
        
        def generate_legal_moves(self):
            # This generates ONLY legal moves for the current position
            # A move is legal if it:
            # 1. Follows the piece's movement rules
            # 2. Doesn't capture own pieces
            # 3. Doesn't leave the king in check
            # 4. For king moves, doesn't move into check
            moves = []
            
            # Check if black king is in check
            black_in_check = is_in_check('black', pieces)
            
            # Debug check status
            if black_in_check:
                print("DEBUG: Black king is in check!")
            
            # Define our Move class inside the function
            class Move:
                def __init__(self, from_pos, to_pos):
                    self.from_row, self.from_col = from_pos
                    self.to_row, self.to_col = to_pos
                    
                def to_algebraic(self):
                    # Convert to algebraic notation like 'e2e4'
                    files = 'abcdefgh'
                    return f"{files[self.from_col]}{8-self.from_row}{files[self.to_col]}{8-self.to_row}"
            
            # Get black king position for checking
            black_king_pos = None
            for p in pieces:
                if p.name == 'k':  # Lowercase k is black king
                    black_king_pos = (p.row, p.col)
                    break
                    
            if black_king_pos is None:
                print("WARNING: Could not find black king on board!")
                return []  # Cannot generate moves without knowing king position
            
            # Process each black piece
            for piece in pieces:
                if piece.name.islower():  # Black pieces are lowercase
                    # Step 1: Get raw candidate moves based on piece type
                    candidate_moves = []
                    
                    # For sliding pieces (bishops, rooks, queens)
                    if piece.name.lower() in ['b', 'r', 'q']:
                        directions = []
                        if piece.name.lower() in ['b', 'q']:  # Bishop or Queen
                            directions.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])  # Diagonals
                        if piece.name.lower() in ['r', 'q']:  # Rook or Queen
                            directions.extend([(-1, 0), (1, 0), (0, -1), (0, 1)])  # Horizontals and verticals
                        
                        # Check each direction
                        for dr, dc in directions:
                            for i in range(1, 8):  # Maximum of 7 squares in any direction
                                new_row = piece.row + dr * i
                                new_col = piece.col + dc * i
                                
                                # Check if position is on the board
                                if not (0 <= new_row < 8 and 0 <= new_col < 8):
                                    break  # Off the board, stop in this direction
                                
                                # Check if there's a piece at this position
                                piece_at_pos = None
                                for other_piece in pieces:
                                    if other_piece.row == new_row and other_piece.col == new_col:
                                        piece_at_pos = other_piece
                                        break
                                
                                if piece_at_pos:
                                    # Can't move through pieces
                                    if piece_at_pos.name.islower():  # Own piece
                                        break  # Can't capture own piece, stop in this direction
                                    else:  # Enemy piece
                                        candidate_moves.append((new_row, new_col))  # Can capture
                                        break  # But can't move through it
                                else:
                                    # Empty square
                                    candidate_moves.append((new_row, new_col))
                    
                    # For non-sliding pieces (pawns, knights, king)
                    else:
                        raw_moves = piece.get_pos_moves()
                        
                        # Filter moves for board boundaries and own pieces
                        for move_row, move_col in raw_moves:
                            # Check if position is on the board
                            if not (0 <= move_row < 8 and 0 <= move_col < 8):
                                continue
                            
                            # Check if there's a piece at this position
                            piece_at_pos = None
                            for other_piece in pieces:
                                if other_piece.row == move_row and other_piece.col == move_col:
                                    piece_at_pos = other_piece
                                    break
                            
                            # Can't capture own pieces
                            if piece_at_pos and piece_at_pos.name.islower():
                                continue
                            
                            # Valid candidate move
                            candidate_moves.append((move_row, move_col))
                    
                    # Step 2: Filter candidates for king safety
                    # For each candidate move, check if making it would leave/put the king in check
                    legal_moves = []
                    for move_to in candidate_moves:
                        move_row, move_col = move_to
                        
                        # If this is a king move, check if destination is under attack
                        if piece.name.lower() == 'k':
                            if is_square_attacked(move_row, move_col, 'white', pieces):  # WHITE pieces attack black king
                                continue  # Skip this move, king would move into check
                        
                        # For any piece: simulate the move and see if it leaves king in check
                        original_row, original_col = piece.row, piece.col
                        
                        # Find piece to capture if any
                        piece_to_capture = None
                        for other_piece in pieces:
                            if other_piece.row == move_row and other_piece.col == move_col:
                                piece_to_capture = other_piece
                                break
                        
                        # Temporarily make the move
                        if piece_to_capture:
                            pieces.remove(piece_to_capture)
                        piece.row, piece.col = move_row, move_col
                        
                        # If this is a king move, update our tracking of king position
                        if piece.name.lower() == 'k':
                            # Update king position for the check
                            check_king_pos = (move_row, move_col)
                        else:
                            check_king_pos = black_king_pos
                        
                        # Check if the king is in check after this move
                        king_in_check = False
                        if check_king_pos:  # We found the king
                            king_row, king_col = check_king_pos
                            king_in_check = is_square_attacked(king_row, king_col, 'white', pieces)  # WHITE pieces attack black king
                        
                        # Restore board state
                        piece.row, piece.col = original_row, original_col
                        if piece_to_capture:
                            pieces.append(piece_to_capture)
                        
                        # Only add move if it doesn't leave king in check
                        if not king_in_check:
                            legal_moves.append(move_to)
                    
                    # Step 3: Create Move objects for each legal move
                    for move_row, move_col in legal_moves:
                        move = Move((piece.row, piece.col), (move_row, move_col))
                        moves.append(move)
            
            return moves
        
        def copy(self):
            # Create a copy of the board for move testing
            new_board = EngineBoard()
            new_board.board = [row[:] for row in self.board]
            return new_board
        
        def make_move(self, move):
            # Update the board with the move
            from_row, from_col = move.from_row, move.from_col
            to_row, to_col = move.to_row, move.to_col
            
            # Move the piece on the board
            self.board[to_row][to_col] = self.board[from_row][from_col]
            self.board[from_row][from_col] = None
        
        def is_in_check(self):
            # Simplified check detection
            return False
        
        def get_pieces(self):
            # Return a dictionary of pieces by type
            result = {}
            for row in range(8):
                for col in range(8):
                    piece = self.board[row][col]
                    if piece:
                        if piece not in result:
                            result[piece] = []
                        result[piece].append((row, col))
            return result
        
        def get_king_position(self, color):
            # Find king position
            king_char = 'k' if color == Color.BLACK else 'K'
            for row in range(8):
                for col in range(8):
                    if self.board[row][col] == king_char:
                        return (row, col)
            return None
        
        def get_piece_positions(self, piece_type):
            # Get all positions of a specific piece type
            positions = []
            for row in range(8):
                for col in range(8):
                    if self.board[row][col] == piece_type:
                        positions.append((row, col))
            return positions
        
        def get_piece_at(self, row, col):
            # Get piece at a specific position
            if 0 <= row < 8 and 0 <= col < 8:
                return self.board[row][col]
            return None
    
    # Create and return the board object
    return EngineBoard()

# Function to handle pawn promotion
def handle_promotion(pawn, row, col, color='white'):
    global waiting_for_promotion, promotion_pawn, promotion_square
    
    # Set up the promotion state
    waiting_for_promotion = True
    promotion_pawn = pawn
    promotion_square = (row, col)
    
    # If black, automatically promote to queen (AI always chooses queen)
    if color == 'black':
        promote_pawn('q')  # Lowercase q for black queen
        return True
    
    # For white (human player), we'll handle the selection in the main loop
    return False

# Function to complete the promotion
def promote_pawn(piece_type):
    global waiting_for_promotion, promotion_pawn, promotion_square, pieces, move_counter, last_capture_or_pawn_move
    
    if promotion_pawn and promotion_square:
        row, col = promotion_square
        
        # Remove the pawn from the pieces list
        pieces.remove(promotion_pawn)
        
        # Create the new piece based on promotion type
        if piece_type.lower() == 'q':
            # Queen
            piece_image = promotion_pieces['white']['Q'] if piece_type.isupper() else promotion_pieces['black']['q']
            new_piece = Piece(piece_image, row, col, piece_type)
        elif piece_type.lower() == 'r':
            # Rook
            piece_image = promotion_pieces['white']['R'] if piece_type.isupper() else promotion_pieces['black']['r']
            new_piece = Piece(piece_image, row, col, piece_type)
        elif piece_type.lower() == 'b':
            # Bishop
            piece_image = promotion_pieces['white']['B'] if piece_type.isupper() else promotion_pieces['black']['b']
            new_piece = Piece(piece_image, row, col, piece_type)
        elif piece_type.lower() == 'n':
            # Knight
            piece_image = promotion_pieces['white']['N'] if piece_type.isupper() else promotion_pieces['black']['n']
            new_piece = Piece(piece_image, row, col, piece_type)
        
        # Add the new piece to the pieces list
        pieces.append(new_piece)
        
        # Reset promotion state
        waiting_for_promotion = False
        promotion_pawn = None
        promotion_square = None
        
        # Reset 50-move counter since pawn moved
        last_capture_or_pawn_move = move_counter
        
        print(f"Pawn promoted to {piece_type}")
        return True
    
    return False

# Function to check for checkmate or stalemate
def check_game_end():
    global game_active, game_result
    
    # Check if black has any legal moves
    black_engine_board = convert_board_for_engine()
    black_legal_moves = black_engine_board.generate_legal_moves()
    
    # Check if white has any legal moves
    # We need to simulate this since we don't have a direct move generator for white
    white_has_moves = False
    for piece in pieces:
        if piece.name.isupper():  # White piece
            # Generate possible moves based on piece type
            possible_moves = []
            if piece.name.lower() in ['b', 'r', 'q']:
                # For sliding pieces
                directions = []
                if piece.name.lower() in ['b', 'q']:  # Bishop or Queen
                    directions.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])  # Diagonals
                if piece.name.lower() in ['r', 'q']:  # Rook or Queen
                    directions.extend([(-1, 0), (1, 0), (0, -1), (0, 1)])  # Horizontals and verticals
                
                for dr, dc in directions:
                    for i in range(1, 8):
                        new_row = piece.row + dr * i
                        new_col = piece.col + dc * i
                        
                        if not (0 <= new_row < 8 and 0 <= new_col < 8):
                            break  # Off the board
                        
                        # Check if there's a piece at this position
                        piece_at_pos = None
                        for other_piece in pieces:
                            if other_piece.row == new_row and other_piece.col == new_col:
                                piece_at_pos = other_piece
                                break
                        
                        if piece_at_pos:
                            # Can't move through pieces
                            if piece_at_pos.name.isupper():  # Own piece
                                break
                            else:  # Enemy piece
                                possible_moves.append((new_row, new_col))
                                break
                        else:
                            possible_moves.append((new_row, new_col))
            else:
                # For non-sliding pieces
                possible_moves = piece.get_pos_moves()
            
            # For each possible move, check if it would leave the king in check
            for move_row, move_col in possible_moves:
                # Simulate the move
                original_row, original_col = piece.row, piece.col
                
                # Find piece to capture if any
                piece_to_capture = None
                for other_piece in pieces:
                    if other_piece.row == move_row and other_piece.col == move_col:
                        piece_to_capture = other_piece
                        break
                
                # Make the move temporarily
                if piece_to_capture:
                    pieces.remove(piece_to_capture)
                piece.row, piece.col = move_row, move_col
                
                # Check if white king is in check after this move
                white_in_check = is_in_check('white', pieces)
                
                # Restore board state
                piece.row, piece.col = original_row, original_col
                if piece_to_capture:
                    pieces.append(piece_to_capture)
                
                # If this move doesn't leave the king in check, white has a legal move
                if not white_in_check:
                    white_has_moves = True
                    break
            
            if white_has_moves:
                break
    
    # Check for checkmate or stalemate
    white_in_check = is_in_check('white', pieces)
    black_in_check = is_in_check('black', pieces)
    
    if not white_has_moves and white_in_check:
        # White has no legal moves and is in check = checkmate, black wins
        game_active = False
        game_result = 'checkmate_black_wins'
        print("Checkmate! Black wins.")
        return True
    elif not white_has_moves and not white_in_check:
        # White has no legal moves but is not in check = stalemate
        game_active = False
        game_result = 'stalemate'
        print("Stalemate! Game is a draw.")
        return True
    
    if not black_legal_moves and black_in_check:
        # Black has no legal moves and is in check = checkmate, white wins
        game_active = False
        game_result = 'checkmate_white_wins'
        print("Checkmate! White wins.")
        return True
    elif not black_legal_moves and not black_in_check:
        # Black has no legal moves but is not in check = stalemate
        game_active = False
        game_result = 'stalemate'
        print("Stalemate! Game is a draw.")
        return True
    
    return False

# Function to make black move using the engine
def make_black_move():
    global move_counter, last_capture_or_pawn_move, game_active, game_result
    
    # Don't make moves if the game is over
    if not game_active:
        return
    
    # Increment move counter
    move_counter += 1
    
    # Check 50-move rule
    if move_counter - last_capture_or_pawn_move >= 100:  # 50 full moves = 100 half-moves
        game_active = False
        game_result = 'fifty_move_rule'
        print("Draw by 50-move rule.")
        return
    
    # Convert our board representation to the format expected by the engine
    engine_board = convert_board_for_engine()
    
    # Get the best move from the engine
    best_move = engine.get_best_move(engine_board)
    
    if best_move:
        # Find the piece to move
        moving_piece = None
        for piece in pieces:
            if piece.row == best_move.from_row and piece.col == best_move.from_col:
                moving_piece = piece
                break
        
        if moving_piece:
            print(f"Black moving {moving_piece.name} from ({moving_piece.row}, {moving_piece.col}) to ({best_move.to_row}, {best_move.to_col})")
            
            # Check if there's a piece to capture
            piece_to_capture = None
            for other_piece in pieces:
                if other_piece.row == best_move.to_row and other_piece.col == best_move.to_col:
                    piece_to_capture = other_piece
                    break
            
            # Make the move
            if piece_to_capture:
                pieces.remove(piece_to_capture)  # Remove the captured piece
                print(f"Black captured {piece_to_capture.name} at ({best_move.to_row}, {best_move.to_col})")
                # Reset 50-move counter on capture
                last_capture_or_pawn_move = move_counter
            
            # Check if this is a pawn move
            is_pawn_move = moving_piece.name.lower() == 'p'
            if is_pawn_move:
                # Reset 50-move counter on pawn move
                last_capture_or_pawn_move = move_counter
            
            # Execute the move
            moving_piece.move(best_move.to_row, best_move.to_col)
            
            # Check for pawn promotion
            if moving_piece.name.lower() == 'p' and moving_piece.row == 7:  # Black pawn reaches the bottom rank
                handle_promotion(moving_piece, moving_piece.row, moving_piece.col, 'black')
            
            # Check for checkmate or stalemate after move
            check_game_end()
    else:
        # This should only happen if there are no legal moves - checkmate or stalemate
        check_game_end()

# Function to draw the game end message
def draw_game_end_message():
    if not game_active and game_result:
        # Create a semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Black with 70% transparency
        screen.blit(overlay, (0, 0))
        
        # Prepare the message
        if game_result == 'checkmate_white_wins':
            message = "Checkmate! White wins!"
        elif game_result == 'checkmate_black_wins':
            message = "Checkmate! Black wins!"
        elif game_result == 'stalemate':
            message = "Stalemate! Game is a draw."
        elif game_result == 'fifty_move_rule':
            message = "Draw by 50-move rule."
        else:
            message = "Game Over"
        
        # Render the message
        font = pygame.font.SysFont('Arial', 36, bold=True)
        text = font.render(message, True, (255, 255, 255))  # White text
        text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
        screen.blit(text, text_rect)
        
        # Add a restart hint
        hint = "Press 'R' to restart game"
        hint_font = pygame.font.SysFont('Arial', 24)
        hint_text = hint_font.render(hint, True, (200, 200, 200))  # Light gray text
        hint_rect = hint_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
        screen.blit(hint_text, hint_rect)

# Function to draw the promotion UI
def draw_promotion_ui():
    if waiting_for_promotion and promotion_square:
        row, col = promotion_square
        
        # Create a semi-transparent overlay for the whole board
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))  # Black with 50% transparency
        screen.blit(overlay, (0, 0))
        
        # Draw the promotion selection box
        box_width = 320  # 4 pieces * 80px
        box_height = 80
        box_x = (WIDTH - box_width) // 2
        box_y = HEIGHT // 2 - 40
        
        # Draw the box background
        pygame.draw.rect(screen, (50, 50, 50), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(screen, GOLD, (box_x, box_y, box_width, box_height), 3)
        
        # Draw the promotion options
        piece_options = promotion_pieces['white']
        for i, (piece_type, img) in enumerate(piece_options.items()):
            screen.blit(img, (box_x + i*80 + 10, box_y + 10))
        
        # Add a prompt message
        font = pygame.font.SysFont('Arial', 24)
        text = font.render("Choose a piece for promotion", True, (255, 255, 255))
        text_rect = text.get_rect(center=(WIDTH//2, box_y - 20))
        screen.blit(text, text_rect)

# Function to restart the game
def restart_game():
    global pieces, selected_piece, valid_moves, game_active, game_result, move_counter, last_capture_or_pawn_move
    
    # Reset pieces to starting positions
    pieces = [
        Piece(pygame.image.load("pieces/black-king.png"), 0, 4, "k"),
        Piece(pygame.image.load("pieces/white-king.png"), 7, 4, "K"),
        Piece(pygame.image.load("pieces/black-bishop.png"), 1, 2, "b"),
        Piece(pygame.image.load("pieces/white-bishop.png"), 6, 5, "B"),
        Piece(pygame.image.load("pieces/black-pawn.png"), 1, 6, "p"),
        Piece(pygame.image.load("pieces/white-pawn.png"), 6, 1, "P"),
        Piece(pygame.image.load("pieces/black-rook.png"), 0, 0, "r"),
        Piece(pygame.image.load("pieces/white-rook.png"), 7, 7, "R")
    ]
    
    # Reset game state variables
    selected_piece = None
    valid_moves = []
    game_active = True
    game_result = None
    move_counter = 0
    last_capture_or_pawn_move = 0
    
    print("Game restarted")

running = True
while running:
    clock.tick(60)  # 60 FPS
    draw_board()
    draw_pieces()
    
    # Check if white king is in check
    in_check = is_in_check('white', pieces)
    
    # If in check, highlight the king
    if in_check and game_active:
        # Find the white king
        for piece in pieces:
            if piece.name == 'K':  # White king
                # Create a transparent surface for the check indicator
                check_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
                pygame.draw.rect(check_surf, check_indicator_color, (0, 0, 80, 80), 4)  # Red border
                screen.blit(check_surf, (piece.col * 80, piece.row * 80))
                break
    
    # Draw move indicators for the selected piece (only if game is active and not in promotion selection)
    if selected_piece and valid_moves and game_active and not waiting_for_promotion:
        for row, col in valid_moves:
            # Check if there's a piece to capture at this position
            capture_move = False
            for other_piece in pieces:
                if other_piece.row == row and other_piece.col == col:
                    capture_move = True
                    break
            
            # Create a transparent surface
            circle_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
            
            if capture_move:
                # For capture moves, draw a thicker circle around the piece
                pygame.draw.circle(circle_surf, (255, 0, 0, 150), (80 // 2, 80 // 2), 80 // 2 - 5, 4)  # Thicker border circle
            else:
                # For regular moves, draw a filled circle
                pygame.draw.circle(circle_surf, (255, 0, 0, 100), (80 // 2, 80 // 2), 80 // 3)
                
            screen.blit(circle_surf, (col * 80, row * 80))
    
    # Draw promotion UI if waiting for promotion
    if waiting_for_promotion:
        draw_promotion_ui()
    
    # Draw game end message if game is over
    if not game_active:
        draw_game_end_message()
        
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        # Handle key presses
        elif event.type == pygame.KEYDOWN:
            # Restart game on 'R' key press
            if event.key == pygame.K_r and not game_active:
                restart_game()
                
        # if the mouse is clicked
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Handle promotion piece selection
            if waiting_for_promotion:
                # Get the position of the mouse click
                mouse_x, mouse_y = pygame.mouse.get_pos()
                
                # Check if click is in the promotion UI area
                box_width = 320  # 4 pieces * 80px
                box_height = 80
                box_x = (WIDTH - box_width) // 2
                box_y = HEIGHT // 2 - 40
                
                if box_x <= mouse_x < box_x + box_width and box_y <= mouse_y < box_y + box_height:
                    # Determine which piece was selected
                    piece_index = (mouse_x - box_x) // 80
                    piece_types = list(promotion_pieces['white'].keys())
                    if 0 <= piece_index < len(piece_types):
                        selected_type = piece_types[piece_index]
                        promote_pawn(selected_type)  # Uppercase for white
                        
                        # Check for checkmate/stalemate after promotion
                        check_game_end()
                        
                        # Black's turn after promotion is complete
                        if game_active:  # Only make black move if game is still active
                            make_black_move()
                continue  # Skip other click handling during promotion
            
            # Don't process board clicks if game is over
            if not game_active:
                continue
                
            mouse_pos = pygame.mouse.get_pos()
            
            # Convert mouse position to board coordinates
            clicked_row = mouse_pos[1] // 80
            clicked_col = mouse_pos[0] // 80
            
            # check if clicked on a piece
            clicked_on_piece = False
            clicked_piece = None
            for piece in pieces:
                if piece.row == clicked_row and piece.col == clicked_col:
                    clicked_on_piece = True
                    clicked_piece = piece
                    break
                    
            # if selected piece + clicked on an enemy piece that's in valid moves
            # capture it instead of selecting it
            if selected_piece and clicked_on_piece and clicked_piece.name.islower() and (clicked_row, clicked_col) in valid_moves:
                # Capture the enemy piece
                print(f"White captured {clicked_piece.name} at ({clicked_row}, {clicked_col})")
                pieces.remove(clicked_piece)
                
                # Reset 50-move counter on capture
                last_capture_or_pawn_move = move_counter
                
                # Track if this is a pawn move for 50-move rule
                is_pawn_move = selected_piece.name.lower() == 'p'
                if is_pawn_move:
                    # Reset 50-move counter on pawn move
                    last_capture_or_pawn_move = move_counter
                
                # Increment move counter for white's move
                move_counter += 1
                
                # Move our piece to the captured piece's position
                selected_piece.move(clicked_row, clicked_col)
                
                # Check for pawn promotion
                if is_pawn_move and clicked_row == 0:  # White pawn reaches top rank
                    handle_promotion(selected_piece, clicked_row, clicked_col, 'white')
                else:
                    # Clear selection after moving
                    selected_piece = None
                    valid_moves = []
                    
                    # Check for checkmate or stalemate
                    if not check_game_end() and game_active:
                        # Add a small delay to ensure UI updates before black moves
                        pygame.time.delay(100)
                        # Make black's move if game isn't over
                        make_black_move()
            # otherwise handle piece selection normally
            elif clicked_on_piece:
                # Only allow selecting white pieces (uppercase)
                if clicked_piece.name.isupper():
                    # if you click on the already selected piece, deselect it
                    if selected_piece == clicked_piece:
                        selected_piece = None
                        valid_moves = []
                    # if u click on a different piece of ur color select it instead
                    else:
                        selected_piece = clicked_piece
                        # Calculate valid moves for the selected piece
                        if selected_piece.name.lower() in ['b', 'r', 'q']:
                            valid_moves = []
                            
                            # define directions based on piece type
                            if selected_piece.name.lower() == 'b':
                                directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]  # Diagonals for bishop
                            elif selected_piece.name.lower() == 'r':
                                directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Horizontals and verticals for rook
                            else:  # Queen
                                directions = [(-1, -1), (-1, 1), (1, -1), (1, 1),  # Diagonals
                                             (-1, 0), (1, 0), (0, -1), (0, 1)]  # Horizontals and verticals
                            
                            # per each direction, add moves until hits a piece or the edge of the board
                            for dr, dc in directions:
                                for i in range(1, 8):  # Maximum 7 squares in any direction
                                    new_row = selected_piece.row + dr * i
                                    new_col = selected_piece.col + dc * i
                                    
                                    # Check if we're still on the board
                                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                                        # Check if there's a piece at this position
                                        piece_at_pos = None
                                        for other_piece in pieces:
                                            if other_piece.row == new_row and other_piece.col == new_col:
                                                piece_at_pos = other_piece
                                                break
                                        
                                        # Decide whether to add the move based on what's in this square
                                        if piece_at_pos:
                                            # If it's an opponent's piece, we can capture it
                                            if ((selected_piece.name.islower() and piece_at_pos.name.isupper()) or 
                                                (selected_piece.name.isupper() and piece_at_pos.name.islower())):
                                                valid_moves.append((new_row, new_col))
                                            # Stop looking in this direction after finding any piece
                                            break
                                        else:
                                            # Empty square, add as valid move
                                            valid_moves.append((new_row, new_col))
                                    else:
                                        # Off the board, stop looking in this direction
                                        break
                        else:
                            # For non-sliding pieces (pawns, kings, knights), use the original logic
                            valid_moves = selected_piece.get_pos_moves()
                            
                            # Special handling for pawns
                            if selected_piece.name.lower() == 'p':
                                moves_to_remove = []
                                
                                for move_row, move_col in valid_moves:
                                    # Check if it's a diagonal move
                                    is_diagonal = move_col != selected_piece.col
                                    
                                    if is_diagonal:
                                        # For diagonal moves, check if there's an opponent's piece to capture
                                        can_capture = False
                                        for other_piece in pieces:
                                            if (other_piece.row == move_row and other_piece.col == move_col and
                                                ((selected_piece.name.islower() and other_piece.name.isupper()) or
                                                 (selected_piece.name.isupper() and other_piece.name.islower()))):
                                                can_capture = True
                                                break
                                        
                                        # If no opponent piece to capture on diagonal, remove the move
                                        if not can_capture:
                                            moves_to_remove.append((move_row, move_col))
                                    else:
                                        # For forward moves, check if there's any piece blocking
                                        for other_piece in pieces:
                                            if other_piece.row == move_row and other_piece.col == move_col:
                                                moves_to_remove.append((move_row, move_col))
                                                break
                                        
                                        # For two-square moves, check if there's any piece blocking the path
                                        if abs(move_row - selected_piece.row) == 2:  # It's a two-square move
                                            # Check the square in between
                                            between_row = (selected_piece.row + move_row) // 2
                                            for other_piece in pieces:
                                                if other_piece.row == between_row and other_piece.col == selected_piece.col:
                                                    moves_to_remove.append((move_row, move_col))
                                                    break
                                    
                                    # Remove invalid pawn moves
                                    for move in moves_to_remove:
                                        if move in valid_moves:
                                            valid_moves.remove(move)
                                else:
                                    # For other non-sliding pieces (kings), remove moves onto own pieces
                                    moves_to_remove = []
                                    for move_row, move_col in valid_moves:
                                        for other_piece in pieces:
                                            if (other_piece.row == move_row and other_piece.col == move_col and
                                                ((selected_piece.name.islower() and other_piece.name.islower()) or
                                                 (selected_piece.name.isupper() and other_piece.name.isupper()))):
                                                moves_to_remove.append((move_row, move_col))
                                                break
                                    
                                    # Remove invalid moves
                                    for move in moves_to_remove:
                                        if move in valid_moves:
                                            valid_moves.remove(move)
                            
                            # If in check, we need special handling for all pieces
                            if in_check:
                                # For all pieces including the king, we need to check if the move resolves the check
                                # Make a copy of all possible moves
                                all_possible_moves = valid_moves.copy()
                                valid_moves = []
                                
                                for move_row, move_col in all_possible_moves:
                                    # Temporarily move the piece to see if it resolves the check
                                    original_row, original_col = selected_piece.row, selected_piece.col
                                    
                                    # Check if there's a piece to capture at the target position
                                    piece_to_capture = None
                                    for other_piece in pieces:
                                        if other_piece.row == move_row and other_piece.col == move_col:
                                            piece_to_capture = other_piece
                                            break
                                    
                                    # Temporarily remove the captured piece from the list
                                    if piece_to_capture:
                                        pieces.remove(piece_to_capture)
                                    
                                    # Temporarily move the piece
                                    selected_piece.row, selected_piece.col = move_row, move_col
                                    
                                    # Check if the king is still in check after the move
                                    still_in_check = is_in_check('white', pieces)
                                    
                                    # Restore the original position
                                    selected_piece.row, selected_piece.col = original_row, original_col
                                    
                                    # Restore the captured piece if there was one
                                    if piece_to_capture:
                                        pieces.append(piece_to_capture)
                                    
                                    # If the move resolves the check, add it to valid moves
                                    if not still_in_check:
                                        valid_moves.append((move_row, move_col))
                            else:
                                # If not in check, just filter moves that would put the king in check
                                valid_moves = filter_moves_for_check(selected_piece, valid_moves, pieces)
                else:
                    # If it's a black piece, don't allow selection
                    selected_piece = None
                    valid_moves = []
            
            # If we didn't click on any piece, check if it's a valid move for the selected piece or deselect
            if not clicked_on_piece and selected_piece:
                # Convert mouse position to board coordinates
                clicked_row = mouse_pos[1] // 80
                clicked_col = mouse_pos[0] // 80
                
                # Check if the clicked position is a valid move
                if (clicked_row, clicked_col) in valid_moves:
                    # Check if there's a piece to capture at the target position
                    piece_to_capture = None
                    for other_piece in pieces:
                        if other_piece.row == clicked_row and other_piece.col == clicked_col:
                            piece_to_capture = other_piece
                            break
                    
                    # If there's a piece to capture, remove it from the pieces list
                    if piece_to_capture:
                        pieces.remove(piece_to_capture)
                    
                    # Track if this is a pawn move for 50-move rule
                    is_pawn_move = selected_piece.name.lower() == 'p'
                    if is_pawn_move:
                        # Reset 50-move counter on pawn move
                        last_capture_or_pawn_move = move_counter
                    
                    # Increment move counter for white's move
                    move_counter += 1
                    
                    # Move the piece to the new position
                    selected_piece.move(clicked_row, clicked_col)
                    
                    # Check for pawn promotion
                    if is_pawn_move and clicked_row == 0:  # White pawn reaches top rank
                        handle_promotion(selected_piece, clicked_row, clicked_col, 'white')
                    else:
                        # Clear selection after moving
                        selected_piece = None
                        valid_moves = []
                        
                        # Check for checkmate, stalemate, or 50-move rule
                        if not check_game_end() and game_active:
                            # After white moves, make a move for black using the engine
                            # Add a small delay to ensure UI updates before black moves
                            pygame.time.delay(100)
                            make_black_move()
                else:
                    # If clicked on an invalid position, clear selection
                    selected_piece = None
                    valid_moves = []
    
    pygame.display.flip()

pygame.quit()
sys.exit()
