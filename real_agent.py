"""
Real agent — not a crash simulator. Runs actual tasks against DeepSeek.
May crash from: API timeouts, rate limits, network errors, OOM.
Designed to run under Steady for 48 hours. Measures: does crash_interval actually lengthen?
"""
import os, json, time, random, sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

STATE_FILE = Path(os.environ.get("STATE_FILE", ".steady/real_agent_state.json"))
TASKS = [
    "Write a one-sentence summary of what gravity is.",
    "Name three countries in Africa and their capitals.",
    "List four prime numbers between 10 and 50.",
    "Explain in one sentence why the sky is blue.",
    "What is the chemical formula for water?",
    "Convert 'hello world' to Pig Latin.",
    "What is 17 * 23?",
    "Name two moons of Jupiter.",
    "In one sentence: what does DNA do?",
    "List three programming languages and their primary use.",
    "What year did the Berlin Wall fall?",
    "Spell 'algorithm' backwards.",
    "What is the speed of light in m/s?",
    "Name a mammal that can fly.",
    "In one word: what gas do plants absorb from the air?",
]
API_URL = os.environ.get("LI_API_URL", "https://api.deepseek.com/v1/chat/completions")
API_KEY = os.environ.get("LI_API_KEY", "")
API_MODEL = os.environ.get("LI_API_MODEL", "deepseek-chat")
TASK_INTERVAL = int(os.environ.get("TASK_INTERVAL", "30"))  # seconds between tasks

def bj_now():
    return (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")

def call_deepseek(prompt, max_tokens=80):
    """Real API call — may fail with timeout, rate limit, network error."""
    import urllib.request as urllib_request
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": max_tokens,
        "model": API_MODEL,
    }
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    req = urllib_request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
    )
    with urllib_request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]


def main():
    ctx = os.environ.get("STEADY_CONTEXT", "")
    state = {"completed": [], "errors": [], "restart_number": 0, "crash_intervals": []}

    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))

    state["restart_number"] += 1
    state["last_context"] = ctx[:300] if ctx else "(no context)"
    last_crash_time = state.get("last_crash_time")
    if last_crash_time:
        interval = time.time() - last_crash_time
        state["crash_intervals"].append(round(interval, 1))

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    for task in TASKS:
        try:
            print(f"[{bj_now()}] Asking: {task[:60]}...", flush=True)
            answer = call_deepseek(task)
            state["completed"].append({
                "task": task, "answer": answer[:100], "time": bj_now(),
                "restart_number": state["restart_number"],
            })
            print(f"[{bj_now()}] OK: {answer[:60]}", flush=True)

            # Save after each success
            if len(state["completed"]) > 200:
                state["completed"] = state["completed"][-200:]
            STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1))

            time.sleep(TASK_INTERVAL)

        except Exception as e:
            state["errors"].append({
                "task": task, "error": str(e)[:100], "time": bj_now(),
                "restart_number": state["restart_number"],
            })
            state["last_crash_time"] = time.time()
            STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1))
            print(f"[{bj_now()}] CRASH: {e}", flush=True)
            sys.exit(1)  # Let Steady catch and restart

    # Loop continuously — more cycles = more real crash opportunities
    state["loops_completed"] = state.get("loops_completed", 0) + 1
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1))
    print(f"[{bj_now()}] LOOP {state['loops_completed']} DONE. {len(state['completed'])} tasks, {len(state['errors'])} errors, {state['restart_number']} restarts. Restarting...", flush=True)
    sys.exit(0)  # Normal exit — Steady restarts, crash_interval still tracked

if __name__ == "__main__":
    main()
