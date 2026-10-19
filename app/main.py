
"""Entry point. Run:  python app/main.py   (or --self-check)"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.common.logbook import LogBook

def self_check():
    from src.solver.solver import Solver, Arrow
    from src.tapper.tapper import Tapper
    from src.readmap.readmap import OrderedStitcher, plan_zigzag
    from src.connection.connection import classify_interruption
    from src.ui import updater
    plan_zigzag(100, 100, 250, 250)
    print("self-check OK: all 5 modules import (ReadMap, Solver, Tapper, Connection, UI)")

if __name__ == "__main__":
    if "--self-check" in sys.argv: self_check()
    else:
        from src.ui.app import App
        App(ROOT).run()
