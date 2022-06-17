import copy
from enum import Enum

class Tile(Enum):
    # Empty tile
    SPACE = " "
    
    # Fixed tile
    START = "S"
    GOAL = "G"
    WALL = "#"
    SPIKE_UP = "A"
    SPIKE_DOWN = "-"
    FIX_SPIKE = "Y"
    KEY = "K"
    LOCK = "L"
    
    # Movable object
    MONSTER = "M"
    BRICK = "B"
    
    # For print solution use only
    PLAYER = "O"

    def is_space(this):
        return this[0] != Tile.WALL and this[1] != Tile.BRICK and this[1] != Tile.MONSTER
    
    def is_against_obstruction(next):
        return next[0] == Tile.WALL or next[0] == Tile.LOCK \
            or next[0] == Tile.SPIKE_UP or next[0] == Tile.FIX_SPIKE \
            or next[1] == Tile.BRICK or next[1] == Tile.MONSTER
    def is_movable(this, next):
        return (this[1] == Tile.BRICK or this[1] == Tile.MONSTER) and not Tile.is_against_obstruction(next)
    def is_killable(this, next):
        return this[1] == Tile.MONSTER and Tile.is_against_obstruction(next)
        
class Dir(Enum):
    # LEFT = "←"
    # RIGHT = "→"
    # UP = "↑"
    # DOWN = "↓"
    
    LEFT = "L"
    RIGHT = "R"
    UP = "U"
    DOWN = "D"
    
    def __str__(self):
        return self.value
    def __repr__(self):
        return self.value

class Player:
    def __init__(self, player_loc, cost=0, has_key=False):
        self.player_loc = player_loc
        self.cost = cost
        self.has_key = has_key
        
        # For solver use
        self.steps = []
        self.explored = set()
        self.last_state_hash = None
        self.target_locs_done = []
        self.heuristic_cost = 0
    
    def copy(self):
        return copy.deepcopy(self)
    
    def __str__(self):
        return "%s-%s" % (self.player_loc, self.cost)
    def __repr__(self):
        return "%s-%s" % (self.player_loc, self.cost)
    
    # For hashing key and comparisons for duplicate
    def __eq__(self, other):
        return self.cost == other.cost and self.player_loc == other.player_loc
    
    # For priority queue
    def __lt__(self, other):
        if self.heuristic_cost < other.heuristic_cost:
            return True
        elif self.heuristic_cost == other.heuristic_cost:
            if self.cost < other.cost:
                return True
            elif self.cost == other.cost:
                return self.player_loc < other.player_loc
        return False

