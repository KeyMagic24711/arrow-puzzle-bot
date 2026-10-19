
"""Update check (spec 7.4). Single source of truth: version.json at repo root.
Nothing downloads in the background: download only happens when the user
presses the update button. Forced floor: a module below its floor version
must be updated before running (same idea as v1)."""
import json, urllib.request

RAW_VERSION_URL = "https://raw.githubusercontent.com/KeyMagic24711/arrow-puzzle-bot/main/version.json"

def parse_version(v): return tuple(int(x) for x in str(v).split(".") if x.isdigit())
def is_newer(remote, local): return parse_version(remote) > parse_version(local)
def load_local(path):
    try: return json.loads(open(path, encoding="utf-8").read())
    except Exception: return {"app": "0.0.0", "modules": {}}
def fetch_remote(url=RAW_VERSION_URL, timeout=15):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))
def check(local, remote):
    out = {"app_update": is_newer(remote.get("app","0"), local.get("app","0")), "modules": {}}
    for name, rv in (remote.get("modules") or {}).items():
        lv = (local.get("modules") or {}).get(name, "0.0.0")
        out["modules"][name] = {"local": lv, "remote": rv, "update": is_newer(rv, lv)}
    return out
def forced_floor_violations(local, remote):
    floors = remote.get("forced_floor") or {}
    bad = []
    for name, floor in floors.items():
        lv = (local.get("modules") or {}).get(name, "0.0.0")
        if parse_version(lv) < parse_version(floor): bad.append((name, lv, floor))
    return bad
