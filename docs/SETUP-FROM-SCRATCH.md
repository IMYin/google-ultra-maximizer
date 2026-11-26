# Zero-to-Production Setup Guide (macOS & Linux)

This guide walks any new user from a fresh `git clone` to a fully running **Google AI Ultra Maximizer** setup with `T3 Code` mobile control, live **Antigravity Dual-Bucket Quotas**, **Agent Desktop**, **Flow / Colab** probes, and accurate **`$10 / $40 / $50 / $100` Cloud Credit calibration**.

---

## 1. Prerequisites

- **OS**: macOS 13+ (Apple Silicon / Intel) or Linux (systemd user session).
- **Python**: `>= 3.11` (standard library only for core!).
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
Installs `ultra`/`fleet` CLI + `pingdotgg/t3code` + `Aoike123/agy-lens` + `vercel-labs/agent-desktop` + `antigravity-usage` + `caronc/apprise` + Matt Pocock engineering skills:
```bash
# If you use an outbound proxy (e.g. Clash/Shadowrocket), export it first:
# export HTTP_PROXY=http://127.0.0.1:1082 HTTPS_PROXY=http://127.0.0.1:1082 NO_PROXY=127.0.0.1,localhost

./scripts/bootstrap.sh --all --start-service
```

> **Using an External SSD on macOS?**
> Set `export FLEET_WORKSPACE_ROOT=/Volumes/YourSSD` before running `./scripts/bootstrap.sh`. Keep heavy `t3code-home`, `worktrees`, and `npm-global` directories on your external disk while logs stay safely in `~/.config/`.

---

## 3. Auto-Sync Google Cloud Credits (API + VPS + Cloud Spend)

Google Cloud Billing CLI does not expose promotional Developer Program credit balances without BigQuery export. `ultra` solves this cleanly with a headless **GCP Billing Credits Probe**:

1. Click **🔄 Auto-Sync GCP Credits** directly on the **Google Cloud / Gemini 赠金池** card in `http://127.0.0.1:7788` (or run `ultra sync-gcp-credits`).
   - If your browser profile is not signed into Google Cloud Console yet, run **`ultra gcp-login`** once to sign in.
2. `ultra` automatically reads all `Available` credit grants (filtering out `Expired` welcome credits), sums remaining vs original USD (automatically capturing VPS/GCE/Cloud Run/API deductions!), finds the earliest-expiring tranche, and renders a collapsible breakdown inside the card.
3. Prefer manual calibration instead? Click **✏️ Calibrate** to choose presets (`Pro $10`, `Ultra $50`, `Ultra 20x $100`) or enter your remaining USD offset manually.

---

## 4. Connect Your Phone with T3 Code (`pingdotgg/t3code`)

1. Start/configure remote relay:
   ```bash
   t3 up --connect --lan
   ```
   *(On macOS with `T3CODE_HOME` on an external SSD, if `launchd` hits `EX_CONFIG 78`, run **`ultra fix-t3-service`** once!)*
2. Enable **Antigravity** on the T3 server (`~/.t3/userdata/settings.json` or `$T3CODE_HOME/userdata/settings.json`):
   ```json
   {
     "providerInstances": {
       "antigravity": {
         "driver": "antigravity",
         "enabled": true,
         "config": {
           "enabled": true,
           "authMethod": "oauth-personal",
           "binaryPath": "agy"
         }
       }
     }
   }
   ```
   Then restart T3 (`t3 service restart` or `ultra fix-t3-service` on external SSD macOS).
3. On your iPhone / Android **T3 Code** app (or `https://app.t3.codes`):
   - Sign in using the **exact same Google login** (not Apple Hide-My-Email).
   - Tap **Settings → Environments → `+` (top-right)** to connect to your host via **T3 Connect** (or scan the LAN QR code at `http://<YOUR_LAN_IP>:3773/pair`).
   - On your Mac browser, T3 pairing tokens are **single-use per browser**: run **`ultra t3-pair`** (or click **`🔑 Auto-Pair ↗`** on the T3 Code card in `http://127.0.0.1:7788`) whenever opening T3 Code in a fresh browser profile.

