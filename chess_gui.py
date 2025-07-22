import pygame
import os
import math
from chess_piece import Piece, PieceType, Color
from chess_position import Position, Move
from chess_board import Board
from chess_move_generator import MoveGenerator

class ChessGUI:
    def __init__(self, window_size=640):
        self.window_size = window_size
        self.square_size = window_size // 8
        self.window = None
        self.board = Board()  # Initialize with default position
        self.move_generator = MoveGenerator(self.board)
        self.selected_pos = None
        self.legal_moves = []
        self.piece_textures = {}
        self.game_status = None  # For displaying checkmate/stalemate messages
        
        # Colors
        self.light_square_color = (240, 217, 181)  # Light brown
        self.dark_square_color = (181, 136, 99)    # Dark brown
        self.selected_square_color = (124, 192, 214)  # Light blue
        self.legal_move_color = (106, 168, 79)     # Green
        self.capture_move_color = (224, 102, 102)  # Red
        self.checkmate_color = (255, 0, 0, 180)    # Semi-transparent red
        self.stalemate_color = (128, 128, 128, 180)  # Semi-transparent gray
        
        # Initialize pygame
        pygame.init()
        self.font = pygame.font.SysFont('Arial', 24)
        self.status_font = pygame.font.SysFont('Arial', 36, bold=True)
    
    def initialize(self):
        """Initialize the GUI window and load textures."""
        self.window = pygame.display.set_mode((self.window_size, self.window_size))
        pygame.display.set_caption("BrothFish Chess Engine")
        self.load_textures()
        return True
    
    def load_textures(self):
        """Load piece textures from PNG files."""
        # Map of piece characters to PNG filenames
        piece_files = {
            'P': 'white-pawn.png',
            'N': 'white-knight.png',
            'B': 'white-bishop.png',
            'R': 'white-rook.png',
            'Q': 'white-queen.png',
            'K': 'white-king.png',
            'p': 'black-pawn.png',
            'n': 'black-knight.png',
            'b': 'black-bishop.png',
            'r': 'black-rook.png',
            'q': 'black-queen.png',
            'k': 'black-king.png'
        }
        
        # Path to the piece images
        base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                "resources", "images", "pieces-basic-png")
        
        print(f"Loading chess pieces from: {base_path}")
        
        # Load each piece texture
        for char, filename in piece_files.items():
            path = os.path.join(base_path, filename)
            try:
                texture = pygame.image.load(path)
                # Scale the texture to fit the square
                texture = pygame.transform.scale(texture, (self.square_size, self.square_size))
                self.piece_textures[char] = texture
                print(f"Loaded piece texture: {filename}")
            except pygame.error as e:
                print(f"Error loading texture {filename}: {e}")
                # Create a fallback texture with text
                fallback = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                color = (255, 255, 255) if char.isupper() else (0, 0, 0)
                pygame.draw.circle(fallback, color, (self.square_size//2, self.square_size//2), self.square_size//3)
                font = pygame.font.SysFont('Arial', self.square_size//2)
                text = font.render(char, True, (255, 0, 0) if char.isupper() else (255, 255, 0))
                text_rect = text.get_rect(center=(self.square_size//2, self.square_size//2))
                fallback.blit(text, text_rect)
                self.piece_textures[char] = fallback
    
    def is_open(self):
        """Check if the window is still open."""
        return self.window is not None
    
    def draw_board(self):
        """Draw the chess board and pieces."""
        self.window.fill((40, 40, 40))
        
        # Draw squares
        for rank in range(8):
            for file in range(8):
                # Determine square color
                is_light = (file + rank) % 2 == 0
                color = self.light_square_color if is_light else self.dark_square_color
                
                # Highlight selected square
                pos = Position(file, rank)
                if self.selected_pos and self.selected_pos.file == file and self.selected_pos.rank == rank:
                    color = self.selected_square_color
                
                # Draw the square
                square_rect = pygame.Rect(
                    file * self.square_size,
                    (7 - rank) * self.square_size,  # Flip rank for display
                    self.square_size,
                    self.square_size
                )
                pygame.draw.rect(self.window, color, square_rect)
                
                # Highlight legal moves
                if self.selected_pos:
                    for move in self.legal_moves:
                        if move.to_pos.file == file and move.to_pos.rank == rank:
                            # Determine if this is a capture move
                            target_piece = self.board.get_piece(move.to_pos)
                            highlight_color = self.capture_move_color if not target_piece.is_empty() else self.legal_move_color
                            
                            # Draw a circle to indicate a legal move
                            center_x = file * self.square_size + self.square_size // 2
                            center_y = (7 - rank) * self.square_size + self.square_size // 2
                            pygame.draw.circle(self.window, highlight_color, (center_x, center_y), self.square_size // 6)
        
        # Draw pieces
        for rank in range(8):
            for file in range(8):
                pos = Position(file, rank)
                piece = self.board.get_piece(pos)
                
                if not piece.is_empty():
                    # Get the piece texture
                    piece_char = piece.to_char()
                    if piece_char in self.piece_textures:
                        texture = self.piece_textures[piece_char]
                        
                        # Calculate the position to draw the piece
                        piece_rect = pygame.Rect(
                            file * self.square_size,
                            (7 - rank) * self.square_size,  # Flip rank for display
                            self.square_size,
                            self.square_size
                        )
                        
                        # Draw the piece
                        self.window.blit(texture, piece_rect)
        
        # Draw rank and file labels
        for i in range(8):
            # Rank labels (1-8)
            rank_label = self.font.render(str(i + 1), True, (200, 200, 200))
            self.window.blit(rank_label, (5, (7 - i) * self.square_size + 5))
            
            # File labels (a-h)
            file_label = self.font.render(chr(97 + i), True, (200, 200, 200))
            self.window.blit(file_label, (i * self.square_size + self.square_size - 15, self.window_size - 20))
        
        # Draw game status (checkmate/stalemate) if applicable
        if self.game_status:
            # Create a semi-transparent overlay
            overlay = pygame.Surface((self.window_size, self.window_size), pygame.SRCALPHA)
            if "Checkmate" in self.game_status:
                overlay.fill(self.checkmate_color)
            else:  # Stalemate
                overlay.fill(self.stalemate_color)
            self.window.blit(overlay, (0, 0))
            
            # Draw the status text
            status_text = self.status_font.render(self.game_status, True, (255, 255, 255))
            text_rect = status_text.get_rect(center=(self.window_size // 2, self.window_size // 2))
            self.window.blit(status_text, text_rect)
        
        pygame.display.flip()
    
    def get_square_from_mouse_pos(self, x, y):
        """Convert mouse coordinates to board position."""
        if x < 0 or x >= self.window_size or y < 0 or y >= self.window_size:
            return Position(-1, -1)  # Invalid position
        
        file = x // self.square_size
        rank = 7 - (y // self.square_size)  # Flip rank (0 at bottom)
        
        return Position(file, rank)
    
    def process_events(self):
        """Process user input events and return a move if one is made."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
                return Move(Position(-1, -1), Position(-1, -1))
            
            # Check for ESC key press to close the window
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    print("ESC key pressed - closing window")
                    self.close()
                    return Move(Position(-1, -1), Position(-1, -1))
            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left mouse button
                # Get the square that was clicked
                mouse_pos = pygame.mouse.get_pos()
                clicked_pos = self.get_square_from_mouse_pos(mouse_pos[0], mouse_pos[1])
                
                if not clicked_pos.is_valid():
                    continue
                
                print(f"Clicked position: {clicked_pos.to_algebraic()}")
                
                # If a piece is already selected
                if self.selected_pos and self.selected_pos.is_valid():
                    # Check if the clicked position is the same as the selected position (deselect)
                    if clicked_pos == self.selected_pos:
                        print("Deselecting piece")
                        self.selected_pos = Position(-1, -1)
                        self.legal_moves = []
                        return Move(Position(-1, -1), Position(-1, -1))
                    
                    # Check if the clicked position is a legal move
                    selected_move = None
                    for move in self.legal_moves:
                        if clicked_pos == move.to_pos:
                            selected_move = move
                            break
                    
                    if selected_move:
                        print(f"Selected move: {selected_move.to_algebraic()}")
                        
                        # Check if this is a capture
                        target_piece = self.board.get_piece(selected_move.to_pos)
                        if not target_piece.is_empty():
                            print(f"Capturing piece: {target_piece.to_char()} at {selected_move.to_pos.to_algebraic()}")
                        
                        # Reset selection
                        self.selected_pos = Position(-1, -1)
                        self.legal_moves = []
                        
                        # Return the move to be executed
                        return selected_move
                    else:
                        # Clicked on an invalid destination, try selecting a new piece
                        piece = self.board.get_piece(clicked_pos)
                        if not piece.is_empty() and piece.color == self.board.get_side_to_move():
                            # Select the new piece
                            self.selected_pos = clicked_pos
                            self.legal_moves = []
                            
                            # Find legal moves for this piece
                            all_legal_moves = self.move_generator.generate_legal_moves()
                            for move in all_legal_moves:
                                if move.from_pos == self.selected_pos:
                                    self.legal_moves.append(move)
                            
                            print(f"Selected position: {self.selected_pos.to_algebraic()}")
                            print("Legal moves: ", end="")
                            for move in self.legal_moves:
                                print(f"{move.to_algebraic()} ", end="")
                            print()
                        else:
                            # Clicked on an empty square or opponent's piece, deselect
                            self.selected_pos = Position(-1, -1)
                            self.legal_moves = []
                else:
                    # No piece is selected, try to select one
                    piece = self.board.get_piece(clicked_pos)
                    if not piece.is_empty() and piece.color == self.board.get_side_to_move():
                        # Select the piece
                        self.selected_pos = clicked_pos
                        
                        # Find legal moves for this piece
                        all_legal_moves = self.move_generator.generate_legal_moves()
                        for move in all_legal_moves:
                            if move.from_pos == self.selected_pos:
                                self.legal_moves.append(move)
                        
                        print(f"Selected position: {self.selected_pos.to_algebraic()}")
                        print("Legal moves: ", end="")
                        for move in self.legal_moves:
                            print(f"{move.to_algebraic()} ", end="")
                        print()
        
        # No move was made
        return Move(Position(-1, -1), Position(-1, -1))
    
    def set_game_status(self, status):
        """Set the game status message (checkmate/stalemate)."""
        self.game_status = status
    
    def close(self):
        """Close the GUI window."""
        if self.window:
            pygame.quit()
            self.window = None
