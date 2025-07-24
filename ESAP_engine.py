from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Tuple, Callable, Optional, Set, Union
import copy
import ESAP_minimax_math

# Constants
BOARD_SIZE = 8
EMPTY_SQUARE = "--"

class PieceColor(Enum):
    WHITE = "w"
    BLACK = "b"
    EMPTY = "-"
    
    @property
    def opposite(self) -> 'PieceColor':
        if self == PieceColor.WHITE:
            return PieceColor.BLACK
        elif self == PieceColor.BLACK:
            return PieceColor.WHITE
        return PieceColor.EMPTY

class PieceType(Enum):
    PAWN = "p"
    ROOK = "R"
    KNIGHT = "N"
    BISHOP = "B"
    QUEEN = "Q"
    KING = "K"
    EMPTY = "-"

# Position class for better coordinate handling
@dataclass(frozen=True)
class Position:
    row: int
    col: int
    
    def __add__(self, other: Position) -> Position:
        return Position(self.row + other.row, self.col + other.col)
    
    def __mul__(self, scalar: int) -> Position:
        return Position(self.row * scalar, self.col * scalar)
    
    def is_valid(self) -> bool:
        return 0 <= self.row < BOARD_SIZE and 0 <= self.col < BOARD_SIZE
        
    @classmethod
    def from_chess_notation(cls, notation: str) -> Position:
        """Convert chess notation (e.g., 'e4') to a Position object"""
        file_to_col = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
        rank_to_row = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
        
        if len(notation) != 2:
            raise ValueError(f"Invalid chess notation: {notation}")
        
        file, rank = notation[0].lower(), notation[1]
        if file not in file_to_col or rank not in rank_to_row:
            raise ValueError(f"Invalid chess notation: {notation}")
            
        return cls(rank_to_row[rank], file_to_col[file])
    
    def to_chess_notation(self) -> str:
        """Convert Position to chess notation (e.g., 'e4')"""
        col_to_file = {0: "a", 1: "b", 2: "c", 3: "d", 4: "e", 5: "f", 6: "g", 7: "h"}
        row_to_rank = {7: "1", 6: "2", 5: "3", 4: "4", 3: "5", 2: "6", 1: "7", 0: "8"}
        
        return col_to_file[self.col] + row_to_rank[self.row]

# Piece class hierarchy
class Piece:
    def __init__(self, color: PieceColor, position: Position):
        self.color = color
        self.position = position
        self.has_moved = False
        
    @property
    def piece_type(self) -> PieceType:
        raise NotImplementedError("Subclasses must implement piece_type")
    
    @property
    def notation(self) -> str:
        """Return the two-character notation used in the board representation"""
        return f"{self.color.value}{self.piece_type.value}"
    
    def get_possible_moves(self, board: 'ChessBoard') -> List['ChessMove']:
        """Get all possible moves for this piece without considering checks"""
        raise NotImplementedError("Subclasses must implement get_possible_moves")

# Move class to represent a chess move
@dataclass
class ChessMove:
    start_pos: Position
    end_pos: Position
    piece_moved: str
    piece_captured: str = EMPTY_SQUARE
    is_pawn_promotion: bool = False
    is_castle_move: bool = False
    is_enpassant_move: bool = False
    
    @property
    def move_id(self) -> int:
        """Unique identifier for the move"""
        return (self.start_pos.row * 1000 + self.start_pos.col * 100 + 
                self.end_pos.row * 10 + self.end_pos.col)
    
    def __eq__(self, other):
        if isinstance(other, ChessMove):
            return self.move_id == other.move_id
        return False
    
    def get_chess_notation(self) -> str:
        """Return the move in chess notation (e.g., 'e2e4')"""
        return f"{self.start_pos.to_chess_notation()}{self.end_pos.to_chess_notation()}"
    
    def __str__(self) -> str:
        # Handle castling notation
        if self.is_castle_move:
            return "O-O" if self.end_pos.col == 6 else "O-O-O"
        
        end_square = self.end_pos.to_chess_notation()
        
        # Pawn move notation
        if self.piece_moved[1] == PieceType.PAWN.value:
            if self.piece_captured != EMPTY_SQUARE:
                file_from = self.start_pos.to_chess_notation()[0]
                return f"{file_from}x{end_square}"
            return end_square
        
        # Piece move notation
        move_string = self.piece_moved[1]
        if self.piece_captured != EMPTY_SQUARE:
            move_string += "x"
        return move_string + end_square

