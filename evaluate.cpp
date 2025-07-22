#include "chess/evaluate.h"

namespace chess {

int Evaluator::evaluate(const Board& board) const {
    // start with material evaluation
    int score = evaluateMaterial(board);
    
    // add center control evaluation
    score += evaluateCenterControl(board);
    
    // add other evaluation components
    score += evaluatePiecePositions(board);
    // score += evaluateMobility(board);
    // score += evaluatePawnStructure(board);
    // score += evaluateKingSafety(board);
    score += evaluateEarlyQueenDevelopment(board);
    score += evaluatePieceDevelopment(board);
    score += evaluateEarlyKingMovement(board);
    score += evaluateCastling(board);
    score += evaluatePawnDoubleMoves(board);
    score += evaluateUndefendedPawns(board); // New evaluation for undefended pawns
    score += evaluateKingPawnShield(board); // Discourage pushing pawns in front of king
    score += evaluateMinorPieceDevelopmentForDefense(board); // Encourage minor piece development for defense
    score += evaluateEarlyFPawnMoves(board); // Discourage early f-pawn pushes in the opening
    
    return score;
}

int Evaluator::evaluateMaterial(const Board& board) const {
    int score = 0;
    
    // material evaluation
    for (int rank = 0; rank < 8; rank++) {
        for (int file = 0; file < 8; file++) {
            Piece piece = board.getPiece(Position(file, rank));
            if (!piece.isEmpty()) {
                int value = piece.getValue();
                if (piece.getColor() == Color::BLACK) {
                    value = -value;
                }
                score += value;
            }
        }
    }
    
    return score;
}

int Evaluator::evaluatePiecePositions(const Board& board) const {
    int score = 0;
    
    // knight position evaluation - knights are better near the center
    for (int rank = 0; rank < 8; rank++) {
        for (int file = 0; file < 8; file++) {
            Position pos(file, rank);
            Piece piece = board.getPiece(pos);
            
            // only evaluate knights
            if (piece.getType() == PieceType::KNIGHT) {
                // calculate distance from center (center is between d4, d5, e4, e5)
                // file distance: how far from columns d and e (files 3,4)
                int fileDistFromCenter = std::min(abs(file - 3), abs(file - 4));
                // rank distance: how far from ranks 4 and 5 (ranks 3,4)
                int rankDistFromCenter = std::min(abs(rank - 3), abs(rank - 4));
                
                // total Manhattan distance from center (its like the hypot but it sounds smart)
                int distFromCenter = fileDistFromCenter + rankDistFromCenter;
                
                // knights get bonus points for being closer to center
                // max bonus of 3 points for being in the center, decreasing as they move away
                int positionBonus = 3 - distFromCenter;
                if (positionBonus < 0) positionBonus = 0; // no penalty for being far
                
                // apply bonus based on piece color
                if (piece.getColor() == Color::WHITE) {
                    score += positionBonus;
                } else {
                    score -= positionBonus;
                }
                
                // Check if knight is vulnerable to pawn attacks
                // For each knight, check if it can be attacked by an enemy pawn on the next move
                Color enemyColor = (piece.getColor() == Color::WHITE) ? Color::BLACK : Color::WHITE;
                int pawnDirection = (enemyColor == Color::WHITE) ? 1 : -1;
                
                // Check left and right pawn push attacks
                for (int fileOffset : {-1, 1}) {
                    // First check: pawns that need to push once to attack (two squares away)
                    // Position where enemy pawn would be after pushing
                    Position pawnAttackPos(file + fileOffset, rank - pawnDirection);
                    
                    // Position where enemy pawn would be before pushing (two squares away)
                    Position pawnPos(file + fileOffset, rank - pawnDirection - pawnDirection);
                    
                    // Check if both positions are valid
                    if (pawnPos.isValid() && pawnAttackPos.isValid()) {
                        Piece potentialPawn = board.getPiece(pawnPos);
                        
                        // Check if there's an enemy pawn that could push
                        if (!potentialPawn.isEmpty() && 
                            potentialPawn.getType() == PieceType::PAWN && 
                            potentialPawn.getColor() == enemyColor) {
                            
                            // Check if the square the pawn would move to is empty
                            if (board.getPiece(pawnAttackPos).isEmpty()) {
                                
                                // Check if the pawn would be safe after attacking
                                // i.e., knight can't capture it and it's not under attack
                                if (!board.isUnderAttack(pawnAttackPos, piece.getColor())) {
                                    // Apply penalty for vulnerable knight position
                                    int penalty = 15; // Increased penalty to make it more punishing
                                    
                                    if (piece.getColor() == Color::WHITE) {
                                        score -= penalty;
                                    } else {
                                        score += penalty;
                                    }
                                }
                            }
                        }
                    }
                    
                    // Second check: pawns that are already one square away from attacking
                    // Position where enemy pawn would be (one square away, ready to attack)
                    Position adjacentPawnPos(file + fileOffset, rank - pawnDirection);
                    
                    // Position where enemy pawn would move to attack
                    Position adjacentAttackPos(file, rank);
                    
                    // Check if positions are valid
                    if (adjacentPawnPos.isValid()) {
                        Piece adjacentPawn = board.getPiece(adjacentPawnPos);
                        
                        // Check if there's an enemy pawn ready to attack
                        if (!adjacentPawn.isEmpty() && 
                            adjacentPawn.getType() == PieceType::PAWN && 
                            adjacentPawn.getColor() == enemyColor) {
                            
                            // Apply penalty for knight being directly threatened by pawn
                            int penalty = 25; // Even higher penalty for immediate threat
                            
                            if (piece.getColor() == Color::WHITE) {
                                score -= penalty;
                            } else {
                                score += penalty;
                            }
                        }
                    }
                }
                
                // Check for pawns that are already in position to attack on the next move
                // This specifically handles the case after 1.e4 Nf6, where the e-pawn can push to e5
                for (int fileOffset : {-1, 1}) {
                    // Position where an enemy pawn could be (ready to push and attack)
                    Position readyPawnPos(file + fileOffset, rank);
                    
                    // Position where that pawn would move to
                    Position readyAttackPos(file + fileOffset, rank + pawnDirection);
                    
                    // Check if positions are valid
                    if (readyPawnPos.isValid() && readyAttackPos.isValid()) {
                        Piece readyPawn = board.getPiece(readyPawnPos);
                        
                        // Check if there's an enemy pawn ready to push and attack
                        if (!readyPawn.isEmpty() && 
                            readyPawn.getType() == PieceType::PAWN && 
                            readyPawn.getColor() == enemyColor) {
                            
                            // Check if the square the pawn would move to is empty
                            if (board.getPiece(readyAttackPos).isEmpty()) {
                                
                                // Apply penalty for knight being vulnerable to pawn push
                                int penalty = 20; // High penalty for this common vulnerability
                                
                                if (piece.getColor() == Color::WHITE) {
                                    score -= penalty;
                                } else {
                                    score += penalty;
                                }
                            }
                        }
                    }
                }

            }
        }
    }
    
    return score;
}

int Evaluator::evaluateCenterControl(const Board& board) const {
    int score = 0;
    
    Position centerSquares[4] = {
        Position(3, 3), // d4
        Position(3, 4), // d5
        Position(4, 3), // e4
        Position(4, 4)  // e5
    };
    
    // Check if we're in the opening phase (fewer than 7 developed pieces)
    int developedPieces = 0;
    for (int rank = 0; rank < 8; rank++) {
        for (int file = 0; file < 8; file++) {
            Position pos(file, rank);
            Piece piece = board.getPiece(pos);
            if (!piece.isEmpty() && piece.getType() != PieceType::PAWN && piece.getType() != PieceType::KING) {
                // Count pieces that are not on their starting ranks as developed
                if ((piece.getColor() == Color::WHITE && pos.rank > 0) ||
                    (piece.getColor() == Color::BLACK && pos.rank < 7)) {
                    developedPieces++;
                }
            }
        }
    }
    
    bool isOpening = (developedPieces < 7);
    
    // bonus for occupying center squares
    for (const auto& pos : centerSquares) {
        Piece piece = board.getPiece(pos);
        if (!piece.isEmpty()) {
            // bonus for having pieces in the center
            int bonus = (piece.getType() == PieceType::PAWN) ? 20 : 10;
            
            // Higher bonus in the opening
            if (isOpening) {
                bonus *= 2; // Double the bonus in the opening
            }
            
            // apply bonus based on piece color
            if (piece.getColor() == Color::WHITE) {
                score += bonus;
            } else {
                score -= bonus;
            }
            
            // check if the piece is under attack
            if (board.isUnderAttack(pos, piece.getColor() == Color::WHITE ? Color::BLACK : Color::WHITE)) {
                // penalize if the piece is under attack
                if (piece.getColor() == Color::WHITE) {
                    score -= 5;
                } else {
                    score += 5;
                }
            }
        }
    }
    
    // bonus for attacking center squares
    for (const auto& pos : centerSquares) {
        // check white's control
        if (board.isUnderAttack(pos, Color::WHITE)) {
            int attackBonus = 5;
            if (isOpening) {
                attackBonus = 15; // Triple the bonus in the opening
            }
            score += attackBonus;
        }
        
        // check black's control
        if (board.isUnderAttack(pos, Color::BLACK)) {
            int attackBonus = 5;
            if (isOpening) {
                attackBonus = 15; // Triple the bonus in the opening
            }
            score -= attackBonus;
        }
    }
    
    return score;
}

int Evaluator::evaluateMobility(const Board& board) const {
    // todo
    return 0;
}

int Evaluator::evaluatePawnStructure(const Board& board) const {
    // todo
    return 0;
}

int Evaluator::evaluateKingSafety(const Board& board) const {
    // todo
    return 0;
}

int Evaluator::evaluateEarlyQueenDevelopment(const Board& board) const {
    int score = 0;
    
    // check white queen position
    Position whiteQueenStartPos(3, 0); // d1
    bool whiteQueenFound = false;
    
    // check black queen position
    Position blackQueenStartPos(3, 7); // d8
    bool blackQueenFound = false;
    
    // scan the board to find the queens
    for (int rank = 0; rank < 8; rank++) {
        for (int file = 0; file < 8; file++) {
            Position pos(file, rank);
            Piece piece = board.getPiece(pos);
            
            if (piece.getType() == PieceType::QUEEN) {
                if (piece.getColor() == Color::WHITE) {
                    whiteQueenFound = true;
                    
                    // if white queen is not on its starting square, apply penalty
                    if (pos != whiteQueenStartPos) {
                        // calculate manhattan distance from starting square
                        int distance = abs(pos.file - whiteQueenStartPos.file) + 
                                      abs(pos.rank - whiteQueenStartPos.rank);
                        
                        // Penalty is higher for moving the queen early
                        // -15 points penalty for moving the queen
                        score -= 15;
                        
                        // Additional penalty for moving it far from home
                        score -= distance * 2;
                    }
                } else { // BLACK
                    blackQueenFound = true;
                    
                    // if black queen is not on its starting square, apply penalty
                    if (pos != blackQueenStartPos) {
                        // calculate manhattan distance from starting square
                        int distance = abs(pos.file - blackQueenStartPos.file) + 
                                      abs(pos.rank - blackQueenStartPos.rank);
                        
                        // Penalty is higher for moving the queen early
                        // +15 points penalty for moving the queen (positive for white's advantage)
                        score += 15;
                        
                        // Additional penalty for moving it far from home
                        score += distance * 2;
                    }
                }
            }
        }
    }
    
    return score;
}

int Evaluator::evaluatePieceDevelopment(const Board& board) const {
    int score = 0;
    
    // define starting positions for pieces
    // white pieces
    const Position whiteKnightStartPos[2] = {Position(1, 0), Position(6, 0)}; // b1, g1
    const Position whiteBishopStartPos[2] = {Position(2, 0), Position(5, 0)}; // c1, f1
    const Position whiteRookStartPos[2] = {Position(0, 0), Position(7, 0)};   // a1, h1
    
    // black pieces
    const Position blackKnightStartPos[2] = {Position(1, 7), Position(6, 7)}; // b8, g8
    const Position blackBishopStartPos[2] = {Position(2, 7), Position(5, 7)}; // c8, f8
    const Position blackRookStartPos[2] = {Position(0, 7), Position(7, 7)};   // a8, h8
    
    // define good development squares for minor pieces
    // Good knight squares in the opening
    const Position goodWhiteKnightSquares[] = {
        Position(2, 2), // c3
        Position(5, 2), // f3
        Position(3, 2), // d3
        Position(4, 2)  // e3
    };
    
    const Position goodBlackKnightSquares[] = {
        Position(2, 5), // c6
        Position(5, 5), // f6
        Position(3, 5), // d6
        Position(4, 5)  // e6
    };
    
    // Good bishop squares in the opening
    const Position goodWhiteBishopSquares[] = {
        Position(2, 2), // c3
        Position(5, 2), // f3
        Position(3, 1), // d2
        Position(4, 1), // e2
        Position(1, 2), // b3
        Position(6, 2)  // g3
    };
    
    const Position goodBlackBishopSquares[] = {
        Position(2, 5), // c6
        Position(5, 5), // f6
        Position(3, 6), // d7
        Position(4, 6), // e7
        Position(1, 5), // b6
        Position(6, 5)  // g6
    };
    
    // Count undeveloped minor pieces
    int whiteUndevelopedMinorPieces = 0;
    int blackUndevelopedMinorPieces = 0;
    
    // Check for pawns under attack
    bool whitePawnsUnderAttack = false;
    bool blackPawnsUnderAttack = false;
    
    // First pass: count undeveloped pieces and check for attacked pawns
    for (int rank = 0; rank < 8; rank++) {
        for (int file = 0; file < 8; file++) {
            Position pos(file, rank);
            Piece piece = board.getPiece(pos);
            
            if (piece.isEmpty()) {
                continue;
            }
            
            // Count undeveloped knights and bishops
            if (piece.getType() == PieceType::KNIGHT) {
                if (piece.getColor() == Color::WHITE) {
                    if (pos == whiteKnightStartPos[0] || pos == whiteKnightStartPos[1]) {
                        whiteUndevelopedMinorPieces++;
                    }
                } else { // BLACK
                    if (pos == blackKnightStartPos[0] || pos == blackKnightStartPos[1]) {
                        blackUndevelopedMinorPieces++;
                    }
                }
            } else if (piece.getType() == PieceType::BISHOP) {
                if (piece.getColor() == Color::WHITE) {
                    if (pos == whiteBishopStartPos[0] || pos == whiteBishopStartPos[1]) {
                        whiteUndevelopedMinorPieces++;
                    }
                } else { // BLACK
                    if (pos == blackBishopStartPos[0] || pos == blackBishopStartPos[1]) {
                        blackUndevelopedMinorPieces++;
                    }
                }
            } else if (piece.getType() == PieceType::PAWN) {
                // Check if any pawns are under attack
                if (piece.getColor() == Color::WHITE) {
                    if (board.isUnderAttack(pos, Color::BLACK)) {
                        whitePawnsUnderAttack = true;
                    }
                } else { // BLACK
                    if (board.isUnderAttack(pos, Color::WHITE)) {
                        blackPawnsUnderAttack = true;
                    }
                }
            }
        }
    }
    
    // Apply strong penalties for undeveloped minor pieces, especially if pawns are under attack
    if (whitePawnsUnderAttack) {
        score -= whiteUndevelopedMinorPieces * 80; // Very strong penalty when pawns are under attack
    } else {
        score -= whiteUndevelopedMinorPieces * 40; // Still significant penalty in normal situations
    }
    
    if (blackPawnsUnderAttack) {
        score += blackUndevelopedMinorPieces * 80; // Very strong penalty for black (positive for white)
    } else {
        score += blackUndevelopedMinorPieces * 40; // Still significant penalty in normal situations
    }
    
    // Second pass: evaluate piece positions
    for (int rank = 0; rank < 8; rank++) {
        for (int file = 0; file < 8; file++) {
            Position pos(file, rank);
            Piece piece = board.getPiece(pos);
            
            if (piece.isEmpty()) {
                continue;
            }
            
            // check if the piece is under attack
            bool isUnderAttack = false;
            if (piece.getColor() == Color::WHITE) {
                isUnderAttack = board.isUnderAttack(pos, Color::BLACK);
            } else {
                isUnderAttack = board.isUnderAttack(pos, Color::WHITE);
            }
            
            // handle knights
            if (piece.getType() == PieceType::KNIGHT) {
                if (piece.getColor() == Color::WHITE) {
                    // check if knight is not on starting square
                    if (pos != whiteKnightStartPos[0] && pos != whiteKnightStartPos[1]) {
                        bool onGoodSquare = false;
                        
                        // check if knight is on a good development square
                        for (const auto& goodSquare : goodWhiteKnightSquares) {
                            if (pos == goodSquare) {
                                onGoodSquare = true;
                                // Strong bonus for developing knights to good squares
                                score += 50;
                                
                                // Extra bonus if pawns are under attack
                                if (whitePawnsUnderAttack) {
                                    score += 30;
                                }
                                break;
                            }
                        }
                        
                        // If knight is not on a good square and not under attack, apply penalty
                        if (!onGoodSquare && !isUnderAttack) {
                            // Penalize knight for being on a suboptimal square
                            // this indirectly penalizes moving the same piece multiple times
                            score -= 20; // Increased penalty
                        }
                    }
                } else { // BLACK
                    // check if knight is not on starting square
                    if (pos != blackKnightStartPos[0] && pos != blackKnightStartPos[1]) {
                        bool onGoodSquare = false;
                        
                        // check if knight is on a good development square
                        for (const auto& goodSquare : goodBlackKnightSquares) {
                            if (pos == goodSquare) {
                                onGoodSquare = true;
                                // Strong bonus for developing knights to good squares
                                score -= 50; // Negative for black's advantage
                                
                                // Extra bonus if pawns are under attack
                                if (blackPawnsUnderAttack) {
                                    score -= 30;
                                }
                                break;
                            }
                        }
                        
                        // if knight is not on a good square and not under attack, apply penalty
                        if (!onGoodSquare && !isUnderAttack) {
                            // penalize knight for being on a suboptimal square
                            score += 20; // Increased penalty (positive for white's advantage)
                        }
                    }
                }
            }
            
            // handle bishops
            else if (piece.getType() == PieceType::BISHOP) {
                if (piece.getColor() == Color::WHITE) {
                    // check if bishop is not on starting square
                    if (pos != whiteBishopStartPos[0] && pos != whiteBishopStartPos[1]) {
                        bool onGoodSquare = false;
                        
                        // check if bishop is on a good development square
                        for (const auto& goodSquare : goodWhiteBishopSquares) {
                            if (pos == goodSquare) {
                                onGoodSquare = true;
                                // Strong bonus for developing bishops to good squares
                                score += 45;
                                
                                // Extra bonus if pawns are under attack
                                if (whitePawnsUnderAttack) {
                                    score += 30;
                                }
                                break;
                            }
                        }
                        
                        // if bishop is not on a good square and not under attack, apply penalty
                        if (!onGoodSquare && !isUnderAttack) {
                            // penalize bishop for being on a suboptimal square
                            score -= 20; // Increased penalty
                        }
                    }
                } else { // BLACK
                    // check if bishop is not on starting square
                    if (pos != blackBishopStartPos[0] && pos != blackBishopStartPos[1]) {
                        bool onGoodSquare = false;
                        
                        // check if bishop is on a good development square
                        for (const auto& goodSquare : goodBlackBishopSquares) {
                            if (pos == goodSquare) {
                                onGoodSquare = true;
                                // Strong bonus for developing bishops to good squares
                                score -= 45; // Negative for black's advantage
                                
                                // Extra bonus if pawns are under attack
                                if (blackPawnsUnderAttack) {
                                    score -= 30;
                                }
                                break;
                            }
                        }
                        
                        // if bishop is not on a good square and not under attack, apply penalty
                        if (!onGoodSquare && !isUnderAttack) {
                            // penalize bishop for being on a suboptimal square
                            score += 20; // Increased penalty (positive for white's advantage)
                        }
                    }
                }
            }
            
            // handle rooks - they generally shouldn't move early unless there's a good reason
            else if (piece.getType() == PieceType::ROOK) {
                if (piece.getColor() == Color::WHITE) {
                    // check if rook is not on starting square
                    if (pos != whiteRookStartPos[0] && pos != whiteRookStartPos[1]) {
                        // if rook is not under attack, apply penalty for early movement
                        if (!isUnderAttack) {
                            score -= 15; // Increased penalty
                        }
                    }
                } else { // BLACK
                    // check if rook is not on starting square
                    if (pos != blackRookStartPos[0] && pos != blackRookStartPos[1]) {
                        // if rook is not under attack, apply penalty for early movement
                        if (!isUnderAttack) {
                            score += 15; // Increased penalty (positive for white's advantage)
                        }
                    }
                }
            }
        }
    }
    
    return score;
}

int Evaluator::evaluateEarlyKingMovement(const Board& board) const {
    int score = 0;
    
    // Define starting positions for kings
    const Position whiteKingStartPos(4, 0); // e1
    const Position blackKingStartPos(4, 7); // e8
    
    // Check castling rights
    bool whiteCanCastle = false;
    bool blackCanCastle = false;
    
    // Scan the board to find the kings
    for (int rank = 0; rank < 8; rank++) {
        for (int file = 0; file < 8; file++) {
            Position pos(file, rank);
            Piece piece = board.getPiece(pos);
            
            if (piece.getType() == PieceType::KING) {
                if (piece.getColor() == Color::WHITE) {
                    // If white king is not on its starting square
                    if (pos != whiteKingStartPos) {
                        // Check if king moved above first rank (rank > 0) but castling might still be possible
                        if (pos.rank > 0) {
                            // Heavy penalty for moving king above first rank before castling
                            // -50 points is a significant penalty (roughly half a pawn)
                            score -= 50;
                            
                            // Additional penalty based on how far the king moved vertically
                            score -= pos.rank * 10;
                        }
                    }
                } else { // BLACK
                    // If black king is not on its starting square
                    if (pos != blackKingStartPos) {
                        // Check if king moved below last rank (rank < 7) but castling might still be possible
                        if (pos.rank < 7) {
                            // Heavy penalty for moving king below last rank before castling
                            // +50 points is a significant penalty (positive for white's advantage)
                            score += 50;
                            
                            // Additional penalty based on how far the king moved vertically
                            score += (7 - pos.rank) * 10;
                        }
                    }
                }
            }
        }
    }
    
    return score;
}

int Evaluator::evaluateCastling(const Board& board) const {
    int score = 0;
    
    // Define starting positions for kings and rooks
    const Position whiteKingStartPos(4, 0);   // e1
    const Position blackKingStartPos(4, 7);   // e8
    
    // Kingside castling positions
    const Position whiteKingsideCastlePos(6, 0);  // g1
    const Position blackKingsideCastlePos(6, 7);  // g8
    
    // Queenside castling positions
    const Position whiteQueensideCastlePos(2, 0); // c1
    const Position blackQueensideCastlePos(2, 7); // c8
    
    // Scan the board to find the kings
    for (int rank = 0; rank < 8; rank++) {
        for (int file = 0; file < 8; file++) {
            Position pos(file, rank);
            Piece piece = board.getPiece(pos);
            
            if (piece.getType() == PieceType::KING) {
                if (piece.getColor() == Color::WHITE) {
                    // Check if king has castled kingside
                    if (pos == whiteKingsideCastlePos) {
                        // Significant bonus for successful castling
                        score += 40;
                    }
                    // Check if king has castled queenside
                    else if (pos == whiteQueensideCastlePos) {
                        // Significant bonus for successful castling
                        score += 40;
                    }
                    // If king is still on starting square, give a small bonus for maintaining castling rights
                    else if (pos == whiteKingStartPos) {
                        // Check if rooks are still on their starting squares
                        Piece kingsideRook = board.getPiece(Position(7, 0)); // h1
                        Piece queensideRook = board.getPiece(Position(0, 0)); // a1
                        
                        // Bonus for maintaining kingside castling option
                        if (!kingsideRook.isEmpty() && kingsideRook.getType() == PieceType::ROOK && 
                            kingsideRook.getColor() == Color::WHITE) {
                            score += 15;
                        }
                        
                        // Bonus for maintaining queenside castling option
                        if (!queensideRook.isEmpty() && queensideRook.getType() == PieceType::ROOK && 
                            queensideRook.getColor() == Color::WHITE) {
                            score += 10; // Slightly less bonus for queenside as it's slightly less common
                        }
                    }
                } else { // BLACK
                    // Check if king has castled kingside
                    if (pos == blackKingsideCastlePos) {
                        // Significant bonus for successful castling (negative for white's advantage)
                        score -= 40;
                    }
                    // Check if king has castled queenside
                    else if (pos == blackQueensideCastlePos) {
                        // Significant bonus for successful castling (negative for white's advantage)
                        score -= 40;
                    }
                    // If king is still on starting square, give a small bonus for maintaining castling rights
                    else if (pos == blackKingStartPos) {
                        // Check if rooks are still on their starting squares
                        Piece kingsideRook = board.getPiece(Position(7, 7)); // h8
                        Piece queensideRook = board.getPiece(Position(0, 7)); // a8
                        
                        // Bonus for maintaining kingside castling option
                        if (!kingsideRook.isEmpty() && kingsideRook.getType() == PieceType::ROOK && 
                            kingsideRook.getColor() == Color::BLACK) {
                            score -= 15;
                        }
                        
                        // Bonus for maintaining queenside castling option
                        if (!queensideRook.isEmpty() && queensideRook.getType() == PieceType::ROOK && 
                            queensideRook.getColor() == Color::BLACK) {
                            score -= 10; // Slightly less bonus for queenside as it's slightly less common
                        }
                    }
                }
            }
        }
    }
    
    return score;
}

int Evaluator::evaluatePawnDoubleMoves(const Board& board) const {
    int score = 0;
    
    // Only apply this evaluation in the opening phase (first 10 moves)
    // We can estimate this by counting the total pieces on the board
    int pieceCount = 0;
    for (int rank = 0; rank < 8; rank++) {
        for (int file = 0; file < 8; file++) {
            Piece piece = board.getPiece(Position(file, rank));
            if (!piece.isEmpty()) {
                pieceCount++;
            }
        }
    }

    /*
    int


    */
    
    // If we're not in the opening phase (too many pieces missing), return early
    if (pieceCount < 28) { // 32 pieces at start, allow for a few captures
        return score;
    }
    
    // Define starting positions for pawns
    const int whitePawnRank = 1; // 2nd rank
    const int blackPawnRank = 6; // 7th rank
    
    // Center squares (d4, d5, e4, e5)
    const Position centerSquares[4] = {
        Position(3, 3), Position(3, 4), Position(4, 3), Position(4, 4)
    };
    
    // Track pawns that have moved more than once
    for (int file = 0; file < 8; file++) {
        // Check white pawns
        bool whitePawnFound = false;
        
        // Check each rank to see if this file's pawn has moved
        for (int rank = 0; rank < 8; rank++) {
            Position pos(file, rank);
            Piece piece = board.getPiece(pos);
            
            if (!piece.isEmpty() && piece.getType() == PieceType::PAWN && piece.getColor() == Color::WHITE) {
                whitePawnFound = true;
                
                // Check if the pawn has moved from its starting position
                if (rank > whitePawnRank) {
                    // Check if the pawn has moved more than once
                    // A pawn on rank 3 (index 2) could have moved there in one move (e2-e4)
                    // But a pawn on rank 4 (index 3) or higher must have moved multiple times
                    if (rank > whitePawnRank + 2) {
                        // Check if the pawn is under attack - if so, we don't penalize movement
                        bool isUnderAttack = board.isUnderAttack(pos, Color::BLACK);
                        
                        if (!isUnderAttack) {
                            // Base penalty for moving a pawn twice
                            score -= 20;
                            
                            // Extra penalty for center pawns (d and e files)
                            if (file == 3 || file == 4) {
                                score -= 10;
                            }
                            
                            // Check if this pawn controls any center squares
                            bool controlsCenter = false;
                            for (const auto& centerPos : centerSquares) {
                                // Pawns control squares diagonally in front of them
                                if (abs(pos.file - centerPos.file) == 1 && 
                                    centerPos.rank == pos.rank + 1) {
                                    controlsCenter = true;
                                    break;
                                }
                            }
                            
                            // Extra penalty if it lost center control
                            if (!controlsCenter && (file == 2 || file == 3 || file == 4 || file == 5)) {
                                score -= 10;
                            }
                        }
                    }
                }
                
                break; // Found the pawn for this file, no need to check further ranks
            }
        }
        
        // Check black pawns
        bool blackPawnFound = false;
        
        // Check each rank to see if this file's pawn has moved
        for (int rank = 0; rank < 8; rank++) {
            Position pos(file, rank);
            Piece piece = board.getPiece(pos);
            
            if (!piece.isEmpty() && piece.getType() == PieceType::PAWN && piece.getColor() == Color::BLACK) {
                blackPawnFound = true;
                
                // Check if the pawn has moved from its starting position
                if (rank < blackPawnRank) {
                    // Check if the pawn has moved more than once
                    // A pawn on rank 4 (index 4) could have moved there in one move (e7-e5)
                    // But a pawn on rank 3 (index 3) or lower must have moved multiple times
                    if (rank < blackPawnRank - 2) {
                        // Check if the pawn is under attack - if so, we don't penalize movement
                        bool isUnderAttack = board.isUnderAttack(pos, Color::WHITE);
                        
                        if (!isUnderAttack) {
                            // Base penalty for moving a pawn twice
                            score += 20; // positive for white's advantage
                            
                            // Extra penalty for center pawns (d and e files)
                            if (file == 3 || file == 4) {
                                score += 10;
                            }
                            
                            // Check if this pawn controls any center squares
                            bool controlsCenter = false;
                            for (const auto& centerPos : centerSquares) {
                                // Pawns control squares diagonally in front of them
                                if (abs(pos.file - centerPos.file) == 1 && 
                                    centerPos.rank == pos.rank - 1) {
                                    controlsCenter = true;
                                    break;
                                }
                            }
                            
                            // Extra penalty if it lost center control
                            if (!controlsCenter && (file == 2 || file == 3 || file == 4 || file == 5)) {
                                score += 10;
                            }
                        }
                    }
                }
                
                break; // Found the pawn for this file, no need to check further ranks
            }
        }
    }
    
    return score;
}

int Evaluator::evaluateUndefendedPawns(const Board& board) const {
    int score = 0;
    
    // This evaluation is primarily for the opening phase
    // Check if we're still in the opening by counting developed pieces
    int developedPieces = 0;
    for (int rank = 0; rank < 8; rank++) {
        for (int file = 0; file < 8; file++) {
            Position pos(file, rank);
            Piece piece = board.getPiece(pos);
            
            // Count pieces that have moved from their starting positions
            if (!piece.isEmpty() && piece.getType() != PieceType::PAWN && piece.getType() != PieceType::KING) {
                // Knights starting on b1, g1, b8, g8
                if (piece.getType() == PieceType::KNIGHT) {
                    if ((piece.getColor() == Color::WHITE && (pos.file != 1 && pos.file != 6)) || 
                        (piece.getColor() == Color::BLACK && (pos.file != 1 && pos.file != 6))) {
                        developedPieces++;
                    }
                }
                // Bishops starting on c1, f1, c8, f8
                else if (piece.getType() == PieceType::BISHOP) {
                    if ((piece.getColor() == Color::WHITE && pos.rank != 0) || 
                        (piece.getColor() == Color::BLACK && pos.rank != 7)) {
                        developedPieces++;
                    }
                }
                // Rooks starting on a1, h1, a8, h8
                else if (piece.getType() == PieceType::ROOK) {
                    if ((piece.getColor() == Color::WHITE && pos.rank != 0) || 
                        (piece.getColor() == Color::BLACK && pos.rank != 7)) {
                        developedPieces++;
                    }
                }
                // Queens starting on d1, d8
                else if (piece.getType() == PieceType::QUEEN) {
                    if ((piece.getColor() == Color::WHITE && (pos.file != 3 || pos.rank != 0)) || 
                        (piece.getColor() == Color::BLACK && (pos.file != 3 || pos.rank != 7))) {
                        developedPieces++;
                    }
                }
            }
        }
    }
    
    // If more than 6 pieces are developed, we're likely not in the opening anymore
    if (developedPieces > 6) {
        return score; // Skip this evaluation outside of the opening
    }
    
    // Check for attacked pawns with no defenders
    for (int rank = 0; rank < 8; rank++) {
        for (int file = 0; file < 8; file++) {
            Position pos(file, rank);
            Piece piece = board.getPiece(pos);
            
            // Only evaluate pawns
            if (!piece.isEmpty() && piece.getType() == PieceType::PAWN) {
                Color pawnColor = piece.getColor();
                Color enemyColor = (pawnColor == Color::WHITE) ? Color::BLACK : Color::WHITE;
                
                // Check if the pawn is under attack
                if (board.isUnderAttack(pos, enemyColor)) {
                    // Check if the pawn is defended by another piece
                    bool isDefended = board.isUnderAttack(pos, pawnColor);
                    
                    if (!isDefended) {
                        // This pawn is under attack and has no defenders
                        // Apply a strong penalty for undefended attacked pawns
                        if (pawnColor == Color::WHITE) {
                            score -= 120; // Strong penalty for white
                        } else {
                            score += 120; // Strong penalty for black (positive for white's advantage)
                        }
                        
                        // Evaluate potential defender moves
                        int defenderBonus = evaluatePotentialDefenders(board, pos, pawnColor);
                        
                        // Apply the bonus/penalty based on pawn color
                        if (pawnColor == Color::WHITE) {
                            score += defenderBonus;
                        } else {
                            score -= defenderBonus;
                        }
                        
                        // Check if any piece can capture the attacker
                        // First, find the attacker(s)
                        std::vector<Position> attackers;
                        for (int aRank = 0; aRank < 8; aRank++) {
                            for (int aFile = 0; aFile < 8; aFile++) {
                                Position attackerPos(aFile, aRank);
                                Piece attackerPiece = board.getPiece(attackerPos);
                                
                                if (!attackerPiece.isEmpty() && attackerPiece.getColor() == enemyColor) {
                                    // Check if this piece is attacking the pawn
                                    std::vector<Move> moves = board.generatePseudoLegalMoves(attackerPos);
                                    for (const Move& move : moves) {
                                        if (move.to.file == pos.file && move.to.rank == pos.rank) {
                                            attackers.push_back(attackerPos);
                                            break;
                                        }
                                    }
                                }
                            }
                        }
                        
                        // Now check if we can capture any attacker
                        for (const Position& attackerPos : attackers) {
                            if (board.isUnderAttack(attackerPos, pawnColor)) {
                                // We can capture the attacker - this is good!
                                if (pawnColor == Color::WHITE) {
                                    score += 100; // Strong bonus for being able to capture the attacker
                                } else {
                                    score -= 100; // Strong bonus for black (negative for white's advantage)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    return score;
}

// Helper function to evaluate potential defenders for an attacked pawn
int Evaluator::evaluatePotentialDefenders(const Board& board, const Position& pawnPos, Color pawnColor) const {
    int bonus = 0;
    
    // Check all pieces of the same color to see if they can move to defend the pawn
    for (int rank = 0; rank < 8; rank++) {
        for (int file = 0; file < 8; file++) {
            Position piecePos(file, rank);
            Piece piece = board.getPiece(piecePos);
            
            // Skip empty squares, pawns, and enemy pieces
            if (piece.isEmpty() || piece.getColor() != pawnColor || piece.getType() == PieceType::PAWN) {
                continue;
            }
            
            // Generate all legal moves for this piece
            std::vector<Move> moves = board.generatePseudoLegalMoves(piecePos);
            
            // Check if any move can defend the pawn
            for (const Move& move : moves) {
                // Check if the move is to a square that would defend the pawn
                // For simplicity, we'll consider a move that puts the piece adjacent to the pawn
                // or a knight's move away as a defending move
                int fileDiff = abs(move.to.file - pawnPos.file);
                int rankDiff = abs(move.to.rank - pawnPos.rank);
                
                bool isDefendingMove = false;
                
                // Adjacent square (including diagonals)
                if (fileDiff <= 1 && rankDiff <= 1) {
                    isDefendingMove = true;
                }
                // Knight's move away
                else if ((fileDiff == 1 && rankDiff == 2) || (fileDiff == 2 && rankDiff == 1)) {
                    isDefendingMove = true;
                }
                
                if (isDefendingMove) {
                    // Check if the defending move is safe (the square is not under attack)
                    if (!board.isUnderAttack(move.to, (pawnColor == Color::WHITE) ? Color::BLACK : Color::WHITE)) {
                        // Assign bonus based on piece type
                        int pieceBonus = 0;
                        switch (piece.getType()) {
                            case PieceType::KNIGHT:
                                pieceBonus = 70; // Knights are excellent defenders - increased bonus
                                break;
                            case PieceType::BISHOP:
                                pieceBonus = 65; // Bishops are also excellent - increased bonus
                                break;
                            case PieceType::ROOK:
                                pieceBonus = 30; // Rooks are less ideal but still useful - increased bonus
                                break;
                            case PieceType::QUEEN:
                                pieceBonus = 10; // Queens should generally not be used for defense in opening
                                break;
                            default:
                                pieceBonus = 0;
                                break;
                        }
                        
                        // Check if the piece is moving from its starting position (development bonus)
                        bool isFromStartingPosition = false;
                        if (piece.getType() == PieceType::KNIGHT) {
                            if ((pawnColor == Color::WHITE && piecePos.rank == 0 && (piecePos.file == 1 || piecePos.file == 6)) || // b1, g1
                                (pawnColor == Color::BLACK && piecePos.rank == 7 && (piecePos.file == 1 || piecePos.file == 6))) { // b8, g8
                                isFromStartingPosition = true;
                            }
                        } else if (piece.getType() == PieceType::BISHOP) {
                            if ((pawnColor == Color::WHITE && piecePos.rank == 0 && (piecePos.file == 2 || piecePos.file == 5)) || // c1, f1
                                (pawnColor == Color::BLACK && piecePos.rank == 7 && (piecePos.file == 2 || piecePos.file == 5))) { // c8, f8
                                isFromStartingPosition = true;
                            }
                        }
                        
                        // Extra bonus if developing a piece from its starting position
                        if (isFromStartingPosition) {
                            pieceBonus += 40;
                        }
                        
                        // Extra bonus if the defending move is to a central square
                        if ((move.to.file >= 2 && move.to.file <= 5) && (move.to.rank >= 2 && move.to.rank <= 5)) {
                            pieceBonus += 25; // Central development bonus
                        }
                        
                        // Add bonus for this potential defender
                        bonus += pieceBonus;
                        
                        // We found a defender, no need to check other moves for this piece
                        break;
                    }
                }
            }
        }
    }
    
    return bonus;
}

int Evaluator::evaluateKingPawnShield(const Board& board) const {
    int score = 0;
    
    // This evaluation is primarily for the opening phase
    // Check if we're still in the opening by counting developed pieces
    int developedPieces = 0;
    for (int rank = 0; rank < 8; rank++) {
        for (int file = 0; file < 8; file++) {
            Position pos(file, rank);
            Piece piece = board.getPiece(pos);
            
            // Count pieces that have moved from their starting positions
            if (!piece.isEmpty() && piece.getType() != PieceType::PAWN && piece.getType() != PieceType::KING) {
                // Knights starting on b1, g1, b8, g8
                if (piece.getType() == PieceType::KNIGHT) {
                    if ((piece.getColor() == Color::WHITE && (pos.file != 1 && pos.file != 6)) || 
                        (piece.getColor() == Color::BLACK && (pos.file != 1 && pos.file != 6))) {
                        developedPieces++;
                    }
                }
                // Bishops starting on c1, f1, c8, f8
                else if (piece.getType() == PieceType::BISHOP) {
                    if ((piece.getColor() == Color::WHITE && pos.rank != 0) || 
                        (piece.getColor() == Color::BLACK && pos.rank != 7)) {
                        developedPieces++;
                    }
                }
                // Rooks starting on a1, h1, a8, h8
                else if (piece.getType() == PieceType::ROOK) {
                    if ((piece.getColor() == Color::WHITE && pos.rank != 0) || 
                        (piece.getColor() == Color::BLACK && pos.rank != 7)) {
                        developedPieces++;
                    }
                }
                // Queens starting on d1, d8
                else if (piece.getType() == PieceType::QUEEN) {
                    if ((piece.getColor() == Color::WHITE && (pos.file != 3 || pos.rank != 0)) || 
                        (piece.getColor() == Color::BLACK && (pos.file != 3 || pos.rank != 7))) {
                        developedPieces++;
                    }
                }
            }
        }
    }
    
    // If more than 6 pieces are developed, we're likely not in the opening anymore
    if (developedPieces > 6) {
        return score; // Skip this evaluation outside of the opening
    }
    
    // Find kings
    Position whiteKingPos(-1, -1);
    Position blackKingPos(-1, -1);
    
    for (int rank = 0; rank < 8; rank++) {
        for (int file = 0; file < 8; file++) {
            Position pos(file, rank);
            Piece piece = board.getPiece(pos);
            
            if (!piece.isEmpty() && piece.getType() == PieceType::KING) {
                if (piece.getColor() == Color::WHITE) {
                    whiteKingPos = pos;
                } else {
                    blackKingPos = pos;
                }
            }
        }
    }
    
    // Check for white king on g1 with f-pawn on f3
    if (whiteKingPos.isValid() && whiteKingPos.rank == 0 && whiteKingPos.file == 6) { // King on g1
        // Check f-pawn
        Position fPawnPos(5, 2); // f3 position
        Piece piece = board.getPiece(fPawnPos);
        
        if (!piece.isEmpty() && piece.getType() == PieceType::PAWN && piece.getColor() == Color::WHITE) {
            // The f-pawn has been pushed to f3 while king is on g1 - strongly penalize
            score -= 80; // Severe penalty
            
            // Check if the moved pawn exposes the king to attacks
            for (int attackRank = 3; attackRank < 8; attackRank++) { // Check ranks above f3
                // Check file (straight ahead)
                Position filePos(5, attackRank);
                Piece filePiece = board.getPiece(filePos);
                
                if (!filePiece.isEmpty() && filePiece.getColor() == Color::BLACK && 
                    (filePiece.getType() == PieceType::QUEEN || filePiece.getType() == PieceType::ROOK)) {
                    score -= 50; // Extra penalty for exposing king to rook/queen
                }
                
                // Check diagonals that could attack the king
                int diagFile = 6; // g-file (king's file)
                if (diagFile >= 0 && diagFile < 8 && attackRank - 2 == 0) { // If the diagonal goes to g1
                    Position diagPos(diagFile, attackRank);
                    Piece diagPiece = board.getPiece(diagPos);
                    
                    if (!diagPiece.isEmpty() && diagPiece.getColor() == Color::BLACK && 
                        (diagPiece.getType() == PieceType::QUEEN || diagPiece.getType() == PieceType::BISHOP)) {
                        score -= 60; // Severe penalty for exposing king to bishop/queen
                    }
                }
            }
        }
    }
    
    // Check for black king on g8 with f-pawn on f6
    if (blackKingPos.isValid() && blackKingPos.rank == 7 && blackKingPos.file == 6) { // King on g8
        // Check f-pawn
        Position fPawnPos(5, 5); // f6 position
        Piece piece = board.getPiece(fPawnPos);
        
        if (!piece.isEmpty() && piece.getType() == PieceType::PAWN && piece.getColor() == Color::BLACK) {
            // The f-pawn has been pushed to f6 while king is on g8 - strongly penalize
            score += 80; // Severe penalty (positive for white's advantage)
            
            // Check if the moved pawn exposes the king to attacks
            for (int attackRank = 4; attackRank >= 0; attackRank--) { // Check ranks below f6
                // Check file (straight ahead)
                Position filePos(5, attackRank);
                Piece filePiece = board.getPiece(filePos);
                
                if (!filePiece.isEmpty() && filePiece.getColor() == Color::WHITE && 
                    (filePiece.getType() == PieceType::QUEEN || filePiece.getType() == PieceType::ROOK)) {
                    score += 50; // Extra penalty for exposing king to rook/queen
                }
                
                // Check diagonals that could attack the king
                int diagFile = 6; // g-file (king's file)
                if (diagFile >= 0 && diagFile < 8 && 7 - attackRank == 2) { // If the diagonal goes to g8
                    Position diagPos(diagFile, attackRank);
                    Piece diagPiece = board.getPiece(diagPos);
                    
                    if (!diagPiece.isEmpty() && diagPiece.getColor() == Color::WHITE && 
                        (diagPiece.getType() == PieceType::QUEEN || diagPiece.getType() == PieceType::BISHOP)) {
                        score += 60; // Severe penalty for exposing king to bishop/queen
                    }
                }
            }
        }
    }
    
    return score;
}

int Evaluator::evaluateEarlyFPawnMoves(const Board& board) const {
    int score = 0;
    
    // Check if we're in the opening phase (fewer than 7 developed pieces)
    int developedPieces = 0;
    for (int rank = 0; rank < 8; rank++) {
        for (int file = 0; file < 8; file++) {
            Position pos(file, rank);
            Piece piece = board.getPiece(pos);
            if (!piece.isEmpty() && piece.getType() != PieceType::PAWN && piece.getType() != PieceType::KING) {
                // Count pieces that are not on their starting ranks as developed
                if ((piece.getColor() == Color::WHITE && pos.rank > 0) ||
                    (piece.getColor() == Color::BLACK && pos.rank < 7)) {
                    developedPieces++;
                }
            }
        }
    }
    
    bool isOpening = (developedPieces < 7);
    
    // Only apply this evaluation in the opening
    if (!isOpening) {
        return 0;
    }
    
    // Check for f-pawn moves
    // White f-pawn
    Position whiteFPawn2(5, 1); // f2
    Position whiteFPawn3(5, 2); // f3
    Position whiteFPawn4(5, 3); // f4
    
    // Black f-pawn
    Position blackFPawn7(5, 6); // f7
    Position blackFPawn6(5, 5); // f6
    Position blackFPawn5(5, 4); // f5
    
    // Check if white has moved the f-pawn
    Piece pieceOnF2 = board.getPiece(whiteFPawn2);
    Piece pieceOnF3 = board.getPiece(whiteFPawn3);
    Piece pieceOnF4 = board.getPiece(whiteFPawn4);
    
    // If f2 is empty and there's a white pawn on f3 or f4, white has moved the f-pawn
    if (pieceOnF2.isEmpty()) {
        if (!pieceOnF3.isEmpty() && pieceOnF3.getType() == PieceType::PAWN && pieceOnF3.getColor() == Color::WHITE) {
            // Apply penalty for f3
            score -= 30;
        }
        if (!pieceOnF4.isEmpty() && pieceOnF4.getType() == PieceType::PAWN && pieceOnF4.getColor() == Color::WHITE) {
            // Apply stronger penalty for f4
            score -= 60;
        }
    }
    
    // Check if black has moved the f-pawn
    Piece pieceOnF7 = board.getPiece(blackFPawn7);
    Piece pieceOnF6 = board.getPiece(blackFPawn6);
    Piece pieceOnF5 = board.getPiece(blackFPawn5);
    
    // If f7 is empty and there's a black pawn on f6 or f5, black has moved the f-pawn
    if (pieceOnF7.isEmpty()) {
        if (!pieceOnF6.isEmpty() && pieceOnF6.getType() == PieceType::PAWN && pieceOnF6.getColor() == Color::BLACK) {
            // Apply penalty for f6 (positive for white's advantage)
            score += 30;
        }
        if (!pieceOnF5.isEmpty() && pieceOnF5.getType() == PieceType::PAWN && pieceOnF5.getColor() == Color::BLACK) {
            // Apply stronger penalty for f5 (positive for white's advantage)
            score += 60;
        }
    }
    
    return score;
}

int Evaluator::evaluateMinorPieceDevelopmentForDefense(const Board& board) const {
    int score = 0;
    
    // This evaluation is primarily for the opening phase
    // Check if we're still in the opening by counting developed pieces
    int developedPieces = 0;
    for (int rank = 0; rank < 8; rank++) {
        for (int file = 0; file < 8; file++) {
            Position pos(file, rank);
            Piece piece = board.getPiece(pos);
            
            // Count pieces that have moved from their starting positions
            if (!piece.isEmpty() && piece.getType() != PieceType::PAWN && piece.getType() != PieceType::KING) {
                // Knights starting on b1, g1, b8, g8
                if (piece.getType() == PieceType::KNIGHT) {
                    if ((piece.getColor() == Color::WHITE && (pos.file != 1 && pos.file != 6)) || 
                        (piece.getColor() == Color::BLACK && (pos.file != 1 && pos.file != 6))) {
                        developedPieces++;
                    }
                }
                // Bishops starting on c1, f1, c8, f8
                else if (piece.getType() == PieceType::BISHOP) {
                    if ((piece.getColor() == Color::WHITE && pos.rank != 0) || 
                        (piece.getColor() == Color::BLACK && pos.rank != 7)) {
                        developedPieces++;
                    }
                }
                // Rooks starting on a1, h1, a8, h8
                else if (piece.getType() == PieceType::ROOK) {
                    if ((piece.getColor() == Color::WHITE && pos.rank != 0) || 
                        (piece.getColor() == Color::BLACK && pos.rank != 7)) {
                        developedPieces++;
                    }
                }
                // Queens starting on d1, d8
                else if (piece.getType() == PieceType::QUEEN) {
                    if ((piece.getColor() == Color::WHITE && (pos.file != 3 || pos.rank != 0)) || 
                        (piece.getColor() == Color::BLACK && (pos.file != 3 || pos.rank != 7))) {
                        developedPieces++;
                    }
                }
            }
        }
    }
    
    // If more than 6 pieces are developed, we're likely not in the opening anymore
    if (developedPieces > 6) {
        return score; // Skip this evaluation outside of the opening
    }
    
    // Find attacked pawns that need defense
    std::vector<Position> whitePawnsNeedingDefense;
    std::vector<Position> blackPawnsNeedingDefense;
    
    // First, identify all pawns that are under attack and have no defenders
    for (int rank = 0; rank < 8; rank++) {
        for (int file = 0; file < 8; file++) {
            Position pos(file, rank);
            Piece piece = board.getPiece(pos);
            
            // Only evaluate pawns
            if (!piece.isEmpty() && piece.getType() == PieceType::PAWN) {
                Color pawnColor = piece.getColor();
                Color enemyColor = (pawnColor == Color::WHITE) ? Color::BLACK : Color::WHITE;
                
                // Check if the pawn is under attack
                if (board.isUnderAttack(pos, enemyColor)) {
                    // Check if the pawn is defended by another piece
                    bool isDefended = board.isUnderAttack(pos, pawnColor);
                    
                    if (!isDefended) {
                        // This pawn is under attack and has no defenders
                        if (pawnColor == Color::WHITE) {
                            whitePawnsNeedingDefense.push_back(pos);
                        } else {
                            blackPawnsNeedingDefense.push_back(pos);
                        }
                    }
                }
            }
        }
    }
    
    // Now evaluate minor piece development for defense
    // First, check white's minor pieces
    for (int rank = 0; rank < 8; rank++) {
        for (int file = 0; file < 8; file++) {
            Position pos(file, rank);
            Piece piece = board.getPiece(pos);
            
            // Only evaluate knights and bishops
            if (!piece.isEmpty() && 
                (piece.getType() == PieceType::KNIGHT || piece.getType() == PieceType::BISHOP) && 
                piece.getColor() == Color::WHITE) {
                
                // Check if the piece is still in its starting position
                bool isInStartingPosition = false;
                
                if (piece.getType() == PieceType::KNIGHT) {
                    isInStartingPosition = (rank == 0 && (file == 1 || file == 6)); // b1 or g1
                } else if (piece.getType() == PieceType::BISHOP) {
                    isInStartingPosition = (rank == 0 && (file == 2 || file == 5)); // c1 or f1
                }
                
                // If there are pawns needing defense and this piece is in starting position
                if (!whitePawnsNeedingDefense.empty() && isInStartingPosition) {
                    // Generate all legal moves for this piece
                    std::vector<Move> moves = board.generatePseudoLegalMoves(pos);
                    
                    // Check if any move can defend a pawn
                    for (const Move& move : moves) {
                        for (const Position& pawnPos : whitePawnsNeedingDefense) {
                            // Check if the move is to a square that would defend the pawn
                            // For simplicity, we'll consider a move that puts the piece adjacent to the pawn
                            // or a knight's move away as a defending move
                            int fileDiff = abs(move.to.file - pawnPos.file);
                            int rankDiff = abs(move.to.rank - pawnPos.rank);
                            
                            bool isDefendingMove = false;
                            
                            // Adjacent square (including diagonals)
                            if (fileDiff <= 1 && rankDiff <= 1) {
                                isDefendingMove = true;
                            }
                            // Knight's move away
                            else if ((fileDiff == 1 && rankDiff == 2) || (fileDiff == 2 && rankDiff == 1)) {
                                isDefendingMove = true;
                            }
                            
                            if (isDefendingMove) {
                                // Check if the defending move is safe (the square is not under attack)
                                if (!board.isUnderAttack(move.to, Color::BLACK)) {
                                    // Strong bonus for developing a minor piece to defend a pawn
                                    score += 35;
                                    
                                    // Extra bonus if the piece is developed to a central square
                                    if ((move.to.file >= 2 && move.to.file <= 5) && (move.to.rank >= 2 && move.to.rank <= 5)) {
                                        score += 15; // Additional bonus for central development
                                    }
                                    
                                    // We found a good defending move, no need to check other pawns for this move
                                    break;
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    // Now check black's minor pieces
    for (int rank = 0; rank < 8; rank++) {
        for (int file = 0; file < 8; file++) {
            Position pos(file, rank);
            Piece piece = board.getPiece(pos);
            
            // Only evaluate knights and bishops
            if (!piece.isEmpty() && 
                (piece.getType() == PieceType::KNIGHT || piece.getType() == PieceType::BISHOP) && 
                piece.getColor() == Color::BLACK) {
                
                // Check if the piece is still in its starting position
                bool isInStartingPosition = false;
                
                if (piece.getType() == PieceType::KNIGHT) {
                    isInStartingPosition = (rank == 7 && (file == 1 || file == 6)); // b8 or g8
                } else if (piece.getType() == PieceType::BISHOP) {
                    isInStartingPosition = (rank == 7 && (file == 2 || file == 5)); // c8 or f8
                }
                
                // If there are pawns needing defense and this piece is in starting position
                if (!blackPawnsNeedingDefense.empty() && isInStartingPosition) {
                    // Generate all legal moves for this piece
                    std::vector<Move> moves = board.generatePseudoLegalMoves(pos);
                    
                    // Check if any move can defend a pawn
                    for (const Move& move : moves) {
                        for (const Position& pawnPos : blackPawnsNeedingDefense) {
                            // Check if the move is to a square that would defend the pawn
                            // For simplicity, we'll consider a move that puts the piece adjacent to the pawn
                            // or a knight's move away as a defending move
                            int fileDiff = abs(move.to.file - pawnPos.file);
                            int rankDiff = abs(move.to.rank - pawnPos.rank);
                            
                            bool isDefendingMove = false;
                            
                            // Adjacent square (including diagonals)
                            if (fileDiff <= 1 && rankDiff <= 1) {
                                isDefendingMove = true;
                            }
                            // Knight's move away
                            else if ((fileDiff == 1 && rankDiff == 2) || (fileDiff == 2 && rankDiff == 1)) {
                                isDefendingMove = true;
                            }
                            
                            if (isDefendingMove) {
                                // Check if the defending move is safe (the square is not under attack)
                                if (!board.isUnderAttack(move.to, Color::WHITE)) {
                                    // Strong bonus for developing a minor piece to defend a pawn
                                    score -= 35; // Negative for white's advantage
                                    
                                    // Extra bonus if the piece is developed to a central square
                                    if ((move.to.file >= 2 && move.to.file <= 5) && (move.to.rank >= 2 && move.to.rank <= 5)) {
                                        score -= 15; // Additional bonus for central development
                                    }
                                    
                                    // We found a good defending move, no need to check other pawns for this move
                                    break;
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    return score;
}

} // namespace chess
