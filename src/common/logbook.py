
"""Full logging from day one (spec section 8). Fixed local logs/ folder.
Each important event / error case gets its own subfolder:
  logs/<time>_<kind>/summary.txt  (human readable, read this first)
                     /params.json  (machine readable numbers)
                     /before.png / after.png ... (when available)
Reading summary.txt alone should explain which module failed and why.
"""
import json, time
from pathlib import Path

class LogBook:
    def __init__(self, root):
        self.root = Path(root); self.root.mkdir(parents=True, exist_ok=True)
        self.events = self.root / "events.log"
    def log(self, module, message, **kw):
        line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} [{module}] {message} {kw if kw else ''}\n"
        with open(self.events, "a", encoding="utf-8") as f: f.write(line)
    def new_case(self, kind, module, summary, params=None, images=None):
        stamp = time.strftime("%Y%m%d_%H%M%S")
        d = self.root / f"{stamp}_{kind}"; n=1
        while d.exists():
            n+=1; d = self.root / f"{stamp}_{kind}_{n}"
        d.mkdir(parents=True)
        (d/"summary.txt").write_text(f"module: {module}\nkind: {kind}\ntime: {stamp}\n\n{summary}\n", encoding="utf-8")
        (d/"params.json").write_text(json.dumps(params or {}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        for name, data in (images or {}).items():
            if data: (d/name).write_bytes(data)
        self.log(module, f"case saved {d.name}: {kind}")
        return d
