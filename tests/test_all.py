import sys, pathlib, random, threading
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import unittest, numpy as np
from src.solver.solver import Arrow, Solver, compute_layers
from src.tapper.tapper import Tapper, HeartMonitor, random_gap_s, TAP_GAP_MIN_MS, TAP_GAP_MAX_MS
from src.readmap.readmap import OrderedStitcher, Frame, strip_virtual_buttons, classify_first_frame, classify_cell, plan_zigzag
from src.connection.connection import classify_interruption, Situation
from src.ui import updater

class TestSolver(unittest.TestCase):
    def test_layers_blocking(self):
        # A at (1,0) points right, B at (1,2) blocks A exit; B free
        A=Arrow("A","right",((1,0),(1,1))); B=Arrow("B","up",((1,2),(0,2)))
        layers, stuck = compute_layers([A,B],3,4)
        self.assertEqual(layers[0],["B"]); self.assertEqual(layers[1],["A"]); self.assertEqual(stuck,[])
    def test_zone_plan_and_dry_run_and_partial(self):
        A=Arrow("A","right",((0,0),(0,1))); B=Arrow("B","up",((0,2),))  # B single cell, blocks? A ray hits (0,2) yes
        s=Solver([A,B],2,3,zone_rows=1,zone_cols=2,zone_overlap=0)
        plan=s.plan(); order=[i for st in plan["steps"] for i in st["tap_order"]]
        self.assertTrue(plan["verified"], plan); self.assertTrue(s.dry_run(order))
        self.assertEqual(order[0],"B")  # blocker first
        # partial: arrow crossing zone boundary assigned to both zones by any-cell rule
        zids=[set(z.arrow_ids([A,B])) for z in s.zones]
        self.assertTrue(any("A" in z for z in zids))
    def test_stuck_detected(self):
        A=Arrow("A","right",((0,1),)); B=Arrow("B","left",((0,0),))  # each blocks other? A head(0,1) ray right none; fix cycle below
        A=Arrow("A","right",((0,0),)); B=Arrow("B","left",((0,1),))
        layers, stuck = compute_layers([A,B],1,2)
        self.assertEqual(sorted(stuck),["A","B"])

class TestTapper(unittest.TestCase):
    def test_gap_range(self):
        rng=random.Random(1)
        for _ in range(200):
            ms=random_gap_s(rng)*1000
            self.assertTrue(TAP_GAP_MIN_MS-1 <= ms <= TAP_GAP_MAX_MS+1)
    def test_heart_loss_switches_way2_and_stops(self):
        taps=[]; hearts=iter([3,3,2,2,2,2])
        tp=Tapper(taps.append, lambda tag=b"x": b"img", lambda: next(hearts), sleep_fn=lambda s: None, rng=random.Random(0))
        res=tp.run_way1([f"a{i}" for i in range(10)])
        self.assertEqual(tp.mode,"way2"); self.assertFalse(res["finished"]); self.assertTrue(tp.stopped)
    def test_way2_layers(self):
        taps=[]; caps=[]
        tp=Tapper(taps.append, lambda tag=b"x": caps.append(tag) or b"i", lambda: 3, sleep_fn=lambda s: None, rng=random.Random(0))
        res=tp.run_way2([["a","b"],["c"]]); self.assertTrue(res["finished"]); self.assertEqual(taps,["a","b","c"])

class TestReadMap(unittest.TestCase):
    def test_queue_order_and_last(self):
        got=[]; st=OrderedStitcher(lambda f: got.append(f.seq))
        t=threading.Thread(target=st.run); t.start()
        for seq in [2,0,3,1]:
            st.put(Frame(seq=seq, is_last=(seq==3)))
        st.done.wait(5); self.assertEqual(got,[0,1,2,3]); self.assertTrue(st.done.is_set())
    def test_strip_and_classify(self):
        img=np.full((100,200,3),255,np.uint8); img[:,190:,:]=128
        clean,w=strip_virtual_buttons(img); self.assertTrue((clean[:,195:,:]==255).all()); self.assertGreater(w,3)
        self.assertEqual(classify_first_frame(np.full((50,50,3),255,np.uint8)),"small")
        big=np.full((50,50,3),255,np.uint8); big[0,:, :] = 0
        self.assertEqual(classify_first_frame(big),"large")
        white=np.full((20,20,3),255,np.uint8); self.assertEqual(classify_cell(white),"empty")
        black=np.full((20,20,3),255,np.uint8); black[5:15,9:11,:]=0; self.assertIn(classify_cell(black),("normal","hint"))
        grey=np.full((20,20,3),255,np.uint8); grey[9:11,9:11,:]=180; self.assertEqual(classify_cell(grey),"dot")
    def test_zigzag_overlap(self):
        pos=plan_zigzag(100,100,250,120,0.18); self.assertEqual(pos[0],(0,0)); self.assertGreater(len(pos),1)
        with self.assertRaises(ValueError): plan_zigzag(100,100,200,200,0.5)

class TestConnection(unittest.TestCase):
    def base(self): return {"board_signature":"s1","view_offset":(0,0),"arrow_ids":{"a","b"}}
    def test_4_situations(self):
        o=self.base()
        self.assertEqual(classify_interruption(o,dict(o)),Situation.SAME)
        n=dict(o); n["view_offset"]=(5,0); self.assertEqual(classify_interruption(o,n),Situation.SHIFTED)
        n=dict(o); n["arrow_ids"]={"a"}; self.assertEqual(classify_interruption(o,n),Situation.ARROWS_MISSING)
        n=dict(o); n["board_signature"]="s2"; self.assertEqual(classify_interruption(o,n),Situation.DIFFERENT)

class TestUpdater(unittest.TestCase):
    def test_versions_and_floor(self):
        local={"app":"2.0.0","modules":{"solver":"1.9.0"}}
        remote={"app":"2.1.0","modules":{"solver":"2.0.0"},"forced_floor":{"solver":"2.0.0"}}
        self.assertTrue(updater.check(local,remote)["app_update"])
        self.assertEqual(updater.forced_floor_violations(local,remote),[("solver","1.9.0","2.0.0")])

if __name__=="__main__": unittest.main()
