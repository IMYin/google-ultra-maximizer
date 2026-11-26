---
name: gemini-web-research
description: Automate high-leverage Google Gemini Web Deep Research (gemini.google.com) and Google AI Studio Web long-context/media audits (aistudio.google.com) through a signed-in desktop Chrome window using agent-desktop AX trees without manual copy-paste.
---

# Gemini Web & AI Studio Automation (`agent-desktop`)

Operate `https://gemini.google.com/app` (**Deep Research / Canvas**) and `https://aistudio.google.com/prompts/new_chat` (**Daily Free Long-Context / Video Workbench**) inside the owner's already signed-in desktop Chrome browser using `agent-desktop` Accessibility (`AX`) trees.

## 1. Choose Direct API vs Web UI First

- **Prefer Direct API / CLI (`GEMINI_API_KEY`, Antigravity ACP, Codex) for standard tasks**: structured JSON extraction, coding, classification, or fast Q&A. API calls are 10x faster and immune to DOM changes.
- **Use Web UI automation ONLY for high-leverage web-exclusive / $0 pools**:
  1. **Gemini Web Deep Research (`gemini.google.com/app`)**: multi-minute autonomous web research synthesizing dozens of sources into a cited report.
  2. **AI Studio Web Workbench (`aistudio.google.com/prompts/new_chat`)**: daily Pacific-midnight reset `$0` pool for 500K–2M token spec bundles, large PDFs, or multimodal video frame reviews without spending GCP credits or Antigravity weekly quota.

## 2. Standard Execution SOP (`agent-desktop`)

Never launch a fresh Playwright/Selenium browser to log in to Google—that triggers security warnings and bot checks. Always drive the user's already-signed-in desktop Chrome session:

1. **Preflight & Window Check**:
   ```bash
   agent-desktop status
   agent-desktop list-windows --app "Google Chrome"
   ```
   - Confirm `permissions.accessibility.state == "granted"`.
   - Ensure Chrome has an active desktop window (not minimized to Dock, which can pause web AX exposure). If needed, open the target page cleanly:
     ```bash
     open -a "Google Chrome" "https://gemini.google.com/app"
     ```
2. **Map the UI via Accessibility Refs**:
   ```bash
   agent-desktop snapshot --skeleton --app "Google Chrome" -i --compact
   agent-desktop snapshot --root @<main_or_composer_ref> -i --compact
   ```
   - Locate the prompt textbox, mode/model selector (e.g., **Deep Research** for `gemini.google.com`, or **Gemini Pro / Flash** for `aistudio.google.com`), and the **Send / Run** button.
   - For AI Studio long-context reviews, paste or attach the file from the requested workspace path before clicking **Run**.
3. **Dispatch & Poll Patiently (Zero Fixed Sleeps for Short Steps)**:
   - After triggering **Deep Research**, poll status every **45–60 seconds** (up to 15 minutes) with `agent-desktop snapshot --root @<root_ref> -i --compact` until generation completes and the **Copy** / **Export to Docs** action becomes active.
   - Copy or extract the complete Markdown report, write it to the project specs folder (e.g., `<AI-Projects>/<project>/specs/YYYY-MM-DD-<slug>.md` or the path the user specified), and reply with a concise summary + clickable saved file path.

## 3. Strict Safety & Anti-Abuse Red Lines

- **Low-frequency heavy jobs only**: use for legitimate Deep Research reports or large long-context audits. Never use web UI automation as a high-frequency polling proxy or batch scraper against Google web properties.
- **Zero CAPTCHA / Verification Bypass**: if Google presents any CAPTCHA, "verify you are human" challenge, 2FA prompt, or login wall, **STOP immediately** and notify the user so they can complete verification directly in Chrome. Never attempt to compute, click through, or bypass anti-bot checks.
