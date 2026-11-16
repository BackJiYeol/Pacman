"""
Pac-Man AI: a fully automatic game where three search algorithms play different roles

    Pac-Man (EAT mode)  : BFS            -> heads to the nearest pellet
    Pac-Man (FLEE mode) : Hill Climbing  -> moves away from ghosts when one gets close
    Ghosts              : A*             -> chase Pac-Man (heuristic = Manhattan distance)

Controls: SPACE pause/resume, R restart, ESC quit
Run:      pip install pygame  ->  python pacman_ai.py

"""

import sys
from collections import deque
import heapq

import pygame

# ----------------------------------------------------------------------------
# Map: # wall, . pellet, P Pac-Man start, G ghost start
# ----------------------------------------------------------------------------
MAP = [
    "###############",
    "#P.....#......#",
    "#.###.#.#.###.#",
    "#.#.........#.#",
    "#.#.##.#.##.#.#",
    "#......G......#",
    "#.##.#####.##.#",
    "#.............#",
    "#.###.#.#.###.#",
    "#......#.....G#",
    "###############",
]

ROWS = len(MAP)
COLS = len(MAP[0])
WALLS = {(r, c) for r in range(ROWS) for c in range(COLS) if MAP[r][c] == "#"}


def get_neighbors(pos):
    """Return the up/down/left/right cells that are not walls. Positions are (row, col)."""
    r, c = pos
    result = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nxt = (r + dr, c + dc)
        if 0 <= nxt[0] < ROWS and 0 <= nxt[1] < COLS and nxt not in WALLS:
            result.append(nxt)
    return result


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


# ============================================================================
# AI functions (to implement)
# Each function returns the ONE cell to move to next.
# If there is nowhere better to go, return start (stay in place).
# ============================================================================

def bfs_to_nearest_pellet(start, pellets):
    # (Pac-Man, EAT mode): BFS outwards from start until you reach ANY cell in pellets.
    #   Because BFS explores cells in order of distance, the first pellet found is the nearest one.
    #   Return the cell right after start on the path to that pellet.
    #   Tools: deque (queue), came_from (dict: cell -> the cell it was reached from)
    #   Note:  pellets is a set, so "cell in pellets" is O(1).
    
    frontier = deque([start])
    visited = {start}
    came_from = {start: None}

    # search for the nearest pellet
    while frontier:
        current = frontier.popleft()
        if current in pellets:
            # reconstruct the path to the pellet
            while came_from[current] != start:
                current = came_from[current]
            return current

        for neighbor in get_neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                came_from[neighbor] = current 
                frontier.append(neighbor)

    return start  # if no pellet is found, stay in place


def astar_next_step(start, goal):
    # (Ghosts): Find the shortest path from start to goal with A*,
    #   and return the cell right after start.
    #   Tools: heapq (priority queue), g_score (dict), came_from (dict)
    #   Push (f, cell) onto the heap, where f = g_score[cell] + manhattan(cell, goal)

    if start == goal:
        return start

    frontier = []
    g_score = {start: 0} # Note for A*: g_score is the cost from start to the current cell
    came_from = {start: None} # Note for A*: came_from is used to reconstruct the path
    heapq.heappush(frontier, (manhattan(start, goal), start))

    while frontier:
        f, current = heapq.heappop(frontier)

        if current == goal:
            # reconstruct the path to the goal
            while came_from[current] != start:
                current = came_from[current]
            return current

        # next step
        for neighbor in get_neighbors(current):
            depth_g = g_score[current] + 1

            if neighbor not in g_score or depth_g < g_score[neighbor]:
                g_score[neighbor] = depth_g 
                came_from[neighbor] = current
                f = depth_g + manhattan(neighbor, goal)
                heapq.heappush(frontier, (f, neighbor))

    return start


def hill_climb_escape(start, ghosts):
    # (Pac-Man, FLEE mode): Look at the neighbours of start.
    #   Score each cell by its distance to the NEAREST ghost:
    #       min(manhattan(cell, ghost) for ghost in ghosts)
    #   Move to the neighbour with the highest score.
    #   If no neighbour scores higher than start itself, stay where you are (return start).
    #   (This is why Pac-Man can get trapped in a dead end: a local optimum.)

    current = start
    best_score = min(manhattan(start, ghost) for ghost in ghosts)    

    for neighbor in get_neighbors(start):
        score = min(manhattan(neighbor, ghost) for ghost in ghosts)
        if score > best_score:
            best_score = score
            current = neighbor
    
    return current


# ============================================================================
# Game framework (no changes needed below)
# ============================================================================

TILE = 40
INFO_H = 60
FPS = 60
PAC_EVERY = 10     # Pac-Man moves one cell every 10 frames (6 cells per second)
GHOST_EVERY = 28  # ghosts move one cell every 28 frames (2 cells per second). Lower = faster ghosts
DANGER = 2         # Pac-Man switches to FLEE mode when a ghost is this close (Manhattan distance)
GHOSTS_ON = False      # set to True to turn on ghosts (A*), False to turn them off (Pac-Man only, BFS)


PAC_COLOR = (255, 220, 0)
GHOST_COLORS = [(235, 64, 52), (255, 120, 200), (60, 200, 90), (80, 200, 255)]


