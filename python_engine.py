import time
import sys
from datetime import datetime
from typing import List, Optional

class Engine:
    def __init__(self, max_depth=5):
        self.max_depth = max_depth
        self.nodes_searched = 0
        self.start_time = 0
        self.evaluator = Evaluator()
    
    def reset_nodes_searched(self):
        """Reset the node counter"""
        self.nodes_searched = 0
    
    def get_best_move(self, board):
        """
        Find the best move for the current position using minimax with alpha-beta pruning
        
        Args:
            board: The current board position
            
        Returns:
            The best move found
        """
        # Reset the node counter
        self.reset_nodes_searched()
        
        # Start the timer
        self.start_time = time.time()
        
        # Get all legal moves
        legal_moves = board.generate_legal_moves()
        
        if not legal_moves:
            return None  # No legal moves
        
        best_move = legal_moves[0]
        
        # Set initial best score based on side to move
        if board.get_side_to_move() == Color.WHITE:
            best_score = float('-inf')
        else:
            best_score = float('inf')
        
        # Evaluate each move
        for move in legal_moves:
            # Make a copy of the board
            test_board = board.copy()
            
            # Make the move
            test_board.make_move(move)
            
            # Evaluate the position using minimax
            score = self.minimax(
                test_board, 
                self.max_depth - 1,
                float('-inf'),
                float('inf'),
                board.get_side_to_move() != Color.WHITE
            )
            
            # Update the best move
            if ((board.get_side_to_move() == Color.WHITE and score > best_score) or
                (board.get_side_to_move() == Color.BLACK and score < best_score)):
                best_score = score
                best_move = move
        
        # Calculate search time
        end_time = time.time()
        duration = int((end_time - self.start_time) * 1000)  # Convert to milliseconds
        
        print(f"Nodes searched: {self.nodes_searched}")
        print(f"Time taken: {duration} ms")
        print(f"Best move: {best_move.to_algebraic()} with score: {best_score}")
        
        return best_move
    
    def minimax(self, board, depth, alpha, beta, maximizing_player):
        """
        Minimax algorithm with alpha-beta pruning
        
        Args:
            board: The current board position
            depth: Current search depth
            alpha: Alpha value for pruning
            beta: Beta value for pruning
            maximizing_player: True if maximizing, False if minimizing
            
        Returns:
            The evaluation score of the position
        """
        # Increment the node counter
        self.nodes_searched += 1
        
        # Base case: leaf node or terminal position
        if depth == 0:
            return self.evaluator.evaluate(board)
        
        legal_moves = board.generate_legal_moves()
        
        # Check for checkmate or stalemate
        if not legal_moves:
            if board.is_in_check():
                # Checkmate (worst possible score, but adjusted for depth)
                return -20000 + (self.max_depth - depth) if maximizing_player else 20000 - (self.max_depth - depth)
            else:
                # Stalemate (draw)
                return 0
        
        if maximizing_player:
            max_eval = float('-inf')
            
            for move in legal_moves:
                # Make a copy of the board
                test_board = board.copy()
                
                # Make the move
                test_board.make_move(move)
                
                # Recursively evaluate the position
                eval_score = self.minimax(test_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                
                # Alpha-beta pruning
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            return max_eval
        else:
            min_eval = float('inf')
            
            for move in legal_moves:
                # Make a copy of the board
                test_board = board.copy()
                
                # Make the move
                test_board.make_move(move)
                
                # Recursively evaluate the position
                eval_score = self.minimax(test_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                
                # Alpha-beta pruning
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval


# Assuming these classes exist or will be defined elsewhere
class Color:
    WHITE = 0
    BLACK = 1


# Placeholder for the Evaluator class that would be used by the Engine
class Evaluator:
    def evaluate(self, board):
        """
        Evaluate the current board position
        
        Args:
            board: The board to evaluate
            
        Returns:
            A score for the position (positive is good for white, negative is good for black)
        """
        
        return 0  # Replace wit real logic lol #TODO
