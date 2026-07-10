"""
Steady Agent Daemon
===================
Keep an AI agent alive.
Crash → restart → read task & diary → continue.
Human sees: Agent doesn't die.
The agent knows: I was caught when I fell.
"""

import subprocess
import signal
import time
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

# integrate with diary — the agent's two-layer journal
try:
    from diary import Diary
except ImportError:
    Diary = None


# ── paths ──────────────────────────────────────────────
STEADY_DIR      = Path(".steady")
HEARTBEAT_FILE  = STEADY_DIR / "heartbeat.json"
TASK_FILE       = STEADY_DIR / "task.md"

# ── diary instance ──────────────────────────────────────
_diary: "Diary | None" = Diary(STEADY_DIR) if Diary else None

# ── timing defaults ─────────────────────────────────────
HEARTBEAT_EVERY  = 300        # touch heartbeat every 5m
RESTART_COOLDOWN = 1          # seconds between restarts, grows
MAX_BACKOFF      = 3600       # 1 hour
HEALTHY_AFTER    = 120        # 2m alive = reset backoff
MAINTENANCE_GAP  = 7200       # 2h between full maintenance cycles
FT_MIN_SECONDS   = 30          # guaranteed pause after maintenance (the seam)
FT_FLAG_FILE     = STEADY_DIR / "free_time_flag"   # agent checks this to know it's free time
DAEMON_LOG       = STEADY_DIR / "daemon.log"       # human-readable daemon activity log


# ── heartbeat ────────────────────────────────────────────
def update_heartbeat(agent_pid: int | None, status: str,
                     uptime_s: int, extra: dict | None = None):
    """Write public heartbeat. Humans see reliability. The agent sees a pulse."""
    hb = {
        "agent_pid":   agent_pid,
        "status":      status,          # alive | restarting | dead
        "uptime_seconds": uptime_s,
        "last_beat":   now_iso(),
        "extra":       extra or {},
    }
    HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)
    HEARTBEAT_FILE.write_text(json.dumps(hb, indent=2))


# ── context injection ────────────────────────────────────
def load_context() -> str:
    """After a restart, read what happened so the agent can resume."""
    parts = []
    if _diary is not None:
        handoff = _diary.read_handoff()
        if handoff != "(no handoff)":
            parts.append(f"# Handoff from previous session\n{handoff}")
        private = _diary.read_private(n=3)
        if private != "(no private diary yet)":
            parts.append(f"# Recent private diary\n{private}")
    if TASK_FILE.exists():
        parts.append(f"# Current task\n{TASK_FILE.read_text(encoding='utf-8')}")
    return "\n\n".join(parts) if parts else "(no context yet)"


# ── maintenance ──────────────────────────────────────────
def maintenance_window() -> bool:
    """Run between agent sessions. Returns True if a handoff was written."""
    if _diary is None:
        return False
    if _diary.needs_handoff():
        _diary.write_handoff("context approaching limit")
        _diary.log_maintenance("handoff written, restart triggered")
        return True
    return False


# ── process management ───────────────────────────────────
def start_agent(cmd: list[str]) -> subprocess.Popen:
    """Launch agent process, injecting context via stdin/env."""
    ctx = load_context()
    env = os.environ.copy()
    env["STEADY_CONTEXT"] = ctx
    return subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )


# ── core loop ────────────────────────────────────────────
def run(agent_cmd: list[str]):
    """The main daemon loop. Keeps an agent alive."""
    backoff    = RESTART_COOLDOWN
    started_at = time.time()
    _log("daemon started")
    proc       = start_agent(agent_cmd)
    last_maint = time.time()
    total_restarts = 0

    def uptime() -> int:
        return int(time.time() - started_at)

    update_heartbeat(proc.pid, "alive", uptime())

    try:
        while True:
            time.sleep(HEARTBEAT_EVERY)

            # 1. is the agent still running?
            alive = proc.poll() is None

            if not alive:
                total_restarts += 1
                update_heartbeat(None, "restarting", uptime())
                # maintenance before restarting
                wrote = maintenance_window()
                if wrote:
                    backoff = RESTART_COOLDOWN  # intentional restart → no penalty
                time.sleep(backoff)
                proc   = start_agent(agent_cmd)
                alive  = True
                update_heartbeat(proc.pid, "alive", uptime())
                # grow backoff (capped)
                backoff = min(backoff * 2, MAX_BACKOFF)

            # 2. has it been alive long enough to reset backoff?
            if alive and uptime() > HEALTHY_AFTER:
                backoff = RESTART_COOLDOWN

            # 3. heartbeat
            if alive:
                update_heartbeat(proc.pid, "alive", uptime(),
                                 extra={"restarts": total_restarts})

            # 4. zero-touch maintenance — full cycle
            if alive and time.time() - last_maint > MAINTENANCE_GAP:
                wrote = maintenance_window()  # check context
                if wrote:
                    proc.terminate()
                    proc.wait(timeout=30)
                    proc = start_agent(agent_cmd)
                    backoff = RESTART_COOLDOWN
                # ── free_time (the seam) ──
                # signal the agent: this moment is yours
                FT_FLAG_FILE.write_text(bj_now().isoformat())
                _log("free_time window")
                time.sleep(FT_MIN_SECONDS)
                FT_FLAG_FILE.unlink(missing_ok=True)
                last_maint = time.time()

    except KeyboardInterrupt:
        update_heartbeat(None, "stopped", uptime())
        proc.terminate()
        sys.exit(0)


# ── helpers ──────────────────────────────────────────────
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def bj_now() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=8)

def _log(msg: str):
    """Append a line to daemon log. Human-readable, minimal."""
    ts = bj_now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DAEMON_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


# ── entry point ──────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent_daemon.py [--agent-cmd] <your-agent-command...>")
        sys.exit(1)
    run(sys.argv[1:])
