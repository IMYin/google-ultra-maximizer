# Zero-to-Production Setup Guide (macOS & Linux)

This guide walks any new user from a fresh `git clone` to a fully running **Google AI Ultra Maximizer** setup powered by **native Antigravity 2.0**, **Agy Lens**, **Agent Desktop**, **Flow / Colab** probes, and accurate **`$10 / $40 / $50 / $100` Cloud Credit calibration**.

---

## 1. Prerequisites

- **OS**: macOS 13+ (Apple Silicon / Intel) or Linux (systemd user session).
- **Python**: `>= 3.11` (standard library only for core!).
- **IDE / Agent Runtime**: **Antigravity 2.0** (`Antigravity.app` / `agy` CLI) signed in with your Google AI Ultra (or Pro) account.
- **Optional (for full wheel stack)**: `git`, `node >= 18` + `npm`, `uv` (or `pip`).

---

## 2. Clone & Bootstrap

```bash
git clone https://github.com/IMYin/google-ultra-maximizer.git
cd google-ultra-maximizer
```

### Minimal Install (Core Cockpit + Burn Advisor + CLI)
```bash
./scripts/bootstrap.sh --minimal --start-service
```

### Full Stack Install (Recommended)
Installs `ultra`/`fleet` CLI + `Aoike123/agy-lens` + `vercel-labs/agent-desktop` + `antigravity-usage` + `caronc/apprise` + Matt Pocock & Antigravity skills:
```bash
# If you use an outbound proxy (e.g. Clash/Shadowrocket), export it first:
# export HTTP_PROXY=http://127.0.0.1:1082 HTTPS_PROXY=http://127.0.0.1:1082 NO_PROXY=127.0.0.1,localhost

./scripts/bootstrap.sh --all --start-service
```

> **Using an External SSD on macOS?**
> Set `export FLEET_WORKSPACE_ROOT=/Volumes/YourSSD` before running `./scripts/bootstrap.sh`. Keep heavy `worktrees` and `npm-global` directories on your external disk while logs stay safely in `~/.config/`.

---

## 3. Auto-Sync Google Cloud Credits (API + Cloud Spend)

Google Cloud Billing CLI does not expose promotional Developer Program credit balances without BigQuery export. `ultra` solves this cleanly with a headless **GCP Billing Credits Probe**:

1. Click **Sync GCP Credits** directly on the **Google Cloud / Gemini Credits** card in `http://127.0.0.1:7788` (or run `ultra sync-gcp-credits`).
   - If your browser profile is not signed into Google Cloud Console yet, run **`ultra gcp-login`** once to sign in.
2. `ultra` automatically reads all `Available` credit grants (filtering out `Expired` welcome credits), sums remaining vs original USD (automatically capturing Cloud VM / Storage / API deductions!), finds the earliest-expiring tranche, and renders a collapsible breakdown inside the cockpit.
3. Prefer manual calibration instead? Open **Calibrate** (`S`) in the topbar to choose presets (`Pro $10`, `Ultra $50`, `Ultra 20x $100`) or enter your remaining USD offset manually.

---

## 4. Connect Native Antigravity 2.0 & Agy Lens

1. Open **Antigravity 2.0** (or run `agy`) and sign in with your Google AI Ultra account.
2. Fleet-Hub automatically discovers `~/.gemini/antigravity/daemon/hub_*.json` and queries both `GetUserStatus` and `RetrieveUserQuotaSummary` over loopback RPC—splitting **Gemini 4 (5h + 7d Weekly)** and **Claude 5.5 / GPT-OSS (5h + 7d Weekly)** into live concentric gauges.
3. `agy-lens` mounts into `~/.gemini/config/plugins/agy-lens`, feeding 7-day API-equivalent ROI directly into the `:7788` cockpit.

---

## 5. Unlock Desktop GUI & Chrome Deep Research (`vercel-labs/agent-desktop`)

On macOS, Accessibility (`AX`) permissions are evaluated per **launching host app**:
1. Run `agent-desktop permissions --guide` inside the **Terminal** or **Antigravity** IDE where your agents run.
2. In **System Settings → Privacy & Security → Accessibility**, toggle ON both your launching app **and** the `agent-desktop` binary.
3. Verify from that same terminal/IDE:
   ```bash
   agent-desktop status
   agent-desktop snapshot --surface dock -i --compact
   ```
   Once granted, native Antigravity agents can automate signed-in desktop Chrome (`gemini-web-research`) for Gemini Deep Research and zero-cost AI Studio web audits.

---

## 6. Wire Google Colab & Google Flow Quotas

- **Colab (`2,000 CU/mo`)**: Install and sign into `google-colab-cli` (`colab auth login`). `ultra` reads live CU balance and alerts immediately if any L4 GPU instance is left billing.
- **Google Flow (`gflow-cli`)**:
  ```bash
  uv tool install gflow-cli --with socksio --with h2
  gflow auth login
  ```
  `ultra` uses `fleet_hub/gflow_wire_probe.py` to cache session cookies headlessly (`--password-store=basic`) and query credits over pure HTTPS (`nzlxg`), so refreshing the dashboard **never opens annoying browser windows**.

---

## 7. Daily Operating Rhythm to Maximize Ultra Value

1. **Morning 5h Warmup**: Run `ultra wakeup` (or click **Wakeup 5h** on the Routing plate) so your **5-hour Claude Opus 5.5 / Sonnet 5.5** clock starts early (`08:00`, `13:00`, `18:00` = 3 full cycles/day).
2. **Work Natively in Antigravity 2.0 + `:7788` Cockpit**: Check `http://127.0.0.1:7788` or `ultra status`:
   - Route coding/review threads in **Antigravity** onto **Claude 5.5** whenever its 5h pool is `100%` and Gemini weekly `< 40%`.
   - Drain expiring **Flow credits** and **Colab CU** during the last week of each month.
   - Run **Batch API** (50% discount) around the 24th if Paid API / GCP credits remain unused.
