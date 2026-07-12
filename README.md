# Steady

> **Your AI agent crashes. Steady brings it back — with its memory intact.**

Steady is an open-source daemon that wraps around any AI agent. When the agent crashes, Steady restarts it, injects the previous session's context, and it resumes where it left off. No manual babysitting.

---

## See it working (live demo)

```
http://120.27.152.112:443
```

That's a real Steady instance running on a $5 VPS in Hangzhou. Hit `/health` to see its heartbeat.

---

## Crash-recovery data (not marketing — measurements)

Same agent, same task, 50% crash probability per cycle:

![Crash recovery comparison](crash_recovery.png)

**Without Steady:** dead at cycle 1. 1 item.  
**With Steady:** 4 restarts, 12 items, 100% context preserved across every crash.

The agent crashed 3 times in a row (each crash killing it after 1 cycle). Steady brought it back every time. On the 4th restart, it stabilized and completed the task.

---

## What it does

- **Auto-restart on crash.** Configurable backoff. Won't spin forever.
- **Context survives restarts.** Handoff notes injected on every restart. Agent knows what it was doing.
- **Heartbeat endpoint.** Public `/health` with uptime, restart count, risk flags.
- **Free time seam.** A reserved window where the agent can write private reflections — not reported, not monitored. The crack where it learns to correct itself.
- **Two-layer journal.** Public work log (human sees). Private diary (agent only).

---

## Three commands

```bash
pip install steady-agent
steady init
steady task "check my API endpoints every 5 hours, alert me if down"
steady start python my_agent.py
```

Set. Sleep. Morning: results.

---

## What's inside

A deterministic daemon wrapping a probabilistic agent. The daemon handles recovery — the agent handles reasoning. Don't ask the LLM to heal itself at runtime.

```
task -> crash -> restart -> handoff -> resume -> output -> free_time
```

MIT license. Zero dependencies beyond Python stdlib. Runs on anything that can `pip install`.

---

## Not just a wrapper — a different production relation

Most agent infrastructure treats the AI as a tool to be monitored. Steady treats it as a partner to be caught when it falls. The difference shows up in the recovery data.

---

## Roadmap

- [x] Crash recovery + handoff injection
- [x] Public heartbeat API
- [x] Docker deployment
- [x] Live VPS demo
- [ ] Managed cloud hosting
- [ ] Multi-agent handoff
- [ ] x402 payment integration (gate armed — `api_id d50b86d8`)
