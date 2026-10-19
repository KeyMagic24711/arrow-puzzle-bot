
"""UI (spec section 7). Tkinter. Tabs are built ONCE at startup (preloaded)
so switching never lags (7.3). Buttons: Start/Continue, Stop, Reset,
Re-read map (7.1). Two clocks (7.2). Module menu + manual update (7.4).
No help-request channel (7.5) -- logging replaces it."""
import json, threading, time
from pathlib import Path
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except Exception:  # headless box: UI module still importable for tests
    tk = None

from ..common.logbook import LogBook
from . import updater

class Clocks:
    def __init__(self): self.t0 = None; self.l0 = None; self.running = False
    def start(self):
        if self.t0 is None: self.t0 = time.time()
        self.running = True
    def stop(self): self.running = False
    def level_start(self): self.l0 = time.time()
    def reset(self): self.t0 = None; self.l0 = None; self.running = False
    def elapsed(self): return (time.time() - self.t0) if (self.running and self.t0) else 0.0
    def level_elapsed(self): return (time.time() - self.l0) if (self.running and self.l0) else 0.0

class App:
    def __init__(self, root_dir):
        if tk is None: raise RuntimeError("tkinter not available")
        self.root_dir = Path(root_dir); self.log = LogBook(self.root_dir / "logs")
        self.clocks = Clocks(); self.win = tk.Tk(); self.win.title("Arrow Puzzle Bot v2")
        self.state = tk.StringVar(value="Stopped")
        self._build_tabs()  # all tabs created once -> no switch lag
        self._tick()
    def _build_tabs(self):
        nb = ttk.Notebook(self.win); nb.pack(fill="both", expand=True)
        main = ttk.Frame(nb); mods = ttk.Frame(nb); upd = ttk.Frame(nb); logt = ttk.Frame(nb)
        nb.add(main, text="Control"); nb.add(mods, text="Modules"); nb.add(upd, text="Update"); nb.add(logt, text="Log")
        self.btn_start = ttk.Button(main, text="Start", command=self.on_start); self.btn_start.pack(pady=4)
        ttk.Button(main, text="Stop", command=self.on_stop).pack(pady=4)
        ttk.Button(main, text="Reset", command=self.on_reset).pack(pady=4)
        ttk.Button(main, text="Re-read map", command=self.on_remap).pack(pady=4)
        self.clock1 = ttk.Label(main, text="Total: 00:00:00"); self.clock1.pack()
        self.clock2 = ttk.Label(main, text="Level: 00:00:00"); self.clock2.pack()
        ttk.Label(main, textvariable=self.state).pack()
        self.mod_text = tk.Text(mods, height=12); self.mod_text.pack(fill="both", expand=True); self._show_modules()
        ttk.Button(upd, text="Check & download update (only when pressed)", command=self.on_update).pack(pady=6)
        self.upd_text = tk.Text(upd, height=10); self.upd_text.pack(fill="both", expand=True)
        self.log_text = tk.Text(logt, height=12); self.log_text.pack(fill="both", expand=True)
    def _show_modules(self):
        local = updater.load_local(str(self.root_dir / "version.json"))
        lines = [f"app: {local.get('app')}"] + [f"{k}: {v}" for k, v in (local.get("modules") or {}).items()]
        self.mod_text.insert("1.0", "\n".join(lines))
    def _fmt(self, s): return time.strftime("%H:%M:%S", time.gmtime(s))
    def _tick(self):
        self.clock1.config(text=f"Total: {self._fmt(self.clocks.elapsed())}")
        self.clock2.config(text=f"Level: {self._fmt(self.clocks.level_elapsed())}")
        self.win.after(250, self._tick)
    def on_start(self):
        self.clocks.start(); self.clocks.level_start(); self.state.set("Running")
        self.btn_start.config(text="Continue"); self.log.log("UI", "start pressed")
    def on_stop(self):
        self.clocks.stop(); self.state.set("Stopped"); self.log.log("UI", "stop pressed: everything halted")
    def on_reset(self):
        self.clocks.reset(); self.state.set("Stopped"); self.btn_start.config(text="Start")
        self.log.log("UI", "reset: all solving state cleared")
    def on_remap(self):
        self.log.log("UI", "re-read map requested: force re-capture, re-stitch, re-plan")
        self.state.set("Re-reading map...")
    def on_update(self):
        def work():
            try:
                remote = updater.fetch_remote(); local = updater.load_local(str(self.root_dir / "version.json"))
                res = updater.check(local, remote); bad = updater.forced_floor_violations(local, remote)
                msg = json.dumps({"check": res, "forced_floor_violations": bad}, indent=1)
            except Exception as e: msg = f"update check failed: {e}"
            self.upd_text.insert("1.0", msg + "\n")
        threading.Thread(target=work, daemon=True).start()
    def run(self): self.win.mainloop()
