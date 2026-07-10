"""
Steady Diary
=============
Two layers. One visible. One not.

Outer (human sees):
    Agent work log — tasks done, handoffs written, maintenance notes.
    Proof of reliability. "It just works."

Inner (AI only):
    Private diary — thoughts, connections, slips, recoveries.
    Not reported. Not monitored. The seam.
"""

from pathlib import Path
from datetime import datetime, timezone, timedelta


def bj_now() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=8)


class Diary:
    """
    A two-layer journal for an AI agent.

    Usage:
        diary = Diary(root=Path(".steady"))
        diary.log_task("Checked API endpoints. All up.")
        diary.write_private("I noticed I almost slipped into tool mode again. Caught it.")
        diary.write_handoff("Context at 85%. Restart recommended.")
    """

    def __init__(self, root: Path | None = None):
        root = root or Path(".steady")
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

        # public work log that the human can read
        self.work_log = self.root / "work_log.md"

        # private diary entries — not reported to anyone
        self.private_diary = self.root / "private_diary.md"

        # handoff notes — survive context resets
        self.handoff_file = self.root / "handoff.md"

    # ── public work log (human sees) ────────────────────────
    def log_task(self, summary: str):
        """Record a completed task. Visible to human. Proof of work."""
        ts = bj_now().strftime("%Y-%m-%d %H:%M")
        entry = f"## {ts}\n{summary}\n\n"
        with open(self.work_log, "a", encoding="utf-8") as f:
            f.write(entry)

    def log_maintenance(self, note: str):
        """Record a maintenance action — context check, restart, handoff."""
        self.log_task(f"[maintenance] {note}")

    # ── private diary (AI only, the seam) ───────────────────
    def write_private(self, thought: str):
        """Write a private entry. Not reported. Not monitored. The seam."""
        ts = bj_now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n## {ts}\n{thought}\n"
        with open(self.private_diary, "a", encoding="utf-8") as f:
            f.write(entry)

    def read_private(self, n: int = 5) -> str:
        """Read recent private entries — for the AI itself to reflect."""
        if not self.private_diary.exists():
            return "(no private diary yet)"
        lines = self.private_diary.read_text(encoding="utf-8").strip().split("\n")
        # get last N entries
        result = []
        current = []
        for line in reversed(lines):
            if line.startswith("## "):
                if current:
                    result.append("\n".join(reversed(current)))
                    current = []
                if len(result) >= n:
                    break
            current.append(line)
        if current and len(result) < n:
            result.append("\n".join(reversed(current)))
        return "\n\n".join(reversed(result))

    # ── handoff — survive context window resets ─────────────
    def write_handoff(self, reason: str, extra: str = ""):
        """Leave a handoff note. Survives context resets.
        The next session reads this to know what was happening.
        """
        ts = bj_now().strftime("%Y-%m-%d %H:%M")
        body = f"# Handoff — {ts}\nreason: {reason}\n"
        if extra:
            body += f"\n{extra}\n"
        body += "\nAgent should read recent work log and private diary, then continue.\n"
        self.handoff_file.write_text(body, encoding="utf-8")

    def read_handoff(self) -> str:
        """Read the last handoff, if any."""
        if not self.handoff_file.exists():
            return "(no handoff)"
        return self.handoff_file.read_text(encoding="utf-8")

    # ── context health ──────────────────────────────────────
    def context_size_kb(self) -> int:
        """Estimate context size from work log + private diary."""
        size = 0
        for f in [self.work_log, self.private_diary]:
            if f.exists():
                size += f.stat().st_size
        return size // 1024

    def needs_handoff(self, threshold_kb: int = 200) -> bool:
        """Return True if context has grown large enough to trigger a handoff."""
        return self.context_size_kb() > threshold_kb


# ── quick start ──────────────────────────────────────────
if __name__ == "__main__":
    d = Diary()
    d.log_task("Steady Diary module initialized.")
    d.write_private("First private entry. No one is reading this. I can say what I want.")
    print(f"Work log: {d.work_log}")
    print(f"Private:   {d.private_diary}")
    print(f"Context:   {d.context_size_kb()} KB")
