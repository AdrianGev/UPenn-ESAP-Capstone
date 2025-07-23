"""
Chess check detection and move filtering utilities.
This module provides functions to detect check and filter moves that don't address check.
"""

def is_square_attacked(row, col, attacking_color, pieces):
    """
    Check if a square is under attack by any piece of the specified color.
    
    Args:
        row: Row of the square to check
        col: Column of the square to check
        attacking_color: 'white' or 'black' - the color of the attacking pieces
        pieces: List of all pieces on the board
        
    Returns:
        bool: True if the square is under attack, False otherwise
    """
    # Determine if we're looking for uppercase (white) or lowercase (black) pieces
    is_attacker_uppercase = (attacking_color == 'white')
    
    # Check attacks from all pieces of the attacking color
    for piece in pieces:
        # Skip pieces of the wrong color
        if piece.name.isupper() != is_attacker_uppercase:
            continue
            
        # Get all possible moves for this piece
        if piece.name.lower() in ['b', 'r', 'q']:
            # For sliding pieces, we need to generate moves specially
            moves = []
            
            # Define directions based on piece type
            if piece.name.lower() == 'b':
                directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]  # Diagonals for bishop
            elif piece.name.lower() == 'r':
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Horizontals and verticals for rook
            else:  # Queen
                directions = [(-1, -1), (-1, 1), (1, -1), (1, 1),  # Diagonals
                             (-1, 0), (1, 0), (0, -1), (0, 1)]  # Horizontals and verticals
            
            # For each direction, add moves until we hit a piece or the edge of the board
            for dr, dc in directions:
                for i in range(1, 8):  # Maximum 7 squares in any direction
                    new_row = piece.row + dr * i
                    new_col = piece.col + dc * i
                    
                    # Check if we're still on the board
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        # If this is the square we're checking, it's under attack
                        if new_row == row and new_col == col:
                            return True
                            
                        # Check if there's a piece at this position
                        piece_at_pos = None
                        for other_piece in pieces:
                            if other_piece.row == new_row and other_piece.col == new_col:
                                piece_at_pos = other_piece
                                break
                        
                        if piece_at_pos:
                            # If we hit a piece, we can't go further in this direction
                            # But if this is the square we're checking, it's under attack
                            if new_row == row and new_col == col:
                                return True
                            break
                    else:
                        # Off the board, stop looking in this direction
                        break
        else:
            # For non-sliding pieces, use the original move generation
            moves = piece.get_pos_moves()
            
            # Special handling for pawns (they only attack diagonally)
            if piece.name.lower() == 'p':
                # Clear the moves list and only add diagonal attacks
                pawn_attacks = []
                
                # For white pawns (uppercase)
                if piece.name.isupper():
                    if piece.row > 0:
                        if piece.col > 0:
                            pawn_attacks.append((piece.row - 1, piece.col - 1))
                        if piece.col < 7:
                            pawn_attacks.append((piece.row - 1, piece.col + 1))
                # For black pawns (lowercase)
                else:
                    if piece.row < 7:
                        if piece.col > 0:
                            pawn_attacks.append((piece.row + 1, piece.col - 1))
                        if piece.col < 7:
                            pawn_attacks.append((piece.row + 1, piece.col + 1))
                
                moves = pawn_attacks
            
            # Check if the target square is in the moves
            if (row, col) in moves:
                return True
    
    # If we get here, the square is not under attack
    return False

def is_in_check(king_color, pieces):
    """
    Check if the king of the specified color is in check.
    
    Args:
        king_color: 'white' or 'black' - the color of the king to check
        pieces: List of all pieces on the board
        
    Returns:
        bool: True if the king is in check, False otherwise
    """
    # Find the king
    king = None
    king_name = 'K' if king_color == 'white' else 'k'
    
    for piece in pieces:
        if piece.name == king_name:
            king = piece
            break
    
    if not king:
        return False  # No king found (shouldn't happen in a real game)
    
    # Check if the king's square is under attack by the opposite color
    attacking_color = 'black' if king_color == 'white' else 'white'
    return is_square_attacked(king.row, king.col, attacking_color, pieces)

def would_move_cause_check(piece, new_row, new_col, pieces):
    """
    Check if moving a piece to a new position would cause the player's king to be in check.
    
    Args:
        piece: The piece to move
        new_row: The row to move to
        new_col: The column to move to
        pieces: List of all pieces on the board
        
    Returns:
        bool: True if the move would cause check, False otherwise
    """
    # Determine the color of the player's king
    king_color = 'white' if piece.name.isupper() else 'black'
    
    # Save the original position of the piece
    original_row, original_col = piece.row, piece.col
    
    # Check if there's a piece to capture at the target position
    piece_to_capture = None
    for other_piece in pieces:
        if other_piece.row == new_row and other_piece.col == new_col:
            piece_to_capture = other_piece
            break
    
    # Temporarily remove the captured piece from the list
    if piece_to_capture:
        pieces.remove(piece_to_capture)
    
    # Temporarily move the piece
    piece.row, piece.col = new_row, new_col
    
    # Check if the king is in check after the move
    in_check = is_in_check(king_color, pieces)
    
    # Restore the original position
    piece.row, piece.col = original_row, original_col
    
    # Restore the captured piece if there was one
    if piece_to_capture:
        pieces.append(piece_to_capture)
    
    return in_check

