#!/usr/bin/env python3
"""Resolve a Bambu Studio preset with its full `inherits` chain (system + user dirs).
Usage: bbs_resolve.py <filament|process|machine> "<preset name>" [key ...]
Prints merged JSON (all keys) or only the requested keys."""
import json, os, sys, glob
BASE = os.path.expanduser("~/Library/Application Support/BambuStudio")
def load(kind, name):
    # user presets first, then system (vendor presets live in system/BBL/<kind>/<Vendor>/)
    pats = [os.path.join(BASE, "user", "*", kind, name + ".json"),
            os.path.join(BASE, "system", "BBL", kind, name + ".json"),
            os.path.join(BASE, "system", "BBL", kind, "*", name + ".json")]
    for pat in pats:
        hits = glob.glob(pat)
        if hits:
            return json.load(open(hits[0])), hits[0]
    raise SystemExit(f"preset not found: {kind}/{name}")
def resolve(kind, name):
    chain = []
    while name:
        j, p = load(kind, name); chain.append((name, j, p)); name = j.get("inherits")
    merged = {}
    for n, j, p in reversed(chain):       # base first, overrides last
        merged.update(j)
    merged["_chain"] = [n for n, _, _ in chain]
    return merged
if __name__ == "__main__":
    kind, name, keys = sys.argv[1], sys.argv[2], sys.argv[3:]
    m = resolve(kind, name)
    if keys:
        for k in keys: print(f"{k} = {m.get(k, '<absent>')}")
    else:
        print(json.dumps(m, indent=1, ensure_ascii=False))
