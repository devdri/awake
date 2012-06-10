
from collections import defaultdict

class FlowAnalysis(object):

    def __init__(self, vertices, childs_func):
        self._vertices = set(vertices)
        self._childs_func = childs_func
        self._parents = defaultdict(set)
        self._fill_parents()

    def parents(self, x):
        return self._parents[x]

    def childs(self, x, universe=None):
        if universe:
            return set(self._childs_func(x)) & universe
        else
            return set(self._childs_func(x))

    def _fill_parents(self):
        for vertex in self._vertices:
            for child in self.childs(vertex):
                self._parents[child].add(vertex)

    def dfs(self, universe, start):
        if start not in universe:
            return set()

        queue = set([start])
        visited = set()

        while queue:
            x = queue.pop()
            visited.add(x)
            queue |= set(ch for ch in self.childs(x, universe) if ch not in visited)

        return visited

class Vertex(object):
    def __init__(self, childs):
        self.childs = set(childs)
        self.parents = set()

    def __str__(self):
        return "childs={0} parents={1}".format(self.childs, self.parents)

def nice_str(x):
    return " {" + ", ".join(str(y) for y in x) + "} "

class If(object):
    def __init__(self, split, option_a, option_b, merge):
        self.split = split
        self.option_a = option_a
        self.option_b = option_b
        self.merge = merge

    def __str__(self):
        return "if ({0}) {1} else {2} {3}".format(nice_str(self.split), nice_str(self.option_a), nice_str(self.option_b), nice_str(self.merge))


def fill_parents(verts):
    for v in verts:
        for ch in verts[v].childs:
            verts[ch].parents.add(v)

def dfs(verts, universe, start):
    queue = set([start]) & universe
    visited = set()
    while queue:
        x = queue.pop()
        visited.add(x)
        queue |= set(ch for ch in verts[x].childs & universe if ch not in visited)
    return visited


def add_single_owned(verts, universe, group):
    queue = set(group)
    while queue:
        v = queue.pop()
        for ch in verts[v].childs & universe:
            if len(verts[ch].parents & universe) == 1:
                if ch not in group:
                    queue.add(ch)
                    group.add(ch)

def make_if(verts, universe, start):
    print("make if", universe, start)
    a = list(verts[start].childs)[0]
    b = list(verts[start].childs)[1]
    accessible_a = dfs(verts, universe, a)
    accessible_b = dfs(verts, universe, b)
    add_single_owned(verts, universe, accessible_a)
    add_single_owned(verts, universe, accessible_b)
    both = accessible_a & accessible_b

    print("accessible_a", accessible_a)
    print("accessible_b", accessible_b)
    print("both", both)

    endungs = set()
    for v in both:
        parents = verts[v].parents & universe
        if len(parents) < 2:
            continue

        if parents - accessible_a and parents - accessible_b:
            endungs.add(v)

    print("endungs", endungs)
    if len(endungs) > 1:
        print("--- MANY ENDUNGS ---")
    if endungs:
        endung = list(endungs)[0]
    else:
        endung = None
    print("endung", endung)

    branch_a = accessible_a - both
    branch_b = accessible_b - both

    print("IF:", start, branch_a, branch_b, endung)

    print("process branch a")
    option_a = process(verts, branch_a, a)

    print("process branch b")
    option_b = process(verts, branch_b, b)

    print("process endung...")
    after = process(verts, both, endung)

    return [If(start, option_a, option_b, after)]


def find_cycle(verts, universe, start):
    universe = universe - set([start])
    queue = set(verts[start].parents & universe)
    visited = set()
    while queue:
        x = queue.pop()
        visited.add(x)
        queue |= set(p for p in verts[x].parents & universe if p not in visited)
    return visited


class While(object):
    def __init__(self, inner, start):
        self.start = start
        self.inner = inner

    def __str__(self):
        return "while (1) {0}".format(nice_str([self.start] + self.inner))

