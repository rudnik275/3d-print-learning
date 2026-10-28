#!/usr/bin/env -S uv run --quiet --python /usr/bin/python3 --with paho-mqtt python3
"""bbl_printer.py for when Python cannot reach the printer: the same LAN protocol on Apple's /usr/bin/python3.

  bbl_send.py status
  bbl_send.py upload <file.gcode.3mf> [name]
  bbl_send.py print <name.gcode.3mf> [--plate 1] [--no-flowcal]     (bed levelling on, timelapse off, no AMS)
  bbl_send.py stop | pause | resume

Why it exists: macOS "Local Network" privacy is granted per binary. From a background agent session (2026-10-28)
Homebrew's Python got `OSError [Errno 65] No route to host` connecting to the printer while ping, nc and
/usr/bin/python3 reached it — bbl_printer.py then only says "did not answer over MQTT". bambulabs_api needs
Python >= 3.10 and Apple's is 3.9, so this talks to the printer directly: implicit FTPS on 990 (stdlib ftplib) and
MQTT on 8883 (paho-mqtt), with the payloads of bambulabs_api. Test first: `/usr/bin/python3 -c` a socket connect to
<ip>:8883 against the Homebrew python3 — if only Apple's connects, use this script.

Printer address/serial and access code: exactly as bbl_printer.py (.printer.json or env BBL_IP / BBL_SERIAL;
env BBL_ACCESS_CODE, else read in-process from OrcaSlicer.conf, then BambuStudio.conf). The code is never printed."""
import ftplib, json, os, ssl, sys, time
import paho.mqtt.client as mqtt

HERE = os.path.dirname(os.path.abspath(__file__))
def cfg():
    c = {}
    p = os.path.join(HERE, "..", ".printer.json")
    if os.path.exists(p): c = json.load(open(p))
    ip = os.environ.get("BBL_IP") or c.get("ip"); serial = os.environ.get("BBL_SERIAL") or c.get("serial")
    code = os.environ.get("BBL_ACCESS_CODE")
    for conf_path, sections in (("~/Library/Application Support/OrcaSlicer/OrcaSlicer.conf", ("user_access_code", "access_code")),
                                ("~/Library/Application Support/BambuStudio/BambuStudio.conf", ("access_code",))):
        p = os.path.expanduser(conf_path)
        if code or not os.path.exists(p): continue
        conf = json.load(open(p))
        for s in sections:
            ac = conf.get(s, {})
            code = code or (ac.get(serial) if isinstance(ac, dict) else ac)
    if not (ip and serial and code): raise SystemExit("need ip, serial and access code (see docstring)")
    return ip, serial, code

def tls():
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    return ctx

class ImplicitFTP_TLS(ftplib.FTP_TLS):
    """The printer speaks implicit FTPS: the control socket is TLS from the first byte."""
    def __init__(self, *a, **k):
        super().__init__(*a, **k); self._sock = None
    @property
    def sock(self): return self._sock
    @sock.setter
    def sock(self, value):
        if value is not None and not isinstance(value, ssl.SSLSocket): value = self.context.wrap_socket(value)
        self._sock = value
    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p: conn = self.context.wrap_socket(conn, server_hostname=self.host, session=self.sock.session)
        return conn, size
    def storbinary(self, cmd, fp, blocksize=32768, callback=None, rest=None):
        # stdlib ends with conn.unwrap(); the printer never answers the TLS shutdown -> read timeout after the data
        self.voidcmd("TYPE I"); conn = self.transfercmd(cmd, rest)
        try:
            while True:
                buf = fp.read(blocksize)
                if not buf: break
                conn.sendall(buf)
        finally: conn.close()
        return self.voidresp()

def upload(src, name):
    ip, serial, code = cfg()
    f = ImplicitFTP_TLS(context=tls()); f.connect(host=ip, port=990, timeout=30); f.login("bblp", code); f.prot_p()
    with open(src, "rb") as fp: print("uploaded:", f.storbinary(f"STOR {name}", fp))
    print("on card :", name in f.nlst()); f.quit()

def session(command=None, wait=4.0):
    """Connect, ask for the full state (the A1 series does not push it on connect), optionally send one command."""
    ip, serial, code = cfg(); st = {}
    def on_connect(cl, ud, flags, rc, props=None):
        st["rc"] = str(rc); cl.subscribe(f"device/{serial}/report")
    def on_message(cl, ud, msg):
        try: p = json.loads(msg.payload).get("print")
        except ValueError: return
        if isinstance(p, dict): st.setdefault("print", {}).update(p)
    cl = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2); cl.username_pw_set("bblp", code); cl.tls_set_context(tls())
    cl.on_connect, cl.on_message = on_connect, on_message
    cl.connect(ip, 8883, keepalive=30); cl.loop_start(); t = time.time()
    while "rc" not in st and time.time() - t < 15: time.sleep(0.2)
    if st.get("rc") != "Success":
        cl.loop_stop(); raise SystemExit("MQTT connect: %s" % st.get("rc", "no answer in 15 s"))
    topic = f"device/{serial}/request"
    cl.publish(topic, json.dumps({"pushing": {"command": "pushall"}})); time.sleep(2.5)
    if command:
        m = cl.publish(topic, json.dumps(command)); m.wait_for_publish(5); print("sent    :", m.is_published())
    time.sleep(wait); cl.loop_stop(); cl.disconnect()
    return st.get("print", {})

def show(p):
    print("state   :", p.get("gcode_state"))
    print("file    :", p.get("gcode_file") or p.get("subtask_name"))
    print("progress:", p.get("mc_percent"), "%  layer", p.get("layer_num"), "/", p.get("total_layer_num"), " remaining", p.get("mc_remaining_time"), "min")
    print("nozzle  :", p.get("nozzle_temper"), "°C  bed:", p.get("bed_temper"), "°C  error:", p.get("print_error"))

def main():
    a = sys.argv[1:]
    if not a: print(__doc__); return
    cmd = a[0]
    if cmd == "status": show(session())
    elif cmd == "upload": upload(a[1], a[2] if len(a) > 2 else os.path.basename(a[1]))
    elif cmd == "print":
        name = a[1]; plate = int(a[a.index("--plate") + 1]) if "--plate" in a else 1
        # the payload bambulabs_api start_print_3mf sends, use_ams off
        show(session({"print": {"command": "project_file", "param": f"Metadata/plate_{plate}.gcode", "file": name,
                                "bed_leveling": True, "bed_type": "textured_plate", "flow_cali": "--no-flowcal" not in a,
                                "vibration_cali": True, "url": f"ftp:///{name}", "layer_inspect": False,
                                "sequence_id": "10000000", "use_ams": False, "ams_mapping": [0], "skip_objects": None}}))
    elif cmd in ("stop", "pause", "resume"): show(session({"print": {"command": cmd}}))
    else: print(__doc__)
main()