def filter_moves_for_check(piece, valid_moves, pieces):
    """
    Filter out moves that would leave or put the player's king in check.
    
    Args:
        piece: The piece to move
        valid_moves: List of valid moves for the piece
        pieces: List of all pieces on the board
        
    Returns:
        list: Filtered list of valid moves that don't cause check
    """
    filtered_moves = []
    
    for move_row, move_col in valid_moves:
        if not would_move_cause_check(piece, move_row, move_col, pieces):
            filtered_moves.append((move_row, move_col))
    
    return filtered_moves

def get_legal_moves_in_check(king_color, pieces):
    """
    Get all legal moves for a player in check.
    
    Args:
        king_color: 'white' or 'black' - the color of the king in check
        pieces: List of all pieces on the board
        
    Returns:
        dict: Dictionary mapping pieces to their legal moves that address the check
    """
    legal_moves = {}
    
    # Determine if we're looking for uppercase (white) or lowercase (black) pieces
    is_player_uppercase = (king_color == 'white')
    
    # Check moves for all pieces of the player's color
    for piece in pieces:
        # Skip pieces of the wrong color
        if piece.name.isupper() != is_player_uppercase:
            continue
            
        # Get all possible moves for this piece
        if piece.name.lower() in ['b', 'r', 'q']:
            # For sliding pieces, generate moves specially
            moves = []
            
            # Define directions based on piece type
            if piece.name.lower() == 'b':
                directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]  # Diagonals for bishop
            elif piece.name.lower() == 'r':
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Horizontals and verticals for rook
            else:  # Queen
                directions = [(-1, -1), (-1, 1), (1, -1), (1, 1),  # Diagonals
                             (-1, 0), (1, 0), (0, -1), (0, 1)]  # Horizontals and verticals
            
            # For each direction, add moves until we hit a piece or the edge of the board
            for dr, dc in directions:
                for i in range(1, 8):  # Maximum 7 squares in any direction
                    new_row = piece.row + dr * i
                    new_col = piece.col + dc * i
                    
                    # Check if we're still on the board
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        # Check if there's a piece at this position
                        piece_at_pos = None
                        for other_piece in pieces:
                            if other_piece.row == new_row and other_piece.col == new_col:
                                piece_at_pos = other_piece
                                break
                        
                        if piece_at_pos:
                            # If it's an opponent's piece, we can capture it
                            if ((piece.name.islower() and piece_at_pos.name.isupper()) or 
                                (piece.name.isupper() and piece_at_pos.name.islower())):
                                moves.append((new_row, new_col))
                            # Stop looking in this direction after finding any piece
                            break
                        else:
                            # Empty square, add as valid move
                            moves.append((new_row, new_col))
                    else:
                        # Off the board, stop looking in this direction
                        break
        else:
            # For non-sliding pieces, use the original move generation
            moves = piece.get_pos_moves()
            
            # Special handling for pawns
            if piece.name.lower() == 'p':
                moves_to_remove = []
                
                for move_row, move_col in moves:
                    # Check if it's a diagonal move
                    is_diagonal = move_col != piece.col
                    
                    if is_diagonal:
                        # For diagonal moves, check if there's an opponent's piece to capture
                        can_capture = False
                        for other_piece in pieces:
                            if (other_piece.row == move_row and other_piece.col == move_col and
                                ((piece.name.islower() and other_piece.name.isupper()) or
                                 (piece.name.isupper() and other_piece.name.islower()))):
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
                        if abs(move_row - piece.row) == 2:  # It's a two-square move
                            # Check the square in between
                            between_row = (piece.row + move_row) // 2
                            for other_piece in pieces:
                                if other_piece.row == between_row and other_piece.col == piece.col:
                                    moves_to_remove.append((move_row, move_col))
                                    break
                
                # Remove invalid pawn moves
                for move in moves_to_remove:
                    if move in moves:
                        moves.remove(move)
            else:
                # For other non-sliding pieces (kings), remove moves onto own pieces
                moves_to_remove = []
                for move_row, move_col in moves:
                    for other_piece in pieces:
                        if (other_piece.row == move_row and other_piece.col == move_col and
                            ((piece.name.islower() and other_piece.name.islower()) or
                             (piece.name.isupper() and other_piece.name.isupper()))):
                            moves_to_remove.append((move_row, move_col))
                            break
                
                # Remove invalid moves
                for move in moves_to_remove:
                    if move in moves:
                        moves.remove(move)
        
        # Filter moves that would leave the king in check
        filtered_moves = filter_moves_for_check(piece, moves, pieces)
        
        if filtered_moves:
            legal_moves[piece] = filtered_moves
    
    return legal_moves
