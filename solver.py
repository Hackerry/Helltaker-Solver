import heapq
import time
from engine import Dir, Engine, Player, Tile

class Solver:
    def __init__(self, board_str, target_locs=[]):
        self.engine = Engine(board_str)
        self.target_locs = target_locs + [self.engine.goal_loc]
    
    def is_new_state(self, hash1, hash2):
        board1 = self.engine.states[hash1]
        board2 = self.engine.states[hash2]
        
        for i in range(self.engine.board_height):
            for j in range(self.engine.board_width):
                if board1[i][j] != board2[i][j]:
                    # Spike difference - doesn't matter
                    if ((board1[i][j][0] == Tile.SPIKE_UP and board2[i][j][0] == Tile.SPIKE_DOWN) or \
                        (board1[i][j][0] == Tile.SPIKE_DOWN and board2[i][j][0] == Tile.SPIKE_UP)) and \
                        board1[i][j][1] == board2[i][j][1]:
                            continue
                    # Otherwise, other difference
                    return True
        return False

    def has_update(self, player, new_state):
        # print(player.steps, visited_states)
        
        # Old state
        if player.last_state_hash != None and \
            (new_state == player.last_state_hash or not self.is_new_state(new_state, player.last_state_hash)):
            if player.player_loc in player.explored:
                return False
            else:
                player.explored.add(player.player_loc)
                return True
        else:
            # New state
            player.last_state_hash = new_state
            player.explored = set()
            
            return True
    
    def compute_heuristic(self, player):
        new_heuristic = 0
        last = player.player_loc
        for i in range(len(player.target_locs_done), len(self.target_locs)):
            new_heuristic += abs(last[0]-self.target_locs[i][0])
            new_heuristic += abs(last[1]-self.target_locs[i][1])
            last = self.target_locs[i]
        player.heuristic_cost = player.cost + new_heuristic
        
    def search(self, cost_limit=40):
        e = self.engine
        frontier = []
        duplicate_cost = set()
        max_frontier_size = 0
        heapq.heappush(frontier, (e.player.copy(), e.init_state_hash))
        iteration_count = 0
        won = False
        
        while len(frontier) > 0:
            (set_player, set_hash) = heapq.heappop(frontier)
            
            # Check target_loc done
            target_done_count = len(set_player.target_locs_done)
            if len(self.target_locs) != target_done_count and \
                set_player.player_loc == self.target_locs[target_done_count]:
                    # Update heuristic cost
                    set_player.target_locs_done.append(self.target_locs[target_done_count])
            
            # Win check
            if set_player.player_loc == e.goal_loc:
                won = True
                break
            
            # Limit check    
            if set_player.cost > cost_limit: raise Exception("Cost limit exceeded")
            
            # print("Curr player:", set_player)
            
            # Move in 4 directions
            success, state_hash = e.move(Dir.LEFT, board_hash=set_hash, player=set_player)
            if success and (e.player.player_loc, e.player.cost, state_hash) not in duplicate_cost and self.has_update(e.player, state_hash):
                e.player.steps.append((Dir.LEFT, set_hash))
                self.compute_heuristic(e.player)
                heapq.heappush(frontier, (e.player, state_hash))
                duplicate_cost.add((e.player.player_loc, e.player.cost, state_hash))
                
            success, state_hash = e.move(Dir.RIGHT, board_hash=set_hash, player=set_player)
            if success and (e.player.player_loc, e.player.cost, state_hash) not in duplicate_cost and self.has_update(e.player, state_hash):
                e.player.steps.append((Dir.RIGHT, set_hash))
                self.compute_heuristic(e.player)
                heapq.heappush(frontier, (e.player, state_hash))
                duplicate_cost.add((e.player.player_loc, e.player.cost, state_hash))
            
            success, state_hash = e.move(Dir.UP, board_hash=set_hash, player=set_player)
            if success and (e.player.player_loc, e.player.cost, state_hash) not in duplicate_cost and self.has_update(e.player, state_hash):
                e.player.steps.append((Dir.UP, set_hash))
                self.compute_heuristic(e.player)
                heapq.heappush(frontier, (e.player, state_hash))
                duplicate_cost.add((e.player.player_loc, e.player.cost, state_hash))
            
            success, state_hash = e.move(Dir.DOWN, board_hash=set_hash, player=set_player)
            if success and (e.player.player_loc, e.player.cost, state_hash) not in duplicate_cost and self.has_update(e.player, state_hash):
                e.player.steps.append((Dir.DOWN, set_hash))
                self.compute_heuristic(e.player)
                heapq.heappush(frontier, (e.player, state_hash))
                duplicate_cost.add((e.player.player_loc, e.player.cost, state_hash))
            
            iteration_count += 1
            if len(frontier) > max_frontier_size:
                max_frontier_size = len(frontier)
        
        if won:
            print("Solution found with cost", set_player.cost)
            self.print_steps(set_player)
        else:
            print("No solution found")
        print("Stop in %s iterations with max %s states in memory" % (iteration_count, max_frontier_size))
            
    def print_steps(self, end_player):
        simulate_player = Player(self.engine.start_loc)
        counter = 0
        steps = []
        
        for (step, step_hash) in end_player.steps:
            board = self.engine.states[step_hash]
            temp = board[simulate_player.player_loc[0]][simulate_player.player_loc[1]]
            board[simulate_player.player_loc[0]][simulate_player.player_loc[1]] = (temp[0], Tile.PLAYER)
            print(Engine.to_board_str(board))
            board[simulate_player.player_loc[0]][simulate_player.player_loc[1]] = temp
            
            success, _ = self.engine.move(step, board_hash=step_hash, player=simulate_player)
            if not success: raise Exception("Invalid move %s in solution: %s\n%s" % (step, counter, Engine.to_board_str(board)))
            
            simulate_player = self.engine.player
            
            print("\nCost:", simulate_player.cost, "Step:", step, "\n")
            steps.append(step)
            
            counter += 1
        
        board = self.engine.board
        board[self.engine.goal_loc[0]][self.engine.goal_loc[1]] = (Tile.GOAL, Tile.PLAYER)
        print(Engine.to_board_str(board))
        
        print("Solution found with cost:", end_player.cost)
        print("\nSteps:", steps)

def solve_board(solver):
    start = time.time()
    solver.search(cost_limit=45)
    end = time.time()
    print("Time elapsed: %fs" % (end-start))
            
import puzzles
for i in range(len(puzzles.puzzles)):
    s = Solver(puzzles.puzzles[i], target_locs=puzzles.target_locs[i])
    solve_board(s)