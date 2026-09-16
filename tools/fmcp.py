#!/usr/bin/env python3
"""Minimal client for Fusion's built-in MCP server (127.0.0.1:27182/mcp).
Usage: fmcp.py tools            -> list tools
       fmcp.py read <what>      -> fusion_mcp_read (e.g. documents, screenshot)
       fmcp.py run <script.py>  -> fusion_mcp_execute featureType=script (must define run(_context))"""
import json, sys, urllib.request
URL = "http://127.0.0.1:27182/mcp"
SID = None
def call(method, params=None, _id=1, notify=False):
    global SID
    body = {"jsonrpc": "2.0", "method": method}
    if params is not None: body["params"] = params
    if not notify: body["id"] = _id
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream", **({"Mcp-Session-Id": SID} if SID else {})})
    with urllib.request.urlopen(req, timeout=120) as r:
        SID = r.headers.get("Mcp-Session-Id", SID)
        raw = r.read().decode()
    if notify or not raw.strip(): return None
    if raw.startswith("event:") or "\ndata:" in raw or raw.startswith("data:"):
        for line in raw.splitlines():
            if line.startswith("data:"): return json.loads(line[5:].strip())
    return json.loads(raw)
def init():
    r = call("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "fmcp", "version": "0.1"}})
    call("notifications/initialized", {}, notify=True)
    return r
if __name__ == "__main__":
    cmd = sys.argv[1]
    init()
    if cmd == "tools":
        r = call("tools/list", {}, 2)
        for t in r["result"]["tools"]: print("-", t["name"], ":", (t.get("description") or "")[:160].replace("\n", " "))
    elif cmd == "read":
        r = call("tools/call", {"name": "fusion_mcp_read", "arguments": {"what": sys.argv[2]}}, 2)
        print(json.dumps(r, indent=1)[:4000])
    elif cmd == "run":
        code = open(sys.argv[2]).read()
        r = call("tools/call", {"name": "fusion_mcp_execute", "arguments": {"featureType": "script", "code": code}}, 2)
        print(json.dumps(r, indent=1)[:6000])