# Castle rights class
@dataclass
class CastleRights:
    white_kingside: bool = True
    white_queenside: bool = True
    black_kingside: bool = True
    black_queenside: bool = True

# Main chess board class
class ChessBoard:
    def __init__(self):
        # Initialize the board with the starting position
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            [EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE],
            [EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE],
            [EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE],
            [EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]
        
    def get_piece(self, pos: Position) -> str:
        """Get the piece at the specified position"""
        if not pos.is_valid():
            return EMPTY_SQUARE
        return self.board[pos.row][pos.col]
    
    def set_piece(self, pos: Position, piece: str) -> None:
        """Set the piece at the specified position"""
        if pos.is_valid():
            self.board[pos.row][pos.col] = piece
    
    def is_empty(self, pos: Position) -> bool:
        """Check if the position is empty"""
        return self.get_piece(pos) == EMPTY_SQUARE
    
    def get_piece_color(self, pos: Position) -> PieceColor:
        """Get the color of the piece at the specified position"""
        piece = self.get_piece(pos)
        if piece == EMPTY_SQUARE:
            return PieceColor.EMPTY
        return PieceColor.WHITE if piece[0] == PieceColor.WHITE.value else PieceColor.BLACK
            
    def __getitem__(self, row):
        """Make the ChessBoard subscriptable with board[row][col]"""
        return self.board[row]
        
    def __setitem__(self, row, value):
        """Allow setting rows with board[row] = value"""
        self.board[row] = value

