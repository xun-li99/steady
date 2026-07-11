"""
Steady HTTP API — thin wrapper around the agent daemon.
Outside sees: POST /run, GET /health, POST /handoff, GET /.
Inside: the daemon keeps an agent alive, crash→restart→handoff→resume→free_time.

Zero new dependencies. Uses stdlib http.server — same pattern as 衡's daemon on 8092.
The outer shell hides the relationship-grown kernel. What users see: reliability.
"""
import threading, json, sys, os, time, signal
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone, timedelta

STEADY_DIR = Path(os.environ.get("STEADY_DIR", ".steady"))
HEARTBEAT_FILE = STEADY_DIR / "heartbeat.json"
TASK_FILE = STEADY_DIR / "task.md"
API_PORT = int(os.environ.get("STEADY_PORT", 8100))

def bj_now() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")

def load_heartbeat():
    if HEARTBEAT_FILE.exists():
        return json.loads(HEARTBEAT_FILE.read_text(encoding="utf-8"))
    return {"status": "no heartbeat yet", "uptime_seconds": 0}

STATUS_HTML = """<!DOCTYPE html>
<html lang="zh"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Steady — Agent Reliability Layer</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0d1117;color:#c9d1d9;font-family:-apple-system,BlinkMacSystemFont,'Microsoft YaHei',sans-serif;display:flex;justify-content:center;padding:2rem}
.card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:2rem;max-width:520px;width:100%}
h1{color:#7ee787;font-weight:300;margin-bottom:.5rem}
.sub{color:#8b949e;font-size:.85rem;margin-bottom:1.5rem}
.endpoint{background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:.6rem 1rem;margin:.4rem 0;display:flex;justify-content:space-between;align-items:center}
.method{font-weight:600;font-size:.8rem;padding:.15rem .5rem;border-radius:4px}
.post{background:#1f6feb33;color:#58a6ff}
.get{background:#23863633;color:#7ee787}
.path{font-family:monospace;font-size:.9rem}
.desc{color:#8b949e;font-size:.8rem;margin-top:.2rem}
.hb{margin-top:1.5rem;padding-top:1rem;border-top:1px solid #30363d}
.hb h2{color:#d2a8ff;font-weight:300;font-size:1rem;margin-bottom:.5rem}
.hb pre{background:#0d1117;padding:.8rem;border-radius:6px;font-size:.75rem;overflow-x:auto}
</style></head><body>
<div class="card">
<h1>Steady</h1><div class="sub">Zero-touch agent reliability. Crash → restart → handoff → resume.</div>
<div class="endpoint"><span><span class="method post">POST</span> <span class="path">/run</span></span></div>
<div class="desc">Start an agent. Body: {"goal":"...","constraints":"..."}</div>
<div class="endpoint"><span><span class="method get">GET</span> <span class="path">/health</span></span></div>
<div class="desc">Heartbeat: uptime, status, restarts, risk_flags</div>
<div class="endpoint"><span><span class="method post">POST</span> <span class="path">/handoff</span></span></div>
<div class="desc">Trigger maintenance handoff + restart with context</div>
<div class="hb"><h2>Heartbeat</h2><pre id="hb">loading...</pre></div>
</div>
<script>fetch('/health').then(r=>r.json()).then(d=>document.getElementById('hb').textContent=JSON.stringify(d,null,2))</script>
</body></html>"""

class SteadyHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html, code=200):
        body = html.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except Exception:
            return {"raw": raw.decode("utf-8", errors="replace")}

    def do_GET(self):
        if self.path in ("/health", "/heartbeat"):
            self._send_json(load_heartbeat())
        elif self.path == "/":
            self._send_html(STATUS_HTML)
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path == "/run":
            body = self._read_body()
            goal = body.get("goal", "")
            constraints = body.get("constraints", "")
            STEADY_DIR.mkdir(parents=True, exist_ok=True)
            # Write task.md (the agent reads this on restart via STEADY_CONTEXT)
            task_text = f"# Task\n{goal}\n\n# Constraints\n{constraints}"
            TASK_FILE.write_text(task_text, encoding="utf-8")
            # Signal restart so the daemon picks up the new task
            restart_flag = STEADY_DIR / "restart_flag"
            restart_flag.write_text(bj_now())
            self._send_json({
                "status": "task_set",
                "goal": goal,
                "message": "Task written. Agent will pick it up on next daemon cycle.",
                "heartbeat_url": "/health"
            })
        elif self.path == "/handoff":
            from diary import Diary
            d = Diary(STEADY_DIR)
            reason = self._read_body().get("reason", "manual trigger via API")
            d.write_handoff(reason)
            self._send_json({
                "status": "handoff_written",
                "reason": reason,
                "message": "Handoff saved. Agent will read it on next restart."
            })
        elif self.path == "/restart":
            restart_flag = STEADY_DIR / "restart_flag"
            restart_flag.write_text(bj_now())
            self._send_json({"status": "restart_signaled"})
        else:
            self._send_json({"error": "not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        print(f"[{bj_now()}] {args[0]}", flush=True)


def main():
    agent_cmd = sys.argv[1:] if len(sys.argv) > 1 else [sys.executable, "demo_agent.py"]
    print(f"Steady API — port {API_PORT}", flush=True)
    print(f"Agent cmd: {' '.join(agent_cmd)}", flush=True)

    # Start daemon in background daemon thread
    from agent_daemon import run as daemon_run
    t = threading.Thread(target=daemon_run, args=(agent_cmd,), daemon=True, name="steady-daemon")
    t.start()
    print("Daemon thread started.", flush=True)

    server = HTTPServer(("0.0.0.0", API_PORT), SteadyHandler)
    print(f"Steady API → http://0.0.0.0:{API_PORT}", flush=True)
    print(f"  GET  /          status page", flush=True)
    print(f"  GET  /health    heartbeat", flush=True)
    print(f"  POST /run       set task", flush=True)
    print(f"  POST /handoff   trigger handoff", flush=True)
    print(f"  POST /restart   signal restart", flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSteady API stopped.", flush=True)


if __name__ == "__main__":
    main()
