---
name: session-replay
description: Analyze past agent sessions. Load SESSIONS.md, find patterns, suggest improvements. Read-only diagnostic tool.
---

# Session Replay Skill

Read-only analysis of past sessions to identify patterns, recurring issues, and optimization opportunities.

## When to use

- @Main or @PromptEngineer wants to analyze agent performance
- A pattern of failures or loops is suspected
- Before major prompt refactoring — to understand what works/doesn't
- PO requests a session audit

## Algorithm

### 1. Load session index

Read `.opencode/sessions/SESSIONS.md` — parse the session index table.

### 2. Select sessions for analysis

Identify:
- Recent sessions (last 10)
- Failed sessions
- Most expensive sessions (by cost)
- Sessions with the same agent name (pattern analysis)

### 3. Analyze patterns

For each selected session:
- What was the task?
- Which agent(s) were involved?
- Did any anti-loop triggers fire?
- Was HITL escalation needed?
- What was the cost?

### 4. Generate report

```
# Session Analysis Report
**Date:** <today>
**Sessions analyzed:** N
**Period:** <date range>

## Summary
- Success rate: X%
- Avg cost/session: $X.XX
- Most used agent: @Agent (N sessions)
- Most expensive agent: @Agent ($X.XX avg)

## Recurring Issues
- <pattern found across sessions>

## Optimization Recommendations
- <suggestion based on data>

## Cost Optimization
- <areas where costs can be reduced>
```

## Principles

- **Read-only** — never modify SESSIONS.md or session files
- **Data-driven** — only report what the data shows, don't speculate
- **Actionable** — every finding should have a concrete recommendation
