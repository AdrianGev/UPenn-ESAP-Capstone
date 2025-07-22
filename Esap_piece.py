import pygame
class Piece:
    def __init__(self, image, row, col, name):
        self.image = pygame.transform.scale(image, (80, 80))
        self.row = row
        self.col = col
        self.name = name  # for example "k", "p", "B", etc.

    def draw(self, screen):
        x = self.col * 80
        y = self.row * 80
        screen.blit(self.image, (x, y))

    def move(self, row, col):
        self.row = row
        self.col = col

    def get_pos(self):
        return (self.row, self.col)
    
    def get_pos_moves(self):
        pos_moves = []
        # Pawns
        if self.name == "P":
            if self.row > 0:
                pos_moves.append((self.row - 1, self.col))
                if self.col > 0:
                    pos_moves.append((self.row - 1, self.col - 1))
                if self.col < 7:
                    pos_moves.append((self.row - 1, self.col + 1))
            return pos_moves

        elif self.name == "p":
            if self.row < 7:
                pos_moves.append((self.row + 1, self.col))
                if self.col > 0:
                    pos_moves.append((self.row + 1, self.col - 1))
                if self.col < 7:
                    pos_moves.append((self.row + 1, self.col + 1))
            return pos_moves

        # Bishops
        if self.name.lower() == "b":
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dr, dc in directions:
                for i in range(1, 8):
                    new_row = self.row + dr * i
                    new_col = self.col + dc * i
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        pos_moves.append((new_row, new_col))
                    else:
                        break

        # Rooks
        elif self.name.lower() == "r":
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in directions:
                for i in range(1, 8):
                    new_row = self.row + dr * i
                    new_col = self.col + dc * i
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        pos_moves.append((new_row, new_col))
                    else:
                        break

        # king
        elif self.name.lower() == "k":
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    new_row = self.row + dr
                    new_col = self.col + dc
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        pos_moves.append((new_row, new_col))

        return pos_moves
    #check if piece is clicked
    def clicked(self,mouse_pos, piece):
        x, y = mouse_pos
        col = x // 80
        row = y // 80

        
        if piece.row == row and piece.col == col:
            return piece  

        return None  




