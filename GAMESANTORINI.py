import pygame, sys, random, math, time, copy
pygame.init()

WIDTH, HEIGHT = 600, 600
ROWS, COLS = 5, 5
CELL_SIZE = WIDTH // COLS

WHITE   = (255,255,255)
BLACK   = (0,0,0)
BLUE    = (0,0,255)      
YELLOW  = (255,255,0)    
GREEN   = (0,255,0)      
RED     = (255,0,0)      
GRAY    = (200,200,200)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Santorini: Human vs. AI")
font = pygame.font.SysFont(None, 24)
rules_font = pygame.font.SysFont(None, 20)
clock = pygame.time.Clock()

try:
    move_sound = pygame.mixer.Sound("move.wav")
except:
    move_sound = None

board = [[0 for _ in range(COLS)] for _ in range(ROWS)]
workers = {(0,0):1, (0,4):1, (4,0):2, (4,4):2}
current_player = 1  
state = "select_worker"   
selected_worker = None

def show_rules():
    screen.fill(WHITE)
    rules = [
        "Santorini Rules:",
        "",
        "Each player controls 2 workers.",
        "Objective: Move one worker onto a level 3 building.",
        "",
        "Turn Phases (Human):",
        "1. Select Worker: Click one of your blue pieces.",
        "2. Move: Click a highlighted GREEN cell adjacent to it.",
        "   - You can move up at most 1 level.",
        "3. Build: Click a highlighted RED cell adjacent to your worker.",
        "   - Building increases the level; level 4 (D) is a dome.",
        "",
        "Win: Moving onto a level 3 cell wins the game.",
        "",
        "Bot (Yellow) uses AI to choose its move.",
        "",
        "Press BACKSPACE to start."
    ]
    y_offset = 10
    line_spacing = 22
    for rule in rules:
        text = rules_font.render(rule, True, BLACK)
        screen.blit(text, (10, y_offset))
        y_offset += line_spacing
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
                waiting = False

