#ifndef CHESS_ENGINE_H
#define CHESS_ENGINE_H

#include "board.h"
#include "evaluate.h"
#include <chrono>
#include <limits>

namespace chess {

/**
 * @brief A simple chess engine that can look 2 moves into the future
 */
class Engine {
private:
    int maxDepth;
    int nodesSearched;
    Evaluator evaluator;
    std::chrono::time_point<std::chrono::steady_clock> startTime;
    
public:
    Engine(int depth = 2) : maxDepth(depth), nodesSearched(0) {}
    
    // Set the search depth
    void setDepth(int depth) { maxDepth = depth; }
    
    // Get the best move for the current position
    Move getBestMove(const Board& board);
    
    // Minimax algorithm with alpha-beta pruning
    int minimax(Board& board, int depth, int alpha, int beta, bool maximizingPlayer);
    
    // Get the number of nodes searched in the last search
    int getNodesSearched() const { return nodesSearched; }
    
    // Reset the node counter
    void resetNodesSearched() { nodesSearched = 0; }
};

} // namespace chess

#endif // CHESS_ENGINE_H
