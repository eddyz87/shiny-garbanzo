import networkx as nx
import matplotlib
import tempfile
import random
import sys
import sh

COLORS = list(matplotlib.colors.TABLEAU_COLORS.values())

def gen_dot(G, loops=None, name=None):
    A = nx.nx_agraph.to_agraph(G)
    i = 0
    if name:
        A.graph_attr["label"] = name
    if loops:
        for loop in loops:
            color = COLORS[i]
            i = (i + 1) % len(COLORS)
            for node in loop:
                n = A.get_node(node)
                n.attr["color"] = color
                n.attr["fontcolor"] = color
                n.attr["xlabel"] = f"{loop[0]}"
        for f, t in A.edges_iter():
            fc = A.get_node(f).attr["color"]
            tc = A.get_node(t).attr["color"]
            if fc == tc:
                A.get_edge(f, t).attr["color"] = fc
    return A.to_string()

def show_xdot(G, loops=None, name=None):
    file = tempfile.NamedTemporaryFile(mode='w', prefix='loops_')
    file.write(gen_dot(G, loops, name))
    file.flush()
    def done(*_):
        file.close()
    sh.xdot(file.name, _bg=True, _done=done)

def find_roots(G):
    visited = set()
    roots = []
    preorder = list(nx.dfs_preorder_nodes(G))
    for n in preorder:
        if n in visited:
            continue
        if not list(G.predecessors(n)):
            roots.append(n)
            visited.update(nx.dfs_preorder_nodes(G, n))
    for n in nx.dfs_preorder_nodes(G):
        if n in visited:
            continue
        roots.append(n)
        visited.update(nx.dfs_preorder_nodes(G, n))
    return roots

def identify_loops_rec(G):
    traversed = set()
    headers = {}
    depths = {}
    path = set()

    def get_loop_header(n):
        h = headers.get(n, None)
        while h in headers and headers[h] != h:
            h = headers[h]
        return h

    def update_loop_header(n, h):
        n1 = get_loop_header(n) or n
        h1 = get_loop_header(h) or h
        if h1 in path and depths[h1] <= depths[n1]:
            headers[n] = h1

    def dfs(n, depth):
        traversed.add(n)
        path.add(n)
        depths[n] = depth
        for succ in G.successors(n):
            if succ not in traversed:
                dfs(succ, depth + 1)
                h = get_loop_header(succ)
                update_loop_header(n, h)
            else:
                update_loop_header(n, succ)
        path.remove(n)

    for n in find_roots(G):
        if n not in traversed:
            dfs(n, 1)

    loops = {}
    for n in G.nodes():
        if not (h := get_loop_header(n)) is None:
            if h not in loops:
                loops[h] = []
            loops[h].append(n)
    return list(loops.values())

def sort_loops(loops):
    return sorted(map(sorted, loops))

def compute_reference_loops(G):
    uf = nx.utils.UnionFind()
    for loop in nx.simple_cycles(G):
        for n in loop:
            uf.union(loop[0], n)
    return list(map(list, uf.to_sets()))

def test(G):
    reference = sort_loops(compute_reference_loops(G))
    mine = sort_loops(identify_loops_rec(G))
    if reference != mine:
        print("Loops don't match:")
        print(f"  expected: {reference}")
        print(f"  result:   {mine}")
        show_xdot(G, reference, "expected")
        show_xdot(G, mine, "result")
        return False
    else:
        return True

def random_graph(_seed):
    G = nx.fast_gnp_random_graph(20, 0.077, directed=True, seed=_seed)
    return intern_graph(G)

def random_test_once(seed):
        rng = random.Random(seed)
        G = random_graph(rng)
        return test(G)

def random_test_many(N):
    for i in range(0, N):
        seed = random.randrange(sys.maxsize)
        if not random_test_once(seed):
            print(f">> random_test_once({seed})")
            return
    print('All ok')

def show_loops(G):
    loops = identify_loops_rec(G)
    show_xdot(G, loops)

def intern_graph(G):
    new_nodes = map(lambda n: n + 1, nx.dfs_preorder_nodes(G))
    mapping = dict(zip(G.nodes(), new_nodes))
    return nx.relabel_nodes(G, mapping)

def test1():
    G = nx.DiGraph()
    G.add_edge(0, 1)
    G.add_edge(1, 2)
    G.add_edge(2, 3)
    G.add_edge(3, 4)
    G.add_edge(1, 0)
    G.add_edge(4, 3)
    #G.add_edge(4, 0)
    G = intern_graph(G)
    loops = identify_loops_rec(G)
    show_xdot(G, loops)
    return loops
