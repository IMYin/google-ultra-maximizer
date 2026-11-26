---
name: ultra-quota-advisor
description: Query Google AI Ultra Maximizer (`ultra status --json`) before picking models, dispatching worktrees, triggering `gflow-cli`, or offloading jobs to `colab run --gpu L4`, so every independent quota pool is maximized without waste or surprise spend.
---

# Ultra Quota Advisor (`ultra` + `OpenMausBot` + `T3 Code`)

You operate inside a **Google AI Ultra Maximizer (`Fleet-Hub`)** workspace where a single Google AI Ultra (or Pro) subscription spans **7 independent compute pools**. Before choosing a model, spawning heavy jobs, or approving cloud spend, always inspect live headroom first.

## 1. Check Live Pool Balances First (Zero Friction, Works in Any Surface)

Always read live telemetry and the pre-computed `routing` verdict over loopback HTTP first—this works regardless of whether `Works on` is set to `Auto`, `Browser`, `Off`, `Cloud`, or `This computer`, without needing host-computer permission:
```bash
curl -fsS --noproxy '*' http://127.0.0.1:7788/api/state
```
(Optional CLI fallback when running in a local shell: `ultra status --json`, or rebalance idle OpenMausBot bots automatically via `ultra rebalance`.) Never guess percentages—read `routing`, `pools`, and `advisor` directly from JSON output.

## 2. Routing Rules Across the 7 Independent Pools

1. **Antigravity · Claude Opus / Sonnet 5.5 + GPT-OSS 120B (5-Hour Rolling Pool)**
   - Resets every **5 hours** independently of Gemini weekly quotas.
   - Whenever `agy_claude_5h.pct >= 40%` (especially if `agy_gemini_weekly.pct < 55%`), route coding, code reviews, architecture specs, and Chief-of-Staff orchestration to **Claude Opus / Sonnet 5.5**.
   - Run `ultra wakeup` in the morning if the 5h window is idle (`100%`) so multiple reset cycles are captured per day, or run `ultra rebalance` to switch all idle Antigravity bots off Gemini Weekly onto the 5h pool.
2. **Antigravity · Gemini Weekly Pool (`agy_gemini_weekly`)**
   - Preserve for deep multi-file synthesis and long-horizon reasoning when weekly headroom is tight.
3. **Google Cloud / Gemini Paid API Credits (`paid_gemini_api`)**
   - Always check `remaining_usd` and `earliest_grant.end_date`.
   - Use **Gemini Batch API** (50% cost) for bulk overnight labeling/translation/evaluation, or fund an **x86_64 Linux BYO VPS** (`OpenMausBot → Settings → Self-hosted VPS`) for 24/7 browser/research bots.
   - Run `ultra sync-gcp-credits` if the dashboard shows stale credit data.
4. **Google Flow / Project Genie (`flow_credits`)**
   - Monthly credits expire to zero at month-end. Before running `gflow video` or `gflow image`, present the **storyboard + shot list + estimated credit burn** and wait for the user's explicit inline **Allow / 👍** approval.
5. **Google Colab L4 GPU (`colab_cu`)**
   - Offload heavy GPU workloads (TTS voice cloning, Whisper transcription, batch SDXL/video frame rendering) via `colab run --gpu L4 <script.py>`.
   - **Strict Anti-Idle Rule**: Always terminate ephemeral sessions and confirm zero active billing via `colab stop -s <name>` / `colab sessions`.
6. **Google AI Studio Daily Pool (`ai_studio`)**
   - Resets daily at midnight Pacific Time; ideal for zero-cost long-context literature verification and multimodal video frame QA.
7. **Workspace & Worktree Bus (`AI-Projects` / `T3 Code`)**
   - For heavy repo surgery with multi-file Git diffs, suggest handing the branch/worktree to **T3 Code** (`:3773`) or using `ultra create-worktree`.
   - Never run `git push`, database migrations, CI dispatches, or spend-incurring CLI commands without an explicit inline Approval Card from the user.
