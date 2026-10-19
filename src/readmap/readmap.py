
"""ReadMap (spec section 3). Owns capturing (Connection only connects).

- First frame only classifies small/large; never stitched (3.1).
- Large boards: hard swipes to top-left corner, zigzag with 15-20% overlap.
- Capture and stitch run in PARALLEL: numbered frames through an ordered
  queue; the last frame is flagged is_last (3.5).
- The grey virtual-button strip on the right edge is removed BEFORE
  stitching (3.4).
- Detection (3.6): black = normal, blue hint = normal, rainbow = reward,
  faint grey dot = grid marker, NOT an arrow.
Detection here is a clean grid-cell heuristic informed by v1; exact pixel
thresholds must be tuned on a real device (documented in docs/ASSUMPTIONS.md).
"""
import queue, threading
from dataclasses import dataclass

OVERLAP_MIN, OVERLAP_MAX = 0.15, 0.20
RIGHT_STRIP_FRACTION = 0.04   # virtual buttons live in the right edge strip

@dataclass
class Frame:
    seq: int
    image: object = None      # numpy array HxWx3 uint8, or bytes path payload
    pos: tuple = (0, 0)       # (x, y) top-left on the stitched canvas
    is_last: bool = False

def plan_zigzag(view_w, view_h, board_w, board_h, overlap=0.18):
    if not (OVERLAP_MIN <= overlap <= OVERLAP_MAX):
        raise ValueError("overlap must be 15-20% per spec 3.3")
    step_x = max(1, int(view_w * (1 - overlap))); step_y = max(1, int(view_h * (1 - overlap)))
    xs = list(range(0, max(1, board_w - view_w + 1), step_x))
    if xs[-1] != max(0, board_w - view_w): xs.append(max(0, board_w - view_w))
    ys = list(range(0, max(1, board_h - view_h + 1), step_y))
    if ys[-1] != max(0, board_h - view_h): ys.append(max(0, board_h - view_h))
    out = []
    for row, y in enumerate(ys):
        row_xs = xs if row % 2 == 0 else list(reversed(xs))
        out += [(x, y) for x in row_xs]
    return out

def strip_virtual_buttons(img, fraction=RIGHT_STRIP_FRACTION):
    """Whiten the right-edge grey strip BEFORE stitching (3.4).
    Returns (clean_image, strip_width_px). Works on numpy arrays."""
    import numpy as np
    a = np.array(img, copy=True); h, w = a.shape[:2]
    sw = max(4, int(w * fraction)); a[:, w - sw:, :] = 255
    return a, sw

def detect_right_strip(img, fraction=RIGHT_STRIP_FRACTION):
    """Heuristic: right strip is grey-ish (low colour spread) vs board."""
    import numpy as np
    a = np.asarray(img); h, w = a.shape[:2]; sw = max(4, int(w * fraction))
    strip = a[:, w - sw:, :].astype(int)
    spread = int(abs(strip[...,0]-strip[...,2]).mean()) if a.ndim == 3 else 0
    return {"strip_width": sw, "colour_spread": spread, "likely_grey": spread < 18}

def classify_first_frame(img):
    """'large' if ink touches any frame edge (board overflows), else 'small'."""
    import numpy as np
    a = np.asarray(img); g = a.mean(axis=2) if a.ndim == 3 else a
    ink = g < 200; e = max(1, g.shape[0] // 100)
    touches = bool(ink[:e,:].any() or ink[-e:,:].any() or ink[:,:e].any() or ink[:,-e:].any())
    return "large" if touches else "small"

class OrderedStitcher:
    """Consumes frames in seq order even if they arrive out of order.
    Runs on its own thread; finishes when the is_last frame is stitched."""
    def __init__(self, stitch_fn):
        self.q = queue.Queue(); self.stitch_fn = stitch_fn; self.done = threading.Event()
        self.buffer = {}; self.next_seq = 0; self.stitched = []; self.error = None
    def put(self, frame): self.q.put(frame)
    def run(self):
        try:
            while True:
                f = self.q.get()
                self.buffer[f.seq] = f
                while self.next_seq in self.buffer:
                    fr = self.buffer.pop(self.next_seq); self.next_seq += 1
                    self.stitch_fn(fr); self.stitched.append(fr.seq)
                    if fr.is_last: self.done.set(); return
        except Exception as e:  # surfaced to caller via .error
            self.error = e; self.done.set()

def classify_cell(cell):
    """Classify one grid cell image (numpy HxWx3).
    -> empty | dot | normal | hint | reward  (3.6)"""
    import numpy as np
    a = np.asarray(cell).astype(int); h, w = a.shape[:2]
    ink = a.mean(axis=2) < 200; frac = float(ink.mean())
    if frac < 0.005: return "empty"
    r, g, b = a[...,0], a[...,1], a[...,2]
    colour_var = float(np.std(r[ink]) + np.std(g[ink]) + np.std(b[ink])) if ink.any() else 0.0
    mean_ink_grey = float(a.mean(axis=2)[ink].mean()) if ink.any() else 255.0
    if frac < 0.16 and 120 < mean_ink_grey < 230 and colour_var < 40: return "dot"  # faint grey marker
    if colour_var > 90: return "reward"      # rainbow / CD-like shimmer
    if ink.any() and float(b[ink].mean()) > float(r[ink].mean()) + 25: return "hint"  # blueish hint
    return "normal"

class ReadMap:
    def __init__(self, connection, logbook=None):
        self.conn = connection; self.log = logbook
    def capture_png(self):
        """ReadMap owns capture; Connection only provides the raw channel."""
        return self.conn.screencap_png()
    def go_top_left(self):
        """Hard, long, fast swipes to the top-left corner (3.2)."""
        w, h = self.conn.screen_size()
        for _ in range(3): self.conn.swipe(w//2, int(h*0.15), w//2, int(h*0.9), 120)
        for _ in range(3): self.conn.swipe(int(w*0.15), h//2, int(w*0.9), h//2, 120)
    def capture_large_board(self, stitch_fn, positions):
        """Parallel capture+stitch (3.5): producer numbers frames, flags the
        last one; stitcher thread consumes strictly in order."""
        stitcher = OrderedStitcher(stitch_fn)
        t = threading.Thread(target=stitcher.run, daemon=True); t.start()
        n = len(positions)
        for i, pos in enumerate(positions):
            png = self.capture_png()
            stitcher.put(Frame(seq=i, image=png, pos=pos, is_last=(i == n-1)))
        stitcher.done.wait(timeout=120)
        if stitcher.error: raise stitcher.error
        return stitcher.stitched
