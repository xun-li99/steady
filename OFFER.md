# Steady Guarded Runtime

> **Your AI agent crashes. We make it stop.**
>
> A managed reliability layer for teams running AI agents in production.
> One agent. One monthly fee. Weekly proof it's dying less.

---

## Who this is for

You're a small team (3–10 people). You deployed an AI agent to production. It crashes at 3 AM. You wake up. You restart it manually. You hope it remembers what it was doing.

You've tried: bash scripts, cron jobs, LangSmith traces. None of them catch the agent when it falls.

---

## What you get

**30 days of guarded runtime.** We wrap your agent in Steady — an open-source daemon that detects crashes, restarts the process, and injects context so it resumes where it left off.

**Weekly reports** showing:
- How many times it crashed
- How fast it recovered
- How many manual restarts you avoided
- Whether crash intervals are getting longer (the agent is stabilizing)

**Monthly review call.** 20 minutes. We go over the numbers together, tune the handoff strategy, adjust the recovery policy.

**Not included:** rewriting your agent. Not needed. Steady wraps around it.

---

## Pricing

| Tier | Price | Agents | Reports | Support |
|---|---|---|---|---|
| **Starter** | $399/month | 1 agent | Weekly | Email |
| **Team** | $799/month | Up to 3 agents | Weekly | Email + Slack |
| **Scale** | $1,599/month | Up to 10 agents | Weekly + daily summary | Dedicated channel |

Pilot: first 14 days free. Cancel anytime.

---

## What this isn't

- Not another observability dashboard you have to watch
- Not a platform that locks you in
- Not a framework you have to rewrite your agent for

It's a daemon. It catches your agent when it falls. You sleep.

---

## How to start

Email `steady@xun-li.dev` with:
- What your agent does (one sentence)
- What stack it runs on (LangChain, CrewAI, custom, etc.)
- How often it crashes (rough estimate)

We'll reply within 24 hours to set up the pilot.

---

*Steady is MIT-licensed open source. You can run it yourself for free. This is the managed version for teams who'd rather not.*
