#include "chess/engine.h"
#include <algorithm>
#include <iostream>

namespace chess {

Move Engine::getBestMove(const Board& board) {
    // reset the node counter
    resetNodesSearched();
    
    // start the timer
    startTime = std::chrono::steady_clock::now();
    
    // get all legal moves
    std::vector<Move> legalMoves = board.generateLegalMoves();
    
    if (legalMoves.empty()) {
        return Move(); // no legal moves
    }
    
    Move bestMove = legalMoves[0];
    int bestScore = (board.getSideToMove() == Color::WHITE) ? 
                    std::numeric_limits<int>::min() : 
                    std::numeric_limits<int>::max();
    
    // evaluate each move
    for (const Move& move : legalMoves) {
        // make a copy of the board
        Board testBoard = board;
        
        // make the move
        testBoard.makeMove(move);
        
        // evaluate the position using minimax
        int score = minimax(testBoard, maxDepth - 1, 
                           std::numeric_limits<int>::min(), 
                           std::numeric_limits<int>::max(), 
                           board.getSideToMove() != Color::WHITE);
        
        // Update the best move
        if ((board.getSideToMove() == Color::WHITE && score > bestScore) ||
            (board.getSideToMove() == Color::BLACK && score < bestScore)) {
            bestScore = score;
            bestMove = move;
        }
    }
    
    // Calculate search time
    auto endTime = std::chrono::steady_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(endTime - startTime).count();
    
    std::cout << "Nodes searched: " << nodesSearched << std::endl;
    std::cout << "Time taken: " << duration << " ms" << std::endl;
    std::cout << "Best move: " << bestMove.toAlgebraic() << " with score: " << bestScore << std::endl;
    
    return bestMove;
}

int Engine::minimax(Board& board, int depth, int alpha, int beta, bool maximizingPlayer) {
    // increment the node counter
    nodesSearched++;
    
    // base case: leaf node or terminal position
    if (depth == 0) {
        return evaluator.evaluate(board);
    }
    
    std::vector<Move> legalMoves = board.generateLegalMoves();
    
    // check for checkmate or stalemate
    if (legalMoves.empty()) {
        if (board.isInCheck()) {
            // checkmate (worst possible score, but adjusted for depth)
            return maximizingPlayer ? -20000 + (maxDepth - depth) : 20000 - (maxDepth - depth);
        } else {
            // stalemate (draw)
            return 0;
        }
    }
    
    if (maximizingPlayer) {
        int maxEval = std::numeric_limits<int>::min();
        
        for (const Move& move : legalMoves) {
            // make a copy of the board
            Board testBoard = board;
            
            // make the move
            testBoard.makeMove(move);
            
            // recursively evaluate the position
            int eval = minimax(testBoard, depth - 1, alpha, beta, false);
            maxEval = std::max(maxEval, eval);
            
            // alpha-beta pruning
            alpha = std::max(alpha, eval);
            if (beta <= alpha) {
                break;
            }
        }
        
        return maxEval;
    } else {
        int minEval = std::numeric_limits<int>::max();
        
        for (const Move& move : legalMoves) {
            // make a copy of the board
            Board testBoard = board;
            
            // make the move
            testBoard.makeMove(move);
            
            // recursively evaluate the position :nerd:
            int eval = minimax(testBoard, depth - 1, alpha, beta, true);
            minEval = std::min(minEval, eval);
            
            // alpha-beta pruning (yup yup yup)
            beta = std::min(beta, eval);
            if (beta <= alpha) {
                break;
            }
        }
        
        return minEval;
    }
}

} // namespace chess
