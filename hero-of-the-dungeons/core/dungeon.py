
import random
MAP_W, MAP_H = 80, 60

class Dungeon:
    def __init__(self, floor=1, mode="normal"):
        self.floor, self.mode = floor, mode
        self.tiles = [["#" for _ in range(MAP_W)] for _ in range(MAP_H)]
        self.rooms = []
        self.generate()
    def generate(self):
        rooms, tries = [], 0
        while len(rooms) < 9 and tries < 300:
            tries += 1
            w, h = random.randint(8, 16), random.randint(6, 12)
            x, y = random.randint(1, MAP_W-w-2), random.randint(1, MAP_H-h-2)
            if any(not (x+w+1 < rx or rx+rw+1 < x or y+h+1 < ry or ry+rh+1 < y) for rx, ry, rw, rh in rooms):
                continue
            rooms.append((x, y, w, h))
        self.rooms = rooms
        for x, y, w, h in rooms:
            for i in range(y, y+h):
                for j in range(x, x+w):
                    self.tiles[i][j] = "."
        for i in range(len(rooms)-1):
            self.connect(rooms[i], rooms[i+1])
        for _ in range(3):
            if len(rooms) > 2:
                a, b = random.sample(rooms, 2)
                self.connect(a, b)
        cx, cy, cw, ch = rooms[0]; self.start = (cx+cw//2, cy+ch//2)
        lx, ly, lw, lh = rooms[-1]; self.stairs = (lx+lw//2, ly+lh//2)
    def connect(self, a, b):
        x1, y1 = a[0]+a[2]//2, a[1]+a[3]//2
        x2, y2 = b[0]+b[2]//2, b[1]+b[3]//2
        if random.random() < 0.5:
            self.hcorr(x1, x2, y1); self.vcorr(y1, y2, x2)
        else:
            self.vcorr(y1, y2, x1); self.hcorr(x1, x2, y2)
    def hcorr(self, x1, x2, y):
        for x in range(min(x1,x2), max(x1,x2)+1):
            self.tiles[y][x] = "."
    def vcorr(self, y1, y2, x):
        for y in range(min(y1,y2), max(y1,y2)+1):
            self.tiles[y][x] = "."
    def is_wall(self, x, y):
        return not (0 <= x < MAP_W and 0 <= y < MAP_H) or self.tiles[y][x] == "#"
    def free_cells(self):
        return [(x, y) for y in range(MAP_H) for x in range(MAP_W) if self.tiles[y][x] == "."]
    def reveal(self, cx, cy, r):
        found = []
        for y in range(max(0, cy-r), min(MAP_H, cy+r+1)):
            for x in range(max(0, cx-r), min(MAP_W, cx+r+1)):
                if (x-cx)**2 + (y-cy)**2 <= r*r:
                    found.append((x, y))
        return found

def bfs_path(d, start, goal, known):
    from collections import deque
    if goal not in known or start not in known:
        return None
    q = deque([(start, [])]); seen = {start}
    while q:
        (x, y), path = q.popleft()
        if (x, y) == goal:
            return path
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            n = (x+dx, y+dy)
            if n in seen or n not in known or d.is_wall(*n):
                continue
            seen.add(n); q.append((n, path+[n]))
    return None
