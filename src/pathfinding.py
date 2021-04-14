from heapq import heappop, heappush, heappushpop
from math import sqrt
from numpy import full_like
import src.movement
from math import dist

cardinal_cost = 100
diagonal_cost = 141

class Pathfinding:

    def __init__(self, state):
        self.state = state
        pass


    class PathNode:
        def __init__(self, state, pos, g=0, h=0, parent=None, action_to_here=0, action_cost=0, legal_actions=0):
            self.pos = pos
            self.g = g
            self.parent = parent
            self.h = h
            self.f = g + h
            self.parent = parent
            self.action_to_here = action_to_here
            self.action_cost = 100
            # if state.node_pointers[pos] is None:
            #     self.action_cost = 100
            # else:
            #     self.action_cost = state.nodes[state.node_pointers[pos]].action_cost
            self.legal_actions = legal_actions
            self.sectors = []
            self.sector_sizes = {}

        def __lt__(self, other):  # required for heapq sort
            return self.f < other.f


    def calc_g(self, parent, g_lookup, p_to_c_cost):
        a = g_lookup[parent] + p_to_c_cost
        return g_lookup[parent] + p_to_c_cost


    i = 0
    def expand(self, parent : PathNode, goal, max_x, max_z, all_legal_actions):  # TODO integtrate legal actions here
        children = []
        x, z = parent.pos
        curr_legal_actions = all_legal_actions[x][z]
        for n in range(len(curr_legal_actions)):
            if curr_legal_actions[n] == False: continue
            dx = src.movement.directions[n][0]
            dz = src.movement.directions[n][1]
            tx = parent.pos[0] + dx
            tz = parent.pos[1] + dz
            if (tx < 0 or tz < 0 or tx > max_x or tz > max_z):
                continue
            pos = (tx, tz)
            g = parent.g
            if n < 4:
                g += cardinal_cost
            else:
                g += diagonal_cost
            h = self.heuristic(*pos, *goal)
            child = self.PathNode(
                self.state, pos, g, h, parent,
                action_to_here=(-dx, -dz), action_cost=cardinal_cost, legal_actions=all_legal_actions[tx][tz]
            )
            children.append(child)
        return children


    def get_path(self, start, end : list, max_x, max_z, legal_actions):
        first = self.PathNode(self.state, start, g=0, h=self.heuristic(*start, *end), parent=None, action_to_here=None, action_cost=0, legal_actions=legal_actions)
        open = [first]  # heap
        closed = set() # change to a dict with coord-node
        g_lookup = {}
        while len(open) > 0:
            node = heappop(open)
            if node.pos[0] == end[0] and node.pos[1] == end[1]:  # to account for both tuples and lists
                return self.backwards_traverse(node, start)
            closed.add(node.pos)
            for child in self.expand(node, end, max_x, max_z, legal_actions):
                p_to_c_cost = child.action_cost
                if child.pos in closed: continue
                # TODO fix the below to be "if child.pos in open" and the last if.
                if child.pos in closed: continue
                if child.pos in g_lookup.keys() and g_lookup[child.pos] <= self.calc_g(node.pos, g_lookup, p_to_c_cost): continue # g is the action cost to get here, parent's g + parent to child g
                g_lookup[child.pos] = child.g
                heappush(open, child)
        return []


    def backwards_traverse(self, node, end):
        curr = node
        path = []
        while curr.pos != end:
            path.append(curr.pos)
            curr = curr.parent
        # path.append(curr.pos)
        return path


    def heuristic(self, x1, z1, x2, z2):
        # return round(dist((x1, z1), (x2, z2)))
        return round(sqrt((x1 - x2) ** 2 + (z1 - z2) ** 2) * cardinal_cost)


    def create_sectors(self, heightmap, legal_actions):
        self.sectors = full_like(heightmap, -1, int)
        self.n_sectors = 0
        self.sector_sizes = {}
        for x in range(len(legal_actions)):
            for z in range(len(legal_actions[0])):
                if self.sectors[x][z] == -1:
                    self.n_sectors +=1
                    self.sector_sizes[self.n_sectors] = 0
                    self.propagate_sector(x, z, self.n_sectors, self.sectors, self.sector_sizes, legal_actions)
                z += 1
            x += 1
        return self.sectors


    def propagate_sector(self, x, z, sector, sectors, sector_sizes, legal_actions, is_redoing=False):
        open = [(x, z)]
        closed = set()
        while len(open) > 0:  # search all adjacent until you cant go anymore
            pos = open.pop(0)
            nx, nz = pos
            if not is_redoing and sectors[nx][nz] != -1:
                continue
            sectors[nx][nz] = sector
            sector_sizes[sector] += 1
            legals = legal_actions[nx][nz]
            for n in range(len(legal_actions[nx][nz])):  # check tiles reachable from here
                a = legal_actions[nx][nz][n]
                if legal_actions[nx][nz][n] == True:
                    dir = src.movement.directions[n]
                    cx = nx + dir[0]
                    cz = nz + dir[1]
                    if cx < 0 or cx >= len(legal_actions) or cz < 0 or cz >= len(legal_actions[0]):
                        continue
                    childs_sector = sectors[cx][cz]
                    if childs_sector == -1 or childs_sector != sector:  # if the tile doesn't have a sector, add to list to expand
                        child_pos = (cx,cz)
                        if not child_pos in closed:
                            open.append(child_pos)
                        closed.add(child_pos)
                    elif childs_sector != sector:
                        sector_sizes[childs_sector] -= 1
                        child_pos = (cx,cz)
                        if not child_pos in closed:
                            open.append(child_pos)  # the or allows re-sectoring
                        closed.add(child_pos)


    def update_sector_for_block(self,x,z, sectors, sector_sizes, legal_actions, old_legal_actions):
        found_legal_action = False
        # i think u should do this only if a change is legal actions was found
        if legal_actions[x][z] != old_legal_actions[x][z]:
            self.n_sectors += 1
            self.sector_sizes[self.n_sectors] = 0
            found_legal_action = False
            for n in range(len(legal_actions[x][z])):
                bit = legal_actions[x][z][n]
                found_legal_action = bit
                if bit is True:
                    self.propagate_sector(x, z, sector=self.n_sectors, sectors=sectors, sector_sizes=sector_sizes, legal_actions=legal_actions, is_redoing=True)
                    break
            if not found_legal_action:
                self.propagate_sector(x, z, self.n_sectors, sectors=sectors, sector_sizes=self.sector_sizes, legal_actions=legal_actions, is_redoing=True)  # might not do the last arg

