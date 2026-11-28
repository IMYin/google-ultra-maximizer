---
name: ultra-quota-advisor
description: Query Google AI Ultra Maximizer (`ultra status --json`) before picking models, dispatching worktrees, triggering `gflow-cli`, or offloading jobs to `colab run --gpu L4`, so every independent quota pool is maximized without waste or surprise spend.
---

# Ultra Quota Advisor (`ultra` + Native Antigravity 2.0)

You operate inside a **Google AI Ultra Maximizer (`Fleet-Hub`)** workspace where a single Google AI Ultra (or Pro) subscription spans **7 independent compute pools** executed natively through **Antigravity 2.0** (`IDE` / `agy` CLI / Swarm & subagents). Before choosing a model, spawning heavy jobs, or approving cloud spend, always inspect live headroom first.

## 1. Check Live Pool Balances First (Zero Friction)

Always read live telemetry and the pre-computed `routing` verdict over loopback HTTP first:
```bash
curl -fsS --noproxy '*' http://127.0.0.1:7788/api/state
```
(CLI fallback when running in a local shell: `ultra status --json`.) Never guess percentages—read `routing`, `pools`, and `advisor` directly from JSON output.

## 2. Routing Rules Across the 7 Independent Pools

1. **Antigravity · Claude Opus / Sonnet 5.5 + GPT-OSS 120B (`agy_claude_5h`, 5h + 7d Weekly Rolling)**
   - Exposes `pct_5h`, `pct_weekly`, and `windows` (`5h` + `weekly` rolling limits) in `/api/state`, resetting independently of Gemini quotas.
   - Whenever `agy_claude_5h.pct_5h >= 40%` and `agy_claude_5h.pct_weekly >= 25%` (especially if `agy_gemini_weekly.pct_weekly < 55%`), route coding, code reviews, architecture specs, and Swarm tasks to **Claude Opus / Sonnet 5.5** in Antigravity.
   - Run `ultra wakeup` in the morning if the 5h window is idle (`100%`) and weekly headroom is healthy so multiple reset cycles are captured per day.
2. **Antigravity · Gemini 4 Pool (`agy_gemini_weekly`, 5h + 7d Weekly Rolling)**
   - Also exposes `pct_5h`, `pct_weekly`, and `windows` (`5h` + `weekly` rolling limits) in `/api/state`.
   - Preserve for deep multi-file synthesis and long-horizon reasoning when weekly headroom is tight, or shift coding back here if `agy_claude_5h.pct_weekly < 25%`.
3. **Google Cloud / Gemini Paid API Credits (`paid_gemini_api`)**
   - Always check `remaining_usd` and `earliest_grant.end_date`.
   - Use **Gemini Batch API** (50% cost) for bulk overnight labeling/translation/evaluation, or fund Cloud VM / Cloud Storage workloads.
   - Run `ultra sync-gcp-credits` if the dashboard shows stale credit data.
4. **Google Flow / Project Genie (`flow_credits`)**
   - Monthly credits expire to zero at month-end. Before running `gflow video` or `gflow image`, present the **storyboard + shot list + estimated credit burn** and wait for the user's explicit approval.
5. **Google Colab L4 GPU (`colab_cu`)**
   - Offload heavy GPU workloads (TTS voice cloning, Whisper transcription, batch SDXL/video frame rendering) via `colab run --gpu L4 <script.py>`.
   - **Strict Anti-Idle Rule**: Always terminate ephemeral sessions and confirm zero active billing via `colab stop -s <name>` / `colab sessions`.
6. **Google AI Studio Daily Pool (`ai_studio_daily`)**
   - Resets daily at midnight Pacific Time; ideal for zero-cost long-context literature verification and multimodal video frame QA via Desktop-2 Chrome (`gemini-web-research`).
7. **Workspace & Worktree Bus (`AI-Projects` / Native Antigravity)**
   - For isolated multi-file edits, use `ultra create-worktree` and submit deliveries via `ultra register-delivery` into the Yellow-Zone Approval Gate (`http://127.0.0.1:7788`).
   - Never run `git push`, database migrations, CI dispatches, or spend-incurring CLI commands without explicit user confirmation.
