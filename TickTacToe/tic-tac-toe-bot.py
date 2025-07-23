import pygame
import sys
import math
import random
import time

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 300, 300
LINE_WIDTH = 2
BOARD_ROWS, BOARD_COLS = 3, 3
SQUARE_SIZE = WIDTH // BOARD_COLS
CIRCLE_RADIUS = SQUARE_SIZE // 3
CIRCLE_WIDTH = 1
CROSS_WIDTH = 2
SPACE = SQUARE_SIZE // 4

# Colors
BG_COLOR = (255, 255, 255)
LINE_COLOR = (0, 0, 0)
CIRCLE_COLOR = (0, 0, 0)
CROSS_COLOR = (0, 0, 0)
TEXT_COLOR = (0, 0, 0)

# Game variables
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Tic Tac Toe')
font = pygame.font.SysFont('Arial', 20)

class Board:
    def __init__(self):
        self.squares = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        self.marked_squares = 0
    
    def final_state(self):
        for col in range(BOARD_COLS):
            if self.squares[0][col] == self.squares[1][col] == self.squares[2][col] != None:
                return self.squares[0][col]
        for row in range(BOARD_ROWS):
            if self.squares[row][0] == self.squares[row][1] == self.squares[row][2] != None:
                return self.squares[row][0]
        if self.squares[0][0] == self.squares[1][1] == self.squares[2][2] != None:
            return self.squares[0][0]
        if self.squares[2][0] == self.squares[1][1] == self.squares[0][2] != None:
            return self.squares[2][0]
        if self.marked_squares == 9:
            return 0
        return None
    
    def mark_square(self, row, col, player):
        self.squares[row][col] = player
        self.marked_squares += 1
    
    def empty_square(self, row, col):
        return self.squares[row][col] is None
    
    def get_empty_squares(self):
        empty_squares = []
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                if self.empty_square(row, col):
                    empty_squares.append((row, col))
        return empty_squares

class AI:
    def __init__(self, level=1, player=2):
        self.level = level
        self.player = player
    
    def random_move(self, board):
        empty_squares = board.get_empty_squares()
        idx = random.randrange(0, len(empty_squares))
        return empty_squares[idx]
    
    def minimax(self, board, maximizing):
        case = board.final_state()
        if case == 1:
            return -1, None
        if case == 2:
            return 1, None
        if case == 0:
            return 0, None
        
        if maximizing:
            max_eval = -math.inf
            best_move = None
            for (row, col) in board.get_empty_squares():
                board.mark_square(row, col, self.player)
                eval, _ = self.minimax(board, False)
                board.squares[row][col] = None
                board.marked_squares -= 1
                if eval > max_eval:
                    max_eval = eval
                    best_move = (row, col)
            return max_eval, best_move
        else:
            min_eval = math.inf
            best_move = None
            for (row, col) in board.get_empty_squares():
                board.mark_square(row, col, 1)
                eval, _ = self.minimax(board, True)
                board.squares[row][col] = None
                board.marked_squares -= 1
                if eval < min_eval:
                    min_eval = eval
                    best_move = (row, col)
            return min_eval, best_move
    
    def eval(self, board):
        if self.level == 0:
            return self.random_move(board)
        else:
            eval, move = self.minimax(board, True)
            return move

class RandomAI:
    def __init__(self, player=1):
        self.player = player

    def eval(self, board):
        empty_squares = board.get_empty_squares()
        idx = random.randrange(0, len(empty_squares))
        return empty_squares[idx]

class Game:
    def __init__(self):
        self.board = Board()
        self.random_ai = RandomAI()
        self.ai = AI()
        self.player = 1  # 1 is random AI, 2 is optimized AI
        self.running = True
        self.show_lines()
        self.game_over = False
        self.winner = None
    
    def show_lines(self):
        screen.fill(BG_COLOR)
        pygame.draw.line(screen, LINE_COLOR, (SQUARE_SIZE, 0), (SQUARE_SIZE, HEIGHT), LINE_WIDTH)
        pygame.draw.line(screen, LINE_COLOR, (WIDTH - SQUARE_SIZE, 0), (WIDTH - SQUARE_SIZE, HEIGHT), LINE_WIDTH)
        pygame.draw.line(screen, LINE_COLOR, (0, SQUARE_SIZE), (WIDTH, SQUARE_SIZE), LINE_WIDTH)
        pygame.draw.line(screen, LINE_COLOR, (0, HEIGHT - SQUARE_SIZE), (WIDTH, HEIGHT - SQUARE_SIZE), LINE_WIDTH)
    
    def draw_figures(self):
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                if self.board.squares[row][col] == 1:
                    start_desc = (col * SQUARE_SIZE + SPACE, row * SQUARE_SIZE + SPACE)
                    end_desc = (col * SQUARE_SIZE + SQUARE_SIZE - SPACE, row * SQUARE_SIZE + SQUARE_SIZE - SPACE)
                    pygame.draw.line(screen, CROSS_COLOR, start_desc, end_desc, CROSS_WIDTH)
                    start_asc = (col * SQUARE_SIZE + SPACE, row * SQUARE_SIZE + SQUARE_SIZE - SPACE)
                    end_asc = (col * SQUARE_SIZE + SQUARE_SIZE - SPACE, row * SQUARE_SIZE + SPACE)
                    pygame.draw.line(screen, CROSS_COLOR, start_asc, end_asc, CROSS_WIDTH)
                elif self.board.squares[row][col] == 2:
                    center = (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2)
                    pygame.draw.circle(screen, CIRCLE_COLOR, center, CIRCLE_RADIUS, CIRCLE_WIDTH)
    
    def make_move(self, row, col):
        if self.board.empty_square(row, col) and not self.game_over:
            self.board.mark_square(row, col, self.player)
            self.check_game_over()
            self.player = 2 if self.player == 1 else 1
            return True
        return False
    
    def check_game_over(self):
        self.winner = self.board.final_state()
        if self.winner is not None:
            self.game_over = True
    
    def reset(self):
        self.__init__()
    
    def ai_move(self):
        if not self.game_over:
            if self.player == 1:
                row, col = self.random_ai.eval(self.board)
            else:
                row, col = self.ai.eval(self.board)
            self.make_move(row, col)
    
    def show_game_over_message(self):
        if self.winner == 1:
            text = 'Random AI Wins!'
        elif self.winner == 2:
            text = 'Optimized AI Wins!'
        else:
            text = 'Draw!'
        pygame.draw.rect(screen, BG_COLOR, (WIDTH//4, HEIGHT//3, WIDTH//2, HEIGHT//3))
        text_surface = font.render(text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=(WIDTH//2, HEIGHT//2 - 10))
        screen.blit(text_surface, text_rect)
        restart_text = font.render('Press R to Restart', True, TEXT_COLOR)
        restart_rect = restart_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 10))
        screen.blit(restart_text, restart_rect)

def main():
    game = Game()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.reset()
        
        if not game.game_over:
            game.ai_move()
            pygame.display.update()
            time.sleep(0.2)
        
        game.show_lines()
        game.draw_figures()
        if game.game_over:
            game.show_game_over_message()
        
        pygame.display.update()

if __name__ == '__main__':
    main()
