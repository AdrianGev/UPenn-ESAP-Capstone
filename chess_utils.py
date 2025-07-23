def blocked_from(piece, blocking_piece):
    """
    Determine if and how blocking_piece is obstructing piece's path.
    
    Args:
        piece: The piece being blocked
        blocking_piece: The piece potentially blocking
        
    Returns:
        None if not blocking
        Direction tuple (dr, dc) if blocking in that direction
    """
    # If pieces are not on the same diagonal, row, or column, there's no blocking
    row_diff = blocking_piece.row - piece.row
    col_diff = blocking_piece.col - piece.col
    
    # Check if on same row
    if row_diff == 0 and col_diff != 0:
        # Return horizontal direction (-1 for left, 1 for right)
        return (0, 1 if col_diff > 0 else -1)
    
    # Check if on same column
    elif col_diff == 0 and row_diff != 0:
        # Return vertical direction (-1 for up, 1 for down)
        return (1 if row_diff > 0 else -1, 0)
    
    # Check if on same diagonal
    elif abs(row_diff) == abs(col_diff):
        # Return diagonal direction
        return (1 if row_diff > 0 else -1, 1 if col_diff > 0 else -1)
    
    # Not blocking
    return None

def get_blocked_directions(piece, all_pieces):
    """
    Get all directions that are blocked for a piece.
    
    Args:
        piece: The piece to check for blocked directions
        all_pieces: List of all pieces on the board
        
    Returns:
        List of direction tuples (dr, dc) that are blocked
    """
    blocked_directions = []
    
    for other_piece in all_pieces:
        # Skip if it's the same piece
        if piece == other_piece:
            continue
            
        # Check if other piece is blocking
        direction = blocked_from(piece, other_piece)
        if direction:
            blocked_directions.append(direction)
    
    return blocked_directions