# Game state class
class GameState:
    def __init__(self):
        self.board = ChessBoard()
        self.white_to_move = True
        self.move_log = []
        self.white_king_position = Position(7, 4)
        self.black_king_position = Position(0, 4)
        self.in_check = False
        self.checkmate = False
        self.stalemate = False
        self.enpassant_target = ()
        self.enpassant_log = [self.enpassant_target]
        self.pins = []
        self.checks = []
        
        # Map piece types to their move generation methods
        self.moveFunctions = {
            'p': self.getPawnMoves,
            'R': self.getRookMoves,
            'N': self.getKnightMoves,
            'B': self.getBishopMoves,
            'Q': self.getQueenMoves,
            'K': self.getKingMoves
        }
        self.castle_rights = castleRight(True, True, True, True)
        self.castle_rights_log = [castleRight(self.castle_rights.wks, self.castle_rights.wqs,
                                            self.castle_rights.bks, self.castle_rights.bqs)]


    def makeMove(self, move):
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.move_log.append(move)
        self.white_to_move = not self.white_to_move
        if move.pieceMoved == "wK":
            self.white_king_position = Position(move.endRow, move.endCol)
        if move.pieceMoved == "bK":
            self.black_king_position = Position(move.endRow, move.endCol)
        # promotion
        if move.isPawnPromotion:
            piecePromote = 'Q' #input("Promote R, N, B, Q: ")
            #piecePromote = piecePromote.upper()
            self.board[move.endRow][move.endCol] = move.pieceMoved[0] + piecePromote
        # Enpassant Move
        if move.isEnpassantMove:
            self.board[move.startRow][move.endCol] = "--"  # capturing the pawn
        # EnpassantPossible update
        if move.pieceMoved[1] == 'p' and (abs(move.startRow - move.endRow) == 2):  # only 2 squares pawn move
            self.enpassant_target = ((move.startRow + move.endRow) // 2, move.endCol)
        else:
            self.enpassant_target = ()  # not en passant move
        self.enpassant_log.append(self.enpassant_target)
        # update castling right - whenever king move or rook move
        self.updateCastleRight(move)
        self.castle_rights_log.append(castleRight(self.castle_rights.wks, self.castle_rights.wqs,
                                                self.castle_rights.bks, self.castle_rights.bqs))
        # castle move
        if move.isCastleMove:
            if move.endCol-move.startCol == 2:
                self.board[move.endRow][move.endCol-1] = self.board[move.endRow][move.endCol+1]
                self.board[move.endRow][move.endCol+1] = "--"
            else:
                self.board[move.endRow][move.endCol+1] = self.board[move.endRow][move.endCol-2]
                self.board[move.endRow][move.endCol-2] = "--"

    def undoMove(self):
        if len(self.move_log) != 0:
            move = self.move_log.pop()
            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured
            self.white_to_move = not self.white_to_move
            if move.pieceMoved == "wK":
                self.white_king_position = Position(move.startRow, move.startCol)
            if move.pieceMoved == "bK":
                self.black_king_position = Position(move.startRow, move.startCol)
        #undo enpassant move
            if move.isEnpassantMove:
                self.board[move.endRow][move.endCol] = "--"
                self.board[move.startRow][move.endCol] = move.pieceCaptured

            self.enpassant_log.pop()
            self.enpassant_target = copy.deepcopy(self.enpassant_log[-1])
        #undo castling right
            self.castle_rights_log.pop()
            self.castle_rights = copy.deepcopy(self.castle_rights_log[-1])
        #undo castle move
            if move.isCastleMove:
                if move.endCol - move.startCol == 2:
                    self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 1]
                    self.board[move.endRow][move.endCol - 1] = "--"
                else:
                    self.board[move.endRow][move.endCol - 2] = self.board[move.endRow][move.endCol + 1]
                    self.board[move.endRow][move.endCol + 1] = "--"

            self.checkmate = False
            self.stalemate = False

    def updateCastleRight(self, move):
        if move.pieceMoved == "wK":
            self.castle_rights.wks = False
            self.castle_rights.wqs = False
        elif move.pieceMoved == "bK":
            self.castle_rights.bks = False
            self.castle_rights.bqs = False
        elif move.pieceMoved == "wR":
            if move.startRow == 7:
                if move.startCol == 0:
                    self.castle_rights.wqs = False
                elif move.startCol == 7:
                    self.castle_rights.wks = False
        elif move.pieceMoved == "bR":
            if move.startRow == 0:
                if move.startCol == 0:
                    self.castle_rights.bqs = False
                elif move.startCol == 7:
                    self.castle_rights.bks = False

        if move.pieceCaptured == 'wR':
            if move.endRow == 7:
                if move.endCol == 0:
                    self.castle_rights.wqs = False
                elif move.endCol == 7:
                    self.castle_rights.wks = False
        elif move.pieceCaptured == 'bR':
            if move.endRow == 0:
                if move.endCol == 0:
                    self.castle_rights.bqs = False
                elif move.endCol == 7:
                    self.castle_rights.bks = False
            


    def getValidMoves(self):
        moves = []
        self.in_check, self.pins, self.checks = self.checkForPinsAndChecks()
        if self.white_to_move:
            kingRow = self.white_king_position.row
            kingCol = self.white_king_position.col
        else:
            kingRow = self.black_king_position.row
            kingCol = self.black_king_position.col

        if self.in_check:
            if len(self.checks) == 1:
                moves = self.getAllPossibleMoves()
                check = self.checks[0]
                checkRow = check[0]
                checkCol = check[1]
                pieceChecking = self.board[checkRow][checkCol]
                validSqs = []
                if pieceChecking[1] == 'N':
                    validSqs = [(checkRow, checkCol)]
                else:
                    for i in range(1, 8):
                        validSq = (kingRow + check[2] * i, kingCol + check[3] * i)
                        validSqs.append(validSq)
                        if validSq[0] == checkRow and validSq[1] == checkCol:
                            break
                for i in range(len(moves) - 1, -1, -1):
                    if moves[i].pieceMoved[1] != 'K':
                        if not (moves[i].endRow, moves[i].endCol) in validSqs:
                            moves.remove(moves[i])
            else:
                self.getKingMoves(kingRow, kingCol, moves)
        else:
            moves = self.getAllPossibleMoves()

        if len(moves) == 0:
            if self.in_check:
                self.checkmate = True
            else:
                self.stalemate = True

        return moves


    def getAllPossibleMoves(self):
        moves = []
        for r in range(8):
            for c in range(8):
                turn = self.board[r][c][0]
                if (turn == 'w' and self.white_to_move) or (turn == 'b' and not self.white_to_move):
                    piece = self.board[r][c][1]
                    self.moveFunctions[piece](r, c, moves)
        return moves

    def getPawnMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
        
        if self.white_to_move:
            kingRow = self.white_king_position.row
            kingCol = self.white_king_position.col
        else:
            kingRow = self.black_king_position.row
            kingCol = self.black_king_position.col
        if self.white_to_move:
            if self.board[r-1][c] == "--":
                if not piecePinned or pinDirection == (-1, 0):
                    moves.append(Move((r, c), (r-1, c), self.board))
                    if r == 6:
                        if self.board[4][c] == "--":
                            moves.append(Move((r, c), (4, c), self.board))
            if c-1 >= 0:
                if self.board[r-1][c-1][0] == "b":
                    if not piecePinned or pinDirection == (-1, -1):
                        moves.append(Move((r, c), (r-1, c-1), self.board))
                elif (r-1, c-1) == self.enpassant_target:
                    attackingPiece = blockingPiece = False
                    if kingRow == r:
                        if kingCol < c:
                            insideRange = range(kingCol + 1, c-1)
                            outsideRange = range(c+1, 8)
                        else:
                            insideRange = range(kingCol - 1, c, -1)
                            outsideRange = range(c-2, -1, -1)
                        for i in insideRange:
                            if self.board[r][i] != "--":
                                blockingPiece = True
                        for i in outsideRange:
                            square = self.board[r][i]
                            if square[0] == 'b' and (square[1] == 'R' or square[1] == 'Q'):
                                attackingPiece = True
                            elif square != "--":
                                blockingPiece = True
                    if not attackingPiece or blockingPiece:
                        moves.append(Move((r, c), (r - 1, c - 1), self.board, isEnpassantMove=True))
            if c+1 <= 7:
                if self.board[r-1][c+1][0] == "b":
                    if not piecePinned or pinDirection == (-1, 1):
                        moves.append(Move((r, c), (r-1, c+1), self.board))
                elif (r-1, c+1) == self.enpassant_target:
                    attackingPiece = blockingPiece = False
                    if kingRow == r:
                        if kingCol < c:
                            insideRange = range(kingCol + 1, c)
                            outsideRange = range(c+2, 8)
                        else:
                            insideRange = range(kingCol - 1, c+1, -1)
                            outsideRange = range(c-1, -1, -1)
                        for i in insideRange:
                            if self.board[r][i] != "--":
                                blockingPiece = True
                        for i in outsideRange:
                            square = self.board[r][i]
                            if square[0] == 'b' and (square[1] == 'R' or square[1] == 'Q'):
                                attackingPiece = True
                            elif square != "--":
                                blockingPiece = True
                    if not attackingPiece or blockingPiece:
                        moves.append(Move((r, c), (r-1, c+1), self.board, isEnpassantMove=True))
        else:
            if self.board[r+1][c] == "--":
                if not piecePinned or pinDirection == (1, 0):
                    moves.append(Move((r, c), (r+1, c), self.board))
                    if r == 1:
                        if self.board[3][c] == "--":
                            moves.append(Move((r, c), (3, c), self.board))
            if c-1 >= 0:
                if self.board[r+1][c-1][0] == "w":
                    if not piecePinned or pinDirection == (1, -1):
                        moves.append(Move((r, c), (r+1, c-1), self.board))
                elif (r+1, c-1) == self.enpassant_target:
                    attackingPiece = blockingPiece = False
                    if kingRow == r:
                        if kingCol < c:
                            insideRange = range(kingCol + 1, c-1)
                            outsideRange = range(c+1, 8)
                        else:
                            insideRange = range(kingCol - 1, c, -1)
                            outsideRange = range(c-2, -1, -1)
                        for i in insideRange:
                            if self.board[r][i] != "--":
                                blockingPiece = True
                        for i in outsideRange:
                            square = self.board[r][i]
                            if square[0] == 'w' and (square[1] == 'R' or square[1] == 'Q'):
                                attackingPiece = True
                            elif square != "--":
                                blockingPiece = True
                    if not attackingPiece or blockingPiece:
                        moves.append(Move((r, c), (r+1, c-1), self.board, isEnpassantMove=True))

            if c+1 <= 7:
                if self.board[r+1][c+1][0] == "w":
                    if not piecePinned or pinDirection == (1, 1):
                        moves.append(Move((r, c), (r+1, c+1), self.board))
                elif (r+1, c+1) == self.enpassant_target:
                    attackingPiece = blockingPiece = False
                    if kingRow == r:
                        if kingCol < c:
                            insideRange = range(kingCol + 1, c)
                            outsideRange = range(c+2, 8)
                        else:
                            insideRange = range(kingCol - 1, c+1, -1)
                            outsideRange = range(c-1, -1, -1)
                        for i in insideRange:
                            if self.board[r][i] != "--":
                                blockingPiece = True
                        for i in outsideRange:
                            square = self.board[r][i]
                            if square[0] == 'w' and (square[1] == 'R' or square[1] == 'Q'):
                                attackingPiece = True
                            elif square != "--":
                                blockingPiece = True
                    if not attackingPiece or blockingPiece:
                        moves.append(Move((r, c), (r+1, c+1), self.board, isEnpassantMove=True))

    def getRookMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                if self.board[r][c][1] != 'Q':
                    self.pins.remove(self.pins[i])
                break

        straightDirections = ((-1, 0), (1, 0), (0, -1), (0, 1))
        enemyColor = 'b' if self.white_to_move else 'w'
        for d in straightDirections:
            for i in range(1, 8):
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if (0 <= endRow < 8) and (0 <= endCol < 8):
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--":
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor:
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                            break
                        else:
                            break
                else:
                    break

    def getKnightMoves(self, r, c, moves):
        piecePinned = False
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                self.pins.remove(self.pins[i])
                break

        knightDirections = ((-2, -1), (-1, -2), (1, -2), (2, -1), (2, 1), (1, 2), (-1, 2), (-2, 1))
        allyColor = 'w' if self.white_to_move else 'b'
        for d in knightDirections:
            endRow = r + d[0]
            endCol = c + d[1]
            if (0 <= endRow < 8) and (0 <= endCol < 8):
                if not piecePinned:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] != allyColor:
                        moves.append(Move((r, c), (endRow, endCol), self.board))

    def getBishopMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        diagonalDirections = ((-1, -1), (1, 1), (1, -1), (-1, 1))
        enemyColor = 'b' if self.white_to_move else 'w'
        for d in diagonalDirections:
            for i in range(1, 8):
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if (0 <= endRow < 8) and (0 <= endCol < 8):
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--":
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor:
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                            break
                        else:
                            break
                else:
                    break

    def getQueenMoves(self, r, c, moves):
        self.getRookMoves(r, c, moves)
        self.getBishopMoves(r, c, moves)

    def getKingMoves(self, r, c, moves):
        kingDirections = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (1, -1), (-1, 1))
        allyColor = 'w' if self.white_to_move else 'b'
        for i in range(8):
            endRow = r + kingDirections[i][0]
            endCol = c + kingDirections[i][1]
            if (0 <= endRow < 8) and (0 <= endCol < 8):
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColor:
                    # place king on the end of square to check
                    if allyColor == 'w':
                        self.white_king_position = Position(endRow, endCol)
                    else:
                        self.black_king_position = Position(endRow, endCol)
                    inCheck, pins, checks = self.checkForPinsAndChecks()
                    if not inCheck:
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                    # place king back
                    if allyColor == 'w':
                        self.white_king_position = Position(r, c)
                    else:
                        self.black_king_position = Position(r, c)
        self.getCastleMoves(r, c, moves, allyColor)

    def checkForPinsAndChecks(self):
        pins = []
        checks = []
        inCheck = False
        if self.white_to_move:
            enemyColor = 'b'
            allyColor = 'w'
            startRow = self.white_king_position.row
            startCol = self.white_king_position.col
        else:
            enemyColor = 'w'
            allyColor = 'b'
            startRow = self.black_king_position.row
            startCol = self.black_king_position.col

        directions = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, 1), (1, -1))
        for j in range(len(directions)):
            d = directions[j]
            possiblePins = ()
            for i in range(1, 8):
                endRow = startRow + d[0] * i
                endCol = startCol + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] == allyColor and endPiece[1] != 'K':
                        if possiblePins == ():
                            possiblePins = (endRow, endCol, d[0], d[1])
                        else:
                            break
                    elif endPiece[0] == enemyColor:
                        pieceType = endPiece[1]
                        if (0 <= j <= 3 and pieceType == 'R') or \
                                (4 <= j <= 7 and pieceType == 'B') or \
                                (i == 1 and pieceType == 'p' and ((enemyColor == 'b' and 4 <= j <= 5) or (enemyColor == 'w' and 6 <= j <= 7))) or \
                                (pieceType == 'Q') or (i == 1 and pieceType == 'K'):
                            if possiblePins == ():
                                inCheck = True
                                checks.append((endRow, endCol, d[0], d[1]))
                                break
                            else:
                                pins.append(possiblePins)
                                break
                        else:
                            break
                else:
                    break

        knightDirections = ((-2, -1), (-1, -2), (1, -2), (2, -1), (2, 1), (1, 2), (-1, 2), (-2, 1))
        for m in knightDirections:
            endRow = startRow + m[0]
            endCol = startCol + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if (endPiece[0] == enemyColor) and (endPiece[1] == 'N'):
                    inCheck = True
                    checks.append((endRow, endCol, m[0], m[1]))
                    break

        return inCheck, pins, checks

    def getCastleMoves(self, r, c, moves, allyColor=""):
        if self.in_check:
            return  #can't castle while be checked
        if (self.white_to_move and self.castle_rights.wks) or (not self.white_to_move and self.castle_rights.bks):
            self.getKingsideCastleMove(r, c, moves, allyColor)
        if (self.white_to_move and self.castle_rights.wqs) or (not self.white_to_move and self.castle_rights.bqs):
            self.getQueensideCastleMove(r, c, moves, allyColor)

    def getKingsideCastleMove(self, r, c, moves, allyColor=""):
        if self.board[r][c+1] == "--" and self.board[r][c+2] == "--":
            if allyColor == 'w':
                self.white_king_position = Position(r, c+1)
            else:
                self.black_king_position = Position(r, c+1)
            inCheck1, pins, checks = self.checkForPinsAndChecks()
            if allyColor == 'w':
                self.white_king_position = Position(r, c+2)
            else:
                self.black_king_position = Position(r, c+2)
            inCheck2, pins, checks = self.checkForPinsAndChecks()
            if allyColor == 'w':
                self.white_king_position = Position(r, c)
            else:
                self.black_king_position = Position(r, c)

            if not inCheck1 and not inCheck2:
                moves.append(Move((r, c), (r, c+2), self.board, isCastleMove=True))

    def getQueensideCastleMove(self, r, c, moves, allyColor=""):
        if self.board[r][c - 1] == "--" and self.board[r][c - 2] == "--" and self.board[r][c-3] == "--":
            if allyColor == 'w':
                self.white_king_position = Position(r, c-1)
            else:
                self.black_king_position = Position(r, c-1)
            inCheck1, pins, checks = self.checkForPinsAndChecks()
            if allyColor == 'w':
                self.white_king_position = Position(r, c-2)
            else:
                self.black_king_position = Position(r, c-2)
            inCheck2, pins, checks = self.checkForPinsAndChecks()
            if allyColor == 'w':
                self.white_king_position = Position(r, c-3)
            else:
                self.black_king_position = Position(r, c-3)
            inCheck3, pins, checks = self.checkForPinsAndChecks()
            if allyColor == 'w':
                self.white_king_position = Position(r, c)
            else:
                self.black_king_position = Position(r, c)

            if not inCheck1 and not inCheck2 and not inCheck3:
                moves.append(Move((r, c), (r, c-2), self.board, isCastleMove=True))

