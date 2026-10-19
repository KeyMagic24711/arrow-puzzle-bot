
"""Connection (spec section 6). ONLY: detect phone, ADB connect, force-open
the game, recover from interruptions. Capturing belongs to ReadMap; this
module just provides the raw screencap/tap/swipe channel over ADB."""
import enum, subprocess
from pathlib import Path

GAME_PACKAGE = "com.ecffri.arrows"

class Situation(enum.Enum):
    SAME = "same"                      # same board, unchanged -> continue
    SHIFTED = "shifted"                # same board, view moved -> re-locate
    ARROWS_MISSING = "arrows_missing"  # user tapped some arrows away
    DIFFERENT = "different"            # completely different board

def classify_interruption(old, new):
    """old/new: {board_signature, view_offset:(x,y), arrow_ids:set} (6)."""
    if old["board_signature"] != new["board_signature"]: return Situation.DIFFERENT
    if set(new["arrow_ids"]) < set(old["arrow_ids"]): return Situation.ARROWS_MISSING
    if tuple(old["view_offset"]) != tuple(new["view_offset"]): return Situation.SHIFTED
    return Situation.SAME

class Connection:
    def __init__(self, adb_path="adb", logbook=None):
        self.adb = adb_path; self.log = logbook; self.serial = None; self._size = None
    def _run(self, *args, timeout=30):
        return subprocess.run([self.adb, *args], capture_output=True, timeout=timeout)
    def find_device(self):
        out = self._run("devices").stdout.decode(errors="ignore")
        for line in out.splitlines()[1:]:
            parts = line.split()
            if len(parts) == 2 and parts[1] == "device": self.serial = parts[0]; return self.serial
        return None
    def _dev(self, *args, timeout=30):
        if not self.serial: raise RuntimeError("no device connected")
        return self._run("-s", self.serial, *args, timeout=timeout)
    def open_game(self):
        self._dev("shell", "monkey", "-p", GAME_PACKAGE, "-c", "android.intent.category.LAUNCHER", "1")
    def screen_size(self):
        if self._size: return self._size
        out = self._dev("shell", "wm", "size").stdout.decode(errors="ignore")
        for tok in out.replace(":", " ").split():
            if "x" in tok and tok.replace("x","").isdigit():
                w, h = tok.split("x"); self._size = (int(w), int(h)); return self._size
        self._size = (1080, 2400); return self._size
    def screencap_png(self):
        r = self._dev("exec-out", "screencap", "-p", timeout=30)
        if not r.stdout: raise RuntimeError("screencap returned empty")
        return r.stdout
    def tap(self, x, y): self._dev("shell", "input", "tap", str(int(x)), str(int(y)))
    def swipe(self, x1, y1, x2, y2, ms=200): self._dev("shell", "input", "swipe", str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(int(ms)))
    def reconnect(self):
        self.serial = None; return self.find_device()
