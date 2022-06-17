# Helltaker Solver

This is a solver for the 8 puzzles (puzzle in chapter 8 is too easy) present in the [Helltaker](https://store.steampowered.com/app/1289310/Helltaker/) game on Steam (it's free!).

It uses A* search with optimizations to prune the search space and allows additional human insights to guide the search.

Every puzzle can be solved within 23000 steps while keeping at the maximum 10000 additional states in memory during the search.

## How to Run
To solve all 8 puzzles and output solution: `python solver.py`.

Individual puzzles are present in `puzzles.py`.

<br>

# Puzzles
In each of the 8 puzzles, the player is tasked to go from a start point to a goal point within a limited number of steps in a map. There are obstructions along the way and some puzzles require the player to obtain a key on the map to open a lock in order to proceed.

    Puzzle 1:
    # # # # # # # # #   # - Walls
    # # # # #   S # #   S - Starting point
    # #      M    # #   M - Monster that can be killed when pushed
    # #    M   M# # #       against walls or blocks
    #     # # # # # #       
    #    B     B  # #   B - Block that can only be pushed
    #    B   B    G #   G - Goal point
    # # # # # # # # # 

<br>

# Why are those puzzles interesting?
Although the puzzle setting is simple to a human player - navigate the game board and reach the goal, it's not straightforward how to teach the computer to solve those puzzles.

Classic graph search algorithms have 2 limitations that need to be addressed:

<details>
<summary><b>Repeating Paths</b></summary>
To start with, it's OK, and sometimes even necessary, to repeat a path so long as the goal is reached. As in the following example, the player needs to go to the left, obtain a key and go back to open a lock to reach the goal.

The left most 3 squares are visited twice and

    # # # # # # # # #   K - Key
    # K     S   L G #   L - Lock
    # # # # # # # # # 
    ← ← ←S
    → → → → → →G

It's possible that a programmer may choose to divide the solution into steps-
        
    1) obtain the key
    2) open the lock
    3) reach the goal
and use any graph searching algorithm to solve each step to form a combined solution.

However, we'd need an "intelligent" being, either some AI or some a human, to help decompose a large objective into easy to solve steps like the ones above.

This put much work on the programmer to learn the game and write specific and correct rules to solve the puzzle.
</details>
and

<details>
<summary><b>State Change</b></summary>
When the player obtains a key or pushes a block, the game board changes and so does the search space from the algorithm's perspective.

In the previous example, once the player obtains the key, they can now access the goal point but not before. Obtaining the key signifies a state change and the algorithm must adjust to that by restarting the search.
</details>

<br>

# Algorithm Design
The basic design is like A* but with the current game board also saved with the coordinates of the player.

The cost used by A* is a combination of the real cost and a heuristic computed as the manhattan distance between the current player location and the goal location.

## Allow Repeating Paths on State Change
It's easy to reason that repeating paths only make sense when the game board state has changed (ie. a key is obtained, a block is removed) as new locations may be accessible or shorter paths are viable. Therefore, it's simple enough to restart the search whenever the game board changes.

## Optimization 1: Reduced State Changes
However, not all state changes are meaningful changes and restarting on every game board tile change is a bit wasteful. Rules can be written to reduce the number of times restarts happen.

For example, in the game, there are spikes at fixed locations that toggles on and off whenever the player moves. The algorithm is written to disregard those state changes as they don't change the algorithm's search space.


## Optimization 2: More Guided Searches with Location Hints
The program accepts a list of coordinates to prioritize visiting those points first when choosing the next move. The points can be chosen by an AI or a human player good at the game.

They are only hints to help guide the search but don't affect the correctness of the algorithm.

