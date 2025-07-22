import pygame
import time
import sys
import os
from chess_board import Board
from chess_gui import ChessGUI
from chess_piece import Color
from chess_position import Position, Move
from engine_wrapper import EngineWrapper

def main():
    # init the gooey
    gui = ChessGUI(window_size=640)
    if not gui.initialize():
        print("Failed to initialize GUI")
        return
    
    # init the board
    board = Board()  # Standard starting position
    
    # init the engine
    engine = EngineWrapper(depth=4)  # Search 4 moves ahead
    
    # game state tracking
    game_over = False
    
    # main game loop
    running = True
    while running and gui.is_open():
        # draw the board
        gui.board = board  # update the gooey's board reference
        gui.move_generator.board = board  # update the move generator's board reference
        gui.draw_board()
        
        # process events even if game is over (to allow window closing)
        if game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                # also check for ESC key press
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    print("ESC key pressed - closing window")
                    running = False
            pygame.time.delay(100)
            continue
            
        # check for game end conditions
        from chess_move_generator import MoveGenerator
        move_generator = MoveGenerator(board)
        legal_moves = move_generator.generate_legal_moves()
        
        if not legal_moves:
            game_over = True
            if move_generator.is_in_check():
                winner = "Black" if board.get_side_to_move() == Color.WHITE else "White"
                status_message = f"checkmate {winner} wins"
                print(status_message)
                gui.set_game_status(status_message)
            else:
                status_message = "stalemate lmaoo the game is a draw"
                print(status_message)
                gui.set_game_status(status_message)
            
            # redraw the board with the status message
            gui.draw_board()
            continue
        
        if board.get_side_to_move() == Color.WHITE:
            # player's turn (white)
            player_move = gui.process_events()
            
            if not gui.is_open():
                # window was closed
                break
            
            # only process the move if it's valid (both from and to positions are valid)
            if player_move.from_pos.is_valid() and player_move.to_pos.is_valid():
                # check if this is a capture
                target_piece = board.get_piece(player_move.to_pos)
                if not target_piece.is_empty():
                    print(f"Capturing piece: {target_piece.to_char()} at {player_move.to_pos.to_algebraic()}")
                
                # make the player's move
                move_generator = MoveGenerator(board)
                move_success = move_generator.make_move_on_board(board, player_move)
                if move_success:
                    print(f"You moved: {player_move.to_algebraic()}")
                    
                    # check if this move resulted in checkmate or stalemate
                    move_generator = MoveGenerator(board)
                    opponent_moves = move_generator.generate_legal_moves()
                    if not opponent_moves:
                        if move_generator.is_in_check():
                            status_message = "checkmate! white wins"
                            print(status_message)
                            gui.set_game_status(status_message)
                            game_over = True
                        else:
                            status_message = "stalemate! the game is a draw"
                            print(status_message)
                            gui.set_game_status(status_message)
                            game_over = True
                else:
                    print(f"Invalid move: {player_move.to_algebraic()}")
        else:
            # engine's turn (black)
            print("Engine is thinking...")
            start_time = time.time()
            
            # get the best move from the engine
            engine_move = engine.get_best_move(board)
            
            end_time = time.time()
            elapsed = end_time - start_time
            
            if engine_move and engine_move.from_pos.is_valid() and engine_move.to_pos.is_valid():
                print(f"Engine move: {engine_move.to_algebraic()} (in {elapsed:.2f} seconds, {engine.get_nodes_searched()} nodes)")
                
                # check if this is a capture
                target_piece = board.get_piece(engine_move.to_pos)
                if not target_piece.is_empty():
                    print(f"Engine captures: {target_piece.to_char()} at {engine_move.to_pos.to_algebraic()}")
                
                # make the engine's move
                move_generator = MoveGenerator(board)
                move_generator.make_move_on_board(board, engine_move)
                
                # check if this move resulted in checkmate or stalemate
                move_generator = MoveGenerator(board)
                player_moves = move_generator.generate_legal_moves()
                if not player_moves:
                    if move_generator.is_in_check():
                        status_message = "checkmate! black wins"
                        print(status_message)
                        gui.set_game_status(status_message)
                        game_over = True
                    else:
                        status_message = "stalemate! the game is a draw"
                        print(status_message)
                        gui.set_game_status(status_message)
                        game_over = True
            else:
                print("engine couldn't find a move!")
        
        # small delay to prevent hogging the CPU
        pygame.time.delay(50)
    
    # clean up
    gui.close()
    print("Game ended")

if __name__ == "__main__":
    main()