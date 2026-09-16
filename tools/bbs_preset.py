#!/usr/bin/env python3
"""Write a Bambu Studio user preset JSON (the on-disk format Studio itself uses: only the overrides
plus `inherits`). Import it in Studio via File → Import → Import Configs; it then syncs to the cloud.

Usage: bbs_preset.py filament|process "<name>" "<inherits>" key=value [key=value ...] [--out dir]
  e.g. bbs_preset.py filament "SUNLU PLA @BBL A1M" "SUNLU PLA+ @BBL A1M" nozzle_temperature=220 filament_flow_ratio=0.98
Filament values are stored as one-element lists (Studio's convention); process values as strings."""
import json, os, sys
def main():
    a = sys.argv[1:]
    kind, name, base = a[0], a[1], a[2]
    out = a[a.index("--out") + 1] if "--out" in a else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "profiles", "user")
    sets = [x for x in a[3:] if "=" in x]
    j = {"from": "User", "inherits": base, "name": name, "version": "2.8.0.6"}
    if kind == "filament":
        j["filament_settings_id"] = [name]; j["filament_extruder_variant"] = ["Direct Drive Standard"]
        for kv in sets: k, v = kv.split("=", 1); j[k] = [v]
        if "nozzle_temperature" in j and "nozzle_temperature_initial_layer" not in j: j["nozzle_temperature_initial_layer"] = j["nozzle_temperature"]
    else:
        j["print_settings_id"] = name; j["print_extruder_id"] = ["1"]; j["print_extruder_variant"] = ["Direct Drive Standard"]
        for kv in sets: k, v = kv.split("=", 1); j[k] = v
    os.makedirs(out, exist_ok=True); p = os.path.join(out, name + ".json")
    json.dump(dict(sorted(j.items())), open(p, "w"), indent=4, ensure_ascii=False); print("written:", p); print(json.dumps(j, indent=2, ensure_ascii=False))
main()
