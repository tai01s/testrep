"""Conforming triangle meshes for faceted rock.

polygon -> ear clipping -> refinement driven by a size field (longest edges
first, interior midpoints nudged sideways so facets look organic) -> Lawson
edge flips (constrained Delaunay: polygon edges are never flipped).

Every split is shared by both triangles of the edge, so the mesh never has
T-junctions: neighbouring gradient triangles share exact corners and leave no
hairline gaps.
"""
import heapq
import math


def _area2(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])


def _key(i, j):
    return (i, j) if i < j else (j, i)


def _clean(poly):
    out = []
    for p in poly:
        p = (float(p[0]), float(p[1]))
        if not out or abs(p[0] - out[-1][0]) > 1e-6 or abs(p[1] - out[-1][1]) > 1e-6:
            out.append(p)
    if len(out) > 1 and abs(out[0][0] - out[-1][0]) < 1e-6 and abs(out[0][1] - out[-1][1]) < 1e-6:
        out.pop()
    area = sum(out[i][0] * out[(i + 1) % len(out)][1] - out[(i + 1) % len(out)][0] * out[i][1]
               for i in range(len(out)))
    return out if area > 0 else out[::-1]


def _in_tri(p, a, b, c):
    return _area2(a, b, p) >= 0 and _area2(b, c, p) >= 0 and _area2(c, a, p) >= 0


def _ear_clip(pts):
    idx = list(range(len(pts)))
    tris = []
    guard = 0
    while len(idx) > 3 and guard < 20000:
        guard += 1
        n = len(idx)
        for k in range(n):
            ia, ib, ic = idx[(k - 1) % n], idx[k], idx[(k + 1) % n]
            a, b, c = pts[ia], pts[ib], pts[ic]
            if _area2(a, b, c) <= 1e-9:
                continue
            if any(_in_tri(pts[j], a, b, c) for j in idx if j not in (ia, ib, ic)):
                continue
            tris.append((ia, ib, ic))
            idx.pop(k)
            break
        else:
            raise ValueError("ear clipping failed (self-intersecting polygon?)")
    if len(idx) == 3:
        tris.append(tuple(idx))
    return tris


