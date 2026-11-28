# Security Policy

## Local-Only Threat Model

- The Web Cockpit binds strictly to loopback **`127.0.0.1`** and must never be exposed directly to `0.0.0.0` or the public internet. For remote access across personal devices, use Tailscale or an SSH tunnel to `127.0.0.1:7788`.
- All state-mutating `POST` routes (`/api/approve`, `/api/revise`, `/api/refresh-telemetry`, `/api/settings`, `/api/notify-test`, `/api/sync-gcp-credits`, `/api/wakeup`, `/api/github-star`, `/api/github-star-dismiss`) enforce persistent CSRF token verification and same-origin `Origin` checks.
- Credentials live strictly outside the repository in `~/.config/ultra-maximizer/secrets.env` (or `~/.config/fleet-hub/secrets.env`) with `0600` permissions. The Web UI never echoes stored secrets back into rendered HTML.
- Headless browser cookies (`gflow_cookies.json`) are stored locally under `~/.config/fleet-hub/` with `0600` permissions and are ignored by Git.

## Reporting a Vulnerability

Please do **not** open a public GitHub issue containing tokens, cookies, or personal logs. Redact sensitive strings (`ultra status --privacy`) and report security issues privately to the repository maintainer.