def draw_board():
    screen.fill(WHITE)
    for row in range(ROWS):
        for col in range(COLS):
            rect = pygame.Rect(col*CELL_SIZE, row*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, BLACK, rect, 2)
            level = board[row][col]
            if level > 0:
                display = str(level) if level < 4 else "D"
                text = font.render(display, True, BLACK)
                screen.blit(text, (col*CELL_SIZE+5, row*CELL_SIZE+5))
    if state == "select_move" and selected_worker:
        for pos in valid_moves(selected_worker):
            r, c = pos
            highlight = pygame.Rect(c*CELL_SIZE, r*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, GREEN, highlight, 3)
    elif state == "select_build" and selected_worker:
        for pos in valid_builds(selected_worker):
            r, c = pos
            highlight = pygame.Rect(c*CELL_SIZE, r*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, RED, highlight, 3)
    for pos, player in workers.items():
        row, col = pos
        center = (col*CELL_SIZE + CELL_SIZE//2, row*CELL_SIZE + CELL_SIZE//2)
        color = BLUE if player==1 else YELLOW
        pygame.draw.circle(screen, color, center, CELL_SIZE//4)
        if selected_worker == pos:
            pygame.draw.circle(screen, BLACK, center, CELL_SIZE//4, 3)
    turn_text = font.render(f"Player {current_player}'s turn: {state}", True, BLACK)
    screen.blit(turn_text, (10, HEIGHT-40))
    pygame.display.flip()

def get_cell_center(pos):
    row, col = pos
    return (col*CELL_SIZE + CELL_SIZE//2, row*CELL_SIZE + CELL_SIZE//2)

def animate_movement(start, end, duration=300):
    start_time = pygame.time.get_ticks()
    while True:
        elapsed = pygame.time.get_ticks() - start_time
        t = min(1, elapsed / duration)
        current_x = start[0] + t*(end[0]-start[0])
        current_y = start[1] + t*(end[1]-start[1])
        draw_board()
        color = BLUE if current_player==1 else YELLOW
        pygame.draw.circle(screen, color, (int(current_x), int(current_y)), CELL_SIZE//4)
        pygame.display.flip()
        if t >= 1:
            break
        clock.tick(60)
    if move_sound:
        move_sound.play()

def adjacent_positions(pos):
    r, c = pos
    positions = []
    for dr in [-1,0,1]:
        for dc in [-1,0,1]:
            if dr==0 and dc==0:
                continue
            nr, nc = r+dr, c+dc
            if 0<=nr<ROWS and 0<=nc<COLS:
                positions.append((nr, nc))
    return positions

def valid_moves(worker_pos):
    moves = []
    r, c = worker_pos
    current_level = board[r][c]
    for pos in adjacent_positions(worker_pos):
        nr, nc = pos
        if pos in workers:
            continue
        if board[nr][nc] == 4:
            continue
        if board[nr][nc] <= current_level + 1:
            moves.append(pos)
    return moves

def valid_builds(worker_pos):
    builds = []
    for pos in adjacent_positions(worker_pos):
        r, c = pos
        if pos in workers:
            continue
        if board[r][c] < 4:
            builds.append(pos)
    return builds

def handle_click(mouse_pos):
    global state, selected_worker, current_player, workers, board
    col = mouse_pos[0] // CELL_SIZE
    row = mouse_pos[1] // CELL_SIZE
    clicked = (row, col)
    if state == "select_worker":
        if clicked in workers and workers[clicked]==current_player:
            selected_worker = clicked
            state = "select_move"
    elif state == "select_move":
        if clicked in valid_moves(selected_worker):
            start_pixel = get_cell_center(selected_worker)
            end_pixel = get_cell_center(clicked)
            animate_movement(start_pixel, end_pixel, duration=300)
            workers[clicked] = workers[selected_worker]
            del workers[selected_worker]
            selected_worker = clicked
            if board[row][col] == 3:
                print("Player 1 wins by moving!")
                pygame.quit(); sys.exit()
            state = "select_build"
    elif state == "select_build":
        if clicked in valid_builds(selected_worker):
            board[row][col] += 1
            selected_worker = None
            state = "select_worker"
            current_player = 2

class GameState:
    def __init__(self, board, workers, current_player):
        self.board = [row[:] for row in board]
        self.workers = dict(workers)
        self.current_player = current_player
    def copy(self):
        return GameState(self.board, self.workers, self.current_player)

def get_adjacent_positions(pos, rows, cols):
    r, c = pos
    positions = []
    for dr in [-1,0,1]:
        for dc in [-1,0,1]:
            if dr==0 and dc==0:
                continue
            nr, nc = r+dr, c+dc
            if 0<=nr<rows and 0<=nc<cols:
                positions.append((nr, nc))
    return positions

def legal_moves_for_worker(state, worker_pos):
    moves = []
    r, c = worker_pos
    current_level = state.board[r][c]
    for pos in get_adjacent_positions(worker_pos, ROWS, COLS):
        nr, nc = pos
        if pos in state.workers:
            continue
        if state.board[nr][nc] == 4:
            continue
        if state.board[nr][nc] <= current_level + 1:
            moves.append(pos)
    return moves

def legal_builds_for_worker(state, worker_pos):
    builds = []
    for pos in get_adjacent_positions(worker_pos, ROWS, COLS):
        r, c = pos
        if pos in state.workers:
            continue
        if state.board[r][c] < 4:
            builds.append(pos)
    return builds

def get_legal_moves(state):
    moves = []
    for worker in state.workers:
        if state.workers[worker]==state.current_player:
            possible_moves = legal_moves_for_worker(state, worker)
            for m in possible_moves:
                temp_state = state.copy()
                temp_state.workers.pop(worker)
                temp_state.workers[m] = state.current_player
                builds = legal_builds_for_worker(temp_state, m)
                for b in builds:
                    moves.append((worker, m, b))
    return moves

def apply_move(state, move):
    worker, m, build = move
    player = state.workers.pop(worker)
    state.workers[m] = player
    br, bc = build
    state.board[br][bc] = min(state.board[br][bc]+1, 4)
    r, c = m
    if state.board[r][c]==3:
        return player
    state.current_player = 1 if state.current_player==2 else 2
    return 0

def is_terminal(state):
    if not get_legal_moves(state):
        return True
    return False

def simulate_random_game(state):
    sim_state = state.copy()
    while True:
        moves = get_legal_moves(sim_state)
        if not moves:
            return 1 if sim_state.current_player==2 else 2
        move = random.choice(moves)
        winner = apply_move(sim_state, move)
        if winner != 0:
            return winner

class Node:
    def __init__(self, state, move=None, parent=None):
        self.state = state.copy()
        self.move = move
        self.parent = parent
        self.children = []
        self.wins = 0
        self.visits = 0
    def is_fully_expanded(self):
        return len(self.children)==len(get_legal_moves(self.state))
    def best_child(self, c_param=math.sqrt(2)):
        choices = []
        for child in self.children:
            uct = (child.wins/child.visits) + c_param * math.sqrt(math.log(self.visits)/child.visits)
            choices.append(uct)
        return self.children[choices.index(max(choices))]

def mcts(root_state, iterations=500):
    root_node = Node(root_state)
    for _ in range(iterations):
        node = root_node
        state = root_state.copy()
        while node.children and node.is_fully_expanded():
            node = node.best_child()
            apply_move(state, node.move)
        legal = get_legal_moves(state)
        if legal:
            tried_moves = [child.move for child in node.children]
            untried = [m for m in legal if m not in tried_moves]
            if untried:
                move = random.choice(untried)
                apply_move(state, move)
                child_node = Node(state, move, node)
                node.children.append(child_node)
                node = child_node
        winner = simulate_random_game(state)
        while node is not None:
            node.visits += 1
            if node.state.current_player != winner:
                node.wins += 1
            node = node.parent
    if root_node.children:
        best_move = max(root_node.children, key=lambda n: n.visits).move
    else:
        best_move = None
    return best_move

def get_game_state():
    return GameState(board, workers, current_player)

def bot_move():
    global board, workers, current_player, state, selected_worker
    print("Bot is thinking...")
    game_state = get_game_state()
    move = mcts(game_state, iterations=500)
    if move is None:
        print("Bot has no moves!")
        return
    worker_pos, move_pos, build_pos = move
    start_pixel = get_cell_center(worker_pos)
    end_pixel = get_cell_center(move_pos)
    animate_movement(start_pixel, end_pixel, duration=300)
    r, c = move_pos
    if board[r][c] == 3:
        print("Bot wins by moving!")
        pygame.quit(); sys.exit()
    player = workers.pop(worker_pos)
    workers[move_pos] = player
    br, bc = build_pos
    board[br][bc] = min(board[br][bc] + 1, 4)
    current_player = 1
    state = "select_worker"
    selected_worker = None
    print("Bot has made its move.")

show_rules()
running = True
while running:
    clock.tick(30)
    if current_player == 2:
        pygame.time.delay(500)
        bot_move()
    else:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                handle_click(pygame.mouse.get_pos())
    draw_board()
pygame.quit()
