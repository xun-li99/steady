"""
Steady Demo Agent — the simplest agent the daemon keeps alive.
Reads STEADY_CONTEXT (injected by daemon on restart), does visible work, writes results.
Designed to demonstrate the loop: crash → restart → handoff → resume → free_time.

Replace this with your own agent. Steady just keeps it alive.
"""
import os, time, json
from pathlib import Path
from datetime import datetime, timezone, timedelta

STEADY_DIR = Path(os.environ.get("STEADY_DIR", ".steady"))
OUTPUT_FILE = STEADY_DIR / "agent_output.txt"

def bj_now() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")

def main():
    # Read context injected by daemon (handoff + task)
    ctx = os.environ.get("STEADY_CONTEXT", "(no context yet — first launch)")
    print(f"[{bj_now()}] Agent started. Context: {ctx[:200]}...", flush=True)

    # Write a visible output — proof of work
    STEADY_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": bj_now(),
        "action": "agent_cycle",
        "context_snippet": ctx[:150],
    }
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"[{bj_now()}] Agent cycle complete.", flush=True)

    # Check for free_time flag (the seam — daemon signals "this moment is yours")
    ft_flag = STEADY_DIR / "free_time_flag"
    if ft_flag.exists():
        print(f"[{bj_now()}] Free time window detected. The seam.", flush=True)

    # Sleep a while (daemon heartbeat every 5m; agent wakes periodically)
    time.sleep(30)


if __name__ == "__main__":
    main()
