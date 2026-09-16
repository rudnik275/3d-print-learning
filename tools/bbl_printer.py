#!/usr/bin/env -S uv run --quiet --with bambulabs_api --with paho-mqtt python3
"""Talk to the Bambu Lab printer over LAN (MQTT 8883 / FTPS 990 / camera 6000).

  bbl_printer.py status                 state, progress, temps, current file
  bbl_printer.py upload <file.gcode.3mf> [name]
  bbl_printer.py print <name.gcode.3mf> [--plate 1] [--no-flowcal]     (bed levelling on, timelapse off)
  bbl_printer.py stop | pause | resume
  bbl_printer.py camera <out.jpg>

Printer address/serial: tools/../.printer.json ({"ip":..., "serial":...}) or env BBL_IP / BBL_SERIAL.
Access code: env BBL_ACCESS_CODE, else read in-process from Bambu Studio's own config
(BambuStudio.conf → access_code[serial]). It is never printed."""
import json, os, sys, time, warnings
warnings.filterwarnings("ignore")
import bambulabs_api as bl

HERE = os.path.dirname(os.path.abspath(__file__))
def cfg():
    c = {}
    p = os.path.join(HERE, "..", ".printer.json")
    if os.path.exists(p): c = json.load(open(p))
    ip = os.environ.get("BBL_IP") or c.get("ip"); serial = os.environ.get("BBL_SERIAL") or c.get("serial")
    code = os.environ.get("BBL_ACCESS_CODE")
    if not code:
        conf = json.load(open(os.path.expanduser("~/Library/Application Support/BambuStudio/BambuStudio.conf")))
        ac = conf.get("access_code", {})
        code = ac.get(serial) if isinstance(ac, dict) else ac
    if not (ip and serial and code): raise SystemExit("need ip, serial and access code (see docstring)")
    return ip, serial, code

def connect(timeout=15):
    ip, serial, code = cfg()
    pr = bl.Printer(ip, code, serial)
    pr.mqtt_start()
    t = time.time()
    while time.time() - t < timeout:
        if pr.mqtt_client_ready(): break
        time.sleep(0.5)
    else: raise SystemExit("printer did not answer over MQTT within %ds (LAN access refused? Developer/LAN mode?)" % timeout)
    # A1 series does not push a full state on connect — ask for it
    mc = getattr(pr, "mqtt_client", None)
    if mc and hasattr(mc, "pushall"): mc.pushall()
    time.sleep(2.5)
    return pr

def main():
    a = sys.argv[1:]
    if not a: print(__doc__); return
    cmd = a[0]
    if cmd == "status":
        pr = connect(); time.sleep(1.5)
        print("state   :", pr.get_state())
        print("file    :", pr.get_file_name() or pr.subtask_name())
        print("progress:", pr.get_percentage(), "%  layer", pr.current_layer_num(), "/", pr.total_layer_num(), " remaining", pr.get_time(), "min")
        print("nozzle  :", pr.get_nozzle_temperature(), "°C  bed:", pr.get_bed_temperature(), "°C  speed:", pr.get_print_speed())
        pr.disconnect()
    elif cmd == "upload":
        ip, serial, code = cfg(); pr = bl.Printer(ip, code, serial)
        src = a[1]; name = a[2] if len(a) > 2 else os.path.basename(src)
        with open(src, "rb") as f: r = pr.upload_file(f, name)
        print("uploaded:", r)
    elif cmd == "print":
        name = a[1]; plate = int(a[a.index("--plate") + 1]) if "--plate" in a else 1
        pr = connect(); time.sleep(1)
        ok = pr.start_print(name, plate, use_ams=False, flow_calibration="--no-flowcal" not in a)
        print("start_print ->", ok); time.sleep(3); print("state:", pr.get_state()); pr.disconnect()
    elif cmd in ("stop", "pause", "resume"):
        pr = connect(); print(cmd, "->", getattr(pr, cmd + "_print")()); pr.disconnect()
    elif cmd == "camera":
        pr = connect(); pr.camera_start(); time.sleep(3)
        img = pr.get_camera_image(); img.save(a[1]); print("saved", a[1]); pr.camera_stop(); pr.disconnect()
    else: print(__doc__)
main()