---

## 5. [Optional] Add Unattended Bot Sentinels with OpenMausBot (`milind-soni/OpenMausBot`)

Because **T3 Code (`:3773`)** already covers mobile coding, live diffs, Mac GUI control, and tool approvals, **most solo developers do not need OpenMausBot running**. Enable this optional add-on only if you want unattended scheduled routines or a 24/7 containerized BYO Linux VPS:

1. Install & launch OpenMausBot (on macOS, `OpenMausBot.app` owns `This computer` & iPhone QR pairing):
   ```bash
   ultra maus install
   ```
2. Sign your local CLI into the desktop app once (click **Allow** on the card inside OpenMausBot):
   ```bash
   NO_PROXY=127.0.0.1,localhost openmausbot login http://127.0.0.1:8799
   ```
3. Inject the lean **2-bot sentinel team** (`Ultra Chief` + `VPS Cloud Scout` in `#ultra-command`, pinned to `antigravity/claude-sonnet-5-5` so it uses `$0` GCP credits):
   ```bash
   ultra maus apply-team
   ```
4. Under **Settings → AI → Providers → Google Gemini (Antigravity)**, sign in with your Google AI Ultra account. To attach a GCP-funded Linux VPS, configure an SSH alias (`ssh my-vps true && docker -H ssh://my-vps info`) and enter it under **Settings → AI → Other services → Self-hosted VPS**.

---

## 6. Unlock Desktop GUI & Chrome Deep Research (`vercel-labs/agent-desktop`)

On macOS, Accessibility (`AX`) permissions are evaluated per **launching host app**:
1. Run `agent-desktop permissions --guide` inside the **Terminal** or **IDE** (e.g., Antigravity / VS Code / Cursor) where your agents run.
2. In **System Settings → Privacy & Security → Accessibility**, toggle ON both your launching app **and** the `agent-desktop` binary (plus `t3` if background T3 agents also control desktop apps).
3. Verify from that same terminal/IDE:
   ```bash
   agent-desktop status
   agent-desktop snapshot --surface dock -i --compact
   ```
   Once granted, both **T3 Code** and optional OpenMausBot bots can automate signed-in desktop Chrome (`gemini-web-research`) for Gemini Deep Research and zero-cost AI Studio web audits.

---

## 7. Wire Google Colab & Google Flow Quotas

- **Colab (`2,000 CU/mo`)**: Install and sign into `google-colab-cli` (`colab auth login`). `ultra` reads live CU balance and alerts immediately (`🟠`) if any L4 GPU instance is left billing.
- **Google Flow (`gflow-cli`)**:
  ```bash
  uv tool install gflow-cli --with socksio --with h2
  gflow auth login
  ```
  `ultra` uses `fleet_hub/gflow_wire_probe.py` to cache session cookies headlessly (`--password-store=basic`) and query credits over pure HTTPS (`nzlxg`), so refreshing the dashboard **never opens annoying browser windows**.

---

## 8. Daily Operating Rhythm to Maximize Ultra Value

1. **Morning 5h Warmup**: Run `ultra wakeup` (or schedule a `08:00` cron) so your **5-hour Claude Opus 5.5 / Sonnet 5.5** clock starts early (`08:00`, `13:00`, `18:00` = 3 full cycles/day).
2. **Work Primarily in T3 Code + `:7788` Cockpit**: Check `http://127.0.0.1:7788` or `ultra status`:
   - Route coding/review threads in **T3 Code** onto **Claude 5.5** whenever its 5h pool is `100%` and Gemini weekly `< 40%`.
   - Drain expiring **Flow credits** and **Colab CU** during the last week of each month.
   - Run **Batch API** (50% discount) around the 24th if Paid API / GCP credits remain unused.
