import math
import pygame as p
import time
import datetime

# Slider class for UI controls bc somehow JAVA SWING has built in sliders
# but PYGAME DOESNT??
class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, default_val, label, font):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_val = min_val
        self.max_val = max_val
        self.value = default_val
        self.label = label
        self.font = font
        self.dragging = False
        self.handle_radius = 10
        self.handle_x = self.x + int((self.value - self.min_val) / (self.max_val - self.min_val) * self.width)
    
    def draw(self, screen):
        label_text = self.font.render(f"{self.label}: {self.value}", True, p.Color("black"))
        screen.blit(label_text, (self.x, self.y - 30))
        
        p.draw.rect(screen, p.Color("gray"), (self.x, self.y, self.width, self.height))
        
        p.draw.circle(screen, p.Color("blue"), (self.handle_x, self.y + self.height // 2), self.handle_radius)
    
    def handle_event(self, event):
        if event.type == p.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = p.mouse.get_pos()
            if abs(mouse_pos[0] - self.handle_x) <= self.handle_radius * 2 and \
               abs(mouse_pos[1] - (self.y + self.height // 2)) <= self.handle_radius * 2:
                self.dragging = True
        
        elif event.type == p.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        
        elif event.type == p.MOUSEMOTION and self.dragging:
            mouse_x = event.pos[0]
            # Constrain to slider bounds cuz like no duh
            if mouse_x < self.x:
                mouse_x = self.x
            elif mouse_x > self.x + self.width:
                mouse_x = self.x + self.width
            
            self.handle_x = mouse_x
            # Calculate value based on position
            value_range = self.max_val - self.min_val
            position_ratio = (self.handle_x - self.x) / self.width
            self.value = round(self.min_val + position_ratio * value_range)

from ESAP_chess_core import BoardCoordinate, ChessMatrix, NULL_SQUARE
from ESAP_chess_moves import Move
from ESAP_chess_game import GameState
import ESAP_minimax_math

# piece name mapping for display
reverse_piece_mapping = {
    "wp": "White Pawn",
    "wR": "White Rook",
    "wN": "White Knight",
    "wB": "White Bishop",
    "wQ": "White Queen",
    "wK": "White King",
    "bp": "Black Pawn",
    "bR": "Black Rook",
    "bN": "Black Knight",
    "bB": "Black Bishop",
    "bQ": "Black Queen",
    "bK": "Black King"
}


window_width = 512
window_height = 512
DIMENSION = 8
SQ_SIZE = window_height // DIMENSION
MAX_FPS = 240
IMAGES = {}

def load_images():
    global PIECE_MAPPING
    PIECE_MAPPING = {
        # white p
        "white_pawn": "wp",
        "white_rook": "wR",
        "white_knight": "wN",
        "white_bishop": "wB",
        "white_queen": "wQ",
        "white_king": "wK",
        # black p
        "black_pawn": "bp",
        "black_rook": "bR",
        "black_knight": "bN",
        "black_bishop": "bB",
        "black_queen": "bQ",
        "black_king": "bK"
    }
    
    global REVERSE_PIECE_MAPPING
    REVERSE_PIECE_MAPPING = {v: k for k, v in PIECE_MAPPING.items()}
    
    piece_codes = ["wp", "wR", "wN", "wB", "wQ", "wK", "bp", "bR", "bN", "bB", "bQ", "bK"]
    for piece_code in piece_codes:
        IMAGES[piece_code] = p.transform.scale(p.image.load("pieces/" + piece_code + ".png"), (SQ_SIZE, SQ_SIZE))

def print_board(board):
    """Print a text representation of the board to the terminal
    Uses uppercase letters for white pieces and lowercase for black pieces
    """
    print("  " + "-" * 33)
    for i, row in enumerate(board):
        print(f"{ 8 - i } |" , end = "")
        for piece_code in row:
            if piece_code == "--":
                print("   |" , end = "")
            else:
                # convert piece code to display format
                display_char = get_display_char(piece_code)
                print(f" {display_char} |" , end = "")
        print("\n  " + "-" * 33)
    print("    a   b   c   d   e   f   g   h")

def main():
    p.init()
    screen = p.display.set_mode((window_width, window_height))
    p.display.set_caption("Out-Of-Stock-Fish Chess Engine")
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    game_state = GameState()
    valid_moves = game_state.get_valid_moves()
    move_made = False
    game_over = False
    game_over_message_shown = False
    player_one = True   
    player_two = False
    load_images()
    square_selected = ()
    player_clicks = []
    game_start_time = time.time()
    move_count = 0
    white_move_times = []
    black_move_times = []
    last_move_time = time.time()
    
    print("\n" + "="*50)
    print("OUT-OF-STOCK-FISH CHESS ENGINE")
    print("Game started at:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*50)
    print("\nGAME CONTROLS:")
    print("  R: Reset game")
    print("  Q: Computer plays White, You play Black")
    print("  E: You play White, Computer plays Black")
    print("="*50 + "\n")
    print("INITIAL BOARD STATE:")
    print_board(game_state.board)
    print("\nGame started! White to move.\n" + "-"*50)

    running = True
    while running:
        human_turn = (game_state.white_to_move and player_one) or (not game_state.white_to_move and player_two)
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            elif e.type == p.MOUSEBUTTONDOWN:
                if not game_over and human_turn:
                    location = p.mouse.get_pos()
                    col = location[0]//SQ_SIZE
                    row = location[1]//SQ_SIZE
                    if square_selected == (row, col) or col >= 8:
                        square_selected = ()
                        player_clicks = []
                    else:
                        square_selected = (row, col)
                        player_clicks.append(square_selected)
                    if len(player_clicks) == 2:
                        start_pos = BoardCoordinate(player_clicks[0][0], player_clicks[0][1])
                        end_pos = BoardCoordinate(player_clicks[1][0], player_clicks[1][1])
                        move = Move(start_pos, end_pos, game_state.board)
                        if move in valid_moves:
                            move = valid_moves[valid_moves.index(move)]
                            move_start_time = time.time()
                            move_time = move_start_time - last_move_time
                            last_move_time = move_start_time
                            
                            game_state.make_move(move)
                            move_made = True
                            square_selected = ()
                            player_clicks = []
                            
                            move_count += 1
                            if game_state.white_to_move:
                                black_move_times.append(move_time)
                                player = "Black"
                            else:
                                white_move_times.append(move_time)
                                player = "White"
                                
                            print(f"\nMove #{move_count}: {player} played {move.get_chess_notation()}")
                            print(f"Piece moved: {REVERSE_PIECE_MAPPING.get(move.piece_moved, move.piece_moved)}, Captured: {REVERSE_PIECE_MAPPING.get(move.piece_captured, 'None') if move.piece_captured != NULL_SQUARE else 'None'}")
                            print(f"Move time: {move_time:.2f} seconds")
                            
                            # Check for special moves
                            if move.is_pawn_promotion:
                                print("Pawn promoted to Queen!")
                            if move.is_castle_move:
                                print("Castles")
                            if move.is_enpassant_move:
                                print("En passant (crossaint) capture!")
                                
                            # print updated board
                            print("\nCurrent board state:")
                            print_board(game_state.board)
                            
                            # print game status
                            if game_state.in_check:
                                print(f"\n{'White' if game_state.white_to_move else 'Black'} is in CHECK!")
                            print_move_log(game_state.move_log)
                            print(f"{'White' if game_state.white_to_move else 'Black'} to move.\n" + "-"*50)
                        else:
                            player_clicks = [square_selected]
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    game_state.undo_move()
                    move_made = True
                    game_over = False
                    player_one = True
                    player_two = True
                elif e.key == p.K_r:
                    gs = GameState()
                    valid_moves = game_state.get_valid_moves()
                    move_made = False
                    animate = False
                    game_over = False
                    player_one = True
                    player_two = True
                    square_selected = ()
                    player_clicks = []
                elif e.key == p.K_q:
                    player_one = False
                    player_two = True
                elif e.key == p.K_e:
                    player_one = True
                    player_two = False

        if move_made:
            valid_moves = game_state.get_valid_moves()
            move_made = False
            
            #print game statistics after each move (this can be turned into csv data later on)
            white_avg = sum(white_move_times) / len(white_move_times) if white_move_times else 0
            black_avg = sum(black_move_times) / len(black_move_times) if black_move_times else 0
            elapsed = time.time() - game_start_time
            
            print(f"Game stats: {move_count} moves | Time elapsed: {elapsed:.1f}s")
            print(f"Average move times - White: {white_avg:.2f}s | Black: {black_avg:.2f}s")

        ''' Bot move finder '''
        if not game_over and not human_turn:
            print("\nBot is thinking...")
            ai_start_time = time.time()
            bot_move = ESAP_minimax_math.findBestMoveMinimax(game_state, valid_moves)
            if bot_move is None:   #when begin the game
                bot_move = ESAP_minimax_math.select_random_move(valid_moves)
                print("Bot is using random move selection for opening")
            else:
                print(f"Bot evaluated position and found best move in {time.time() - ai_start_time:.2f} seconds")
                
            move_start_time = time.time()
            move_time = move_start_time - last_move_time
            last_move_time = move_start_time
            
            game_state.make_move(bot_move)
            move_made = True
            animate = True
            
            move_count += 1
            if game_state.white_to_move:
                black_move_times.append(move_time)
                player = "Black (Bot)"
            else:
                white_move_times.append(move_time)
                player = "White (Bot)"
                
            print(f"\nMove #{move_count}: {player} played {bot_move.get_chess_notation()}")
            print(f"Piece moved: {reverse_piece_mapping.get(bot_move.piece_moved, bot_move.piece_moved)}, Captured: {reverse_piece_mapping.get(bot_move.piece_captured, 'None') if bot_move.piece_captured != NULL_SQUARE else 'None'}")
            
            # check for en crossaint and pawns becoming cooler and castling
            if bot_move.is_pawn_promotion:
                print("Pawn -> Queen")
            if bot_move.is_castle_move:
                print("Castles")
            if bot_move.is_enpassant_move:
                print("En passant capture")
                
            # print updated board
            print("\nCurrent board state:")
            print_board(game_state.board)
            
            # print game status
            if game_state.in_check:
                print(f"\n{'White' if game_state.white_to_move else 'Black'} is in CHECK!")
            print_move_log(game_state.move_log)
            print(f"{'White' if game_state.white_to_move else 'Black'} to move.\n" + "-"*50)


        # calculate game duration for statistics (used in both game over and normal states)
        game_duration = time.time() - game_start_time
        
        # check for game over conditions BEFORE drawing the game state
        # this ensures the game over state is detected immediately after a move
        # took me 45 minutes to figure this out argh
        if game_state.checkmate or game_state.stalemate or game_state.threefold_repetition or game_state.insufficient_material:
            game_over = True
            
            # draw the final game state first
            draw_game_state(screen, game_state, valid_moves, square_selected)
            
            # then display the appropriate end game message - but only once
            if not game_over_message_shown:
                # create a transparent overlay cuz it looks cool
                overlay = p.Surface((window_width, window_height), p.SRCALPHA)
                overlay.fill((255, 255, 255, 128))  # semi -transparent white
                screen.blit(overlay, (0, 0))
                
                # show da msg
                if game_state.stalemate:
                    message = "Draw by Stalemate"
                    print("\n" + "*"*50)
                    print("GAME OVER: STALEMATE - DRAW")
                    print("*"*50)
                elif game_state.threefold_repetition:
                    message = "Draw by Threefold Repetition"
                    print("\n" + "*"*50)
                    print("GAME OVER: THREEFOLD REPETITION - DRAW")
                    print("*"*50)
                elif game_state.insufficient_material:
                    message = "Draw by Insufficient Material"
                    print("\n" + "*"*50)
                    print("GAME OVER: INSUFFICIENT MATERIAL - DRAW")
                    print("*"*50)
                else:  # It's checkmate
                    # The player whose turn it is has lost (they have no legal moves and are in check)
                    if game_state.white_to_move:  # White has no moves and is in check
                        message = "Black Wins by Checkmate!"
                        print("\n" + "*"*50)
                        print("GAME OVER: CHECKMATE - BLACK WINS!")
                        print("*"*50)
                    else:  # Black has no moves and is in check
                        message = "White Wins by Checkmate!"
                        print("\n" + "*"*50)
                        print("GAME OVER: CHECKMATE - WHITE WINS!")
                        print("*"*50)
                
                # Draw the message with a more visible approach
                draw_end_game_text(screen, message)
                
                # Print final game statistics
                print(f"\nFinal Game Statistics:")
                print(f"Total moves: {move_count}")
                
                # Set the flag so we don't show the message again
                game_over_message_shown = True
            
            # Force a display update to show the end game state immediately
            p.display.flip()
            
            # When game is over, wait for user to close the window
            if game_over and game_over_message_shown:
                waiting_for_close = True
                while waiting_for_close:
                    for e in p.event.get():
                        if e.type == p.QUIT:
                            waiting_for_close = False
                            running = False  # Exit the main game loop
                        elif e.type == p.KEYDOWN:
                            if e.key == p.K_ESCAPE:
                                waiting_for_close = False
                                running = False  # Exit the main game loop
                    
                    # Keep displaying the end game message
                    p.display.flip()
                    clock.tick(15)  # Lower frame rate while waiting
        else:
            # Normal game state drawing if the game is not over
            draw_game_state(screen, game_state, valid_moves, square_selected)


        clock.tick(MAX_FPS)
        p.display.flip()

def draw_end_game_text(screen, text):
    """Draw end game message with specific reason"""
    font = p.font.SysFont("Arial", 32, True, False)
    text_object = font.render(text, True, p.Color("red"))
    text_location = p.Rect(0, 0, window_width, window_height).move(
        window_width/2 - text_object.get_width()/2, window_height/2 - text_object.get_height()/2)
    screen.blit(text_object, text_location)
    # Force immediate display update
    p.display.flip()

def highlight_move(screen, game_state, valid_moves, square_selected):
    sq = p.Surface((SQ_SIZE, SQ_SIZE))
    sq.set_alpha(100)
    if square_selected != ():
        r, c = square_selected
        if game_state.board[r][c][0] == ('w' if game_state.white_to_move else 'b'): #square_selected is a piece that can be moved
            #highlight selected square
            sq.fill(p.Color("blue"))
            screen.blit(sq, (c * SQ_SIZE, r * SQ_SIZE))
            #draw dots for valid moves
            for move in valid_moves:
                if move.start_row == r and move.start_col == c:
                    # Calculate center position for the dot
                    center_x = move.end_col * SQ_SIZE + SQ_SIZE // 2
                    center_y = move.end_row * SQ_SIZE + SQ_SIZE // 2
                    # Draw a large red dot with radius of 1/4 of the square size
                    dot_radius = SQ_SIZE // 4
                    p.draw.circle(screen, p.Color("red"), (center_x, center_y), dot_radius)

    if game_state.in_check:
        if game_state.white_to_move:
            sq.fill(p.Color("red"))
            screen.blit(sq, (game_state.white_king_position.col * SQ_SIZE, game_state.white_king_position.row * SQ_SIZE))
        else:
            sq.fill(p.Color("red"))
            screen.blit(sq, (game_state.black_king_position.col * SQ_SIZE, game_state.black_king_position.row * SQ_SIZE))
    
    if len(game_state.move_log) != 0:
        sq.fill(p.Color("yellow"))
        screen.blit(sq, (game_state.move_log[-1].start_col * SQ_SIZE, game_state.move_log[-1].start_row * SQ_SIZE))
        screen.blit(sq, (game_state.move_log[-1].end_col * SQ_SIZE, game_state.move_log[-1].end_row * SQ_SIZE))


# Animation function removed as per user request

def draw_game_state(screen, game_state, valid_moves, square_selected):
    draw_board(screen)
    highlight_move(screen, game_state, valid_moves, square_selected)
    draw_pieces(screen, game_state.board)
    # Move log is now displayed in terminal instead of side panel

def draw_board(screen):
    colors = [p.Color("white"), p.Color("light blue")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r + c) % 2)]
            p.draw.rect(screen, color, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

def draw_pieces(screen, board):
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            piece = board[row][col]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(col*SQ_SIZE, row*SQ_SIZE, SQ_SIZE, SQ_SIZE))

# This function is now defined earlier in the file


def print_board(board):
    """Print a text representation of the board to the terminal
    Uses uppercase letters for white pieces and lowercase for black pieces
    """
    print("  ---------------------------------")
    for r in range(8):
        print(f"{8-r} |", end="")
        for c in range(8):
            piece = board[r][c]
            if piece == "--":
                print("   |", end="")
            else:
                # Use uppercase for white pieces, lowercase for black
                if piece[0] == 'w':
                    print(f" {piece[1].upper()} |", end="")
                else:
                    print(f" {piece[1].lower()} |", end="")
        print("\n  ---------------------------------")
    print("    a   b   c   d   e   f   g   h")

def print_move_log(move_log):
    """Print the move log to the terminal in a readable format"""
    if not move_log:
        return
        
    print("\nMove history:")
    print("-" * 30)
    for i in range(0, len(move_log), 2):
        move_string = f"{i//2 + 1}. {move_log[i]}"
        if i+1 < len(move_log):
            move_string += f" {move_log[i+1]}"
        print(move_string)

def get_display_char(piece_code):
    """Convert piece code to display character
    White pieces: uppercase (P, R, N, B, Q, K)
    Black pieces: lowercase (p, r, n, b, q, k)
    """
    if piece_code == "--":
        return " "
    
    color = piece_code[0]  # 'w' or 'b'
    piece_type = piece_code[1]  # 'p', 'R', 'N', etc.
    
    # Map piece types to standard chess notation
    piece_map = {
        'p': 'P',  # Pawn
        'R': 'R',  # Rook
        'N': 'N',  # Knight
        'B': 'B',  # Bishop
        'Q': 'Q',  # Queen
        'K': 'K'   # King
    }
    
    display_char = piece_map.get(piece_type, '?')
    
    # Use lowercase for black pieces
    if color == 'b':
        display_char = display_char.lower()
    
    return display_char

class slider:
    def __init__(self, x, y, width, height, min_val, max_val, default_val, label, font):
        self.rect = p.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = default_val
        self.label = label
        self.font = font
        self.active = False
        self.handle_width = 20
        self.handle_rect = p.Rect(self.get_handle_pos(), y - 5, self.handle_width, height + 10)
        
    def get_handle_pos(self):
        # Calculate handle position based on value
        range_width = self.rect.width - self.handle_width
        value_ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        return self.rect.x + int(range_width * value_ratio)
    
    def update_value_from_pos(self, x_pos):
        # Calculate value based on handle position
        range_width = self.rect.width - self.handle_width
        pos_ratio = max(0, min(1, (x_pos - self.rect.x) / range_width))
        self.value = self.min_val + int(pos_ratio * (self.max_val - self.min_val))
        self.handle_rect.x = self.get_handle_pos()
    
    def draw(self, screen):
        # Draw slider track
        p.draw.rect(screen, p.Color("darkgray"), self.rect)
        
        # Draw slider handle
        p.draw.rect(screen, p.Color("blue"), self.handle_rect, 0, 5)
        
        # Draw label and value
        label_text = self.font.render(f"{self.label}: {self.value}", True, p.Color("black"))
        screen.blit(label_text, (self.rect.x, self.rect.y - 25))
    
    def handle_event(self, event):
        if event.type == p.MOUSEBUTTONDOWN:
            if self.handle_rect.collidepoint(event.pos):
                self.active = True
        elif event.type == p.MOUSEBUTTONUP:
            self.active = False
        elif event.type == p.MOUSEMOTION and self.active:
            self.update_value_from_pos(event.pos[0])

def show_menu():
    """Display a menu to choose between normal mode and data mode"""
    p.init()
    title_font = p.font.SysFont("Arial", 40, True, False)
    menu_font = p.font.SysFont("Arial", 32, True, False)
    small_font = p.font.SysFont("Arial", 24, True, False)
    
    # Create menu screen
    screen = p.display.set_mode((window_width, window_height))
    p.display.set_caption("Out-Of-Stock-Fish Chess Engine")
    
    # Menu options
    options = ["You VS Bot", "Bot VS Bot (Data Mode)"]
    selected_option = 0
    
    # Menu loop
    running = True
    while running:
        screen.fill(p.Color("white"))
        
        # Draw chess board background
        board_size = 300
        square_size = board_size // 8
        board_x = (window_width - board_size) // 2
        board_y = 50
        colors = [p.Color("white"), p.Color("light blue")]
        for r in range(8):
            for c in range(8):
                color = colors[((r + c) % 2)]
                p.draw.rect(screen, color, p.Rect(board_x + c*square_size, board_y + r*square_size, square_size, square_size))
        
        # Draw title overlay
        title_bg = p.Surface((400, 80), p.SRCALPHA)
        title_bg.fill((255, 255, 255, 200))
        screen.blit(title_bg, (window_width//2 - 200, board_y + board_size//2 - 40))
        
        # Draw title
        title_text = title_font.render("Out-Of-Stock-Fish", True, p.Color("black"))
        subtitle_text = menu_font.render("Chess Engine", True, p.Color("black"))
        screen.blit(title_text, (window_width//2 - title_text.get_width()//2, board_y + board_size//2 - 30))
        screen.blit(subtitle_text, (window_width//2 - subtitle_text.get_width()//2, board_y + board_size//2 + 10))
        
        # Draw options
        for i, option in enumerate(options):
            color = p.Color("red") if i == selected_option else p.Color("black")
            text = menu_font.render(option, True, color)
            screen.blit(text, (window_width//2 - text.get_width()//2, 380 + i * 50))
        
        # Draw instructions
        instruction_text = small_font.render("Use UP/DOWN arrows to select, ENTER to confirm", True, p.Color("black"))
        screen.blit(instruction_text, (window_width//2 - instruction_text.get_width()//2, 480))
        
        p.display.flip()
        
        # Handle events
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
                return None
            elif e.type == p.KEYDOWN:
                if e.key == p.K_UP:
                    selected_option = (selected_option - 1) % len(options)
                elif e.key == p.K_DOWN:
                    selected_option = (selected_option + 1) % len(options)
                elif e.key == p.K_RETURN:
                    return selected_option
    
    return None

def get_simulation_parameters():
    """Get parameters for bot vs bot simulation using sliders"""
    p.init()
    title_font = p.font.SysFont("Arial", 36, True, False)
    menu_font = p.font.SysFont("Arial", 28, True, False)
    small_font = p.font.SysFont("Arial", 22, False, False)
    
    # Create screen
    window_width = 512
    board_height = 512
    progress_height = 200  # Data section height
    window_height = board_height + progress_height  # Total window height
    screen = p.display.set_mode((window_width, window_height))
    p.display.set_caption("Out-Of-Stock-Fish: Data Mode")
    
    # Create sliders
    white_depth_slider = Slider(100, 150, 312, 10, 0, 4, 2, "White Bot Depth", small_font)
    black_depth_slider = Slider(100, 220, 312, 10, 0, 4, 2, "Black Bot Depth", small_font)
    games_slider = Slider(100, 290, 312, 10, 1, 100, 10, "Number of Games", small_font)
    
    sliders = [white_depth_slider, black_depth_slider, games_slider]
    
    # Create start button
    start_button = p.Rect(window_width//2 - 75, 380, 150, 50)
    
    # Settings loop
    running = True
    while running:
        screen.fill(p.Color("white"))
        
        # Draw title
        title_text = title_font.render("Bot VS Bot Simulation Settings", True, p.Color("black"))
        screen.blit(title_text, (window_width//2 - title_text.get_width()//2, 50))
        
        # Draw depth info
        depth_info = small_font.render("Depth 0 = Random Moves, Higher = Stronger AI", True, p.Color("gray"))
        screen.blit(depth_info, (window_width//2 - depth_info.get_width()//2, 100))
        
        # Draw sliders
        for slider in sliders:
            slider.draw(screen)
        
        # Draw start button
        p.draw.rect(screen, p.Color("green"), start_button, 0, 10)
        start_text = menu_font.render("Start", True, p.Color("white"))
        screen.blit(start_text, (start_button.x + start_button.width//2 - start_text.get_width()//2, 
                                start_button.y + start_button.height//2 - start_text.get_height()//2))
        
        p.display.flip()
        
        # Handle events
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
                return 2, 2, 10  # Default values
            
            # Handle slider events
            for slider in sliders:
                slider.handle_event(e)
            
            # Handle button click
            if e.type == p.MOUSEBUTTONDOWN:
                if start_button.collidepoint(e.pos):
                    return white_depth_slider.value, black_depth_slider.value, games_slider.value
    
    return 2, 2, 10  # Default values

def run_data_mode(white_depth, black_depth, num_games):
    """Run bot vs bot simulation and collect statistics"""
    # Initialize statistics
    white_wins = 0
    black_wins = 0
    draws = 0
    total_moves = 0
    white_move_times = []
    black_move_times = []
    
    # Initialize pygame with adjusted window height for progress display
    p.init()
    board_height = 512  # Standard board height
    progress_height = 200
    window_height = board_height + progress_height  # Total window height
    screen = p.display.set_mode((window_width, window_height))
    p.display.set_caption("Out-Of-Stock-Fish Chess Engine - Data Mode")
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    load_images()
    
    # Fonts for progress display
    progress_font = p.font.SysFont("Arial", 18, True, False)
    
    # Progress tracking variables
    start_time = time.time()
    total_time_elapsed = 0
    
    # Clear terminal and print header
    print("\n" + "="*60)
    print("BOT VS BOT SIMULATION - DATA COLLECTION MODE")
    print("="*60)
    print(f"White Bot Depth: {white_depth} {'(Random Moves)' if white_depth == 0 else ''}")
    print(f"Black Bot Depth: {black_depth} {'(Random Moves)' if black_depth == 0 else ''}")
    print(f"Number of Games: {num_games}")
    print("="*60 + "\n")
    
    # Run simulation
    for game_num in range(1, num_games + 1):
        # Initialize game state
        gs = GameState()
        valid_moves = gs.get_valid_moves()
        game_over = False
        move_count = 0
        game_start_time = time.time()
        
        print(f"\nGame {game_num}/{num_games} started at {time.strftime('%H:%M:%S')}")
        print("-"*60)
        
        # Game loop
        while not game_over:
            # Get bot move
            move_start = time.time()
            if gs.white_to_move:
                # White bot's turn
                if white_depth == 0:
                    bot_move = ESAP_minimax_math.select_random_move(valid_moves)
                else:
                    ESAP_minimax_math.SEARCH_DEPTH = white_depth
                    bot_move = ESAP_minimax_math.find_best_move_minimax(gs, valid_moves)
                    if bot_move is None:
                        bot_move = ESAP_minimax_math.select_random_move(valid_moves)
                player = "White"
            else:
                # Black bot's turn
                if black_depth == 0:
                    bot_move = ESAP_minimax_math.select_random_move(valid_moves)
                else:
                    ESAP_minimax_math.SEARCH_DEPTH = black_depth
                    bot_move = ESAP_minimax_math.find_best_move_minimax(gs, valid_moves)
                    if bot_move is None:
                        bot_move = ESAP_minimax_math.select_random_move(valid_moves)
                player = "Black"
                
            # Calculate move time
            move_time = time.time() - move_start
            if gs.white_to_move:
                white_move_times.append(move_time)
            else:
                black_move_times.append(move_time)
            
            # Make move
            gs.make_move(bot_move)
            move_count += 1
            valid_moves = gs.get_valid_moves()
            
            # Check for game over
            if gs.checkmate or gs.stalemate:
                game_over = True
                total_moves += move_count
                game_duration = time.time() - game_start_time
                total_time_elapsed += game_duration
                
                # Update statistics
                if gs.white_to_move:
                    result = "BLACK WINS (Checkmate)"
                    black_wins += 1
                else:
                    result = "WHITE WINS (Checkmate)"
                    white_wins += 1
            elif gs.stalemate:
                result = "DRAW (Stalemate)"
                draws += 1
                game_over = True
            elif gs.threefold_repetition:
                result = "DRAW (Threefold Repetition)"
                draws += 1
                game_over = True
            
            if game_over:
                game_duration = time.time() - game_start_time
                print(f"Game {game_num} completed in {game_duration:.2f} seconds ({move_count} moves)")
                print(f"Result: {result}")
            
            # Process events to keep the window responsive (oopsie daisy)
            for e in p.event.get():
                if e.type == p.QUIT:
                    return
            
            # Calculate estimated time remaining
            current_time = time.time()
            elapsed = current_time - start_time
            # Calculate average move time from both white and black moves
            all_move_times = white_move_times + black_move_times
            avg_move_time = sum(all_move_times) / len(all_move_times) if all_move_times else 0.1
            avg_game_moves = total_moves / game_num if game_num > 1 else move_count
            
            # Estimate remaining moves and time
            remaining_games = num_games - game_num
            remaining_moves_current_game = 50 - move_count  # Assume average game is 50 moves (just an estimate)
            if remaining_moves_current_game < 0:
                remaining_moves_current_game = 0
            estimated_remaining_moves = remaining_moves_current_game + (remaining_games * avg_game_moves)
            estimated_remaining_time = estimated_remaining_moves * avg_move_time
            
            # Format time remaining
            hours, remainder = divmod(estimated_remaining_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_remaining_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            
            # Update display with progress info
            draw_game_state(screen, gs, valid_moves, ())
            
            # Draw progress overlay at the bottom of the board (not overlapping the board)
            board_height = 512  # Standard board height
            progress_height = 200  # Significantly increased height for more space
            progress_bg = p.Surface((window_width, progress_height), p.SRCALPHA)
            progress_bg.fill((0, 0, 0, 180))
            screen.blit(progress_bg, (0, board_height))
            
            # Draw progress text - left column
            left_margin = 20
            game_text = progress_font.render(f"Game: {game_num}/{num_games}", True, p.Color("white"))
            move_text = progress_font.render(f"Move: {move_count} | {player} played {bot_move.get_chess_notation()}", True, p.Color("white"))
            time_text = progress_font.render(f"Est. Time Remaining: {time_remaining_str}", True, p.Color("white"))
            
            # Calculate average move times for white and black
            white_avg = sum(white_move_times) / len(white_move_times) if white_move_times else 0
            black_avg = sum(black_move_times) / len(black_move_times) if black_move_times else 0
            
            # Split move time text into two lines for clarity
            white_time_text = progress_font.render(f"White Avg Move: {white_avg*1000:.1f}ms", True, p.Color("white"))
            black_time_text = progress_font.render(f"Black Avg Move: {black_avg*1000:.1f}ms", True, p.Color("white"))
            
            # Layout positioning variables
            right_margin = 20
            right_x = window_width - right_margin
            center_x = window_width // 2
            wins_text = progress_font.render(f"White Wins: {white_wins} ({white_wins/game_num*100:.1f}%)", True, p.Color("white"))
            losses_text = progress_font.render(f"Black Wins: {black_wins} ({black_wins/game_num*100:.1f}%)", True, p.Color("white"))
            draws_text = progress_font.render(f"Draws: {draws} ({draws/game_num*100:.1f}%)", True, p.Color("white"))
            avg_moves_text = progress_font.render(f"Avg Moves: {avg_game_moves:.1f}", True, p.Color("white"))
            
            # Top section - Game progress info
            section_title = progress_font.render("GAME PROGRESS", True, p.Color("yellow"))
            screen.blit(section_title, (center_x - section_title.get_width() // 2, board_height + 15))
            
            # Left column positioning
            screen.blit(game_text, (left_margin, board_height + 45))
            screen.blit(move_text, (left_margin, board_height + 75))
            screen.blit(time_text, (left_margin, board_height + 105))
            
            # Right column positioning (right-aligned)
            screen.blit(wins_text, (right_x - wins_text.get_width(), board_height + 45))
            screen.blit(losses_text, (right_x - losses_text.get_width(), board_height + 75))
            screen.blit(draws_text, (right_x - draws_text.get_width(), board_height + 105))
            
            # Bottom section - Statistics
            stats_title = progress_font.render("STATISTICS", True, p.Color("yellow"))
            screen.blit(stats_title, (center_x - stats_title.get_width() // 2, board_height + 135))
            
            # Move statistics in bottom section
            screen.blit(avg_moves_text, (left_margin, board_height + 165))
            white_x = window_width // 2.3
            screen.blit(white_time_text, (white_x - white_time_text.get_width() // 2, board_height + 165))
            screen.blit(black_time_text, (right_x - black_time_text.get_width(), board_height + 165))
            
            p.display.flip()
            clock.tick(MAX_FPS)
        
        # Print current statistics
        games_played = white_wins + black_wins + draws
        print("\nCurrent Statistics:")
        print(f"Games played: {games_played}/{num_games}")
        print(f"White wins: {white_wins} ({white_wins/games_played*100:.1f}%)")
        print(f"Black wins: {black_wins} ({black_wins/games_played*100:.1f}%)")
        print(f"Draws: {draws} ({draws/games_played*100:.1f}%)")
        print(f"Average moves per game: {total_moves/games_played:.1f}")
        
        # Calculate and display time statistics
        avg_game_time = total_time_elapsed / game_num
        white_avg_time = sum(white_move_times) / len(white_move_times) if white_move_times else 0
        black_avg_time = sum(black_move_times) / len(black_move_times) if black_move_times else 0
        print(f"Average game duration: {avg_game_time:.2f} seconds")
        print(f"Average move calculation time: White: {white_avg_time*1000:.2f} ms | Black: {black_avg_time*1000:.2f} ms")
        
        # Estimate time remaining
        games_remaining = num_games - game_num
        est_remaining_time = games_remaining * avg_game_time
        hours, remainder = divmod(est_remaining_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"Estimated time remaining: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
        print("-"*60)
    
    # Display final statistics
    total_duration = time.time() - start_time
    hours, remainder = divmod(total_duration, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    print("\n" + "="*60)
    print("FINAL SIMULATION RESULTS")
    print("="*60)
    print(f"White Bot Depth: {white_depth} {'(Random Moves)' if white_depth == 0 else ''}")
    print(f"Black Bot Depth: {black_depth} {'(Random Moves)' if black_depth == 0 else ''}")
    print(f"Total Games: {num_games}")
    print(f"Total Duration: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
    print("\nResults:")
    print(f"White wins: {white_wins} ({white_wins/num_games*100:.1f}%)")
    print(f"Black wins: {black_wins} ({black_wins/num_games*100:.1f}%)")
    print(f"Draws: {draws} ({draws/num_games*100:.1f}%)")
    print(f"Average moves per game: {total_moves/num_games:.1f}")
    print(f"Average game duration: {total_time_elapsed/num_games:.2f} seconds")
    white_avg_time = sum(white_move_times) / len(white_move_times) if white_move_times else 0
    black_avg_time = sum(black_move_times) / len(black_move_times) if black_move_times else 0
    print(f"Average move calculation time: White: {white_avg_time*1000:.2f} ms | Black: {black_avg_time*1000:.2f} ms")
    print("="*60)
    
    # Display final results on screen
    screen.fill(p.Color("white"))
    title_font = p.font.SysFont("Arial", 36, True, False)
    result_font = p.font.SysFont("Arial", 24, True, False)
    small_font = p.font.SysFont("Arial", 18, False, False)
    
    # Draw title
    title_text = title_font.render("Simulation Complete", True, p.Color("black"))
    screen.blit(title_text, (window_width//2 - title_text.get_width()//2, 50))
    
    # Draw results
    y_pos = 120
    line_height = 30
    
    config_text = result_font.render(f"White: Depth {white_depth} vs Black: Depth {black_depth}", True, p.Color("black"))
    screen.blit(config_text, (window_width//2 - config_text.get_width()//2, y_pos))
    y_pos += line_height * 1.5
    
    games_text = result_font.render(f"Total Games: {num_games}", True, p.Color("black"))
    screen.blit(games_text, (window_width//2 - games_text.get_width()//2, y_pos))
    y_pos += line_height * 2
    
    # Draw win percentages with colored bars
    white_pct = white_wins/num_games*100
    black_pct = black_wins/num_games*100
    draw_pct = draws/num_games*100
    
    # Draw percentage bars
    bar_width = 300
    bar_height = 25
    bar_x = window_width//2 - bar_width//2
    
    # White wins bar
    white_bar_width = int(bar_width * white_pct / 100)
    if white_bar_width > 0:
        p.draw.rect(screen, p.Color("lightgreen"), p.Rect(bar_x, y_pos, white_bar_width, bar_height))
    white_text = small_font.render(f"White: {white_wins} ({white_pct:.1f}%)", True, p.Color("black"))
    screen.blit(white_text, (bar_x + 10, y_pos + 3))
    y_pos += bar_height + 10
    
    # Black wins bar
    black_bar_width = int(bar_width * black_pct / 100)
    if black_bar_width > 0:
        p.draw.rect(screen, p.Color("lightblue"), p.Rect(bar_x, y_pos, black_bar_width, bar_height))
    black_text = small_font.render(f"Black: {black_wins} ({black_pct:.1f}%)", True, p.Color("black"))
    screen.blit(black_text, (bar_x + 10, y_pos + 3))
    y_pos += bar_height + 10
    
    # Draw bar
    draw_bar_width = int(bar_width * draw_pct / 100)
    if draw_bar_width > 0:
        p.draw.rect(screen, p.Color("lightgray"), p.Rect(bar_x, y_pos, draw_bar_width, bar_height))
    draw_text = small_font.render(f"Draws: {draws} ({draw_pct:.1f}%)", True, p.Color("black"))
    screen.blit(draw_text, (bar_x + 10, y_pos + 3))
    y_pos += bar_height + 30
    
    # Draw additional stats
    moves_text = result_font.render(f"Average moves per game: {total_moves/num_games:.1f}", True, p.Color("black"))
    screen.blit(moves_text, (window_width//2 - moves_text.get_width()//2, y_pos))
    y_pos += line_height
    
    time_text = result_font.render(f"Total time: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}", True, p.Color("black"))
    screen.blit(time_text, (window_width//2 - time_text.get_width()//2, y_pos))
    y_pos += line_height * 2
    
    # Draw exit instruction
    exit_text = small_font.render("Press ESC or close window to exit", True, p.Color("gray"))
    screen.blit(exit_text, (window_width//2 - exit_text.get_width()//2, y_pos))
    
    p.display.flip()
    
    # Wait for user to close window
    waiting = True
    while waiting:
        for e in p.event.get():
            if e.type == p.QUIT or (e.type == p.KEYDOWN and e.key == p.K_ESCAPE):
                waiting = False

if __name__ == "__main__":
    # Show menu and get selection
    option = show_menu()
    
    if option == 0:  # You VS Bot
        main()
    elif option == 1:  # Bot VS Bot (Data Mode)
        white_depth, black_depth, num_games = get_simulation_parameters()
        run_data_mode(white_depth, black_depth, num_games)
