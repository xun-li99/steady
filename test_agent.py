"""
Steady Test Agent — accumulates state across cycles, survives crashes via handoff.
Used for A/B comparison: Steady-managed vs bare run. Measures recovery, not toy scores.
"""
import os, json, time, random, sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

STATE_FILE = Path(os.environ.get("STATE_FILE", ".steady/test_state.json"))
CYCLES = int(os.environ.get("CYCLES", "60"))
CRASH_PROB = float(os.environ.get("CRASH_PROB", "0.15"))  # 15% chance per cycle

def bj_now() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"cycle": 0, "items": [], "started": bj_now(), "restarts": 0, "history": []}

def save_state(s):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(s, ensure_ascii=False, indent=1))

def main():
    ctx = os.environ.get("STEADY_CONTEXT", "")
    state = load_state()
    state["restarts"] += 1
    state["last_context"] = ctx[:200] if ctx else "(no context)"

    for i in range(CYCLES):
        cycle = state["cycle"] + 1
        item = f"item_{cycle}"
        state["cycle"] = cycle
        state["items"].append(item)
        state["history"].append({
            "cycle": cycle, "item": item, "time": bj_now(),
            "had_context": bool(ctx and len(ctx) > 10),
            "restart_number": state["restarts"],
        })
        # keep only last 200 history entries
        if len(state["history"]) > 200:
            state["history"] = state["history"][-200:]
        save_state(state)
        print(f"[{bj_now()}] cycle={cycle} items={len(state['items'])} restarts={state['restarts']}", flush=True)

        # random crash — daemon should restart and resume if Steady is managing
        if random.random() < CRASH_PROB:
            print(f"[{bj_now()}] CRASH at cycle {cycle}", flush=True)
            sys.exit(1)

        time.sleep(2)  # simulate real work per cycle

    # normal completion
    save_state(state)
    print(f"[{bj_now()}] DONE: {len(state['items'])} items, {state['restarts']} restarts", flush=True)

if __name__ == "__main__":
    main()
