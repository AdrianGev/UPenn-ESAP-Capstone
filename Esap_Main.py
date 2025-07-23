import pygame
import time
import sys
import os
from esap_Board import Board
# from chess_gui import ChessGUI
from esap_piece import *
from chess_utils import blocked_from, get_blocked_directions
from chess_check_utils import is_in_check, filter_moves_for_check, is_square_attacked


WIDTH, HEIGHT = 640, 640  # window size
ROWS, COLS = 8, 8


# Colors
WHITE = (232, 235, 239)
BLUE = (125, 135, 150)

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
in_check = False
check_indicator_color = (255, 255, 0, 150)  # Yellow with transparency

running = True
while running:
    clock.tick(60)  # 60 FPS
    draw_board()
    draw_pieces()
    
    # Check if white king is in check
    in_check = is_in_check('white', pieces)
    
    # If in check, highlight the king
    if in_check:
        # Find the white king
        for piece in pieces:
            if piece.name == 'K':  # White king
                # Create a transparent surface for the check indicator
                check_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
                pygame.draw.rect(check_surf, check_indicator_color, (0, 0, 80, 80), 4)  # Yellow border
                screen.blit(check_surf, (piece.col * 80, piece.row * 80))
                break
    
    # Draw move indicators for the selected piece
    if selected_piece and valid_moves:
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
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # if the mouse is clicked
        elif event.type == pygame.MOUSEBUTTONDOWN:
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
                pieces.remove(clicked_piece)
                
                # Move our piece to the captured piece's position
                selected_piece.move(clicked_row, clicked_col)
                
                # Clear selection after moving
                selected_piece = None
                valid_moves = []
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
                    
                    # Move the piece to the new position
                    selected_piece.move(clicked_row, clicked_col)
                    
                    # Clear selection after moving
                    selected_piece = None
                    valid_moves = []
                else:
                    # If clicked on an invalid position, clear selection
                    selected_piece = None
                    valid_moves = []
    
    pygame.display.flip()

pygame.quit()
sys.exit()
