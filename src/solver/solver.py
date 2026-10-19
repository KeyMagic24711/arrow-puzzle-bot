
"""Solver (spec section 4). Pure logic, no device access, fully testable.

- Layer (4.4): arrows whose exit ray is not blocked by any other remaining
  arrow. Exit-ray crossing between arrows in the same layer does not matter.
- Zones (4.1): fewest zones covering the board, slight overlap.
- Zone order (4.2): zone with most currently-solvable arrows first,
  recomputed after every zone.
- Partial arrows (4.3): an arrow assigned to a zone if ANY of its cells is
  in the zone; a solvable partial arrow is still tapped.
"""
from dataclasses import dataclass, field

DIRS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}

@dataclass(frozen=True)
class Arrow:
    id: str
    direction: str            # up/down/left/right (direction the head points)
    cells: tuple              # ((row,col),...) tail..head; head = cells[-1]
    kind: str = "normal"      # normal | hint(=normal) | reward
    @property
    def head(self): return self.cells[-1]

def exit_blockers(arrow, others, rows, cols):
    """Arrows whose cells lie on arrow's exit ray from its head to the edge."""
    dr, dc = DIRS[arrow.direction]; r, c = arrow.head; ray = set()
    r, c = r + dr, c + dc
    while 0 <= r < rows and 0 <= c < cols:
        ray.add((r, c)); r, c = r + dr, c + dc
    return {o.id for o in others if o.id != arrow.id and ray.intersection(o.cells)}

def compute_layers(arrows, rows, cols):
    """Return (layers, stuck_ids). layers = list of lists of arrow ids."""
    remaining = {a.id: a for a in arrows}; layers = []
    while remaining:
        layer = [aid for aid, a in remaining.items()
                 if not exit_blockers(a, remaining.values(), rows, cols)]
        if not layer: break
        layers.append(sorted(layer))
        for aid in layer: del remaining[aid]
    return layers, sorted(remaining)

@dataclass
class Zone:
    index: int; r0: int; c0: int; r1: int; c1: int  # inclusive bounds
    def contains(self, cell):
        r, c = cell; return self.r0 <= r <= self.r1 and self.c0 <= c <= self.c1
    def arrow_ids(self, arrows):
        return [a.id for a in arrows if any(self.contains(x) for x in a.cells)]

class Solver:
    def __init__(self, arrows, rows, cols, zone_rows=8, zone_cols=8, zone_overlap=1):
        self.arrows = list(arrows); self.rows = rows; self.cols = cols
        self.by_id = {a.id: a for a in self.arrows}
        self.zones = self._make_zones(zone_rows, zone_cols, zone_overlap)
    def _make_zones(self, zr, zc, ov):
        zones = []; idx = 0
        r_starts = self._starts(self.rows, zr, ov); c_starts = self._starts(self.cols, zc, ov)
        for r0 in r_starts:
            for c0 in c_starts:
                zones.append(Zone(idx, r0, c0, min(self.rows-1, r0+zr-1), min(self.cols-1, c0+zc-1))); idx += 1
        return zones
    @staticmethod
    def _starts(size, span, ov):
        if span >= size: return [0]
        step = max(1, span - ov); starts = list(range(0, size - span + 1, step))
        if starts[-1] != size - span: starts.append(size - span)
        return starts
    def solvable_now(self, remaining_ids):
        rem = [self.by_id[i] for i in remaining_ids]
        return {a.id for a in rem if not exit_blockers(a, rem, self.rows, self.cols)}
    def plan(self):
        """Greedy zone order, recomputed after each zone (4.2).
        Returns list of steps: {zone, tap_order:[ids]} covering all solvable
        arrows; plus stuck ids that no order can free (dry-run verified)."""
        remaining = set(self.by_id); steps = []
        while remaining:
            solvable = self.solvable_now(remaining)
            if not solvable: break
            best, best_ids = None, []
            for z in self.zones:
                ids = [i for i in z.arrow_ids([self.by_id[x] for x in remaining]) if i in solvable]
                if len(ids) > len(best_ids): best, best_ids = z, ids
            if best is None or not best_ids: break
            layers, _ = compute_layers([self.by_id[x] for x in remaining], self.rows, self.cols)
            rank = {aid: n for n, lay in enumerate(layers) for aid in lay}
            best_ids.sort(key=lambda i: (rank.get(i, 99), i))
            steps.append({"zone": best.index, "tap_order": best_ids})
            remaining -= set(best_ids)
        return {"steps": steps, "stuck": sorted(remaining), "verified": not remaining}
    def dry_run(self, ordered_ids):
        """Simulate taps; True only if every arrow is unblocked at its turn."""
        remaining = set(self.by_id)
        for aid in ordered_ids:
            if aid not in remaining: return False
            if aid not in self.solvable_now(remaining): return False
            remaining.discard(aid)
        return not remaining
