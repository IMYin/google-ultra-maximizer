# Google AI Ultra Maximizer

Domain vocabulary for orchestrating independent Google AI Ultra compute quotas, asynchronous approval gates, and open-source developer tools without reinventing wheels.

## Language

**Quota Pool**:
An independent subscription budget or rate-limit bucket included in Google AI Ultra (`agy_gemini_weekly`, `agy_claude_5h`, `colab_cu`, `flow_credits`, `gdrive_bus`, `ai_studio_daily`, `paid_gemini_api`), each with its own reset clock and **Probe**.
_Avoid_: Account, credit card, bucket

**Probe**:
A read-only telemetry adapter that inspects a live **Quota Pool** or integrated **Wheel** via local loopback RPC, CLI stdout, or cached wire state without burning LLM tokens.
_Avoid_: Scraper, poller, mock check

**Burn Advisor**:
The deterministic recommendation engine that compares remaining percentages and reset clocks across all **Quota Pools** to surface idle rolling capacity and month-end expiry targets.
_Avoid_: Scheduler, planner, heuristic

**Wheel**:
An off-the-shelf open-source project composed into the architecture (`T3 Code`, `Agy Lens`, `Agent Desktop`, `Apprise`, `gflow-cli`, `google-colab-cli`, and optional `OpenMausBot`) instead of maintaining custom glue code.
_Avoid_: Plugin, dependency, integration

**Approval Ticket**:
A unit of proposed repository work queued from `INBOX.md` or an isolated Git **Worktree** delivery that pauses in the **Yellow Zone** until a human approves or requests revision.
_Avoid_: Task, job, PR

**Worktree**:
An isolated Git checkout directory created under `<workspace>/worktrees/` on a protected `bot/*` branch so parallel agents never corrupt `main`.
_Avoid_: Workspace, folder, sandbox

**Yellow Zone**:
Work that runs tests and builds freely inside an isolated **Worktree** but cannot touch `main` or remotes without explicit human confirmation in **T3 Code** or the Cockpit.
_Avoid_: Staging, draft

**Red Zone**:
Destructive or irreversible actions (production migrations, `git push` from `bot/*`, paid/external publishes, CI triggers) blocked by deterministic hooks and triage rules.
_Avoid_: Danger zone, restricted action