class Mesh:
    def __init__(self, poly):
        self.p = _clean(poly)
        self.t = {}
        self.e = {}
        self.fixed = set()
        self._tid = 0
        n = len(self.p)
        for a, b, c in _ear_clip(self.p):
            self._add(a, b, c)
        for i in range(n):
            self.fixed.add(_key(i, (i + 1) % n))

    # --------------------------------------------------------- bookkeeping
    def _add(self, a, b, c):
        if _area2(self.p[a], self.p[b], self.p[c]) < 0:
            b, c = c, b
        tid = self._tid
        self._tid += 1
        self.t[tid] = (a, b, c)
        for i, j in ((a, b), (b, c), (c, a)):
            self.e.setdefault(_key(i, j), set()).add(tid)
        return tid

    def _remove(self, tid):
        a, b, c = self.t.pop(tid)
        for i, j in ((a, b), (b, c), (c, a)):
            k = _key(i, j)
            s = self.e[k]
            s.discard(tid)
            if not s:
                del self.e[k]

    def _oriented(self, tid, i, j):
        """Rotate triangle tid so that its edge {i,j} comes first: returns (a, b, c)."""
        a, b, c = self.t[tid]
        for x, y, z in ((a, b, c), (b, c, a), (c, a, b)):
            if {x, y} == {i, j}:
                return x, y, z
        raise KeyError

    def edge_len(self, k):
        (ax, ay), (bx, by) = self.p[k[0]], self.p[k[1]]
        return math.hypot(bx - ax, by - ay)

    # --------------------------------------------------------------- split
    def split(self, i, j, rng=None, jitter=0.0):
        k = _key(i, j)
        tids = list(self.e[k])
        pi, pj = self.p[i], self.p[j]
        m = ((pi[0] + pj[0]) / 2, (pi[1] + pj[1]) / 2)
        if rng is not None and jitter > 0 and k not in self.fixed and len(tids) == 2:
            L = math.hypot(pj[0] - pi[0], pj[1] - pi[1])
            nx, ny = -(pj[1] - pi[1]) / L, (pj[0] - pi[0]) / L
            d = rng.uniform(-jitter, jitter) * L
            cand = (m[0] + nx * d, m[1] + ny * d)
            ok = True
            for tid in tids:
                a, b, c = self._oriented(tid, i, j)
                pa, pb, pc = self.p[a], self.p[b], self.p[c]
                # both halves must keep a healthy positive area
                full = _area2(pa, pb, pc)
                if _area2(pa, cand, pc) < 0.2 * full or _area2(cand, pb, pc) < 0.2 * full:
                    ok = False
            if ok:
                m = cand
        mi = len(self.p)
        self.p.append(m)
        new = []
        for tid in tids:
            a, b, c = self._oriented(tid, i, j)
            self._remove(tid)
            new.append(self._add(a, mi, c))
            new.append(self._add(mi, b, c))
        if k in self.fixed:
            self.fixed.discard(k)
            self.fixed.add(_key(i, mi))
            self.fixed.add(_key(mi, j))
        return mi, new

    def refine(self, size, rng=None, jitter=0.0, max_tris=6000):
        """Split edges longer than size(midpoint) - worst ratio first."""
        heap = []

        def push(k):
            (ax, ay), (bx, by) = self.p[k[0]], self.p[k[1]]
            L = math.hypot(bx - ax, by - ay)
            s = size(((ax + bx) / 2, (ay + by) / 2))
            if L > s:
                heapq.heappush(heap, (-L / s, k))

        for k in self.e:
            push(k)
        while heap and len(self.t) < max_tris:
            _, k = heapq.heappop(heap)
            if k not in self.e:
                continue
            (ax, ay), (bx, by) = self.p[k[0]], self.p[k[1]]
            if math.hypot(bx - ax, by - ay) <= size(((ax + bx) / 2, (ay + by) / 2)):
                continue
            _, new = self.split(k[0], k[1], rng, jitter)
            for tid in new:
                if tid in self.t:
                    a, b, c = self.t[tid]
                    for e in ((a, b), (b, c), (c, a)):
                        push(_key(*e))

    # ---------------------------------------------------------------- flips
    def flip_delaunay(self, max_pass=30):
        for _ in range(max_pass):
            flips = 0
            for k in list(self.e.keys()):
                if k in self.fixed or k not in self.e or len(self.e[k]) != 2:
                    continue
                t1, t2 = tuple(self.e[k])
                a, b, c = self._oriented(t1, *k)
                if (a, b) != (k[0], k[1]) and (a, b) != (k[1], k[0]):
                    continue
                # t2 holds the same edge in reverse order: (b, a, d)
                x, y, d = self._oriented(t2, *k)
                pa, pb, pc, pd = self.p[a], self.p[b], self.p[c], self.p[d]
                # quad a,d,b,c must be strictly convex for the flip
                if _area2(pa, pd, pc) <= 1e-6 or _area2(pd, pb, pc) <= 1e-6:
                    continue
                if not self._in_circle(pa, pb, pc, pd):
                    continue
                self._remove(t1)
                self._remove(t2)
                self._add(a, d, c)
                self._add(d, b, c)
                flips += 1
            if not flips:
                break

    @staticmethod
    def _in_circle(a, b, c, d):
        """True if d is strictly inside the circumcircle of CCW triangle abc."""
        adx, ady = a[0] - d[0], a[1] - d[1]
        bdx, bdy = b[0] - d[0], b[1] - d[1]
        cdx, cdy = c[0] - d[0], c[1] - d[1]
        det = ((adx * adx + ady * ady) * (bdx * cdy - cdx * bdy)
               - (bdx * bdx + bdy * bdy) * (adx * cdy - cdx * ady)
               + (cdx * cdx + cdy * cdy) * (adx * bdy - bdx * ady))
        scale = max(1.0, (abs(adx) + abs(ady) + abs(bdx) + abs(bdy) + abs(cdx) + abs(cdy)) ** 4)
        return det > 1e-9 * scale

    # --------------------------------------------------------------- output
    def triangles(self):
        return [(self.p[a], self.p[b], self.p[c]) for a, b, c in self.t.values()]

    def check(self):
        """Sanity: every triangle CCW, every interior edge shared by exactly two
        triangles, every polygon edge (possibly split) by exactly one."""
        for a, b, c in self.t.values():
            assert _area2(self.p[a], self.p[b], self.p[c]) > 0
        for k, s in self.e.items():
            if k in self.fixed:
                assert len(s) == 1, ("boundary edge", k, s)
            else:
                assert len(s) == 2, ("interior edge", k, s)
        return True


def build_mesh(poly, size, rng=None, jitter=0.18, rounds=3, max_tris=6000):
    m = Mesh(poly)
    m.flip_delaunay()
    for _ in range(rounds):
        m.refine(size, rng, jitter, max_tris)
        m.flip_delaunay()
    m.check()
    return m
