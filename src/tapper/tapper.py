
"""Tapper (spec section 5; renamed from Stepper per owner decision).

- Gap between taps: random 150-200 ms (constants below, easy to tune;
  Appendix A item 2 not fully settled, 150-200 is the file's value).
- Way 1 (fast): batches of 5-10, screenshot after each batch.
- ANY heart loss: stop immediately, diagnostic captures, full log case,
  then switch to Way 2 (slow, by layer) -- spec 5.3 / Appendix A item 3.
- Way 2: tap one whole layer, screenshot, next layer.
- Reward arrow: quick capture around it right after tapping (5.5).
- Before leaving a zone: one final check capture (5.6).
All device actions are injected callables, so this is unit-testable.
"""
import random, time

TAP_GAP_MIN_MS = 150
TAP_GAP_MAX_MS = 200
BATCH_MIN, BATCH_MAX = 5, 10

def random_gap_s(rng=None):
    rng = rng or random
    return rng.randint(TAP_GAP_MIN_MS, TAP_GAP_MAX_MS) / 1000.0

class HeartMonitor:
    def __init__(self, hearts=3): self.hearts = hearts; self.lost_total = 0
    def update(self, hearts_now):
        lost = max(0, self.hearts - hearts_now)
        if lost: self.lost_total += lost
        self.hearts = hearts_now
        return lost

class Tapper:
    def __init__(self, tap_fn, capture_fn, hearts_fn, logbook=None, sleep_fn=time.sleep, rng=None):
        self.tap, self.capture, self.hearts_fn = tap_fn, capture_fn, hearts_fn
        self.log = logbook; self.sleep = sleep_fn; self.rng = rng or random.Random()
        self.monitor = HeartMonitor(); self.mode = "way1"; self.stopped = False
    def _gap(self): self.sleep(random_gap_s(self.rng))
    def _tap_arrow(self, arrow_id, kind="normal"):
        self.tap(arrow_id); self._gap()
        if kind == "reward": self.capture(f"reward_{arrow_id}")  # 5.5 quick nearby capture
    def _check_hearts(self, context, last_id=None):
        lost = self.monitor.update(self.hearts_fn())
        if lost:
            self.stopped = True
            before = self.capture("diagnose_1"); self.capture("diagnose_2")
            if self.log:
                self.log.new_case("heart_loss", "Tapper",
                    f"Lost {lost} heart(s) during {context}, last tap={last_id}. "
                    f"Stopped immediately and switched to Way 2 (slow, by layer).",
                    {"lost": lost, "context": context, "last_tap": last_id, "mode_before": self.mode},
                    {"diagnose_1.png": before} if isinstance(before, (bytes, bytearray)) else None)
            self.mode = "way2"
            return True
        return False
    def run_way1(self, ordered_ids, kinds=None):
        kinds = kinds or {}; i = 0
        while i < len(ordered_ids) and not self.stopped:
            batch = ordered_ids[i:i + self.rng.randint(BATCH_MIN, BATCH_MAX)]
            for aid in batch:
                self._tap_arrow(aid, kinds.get(aid, "normal"))
                if self._check_hearts("way1_batch", aid): return {"finished": False, "tapped": i, "mode": self.mode}
                i += 1
            self.capture("after_batch")  # confirm batch (5.2)
        return {"finished": not self.stopped, "tapped": i, "mode": self.mode}
    def run_way2(self, layers, kinds=None):
        kinds = kinds or {}; tapped = 0
        for layer in layers:
            for aid in layer:
                self._tap_arrow(aid, kinds.get(aid, "normal")); tapped += 1
                if self._check_hearts("way2_layer", aid): return {"finished": False, "tapped": tapped, "mode": self.mode}
            self.capture("after_layer")  # confirm, then next layer (5.4)
        return {"finished": True, "tapped": tapped, "mode": self.mode}
    def final_zone_check(self, capture_fn=None):
        return (capture_fn or self.capture)("final_zone_check")  # 5.6
