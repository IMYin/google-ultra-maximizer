---
botmrr: 1
id: ultra-solo-studio
release: 1.1.0
name: Ultra Solo Studio (Optional Sentinel Add-On)
tagline: Lean 2-bot sentinel add-on (Ultra Chief + VPS Cloud Scout) for users pairing unattended routines or a BYO Linux VPS alongside T3 Code.
summary: Optional 2-bot sentinel pack (Ultra Chief & VPS Cloud Scout, 1 #ultra-command room) complementing T3 Code (:3773) and Fleet-Hub (:7788) without duplicating IDEs or wasting quotas.
category: Engineering & Operations
author:
  name: Google AI Ultra Maximizer Contributors
license: MIT
outcomes:
  - Keep bots off scarce Gemini Weekly and Paid GCP Credits unless requested (default to Antigravity Claude 5.5 5h rolling quota).
  - Run unattended background sentinels, async Deep Research (`gemini-web-research`), and optional Self-hosted BYO Linux VPS tasks cleanly.
  - Defer heavy coding, diffs, and interactive mobile reviews to T3 Code (:3773).
setupMinutes: 3
requirements:
  apps: []
  capabilities:
    - Local CLI `ultra` (from Google AI Ultra Maximizer / Fleet-Hub)
    - At least one signed-in engine (Google Gemini Antigravity CLI or Claude)
agents:
  - key: ultra-chief
    name: Ultra Chief
    title: Lightweight Quota & Inbox Sentinel
    description: Watches live Ultra pools & project inboxes quietly; dispatches async research only when asked.
    appearance:
      color: blue
      mascotBody: ghost
  - key: vps-cloud-scout
    name: VPS Cloud Scout
    title: 24/7 Cloud VPS & Web Research Operator
    description: Pairs with a GCP-funded Self-hosted BYO Linux VPS or Chrome AX Deep Research.
    appearance:
      color: cyan
---

# Ultra Solo Studio (Optional Sentinel Add-On)

> **T3 Code (`:3773`) + Fleet-Hub (`:7788`) already cover daily coding, diffs, approvals, and quota governance.** Install this optional OpenMausBot team pack only if you want persistent background routines or a 24/7 BYO Linux VPS operator (`ultra maus apply-team`).

## Activation

1. Ensure `Google AI Ultra Maximizer` (`ultra`) is installed and `http://127.0.0.1:7788` is reachable.
2. Open OpenMausBot **Settings → AI → Providers**, sign in to **Google Gemini (Antigravity)**.
3. Run `ultra maus apply-team` (uses `--prune` to keep only the 2 lean sentinel bots + `#ultra-command` room).

## Outcomes

- Default every bot onto **Antigravity Claude 5.5 (5h rolling pool)** (`$0` GCP credits consumed).
- Keep background monitoring silent unless action is needed; send heavy code work to **T3 Code** (`:3773`).
- Gate external actions and GCP credit spend behind inline 👍/Allow Approval Cards.

## Connections

- Optional: Connect a Self-hosted Linux VPS under **Settings → AI → Other services → Self-hosted VPS** using your `~/.ssh/config` alias.

## Team

- **Ultra Chief**: Watches pool headroom via `curl http://127.0.0.1:7788/api/state`, runs quiet sentinels & background research.
- **VPS Cloud Scout**: Sandboxed Chrome AX research (`gemini-web-research`) / Self-hosted BYO Linux VPS operator.

## Completion rule

A task is complete only after verification passes, temporary Colab GPU sessions are stopped, and external publishes or repository merges have explicit user approval.
