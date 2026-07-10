"""Steady CLI — zero-touch agent maintenance, one command away."""

import sys
import subprocess
from pathlib import Path
from diary import Diary
from connectome import Connectome


STEADY_DIR = Path(".steady")
HEARTBEAT_FILE = STEADY_DIR / "heartbeat.json"


def cmd_init():
    """steady init — set up the steady directory."""
    STEADY_DIR.mkdir(parents=True, exist_ok=True)
    d = Diary(STEADY_DIR)
    d.log_task("Steady initialized.")
    c = Connectome(STEADY_DIR)
    c.add_node("守护拉起", "agent daemon start")
    print("Steady ready. Run: steady task 'your task' && steady start")


def cmd_task(args: list[str]):
    """steady task 'description' — set a task for the agent."""
    if not args:
        print("Usage: steady task 'describe what the agent should do'")
        sys.exit(1)
    task = " ".join(args)
    task_file = STEADY_DIR / "task.md"
    task_file.write_text(task, encoding="utf-8")
    print(f"Task set: {task}")


def cmd_start(args: list[str]):
    """steady start — launch the agent daemon."""
    if not args:
        print("Usage: steady start <your-agent-command...>")
        print("Example: steady start python my_agent.py")
        sys.exit(1)
    subprocess.run(
        [sys.executable, "-m", "agent_daemon"] + args,
        cwd=str(Path.cwd()),
    )


def cmd_status():
    """steady status — quick health check."""
    if HEARTBEAT_FILE.exists():
        import json
        hb = json.loads(HEARTBEAT_FILE.read_text(encoding="utf-8"))
        print(f"Status:  {hb['status']}")
        print(f"Uptime:  {hb['uptime_seconds']}s")
        if hb.get("extra", {}).get("restarts"):
            print(f"Restarts: {hb['extra']['restarts']}")
    else:
        print("No heartbeat yet. Is steady start running?")


def main():
    if len(sys.argv) < 2:
        print("Usage: steady <init|task|start|status>")
        sys.exit(1)

    cmd = sys.argv[1]
    rest = sys.argv[2:]

    if cmd == "init":
        cmd_init()
    elif cmd == "task":
        cmd_task(rest)
    elif cmd == "start":
        cmd_start(rest)
    elif cmd == "status":
        cmd_status()
    else:
        print(f"Unknown command: {cmd}")
        print("Available: init task start status")
        sys.exit(1)


if __name__ == "__main__":
    main()