def new_game():
    pellets, ghosts, pac = set(), [], None
    for r in range(ROWS):
        for c in range(COLS):
            ch = MAP[r][c]
            if ch == ".":
                pellets.add((r, c))
            elif ch == "P":
                pac = (r, c)
            elif ch == "G" and GHOSTS_ON:
                ghosts.append((r, c))
    return {"pac": pac, "pellets": pellets, "ghosts": ghosts, "mode": "EAT",
            "score": 0, "state": "play", "frame": 0, "paused": False}


def is_valid_move(old, new):
    """Safety check: only allow staying put or moving to a neighbouring open cell."""
    return new == old or new in get_neighbors(old)


def step_pacman(g):
    nearest_ghost = min((manhattan(g["pac"], gh) for gh in g["ghosts"]), default=999)
    if nearest_ghost <= DANGER:
        g["mode"] = "FLEE"
        nxt = hill_climb_escape(g["pac"], g["ghosts"])
    else:
        g["mode"] = "EAT"
        nxt = bfs_to_nearest_pellet(g["pac"], g["pellets"])
    if is_valid_move(g["pac"], nxt):
        g["pac"] = nxt
    if g["pac"] in g["pellets"]:
        g["pellets"].remove(g["pac"])
        g["score"] += 10


def step_ghosts(g):
    for i, pos in enumerate(g["ghosts"]):
        # Each ghost treats the OTHER ghosts as walls while planning,
        # so two ghosts never stack on one cell, and the one behind
        # looks for a different route (it tries to cut Pac-Man off).
        others = {gh for j, gh in enumerate(g["ghosts"]) if j != i} - {g["pac"]}
        added = others - WALLS
        WALLS.update(added)
        try:
            nxt = astar_next_step(pos, g["pac"])
            ok = is_valid_move(pos, nxt)
        finally:
            WALLS.difference_update(added)
        if ok:
            g["ghosts"][i] = nxt


def check_end(g):
    if g["pac"] in g["ghosts"]:
        g["state"] = "lose"
    elif not g["pellets"]:
        g["state"] = "win"


def update(g):
    if g["state"] != "play" or g["paused"]:
        return
    g["frame"] += 1
    if g["frame"] % PAC_EVERY == 0:
        step_pacman(g)
        check_end(g)
    if g["state"] == "play" and g["frame"] % GHOST_EVERY == 0:
        step_ghosts(g)
        check_end(g)


def draw(screen, font, small, g):
    screen.fill((10, 10, 30))
    for (r, c) in WALLS:
        pygame.draw.rect(screen, (40, 70, 200), (c * TILE, r * TILE, TILE, TILE), border_radius=6)
    for (r, c) in g["pellets"]:
        pygame.draw.circle(screen, (250, 220, 180), (c * TILE + TILE // 2, r * TILE + TILE // 2), 4)

    pr, pc = g["pac"]
    center = (pc * TILE + TILE // 2, pr * TILE + TILE // 2)
    pygame.draw.circle(screen, PAC_COLOR, center, TILE // 2 - 4)
    if g["mode"] == "FLEE":   # red ring = Pac-Man is fleeing
        pygame.draw.circle(screen, (255, 60, 60), center, TILE // 2 - 1, 3)

    for i, (gr, gc) in enumerate(g["ghosts"]):
        color = GHOST_COLORS[i % len(GHOST_COLORS)]
        pygame.draw.rect(screen, color, (gc * TILE + 4, gr * TILE + 4, TILE - 8, TILE - 8), border_radius=12)
        text = small.render("A*", True, (255, 255, 255))
        screen.blit(text, text.get_rect(center=(gc * TILE + TILE // 2, gr * TILE + TILE // 2)))

    y = ROWS * TILE + 8
    mode = "EAT (BFS)" if g["mode"] == "EAT" else "FLEE (Hill Climbing)"
    screen.blit(font.render(f"Score: {g['score']}    Pac-Man: {mode}", True, (255, 255, 255)), (10, y))
    hint = "SPACE pause   R restart   ESC quit" + ("     [PAUSED]" if g["paused"] else "")
    screen.blit(small.render(hint, True, (200, 200, 200)), (10, y + 30))

    if g["state"] != "play":
        msg = "ALL PELLETS EATEN!" if g["state"] == "win" else "CAUGHT!  Press R"
        text = font.render(msg, True, (255, 255, 255))
        box = text.get_rect(center=(COLS * TILE // 2, ROWS * TILE // 2))
        pygame.draw.rect(screen, (0, 0, 0), box.inflate(30, 20), border_radius=8)
        screen.blit(text, box)


def main(max_frames=None):
    pygame.init()
    screen = pygame.display.set_mode((COLS * TILE, ROWS * TILE + INFO_H))
    pygame.display.set_caption("Pac-Man AI: BFS + Hill Climbing vs A*")
    font = pygame.font.SysFont(None, 32)
    small = pygame.font.SysFont(None, 24)
    clock = pygame.time.Clock()
    g = new_game()

    frames = 0
    while max_frames is None or frames < max_frames:
        frames += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return g
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return g
                if event.key == pygame.K_r:
                    g = new_game()
                if event.key == pygame.K_SPACE:
                    g["paused"] = not g["paused"]
        update(g)
        draw(screen, font, small, g)
        pygame.display.flip()
        clock.tick(FPS)
    return g


if __name__ == "__main__":
    main()
    pygame.quit()
    sys.exit()