class castleRight():
    def __init__(self, wks, wqs, bks, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs



class Move():
    ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}
    filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}

    def __init__(self, startSq, endSq, board, isEnpassantMove=False, isCastleMove=False):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.isPawnPromotion = (self.pieceMoved == "wp" and self.endRow == 0) or (self.pieceMoved == "bp" and self.endRow == 7)
        self.isEnpassantMove = isEnpassantMove
        if self.isEnpassantMove:
            self.pieceCaptured = "wp" if self.pieceMoved == "bp" else "bp"
        self.isCastleMove = isCastleMove
        self.isCapture = (self.pieceCaptured != "--")
        self.moveID = self.startCol * 1000 + self.startRow * 100 + self.endCol * 10 + self.endRow

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def getChessNotation(self):
        return self.getFileRank(self.startRow, self.startCol) + self.getFileRank(self.endRow, self.endCol)
    def getFileRank(self, row, col):
        return str(self.colsToFiles[col] + self.rowsToRanks[row])

    def __str__(self):
        #castleMove:
        if self.isCastleMove:
            return "O-O" if self.endCol == 6 else "O-O-O"
        endSquare = self.getFileRank(self.endRow, self.endCol)
        #pawn move
        if self.pieceMoved[1] == 'p':
            if self.isCapture:
                return self.colsToFiles[self.startCol] + "x" + endSquare
            else:
                return endSquare

        #piece moves
        moveString = self.pieceMoved[1]
        if self.isCapture:
            moveString += "x"
        return moveString + endSquare