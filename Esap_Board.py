import pygame
from Esap_piece import *
class Board:
    def __init__(self):
        self.pieces = [["." for _ in range(8)] for _ in range(8)]

    def _setup_initial_position(self):
        # Set up pieces
        #white king
        self.pieces[3][1] = "K"
        #white pawn
        self.pieces[0][6] = "P"
        #white rook
        self.pieces[3][4] = "R"
        #white bishop
        self.pieces[1][7] = "B"

        #black king
        self.pieces[7][2] = "k"
        #black pawn
        self.pieces[5][7] = "p"
        #black rook
        self.pieces[7][7] = "r"
        #black bishop
        self.pieces[6][4] = "b"

test = Board()
test._setup_initial_position()