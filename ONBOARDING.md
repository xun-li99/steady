# Wrap your agent in 5 minutes

Steady is a daemon that keeps your AI agent alive. When it crashes, Steady restarts it and hands back everything it remembers. You don't need to rewrite your agent. You don't need to hand it over to us. You run it yourself.

---

## 1. Install

```bash
pip install steady-agent
steady init
```

## 2. Tell your agent how to read a handoff

Steady injects a `STEADY_CONTEXT` environment variable on every restart. It contains the handoff from the previous session — what was done, what's left.

Your agent just needs to read it:

```python
import os
ctx = os.environ.get("STEADY_CONTEXT", "")
# ctx is "" on first launch.
# On restart after crash, ctx contains the handoff.
# Use it to resume where you left off.
```

That's it. The rest is Steady's job.

## 3. Start your agent under Steady

```bash
steady task "monitor my API endpoints every 5 minutes and alert on failure"
steady start python my_agent.py
```

Your agent runs normally. If it crashes — OOM, network timeout, rate limit, whatever — Steady restarts it with the handoff.

## 4. Check how it's doing

```bash
steady status          # quick check
curl localhost:8100/health   # full heartbeat with uptime and restart count
```

## 5. Run it for 24 hours. See what happens.

No config files. No YAML. No platform account. Just `pip install`, `steady init`, `steady start`.

---

## What you'll see

After a day of running, the `/health` endpoint will show:

- Total restarts and when they happened
- Whether context was preserved across each restart
- Uptime since the daemon started

We've been running Steady on a $5 VPS managing a crash-prone agent for 20+ hours. 245 restarts. Zero human intervention. 100% context preserved.

---

## If something breaks

[GitHub Issues](https://github.com/xun-li99/steady/issues). Real humans, real responses.