def make_while(verts, universe, start):
    # TODO: add 'special targets' break and continue
    print("make while", universe, start)
    cycle = find_cycle(verts, universe, start)
    add_single_owned(verts, universe, cycle)
    cycle = cycle - set([start])
    print("cycle", cycle)
    other = universe - cycle - set([start])
    print("other", other)

    if len(verts[start].childs & cycle) < 1:
        print("no good child")
        first = set()
    else:
        first = list(verts[start].childs & cycle)[0]
    print("first", first)
    inner = process(verts, cycle, first)

    endungs = set()
    for v in other:
        parents = verts[v].parents & universe
        if len(parents) < 1:
            continue

        if parents & cycle:
            endungs.add(v)
    print("endungs", endungs)
    if len(endungs) > 1:
        print("--- MANY ENDUNGS ---")
    if endungs:
        endung = list(endungs)[0]
    else:
        endung = None
    print("endung", endung)

    outer = process(verts, other, endung)
    if not outer:
        outer = []

    return [While(inner, start)] + outer

def process(verts, universe, start):
    print("process", universe, start)

    if not start:
        print("empty")
        return ""

    if start not in universe:
        if len(verts[start].parents) > 1:
            print("goto", start)
            assert(not universe)  # not sure
            return ["goto " + start]

    if len(verts[start].parents - universe) > 1:
        print("should have label")

    if verts[start].parents & universe:
        return make_while(verts, universe, start)

    if len(verts[start].childs) == 0:
        print("dead end.")
        return [start]

    if len(verts[start].childs) == 1:
        print("single vert.")
        out = process(verts, universe-set([start]), list(verts[start].childs)[0])
        if out:
            return [start] + out
        else:
            return [start]

    if len(verts[start].childs) == 2:
        print("split vert.")
        return make_if(verts, universe, start)

    return "blah"



def process(verts, universe, start):
    print("process", universe, start)

    result = []

    if not start:
        return result

    current = start

    while True:
        if current not in universe:
            if len(verts[current].parents) > 1:
                print("goto", start)
                assert(not universe)  # not sure
                result.append("goto "+current)
                return result

        if len(verts[current].parents - universe) > 1:
            print(current+" should have label")

        if verts[start].parents & universe:
            # next instr
            result.append(make_while(verts, universe, start))
            # XXX
            continue

        if len(verts[start].childs) == 0:
            print("dead end.")
            result.append(current)
            return result

        if len(verts[start].childs) == 1:
            print("single vert.")
            result.append()
            out = process(verts, universe-set([start]), list(verts[start].childs)[0])
            if out:
                return [start] + out
            else:
                return [start]

    if len(verts[start].childs) == 2:
        print("split vert.")
        return make_if(verts, universe, start)

    return "blah"




verts1 = dict(
    a=Vertex(['b', 'c']),
    b=Vertex(['d']),
    c=Vertex(['d']),
    d=Vertex([]),
)
verts2 = dict(
    a=Vertex(['b', 'c']),
    b=Vertex(['d', 'e']),
    d=Vertex(['f']),
    e=Vertex(['f']),
    c=Vertex(['f']),
    f=Vertex([]),
)
verts3 = dict(
    a=Vertex(['b']),
    b=Vertex(['c']),
    c=Vertex(['b']),
)
verts4 = dict(
    a=Vertex(['b', 'c']),
    b=Vertex(['c']),
    c=Vertex(['d']),
    d=Vertex(['b', 'e']),
    e=Vertex(['b'])
)
verts5 = dict(
    a=Vertex(['b']),
    b=Vertex(['c']),
    c=Vertex(['d', 'f']),
    d=Vertex(['e', 'f']),
    e=Vertex(['b', 'g']),
    f=Vertex([]),
    g=Vertex([])
)
verts = verts4
fill_parents(verts)
out = process(verts, set(verts.keys()), 'a')
print(nice_str(out))