class Engine:
    def __init__(self, board_str):
        self.board = self.from_board_str(board_str)
        self.player = Player(self.start_loc)
        
        # For solver use
        self.init_state_hash = hash(Engine.to_board_str(self.board))
        
        # Store states and hash
        self.states = dict()
        self.states[self.init_state_hash] = copy.deepcopy(self.board)
    
    def try_move_to(self, player_loc, move_loc):
        move_tile = self.board[move_loc[0]][move_loc[1]]
        
        # Move to a wall
        if move_tile[0] == Tile.WALL:
            return False
        
        # Move to a lock
        if move_tile[0] == Tile.LOCK:
            if self.player.has_key:
                self.player.player_loc = move_loc
                self.has_key = False
                self.board[move_loc[0]][move_loc[1]] = (Tile.SPACE, Tile.SPACE)
                return True
            else:
                return False
        
        # Move to a space
        if Tile.is_space(move_tile):
            self.player.player_loc = move_loc
            
            # Check obtain key
            if move_tile[0] == Tile.KEY:
                self.player.has_key = True
                self.board[move_loc[0]][move_loc[1]] = (Tile.SPACE, move_tile[1])
            return True
        
        # Kill a monster
        next_loc = (2*move_loc[0]-player_loc[0], 2*move_loc[1]-player_loc[1])
        try:
            next_tile = self.board[next_loc[0]][next_loc[1]]
        except:
            print("Next loc:", player_loc, move_loc, next_loc)
            print(Engine.to_board_str(self.board))
        if Tile.is_killable(move_tile, next_tile):
            self.board[move_loc[0]][move_loc[1]] = (move_tile[0], Tile.SPACE)
            return True
        
        # Move a brick or monster
        if Tile.is_movable(move_tile, next_tile):
            self.board[next_loc[0]][next_loc[1]] = (next_tile[0], move_tile[1])
            self.board[move_loc[0]][move_loc[1]] = (move_tile[0], Tile.SPACE)
            return True
    
    def is_win(self):
        return self.goal_loc == self.player.player_loc
        
    def move(self, direction, board_hash=None, player=None):      
        # Update board to given state
        if board_hash != None:
            if board_hash not in self.states: raise Exception("State hash not found:", self.states, board_hash)
            self.board = copy.deepcopy(self.states[board_hash])
            self.player = copy.deepcopy(player)
        
        # Get tile to move to
        if direction == Dir.LEFT: move_loc = (self.player.player_loc[0], self.player.player_loc[1]-1)
        elif direction == Dir.RIGHT: move_loc = (self.player.player_loc[0], self.player.player_loc[1]+1)
        elif direction == Dir.UP: move_loc = (self.player.player_loc[0]-1, self.player.player_loc[1])
        elif direction == Dir.DOWN: move_loc = (self.player.player_loc[0]+1, self.player.player_loc[1])
        
        # Check can move
        if move_loc[0] < 0 or move_loc[1] < 0 or move_loc[0] >= len(self.board) or move_loc[1] >= len(self.board[0]) \
            or not self.try_move_to(self.player.player_loc, move_loc):
            return (False, None)
        
        # Update state
        self.update_spikes()
        
        # Move and compute cost
        tile = self.board[self.player.player_loc[0]][self.player.player_loc[1]][0]
        if tile == Tile.SPIKE_UP or tile == Tile.FIX_SPIKE:
            self.player.cost += 2
        else:
            self.player.cost += 1
        
        # Register new state
        state_hash = hash(Engine.to_board_str(self.board))
        if state_hash not in self.states:
            self.states[state_hash] = copy.deepcopy(self.board)
        
        # Return state
        # print(Engine.to_board_str(self.board))
        return (True, state_hash)
    
    def update_spikes(self):
        for i in range(self.board_height):
            for j in range(self.board_width):
                if self.board[i][j][0] == Tile.SPIKE_UP:
                    self.board[i][j] = (Tile.SPIKE_DOWN, self.board[i][j][1])
                elif self.board[i][j][0] == Tile.SPIKE_DOWN:
                    self.board[i][j] = (Tile.SPIKE_UP, self.board[i][j][1])
    
    def from_board_str(self, board_str):
        result = [[(Tile(row[i]), Tile(row[i+1])) for i in range(0, len(row), 2)] for row in board_str.split("\n") if row != ""]
        
        self.start_loc = None
        self.goal_loc = None
        
        # Ensure matrix property
        self.board_width = len(result[0])
        self.board_height = len(result)
        for i in range(self.board_height):
            if len(result[i]) != self.board_width:
                raise Exception("Width mismatch: %s-%s" % (self.board_width, len(result[i])))
            
            for j in range(self.board_width):
                if result[i][j][0] == Tile.START:
                    if self.start_loc != None: raise Exception("More than 1 starting point")
                    self.start_loc = (i, j)
                if result[i][j][0] == Tile.GOAL:
                    if self.goal_loc != None: raise Exception("More than 1 goal")
                    self.goal_loc = (i, j)
                if (i == 0 or i == self.board_height-1 or j == 0 or j == self.board_width-1) and result[i][j][0] != Tile.WALL:
                    raise Exception("Maze not bounded by walls")
            
        if self.start_loc == None: raise Exception("No starting point set")
        if self.goal_loc == None: raise Exception("No goal set")

        return result
    
    def to_board_str(board):
        result = ""
        for row in board:
            for cell in row:
                result += cell[0].value
                result += cell[1].value
            result += "\n"
        return result[:-1]

if __name__ == "__main__":
    board = """
# # # # # # 
# S     G # 
# # # # # # 
"""

    e = Engine(board)
    print(e.start_loc, e.goal_loc)
    print("Move:", e.move(Dir.RIGHT), e.player)
    print("Won:", e.is_win())
    print("Move:", e.move(Dir.RIGHT), e.player)
    print("Won:", e.is_win())
    print("Move:", e.move(Dir.RIGHT), e.player)
    print("Won:", e.is_win())
    print("Move:", e.move(Dir.RIGHT), e.player)
    print("Won:", e.is_win())