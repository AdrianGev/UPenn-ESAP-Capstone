import pygame
import time
import sys
import os
from Esap_Board import Board
from chess_gui import ChessGUI
from Esap_piece import *


WIDTH, HEIGHT = 640, 640  # window size
ROWS, COLS = 8, 8


# Colors
WHITE = (232, 235, 239)
BLUE = (125, 135, 150)

#pieces 



kingBlack = Piece(pygame.image.load("pieces/black-king.png"), 0,4, "k")
kingWhite = Piece(pygame.image.load("pieces/white-king.png"), 7,4, "K")

bishopBlack = Piece(pygame.image.load("pieces/black-bishop.png"), 1,2, "b")
bishopWhite = Piece(pygame.image.load("pieces/white-bishop.png"), 6,5, "B")

pawnBlack = Piece(pygame.image.load("pieces/black-pawn.png"), 1,6, "p")
pawnWhite = Piece(pygame.image.load("pieces/white-pawn.png"), 6,1, "P")

rookBlack = Piece(pygame.image.load("pieces/black-rook.png"), 0,0, "r")
rookWhite = Piece(pygame.image.load("pieces/white-rook.png"), 7,7, "R")
#piece base positions
# piece_positions = [
#     (0, 4),  # kingBlack
#     (7, 4),  # kingWhite
#     (1, 2),  # bishopBlack
#     (6, 5),  # bishopWhite
#     (1, 6),  # pawnBlack
#     (6, 1),  # pawnWhite
#     (0, 0),  # rookBlack
#     (7, 7)   # rookWhite
# ]

#hasmap for each piece to use when finding movement
# startPos_to_piece = {(0,4):"k", (7,4):"K", (1,2):"b", (6,5): "B", (1,6) : "p", (6,1): "P", (0,0): "r", (7,7): "R"}


#list of pieces were doing
pieces = [kingBlack, kingWhite, bishopBlack,bishopWhite, pawnBlack,pawnWhite, rookBlack, rookWhite]

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess Board")
clock = pygame.time.Clock()

#board function draw
def draw_board():
    screen.fill(WHITE)
    for row in range(ROWS):
        for col in range(COLS):
            color = BLUE if (row + col) % 2 else WHITE
            pygame.draw.rect(screen, color, (col * 80, row * 80, 80, 80))

def draw_pieces():
    for piece in pieces:
        piece.draw(screen)


running = True
while running:
    clock.tick(60)  # 60 FPS
    draw_board()
    draw_pieces()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        #if the mouse is clicked
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            #iterate through all pieces to find which piece is clicked
            for piece in pieces:
                #function that returns name of piece clicked
                clicked_piece = piece.clicked(mouse_pos, piece) 
                if clicked_piece:
                    pos_moves = piece.get_pos_moves()
                    #loop to remove moves possible moves where you capture your own piece
                    for each in pieces:
                        if (each.name.islower() and piece.name.islower()) or (each.name.isupper() and each.name.isupper()):
                            if (each.row,each.col) in pos_moves:
                                pos_moves.remove((each.row,each.col))
                    
                    for row, col in pos_moves:
                        # Create a transparent surface
                        circle_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
                        pygame.draw.circle(circle_surf, (255, 0, 0, 100), (80 // 2, 80 // 2), 80 // 3)
                        screen.blit(circle_surf, (col * 80, row * 80))
                            
    
    
    pygame.display.flip()

pygame.quit()
sys.exit()
