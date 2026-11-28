"""Spatial Observatory Telemetry & Governance Cockpit UI (zero external deps, dual-theme, bilingual ZH/EN)."""

from __future__ import annotations

import html
import json
import re
from typing import Any

from . import __version__
from .config import RuntimeSecrets, redact_path

GITHUB_REPO_URL = "https://github.com/IMYin/google-ultra-maximizer"

_LEADING_EMOJI_RE = re.compile(r"^[\s🟢🟡🟠🔵⚪⚡🔄📋⚙️✅🤖📱🔥📊🧩🗂️🔗🕶️🔓🌐✏️🔑⚖️⭐☆★🎉✨]+")

ICONS: dict[str, str] = {
    "bolt": '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    "refresh": '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a9 9 0 1 1-2.64-6.36"/><polyline points="21 3 21 9 15 9"/></svg>',
    "eye_off": '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>',
    "eye": '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>',
    "sliders": '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>',
    "copy": '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>',
    "arrow_up_right": '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/></svg>',
    "check": '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>',
    "close": '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
    "bell": '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>',
    "sun": '<svg class="ico theme-ico-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>',
    "moon": '<svg class="ico theme-ico-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>',
    "globe": '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
    "star": '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
    "sparkle": '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2z"/></svg>',
    "download": '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
}

STRINGS: dict[str, dict[str, str]] = {
    "zh": {
        "page_title": "Google AI Ultra Maximizer",
        "runtime_fallback": "Antigravity 2.0 原生控制面",
        "btn_refresh": "刷新",
        "btn_wakeup": "唤醒 5h 池",
        "copy_model_tip": "点击复制模型 ID",
        "btn_settings": "校准设置",
        "btn_test_push": "测试推送",
        "btn_privacy_on": "脱敏",
        "btn_privacy_off": "已脱敏",
        "btn_theme_title": "切换明暗主题",
        "sec_gauges": "Antigravity 双周期同心仪表",
        "sec_routing": "当下最优算力路由决策",
        "lbl_rec_coding": "主力编码",
        "lbl_rec_triage": "轻量调度",
        "sec_advisor": "Google Ultra 算力榨干参谋",
        "advisor_empty": "当前各算力池均处于健康平衡状态。",
        "sec_pools": "外部与云端算力池",
        "sec_wheels": "原生 Antigravity 运行底座",
        "sec_awaiting": "黄区合入闸门",
        "awaiting_clear": "0 个待合入工单 · 隔离 Worktree 待命",
        "diff_verify": "差异统计与单测输出",
        "btn_approve": "批准并合入 main",
        "btn_revise": "退回修改",
        "placeholder_revise": "输入修改意见...",
        "sec_history": "任务历史归档",
        "sec_matrix": "跨端同步项目矩阵（AI-Projects）",
        "th_id": "工单 ID",
        "th_proj": "项目",
        "th_title": "标题",
        "th_status": "状态",
        "th_updated": "更新时间",
        "th_path": "本地路径",
        "th_summary": "状态摘要",
        "sync_gcp": "同步 GCP 赠金",
        "gcp_credits": "账单页",
        "grants_summary": "查看生效赠金明细",
        "modal_title": "设置与赠金额度校准",
        "modal_desc": "保存至本机 secrets.env（权限 600，绝不入库）。密钥框留空表示保持原有配置不变。",
        "preset_label": "一键填入月度赠金基数：",
        "lbl_budget": "Cloud / Gemini API 本月赠金总额 (USD)",
        "lbl_rem_quick": "按 GCP 账单页「当前剩余美元」快速校准（可选，填了自动反推外部已用）",
        "lbl_ext_used": "外部已消耗金额 (USD)",
        "lbl_flow_cap": "Flow 月度基础积分",
        "lbl_colab_cap": "Colab 月度 CU 基数",
        "lbl_model": "默认分诊模型",
        "lbl_proxy": "本地代理地址（可选）",
        "lbl_notify": "Apprise 推送通道 URL（多个逗号分隔，如 tgram://... 或 bark://...）",
        "lbl_api_key": "Gemini Paid API Key（留空保持不变）",
        "lbl_tg_token": "Telegram Bot Token（可选快捷兼容，留空保持不变）",
        "lbl_tg_chat": "Telegram Chat ID（可选，留空保持不变）",
        "btn_save": "保存配置并刷新",
        "btn_cancel": "取消",
        "no_rows": "暂无记录",
        "copy_cmd": "复制",
        "copied": "已复制",
        "copy_err": "复制失败，请手动复制",
        "run_now": "执行",
        "footer_left": "纯本机 127.0.0.1 · 原生 Antigravity 2.0 驱动 · 快捷键：R 刷新 · S 校准 · Esc 关闭弹窗",
        "github_repo": "GitHub 仓库",
        "star_prompt_title": "觉得 Google AI Ultra Maximizer 好用吗？",
        "star_prompt_desc": "给 GitHub 仓库点亮一颗 Star 支持开源迭代，点完有惊喜散花",
        "star_cta": "一键点亮 Star",
        "star_starring": "正在点亮…",
        "star_open_gh": "前往 GitHub 点 Star",
        "star_dismiss": "暂不",
        "star_thanks_title": "感谢你的 Star 支持！",
        "star_thanks_desc": "祝你每天榨干双 5h 池与全部 Ultra 算力额度！",
        "btn_check_update": "检查更新",
        "upd_checking": "检查中…",
        "upd_title": "发现 GitHub 新版本",
        "upd_later": "暂不",
        "upd_now": "立即自动更新",
        "upd_updating": "正在更新…",
        "upd_restarting": "正在重启驾驶舱…",
        "upd_view_diff": "查看变更",
        "upd_latest": "当前已是最新版本",
        "upd_offline": "检查更新失败（无法连接 GitHub）",
        "upd_behind": "领先本地 {n} 个提交",
    },
    "en": {
        "page_title": "Google AI Ultra Maximizer",
        "runtime_fallback": "Antigravity 2.0 Native Control Plane",
        "btn_refresh": "Refresh",
        "btn_wakeup": "Wakeup 5h",
        "copy_model_tip": "Click to copy model ID",
        "btn_settings": "Calibrate",
        "btn_test_push": "Test Alert",
        "btn_privacy_on": "Mask",
        "btn_privacy_off": "Masked",
        "btn_theme_title": "Toggle color theme",
        "sec_gauges": "Antigravity Dual-Cycle Gauges",
        "sec_routing": "Next Best Routing Move",
        "lbl_rec_coding": "Coding Route",
        "lbl_rec_triage": "Triage Route",
        "sec_advisor": "Ultra Burn Advisor",
        "advisor_empty": "All quota pools are balanced.",
        "sec_pools": "Cloud & External Quota Pools",
        "sec_wheels": "Native Antigravity Stack",
        "sec_awaiting": "Yellow-Zone Approval Gate",
        "awaiting_clear": "0 pending merges · isolated worktrees idle",
        "diff_verify": "Diff & Verification",
        "btn_approve": "Approve & Merge to main",
        "btn_revise": "Request Revision",
        "placeholder_revise": "Enter revision notes...",
        "sec_history": "Task History",
        "sec_matrix": "Synced Project Matrix (AI-Projects)",
        "th_id": "Task ID",
        "th_proj": "Project",
        "th_title": "Title",
        "th_status": "Status",
        "th_updated": "Updated",
        "th_path": "Local Path",
        "th_summary": "Summary",
        "sync_gcp": "Sync GCP Credits",
        "gcp_credits": "GCP Console",
        "grants_summary": "Active grants & deductions",
        "modal_title": "Settings & Credit Calibration",
        "modal_desc": "Saved locally to secrets.env (chmod 600, never committed). Leave secret inputs blank to keep existing values.",
        "preset_label": "Quick-fill monthly Cloud credit tier:",
        "lbl_budget": "Monthly Cloud / Gemini Credit Budget (USD)",
        "lbl_rem_quick": "Quick-calibrate from GCP Remaining Balance USD (optional)",
        "lbl_ext_used": "External Used USD",
        "lbl_flow_cap": "Flow Monthly Baseline Credits",
        "lbl_colab_cap": "Colab Monthly Baseline CU",
        "lbl_model": "Triage Model",
        "lbl_proxy": "HTTP Proxy URL (optional)",
        "lbl_notify": "Apprise Notify URLs (comma-separated, e.g. tgram://..., bark://...)",
        "lbl_api_key": "Gemini Paid API Key (leave blank to keep)",
        "lbl_tg_token": "Telegram Bot Token (leave blank to keep)",
        "lbl_tg_chat": "Telegram Chat ID (leave blank to keep)",
        "btn_save": "Save & Refresh",
        "btn_cancel": "Cancel",
        "no_rows": "No records yet",
        "copy_cmd": "Copy",
        "copied": "Copied",
        "copy_err": "Copy failed",
        "run_now": "Run Now",
        "footer_left": "Loopback 127.0.0.1 · Native Antigravity 2.0 · Shortcuts: R Refresh · S Calibrate · Esc Close",
        "github_repo": "GitHub",
        "star_prompt_title": "Enjoying Google AI Ultra Maximizer?",
        "star_prompt_desc": "Give us a star on GitHub to help the project grow!",
        "star_cta": "Star on GitHub",
        "star_starring": "Starring…",
        "star_open_gh": "Open GitHub",
        "star_dismiss": "Dismiss",
        "star_thanks_title": "Thanks for the star!",
        "star_thanks_desc": "May your dual 5h and Ultra pools never go to waste.",
        "btn_check_update": "Check Updates",
        "upd_checking": "Checking…",
        "upd_title": "Update Available",
        "upd_later": "Later",
        "upd_now": "Update Now",
        "upd_updating": "Updating…",
        "upd_restarting": "Restarting cockpit…",
        "upd_view_diff": "View Changes",
        "upd_latest": "Already up to date",
        "upd_offline": "Update check failed (GitHub unreachable)",
        "upd_behind": "{n} new commit(s) on main",
    },
}

_EXT_POOL_ORDER: dict[str, int] = {
    "colab_cu": 0,
    "flow_credits": 1,
    "paid_gemini_api": 2,
    "gdrive_bus": 3,
    "ai_studio_daily": 4,
}


def _clean_badge(text: str) -> str:
    return _LEADING_EMOJI_RE.sub("", str(text or "")).strip()


def _bar_color(pool_id: str, pct: float) -> str:
    if pool_id == "gdrive_bus":
        return "var(--info)"
    if pct >= 40.0:
        return "var(--ok)"
    if pct >= 15.0:
        return "var(--warn)"
    return "var(--danger)"


def _pick_lang(item: dict[str, Any], key: str, is_en: bool) -> str:
    if is_en:
        en_val = item.get(f"{key}_en")
        if en_val is not None and str(en_val) != "":
            return str(en_val)
    return str(item.get(key) or "")


def _concentric_gauge_svg(
    pct_outer: float | None,
    pct_inner: float | None,
    color_outer: str,
    color_inner: str,
) -> str:
    """Render a 92x92 dual-ring concentric SVG gauge (outer=5h, inner=7d weekly)."""
    r_o = 36.0
    c_o = 2.0 * 3.14159265 * r_o
    r_i = 26.0
    c_i = 2.0 * 3.14159265 * r_i

    if pct_outer is None and pct_inner is None:
        return (
            '<svg class="gauge-svg" viewBox="0 0 92 92" aria-hidden="true">'
            f'<circle cx="46" cy="46" r="{r_o}" fill="none" stroke="var(--track)" stroke-width="6.5" stroke-dasharray="4 4"/>'
            f'<circle cx="46" cy="46" r="{r_i}" fill="none" stroke="var(--track)" stroke-width="6.5" stroke-dasharray="4 4"/>'
            '<text x="46" y="49" text-anchor="middle" fill="var(--muted)" font-size="11" font-weight="700" class="num">--</text>'
            "</svg>"
        )

    po = max(0.0, min(100.0, float(pct_outer if pct_outer is not None else pct_inner or 0.0)))
    off_o = c_o * (1.0 - po / 100.0)
    inner_svg = ""
    sub_svg = ""
    if pct_inner is not None:
        pi = max(0.0, min(100.0, float(pct_inner)))
        off_i = c_i * (1.0 - pi / 100.0)
        inner_svg = (
            f'<circle cx="46" cy="46" r="{r_i}" fill="none" stroke="var(--track)" stroke-width="6.5"/>'
            f'<circle cx="46" cy="46" r="{r_i}" fill="none" stroke="{color_inner}" stroke-width="6.5" '
            f'stroke-linecap="round" stroke-dasharray="{c_i:.1f}" stroke-dashoffset="{off_i:.1f}" '
            'transform="rotate(-90 46 46)"/>'
        )
        sub_svg = f'<text x="46" y="58" text-anchor="middle" fill="var(--muted)" font-size="9.5" font-weight="600" class="num">W {pi:.0f}%</text>'

    center_y = "44" if pct_inner is not None else "50"
    return (
        '<svg class="gauge-svg" viewBox="0 0 92 92" aria-hidden="true">'
        f'<circle cx="46" cy="46" r="{r_o}" fill="none" stroke="var(--track)" stroke-width="6.5"/>'
        f'<circle cx="46" cy="46" r="{r_o}" fill="none" stroke="{color_outer}" stroke-width="6.5" '
        f'stroke-linecap="round" stroke-dasharray="{c_o:.1f}" stroke-dashoffset="{off_o:.1f}" '
        'transform="rotate(-90 46 46)"/>'
        f"{inner_svg}"
        f'<text x="46" y="{center_y}" text-anchor="middle" fill="var(--ink)" font-size="13" font-weight="700" class="num">{po:.0f}%</text>'
        f"{sub_svg}"
        "</svg>"
    )


_CSS_BLOCK = """
  :root {
    --bg-light: oklch(0.958 0.008 250);
    --surface-light: oklch(0.992 0.003 250);
    --surface-2-light: oklch(0.935 0.010 250);
    --hover-light: oklch(0.978 0.005 250);
    --ink-light: oklch(0.18 0.012 255);
    --ink-soft-light: oklch(0.36 0.012 255);
    --muted-light: oklch(0.50 0.012 255);
    --line-light: oklch(0.22 0.012 255 / 0.09);
    --line-strong-light: oklch(0.22 0.012 255 / 0.19);
    --ok-light: oklch(0.52 0.15 164);
    --ok-ink-light: oklch(0.99 0.003 250);
    --ok-bg-light: oklch(0.52 0.15 164 / 0.12);
    --warn-light: oklch(0.62 0.15 70);
    --warn-bg-light: oklch(0.62 0.15 70 / 0.13);
    --warn-ink-light: oklch(0.42 0.12 65);
    --danger-light: oklch(0.55 0.19 25);
    --danger-bg-light: oklch(0.55 0.19 25 / 0.12);
    --danger-ink-light: oklch(0.45 0.16 25);
    --info-light: oklch(0.52 0.14 242);
    --info-bg-light: oklch(0.52 0.14 242 / 0.11);
    --info-ink-light: oklch(0.42 0.12 242);
    --muted-bg-light: oklch(0.22 0.012 255 / 0.07);
    --track-light: oklch(0.22 0.012 255 / 0.08);
    --header-light: oklch(0.958 0.008 250 / 0.85);
    --shadow-light: 0 6px 24px oklch(0.20 0.015 255 / 0.06), inset 0 1px 0 oklch(1 0 0 / 0.9);

    --bg-dark: oklch(0.13 0.012 265);
    --surface-dark: oklch(0.185 0.014 265);
    --surface-2-dark: oklch(0.155 0.012 265);
    --hover-dark: oklch(0.22 0.015 265);
    --ink-dark: oklch(0.955 0.006 260);
    --ink-soft-dark: oklch(0.82 0.008 260);
    --muted-dark: oklch(0.64 0.012 260);
    --line-dark: oklch(1 0 0 / 0.085);
    --line-strong-dark: oklch(1 0 0 / 0.17);
    --ok-dark: oklch(0.74 0.14 168);
    --ok-ink-dark: oklch(0.14 0.03 168);
    --ok-bg-dark: oklch(0.74 0.14 168 / 0.14);
    --warn-dark: oklch(0.80 0.14 78);
    --warn-bg-dark: oklch(0.80 0.14 78 / 0.15);
    --warn-ink-dark: oklch(0.86 0.11 82);
    --danger-dark: oklch(0.69 0.18 22);
    --danger-bg-dark: oklch(0.69 0.18 22 / 0.15);
    --danger-ink-dark: oklch(0.82 0.12 22);
    --info-dark: oklch(0.73 0.13 238);
    --info-bg-dark: oklch(0.73 0.13 238 / 0.14);
    --info-ink-dark: oklch(0.82 0.10 238);
    --muted-bg-dark: oklch(1 0 0 / 0.07);
    --track-dark: oklch(1 0 0 / 0.08);
    --header-dark: oklch(0.13 0.012 265 / 0.84);
    --shadow-dark: 0 10px 32px oklch(0 0 0 / 0.30), inset 0 1px 0 oklch(1 0 0 / 0.09);

    --bg: var(--bg-light);
    --surface: var(--surface-light);
    --surface-2: var(--surface-2-light);
    --hover: var(--hover-light);
    --ink: var(--ink-light);
    --ink-soft: var(--ink-soft-light);
    --muted: var(--muted-light);
    --line: var(--line-light);
    --line-strong: var(--line-strong-light);
    --ok: var(--ok-light);
    --ok-ink: var(--ok-ink-light);
    --ok-bg: var(--ok-bg-light);
    --warn: var(--warn-light);
    --warn-bg: var(--warn-bg-light);
    --warn-ink: var(--warn-ink-light);
    --danger: var(--danger-light);
    --danger-bg: var(--danger-bg-light);
    --danger-ink: var(--danger-ink-light);
    --info: var(--info-light);
    --info-bg: var(--info-bg-light);
    --info-ink: var(--info-ink-light);
    --muted-bg: var(--muted-bg-light);
    --track: var(--track-light);
    --header-bg: var(--header-light);
    --shadow: var(--shadow-light);

    color-scheme: light dark;
    accent-color: var(--ok);
    scrollbar-color: var(--line-strong) transparent;
  }

  :root:has(> head > meta[name="color-scheme"][content="dark"]) { color-scheme: dark; }
  :root:has(> head > meta[name="color-scheme"][content="light"]) { color-scheme: light; }

  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --bg: var(--bg-dark); --surface: var(--surface-dark); --surface-2: var(--surface-2-dark);
      --hover: var(--hover-dark); --ink: var(--ink-dark); --ink-soft: var(--ink-soft-dark);
      --muted: var(--muted-dark); --line: var(--line-dark); --line-strong: var(--line-strong-dark);
      --ok: var(--ok-dark); --ok-ink: var(--ok-ink-dark); --ok-bg: var(--ok-bg-dark);
      --warn: var(--warn-dark); --warn-bg: var(--warn-bg-dark); --warn-ink: var(--warn-ink-dark);
      --danger: var(--danger-dark); --danger-bg: var(--danger-bg-dark); --danger-ink: var(--danger-ink-dark);
      --info: var(--info-dark); --info-bg: var(--info-bg-dark); --info-ink: var(--info-ink-dark);
      --muted-bg: var(--muted-bg-dark); --track: var(--track-dark); --header-bg: var(--header-dark);
      --shadow: var(--shadow-dark);
    }
  }
  :root[data-theme="dark"] {
    --bg: var(--bg-dark); --surface: var(--surface-dark); --surface-2: var(--surface-2-dark);
    --hover: var(--hover-dark); --ink: var(--ink-dark); --ink-soft: var(--ink-soft-dark);
    --muted: var(--muted-dark); --line: var(--line-dark); --line-strong: var(--line-strong-dark);
    --ok: var(--ok-dark); --ok-ink: var(--ok-ink-dark); --ok-bg: var(--ok-bg-dark);
    --warn: var(--warn-dark); --warn-bg: var(--warn-bg-dark); --warn-ink: var(--warn-ink-dark);
    --danger: var(--danger-dark); --danger-bg: var(--danger-bg-dark); --danger-ink: var(--danger-ink-dark);
    --info: var(--info-dark); --info-bg: var(--info-bg-dark); --info-ink: var(--info-ink-dark);
    --muted-bg: var(--muted-bg-dark); --track: var(--track-dark); --header-bg: var(--header-dark);
    --shadow: var(--shadow-dark);
  }
  :root[data-theme="light"] {
    --bg: var(--bg-light); --surface: var(--surface-light); --surface-2: var(--surface-2-light);
    --hover: var(--hover-light); --ink: var(--ink-light); --ink-soft: var(--ink-soft-light);
    --muted: var(--muted-light); --line: var(--line-light); --line-strong: var(--line-strong-light);
    --ok: var(--ok-light); --ok-ink: var(--ok-ink-light); --ok-bg: var(--ok-bg-light);
    --warn: var(--warn-light); --warn-bg: var(--warn-bg-light); --warn-ink: var(--warn-ink-light);
    --danger: var(--danger-light); --danger-bg: var(--danger-bg-light); --danger-ink: var(--danger-ink-light);
    --info: var(--info-light); --info-bg: var(--info-bg-light); --info-ink: var(--info-ink-light);
    --muted-bg: var(--muted-bg-light); --track: var(--track-light); --header-bg: var(--header-light);
    --shadow: var(--shadow-light);
  }

  @supports (color: light-dark(white, black)) {
    :root {
      --bg: light-dark(var(--bg-light), var(--bg-dark));
      --surface: light-dark(var(--surface-light), var(--surface-dark));
      --surface-2: light-dark(var(--surface-2-light), var(--surface-2-dark));
      --hover: light-dark(var(--hover-light), var(--hover-dark));
      --ink: light-dark(var(--ink-light), var(--ink-dark));
      --ink-soft: light-dark(var(--ink-soft-light), var(--ink-soft-dark));
      --muted: light-dark(var(--muted-light), var(--muted-dark));
      --line: light-dark(var(--line-light), var(--line-dark));
      --line-strong: light-dark(var(--line-strong-light), var(--line-strong-dark));
      --ok: light-dark(var(--ok-light), var(--ok-dark));
      --ok-ink: light-dark(var(--ok-ink-light), var(--ok-ink-dark));
      --ok-bg: light-dark(var(--ok-bg-light), var(--ok-bg-dark));
      --warn: light-dark(var(--warn-light), var(--warn-dark));
      --warn-bg: light-dark(var(--warn-bg-light), var(--warn-bg-dark));
      --warn-ink: light-dark(var(--warn-ink-light), var(--warn-ink-dark));
      --danger: light-dark(var(--danger-light), var(--danger-dark));
      --danger-bg: light-dark(var(--danger-bg-light), var(--danger-bg-dark));
      --danger-ink: light-dark(var(--danger-ink-light), var(--danger-ink-dark));
      --info: light-dark(var(--info-light), var(--info-dark));
      --info-bg: light-dark(var(--info-bg-light), var(--info-bg-dark));
      --info-ink: light-dark(var(--info-ink-light), var(--info-ink-dark));
      --muted-bg: light-dark(var(--muted-bg-light), var(--muted-bg-dark));
      --track: light-dark(var(--track-light), var(--track-dark));
      --header-bg: light-dark(var(--header-light), var(--header-dark));
      --shadow: light-dark(var(--shadow-light), var(--shadow-dark));
    }
  }

  @supports not (scrollbar-color: auto) {
    *::-webkit-scrollbar { width: 10px; height: 10px; }
    *::-webkit-scrollbar-thumb { background: var(--line-strong); border-radius: 999px; }
    *::-webkit-scrollbar-track { background: transparent; }
  }

  *, *::before, *::after { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--ink);
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "PingFang SC", "Noto Sans SC", sans-serif;
    font-size: 14px;
    line-height: 1.48;
    -webkit-font-smoothing: antialiased;
  }
  code, .num {
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
    font-variant-numeric: tabular-nums;
  }
  code {
    background: var(--track);
    padding: 1px 6px;
    border-radius: 5px;
    font-size: 12px;
  }
  svg.ico {
    width: 15px;
    height: 15px;
    flex-shrink: 0;
    display: inline-block;
    vertical-align: middle;
  }

  /* Theme icon visibility driven purely by color-scheme CSS */
  .theme-ico-sun { display: none; }
  .theme-ico-moon { display: inline-block; }
  @media (prefers-color-scheme: dark) {
    :root:not(:has(> head > meta[name="color-scheme"][content="light"])):not([data-theme="light"]) .theme-ico-sun { display: inline-block; }
    :root:not(:has(> head > meta[name="color-scheme"][content="light"])):not([data-theme="light"]) .theme-ico-moon { display: none; }
  }
  :root:has(> head > meta[name="color-scheme"][content="dark"]) .theme-ico-sun,
  :root[data-theme="dark"] .theme-ico-sun { display: inline-block; }
  :root:has(> head > meta[name="color-scheme"][content="dark"]) .theme-ico-moon,
  :root[data-theme="dark"] .theme-ico-moon { display: none; }

  /* Compact Single-Row Sticky Topbar */
  .topbar {
    position: sticky;
    top: 0;
    z-index: 40;
    height: 52px;
    background: var(--header-bg);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border-bottom: 1px solid var(--line);
  }
  .topbar-inner {
    max-width: 1320px;
    height: 100%;
    margin: 0 auto;
    padding: 0 22px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
  }
  .brand { display: flex; align-items: center; gap: 10px; min-width: 0; }
  .brand-mark {
    width: 26px;
    height: 26px;
    border-radius: 7px;
    flex-shrink: 0;
    background: var(--ok);
    color: var(--ok-ink);
    display: grid;
    place-items: center;
  }
  .brand h1 {
    margin: 0;
    font-size: 14.5px;
    font-weight: 700;
    letter-spacing: -0.02em;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .runtime-pill {
    font-size: 11px;
    font-weight: 600;
    padding: 2px 9px;
    border-radius: 999px;
    background: var(--ok-bg);
    color: var(--ok);
    white-space: nowrap;
  }
  .toolbar { display: flex; gap: 6px; align-items: center; flex-shrink: 0; }

  .btn {
    padding: 5px 10px;
    border-radius: 9px;
    border: 1px solid var(--line-strong);
    background: var(--surface);
    color: var(--ink);
    cursor: pointer;
    font-weight: 600;
    font-size: 12px;
    text-decoration: none;
    white-space: nowrap;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    transition: background-color .14s ease, border-color .14s ease;
  }
  .btn:hover { background: var(--hover); }
  .btn:disabled { opacity: .58; cursor: wait; }
  .btn.primary { background: var(--ok); color: var(--ok-ink); border-color: transparent; font-weight: 700; }
  .btn.primary:hover { filter: brightness(1.06); }
  .btn.ghost { background: transparent; border-color: var(--line); color: var(--ink-soft); }
  .btn.xs { padding: 3px 8px; font-size: 11px; border-radius: 7px; }
  @keyframes spinOnce { to { transform: rotate(360deg); } }
  .spinning { animation: spinOnce .55s linear; }

  .wrap { max-width: 1320px; margin: 0 auto; padding: 18px 22px 36px; }

  .banner {
    padding: 10px 14px;
    border-radius: 12px;
    margin-bottom: 14px;
    font-weight: 600;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 8px;
    border: 1px solid var(--line);
  }
  .banner.ok { background: var(--ok-bg); color: var(--ok); border-color: var(--ok); }
  .banner.err { background: var(--danger-bg); color: var(--danger-ink); border-color: var(--danger); }

  /* Status Pills (zero emoji dots; single CSS indicator) */
  .source-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 999px;
    font-weight: 600;
    white-space: normal;
    line-height: 1.3;
    overflow-wrap: anywhere;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .source-badge::before {
    content: "";
    width: 6px;
    height: 6px;
    border-radius: 999px;
    background: currentColor;
    flex-shrink: 0;
  }
  .source-badge.live { background: var(--ok-bg); color: var(--ok); }
  .source-badge.local { background: var(--info-bg); color: var(--info-ink); }
  .source-badge.stale { background: var(--warn-bg); color: var(--warn-ink); }
  .source-badge.warn { background: var(--danger-bg); color: var(--danger-ink); }
  .source-badge.muted { background: var(--muted-bg); color: var(--muted); }

  /* Spatial Observatory Plates */
  .vb-card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 18px;
    box-shadow: var(--shadow);
    padding: 18px 20px;
    min-width: 0;
  }
  .plate-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 12px;
  }
  .plate-title {
    margin: 0;
    font-size: 12.5px;
    font-weight: 700;
    color: var(--ink-soft);
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }
  .count-pill {
    font-size: 11px;
    padding: 1px 7px;
    border-radius: 999px;
    background: var(--track);
    color: var(--ink);
  }
  .count-pill.warn { background: var(--warn-bg); color: var(--warn-ink); }

  /* Hero 2-Column Row */
  .vb-hero {
    display: grid;
    grid-template-columns: 1.35fr 1fr;
    gap: 14px;
    margin-bottom: 14px;
  }
  .vb-gauges {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
  }
  .gauge-panel {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    min-width: 0;
  }
  .gauge-svg { width: 92px; height: 92px; flex-shrink: 0; }
  .gauge-info { min-width: 0; flex: 1; }
  .gauge-name { font-size: 13.5px; font-weight: 700; color: var(--ink); margin-bottom: 4px; }
  .quota-windows { display: flex; flex-direction: column; gap: 5px; }
  .quota-win { font-size: 11.5px; line-height: 1.35; }
  .quota-win-row { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; }
  .quota-win-lbl { color: var(--ink-soft); font-weight: 600; }
  .quota-win-val { font-weight: 700; color: var(--ink); }
  .quota-win-sub { font-size: 11px; color: var(--muted); }
  .gauge-kicker { font-size: 11px; color: var(--muted); margin-top: 5px; overflow-wrap: anywhere; }

  .verdict-plate {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 14px;
  }
  .roi-stat {
    font-size: 13px;
    font-weight: 700;
    color: var(--ok);
  }
  .verdict-headline {
    font-size: 15.5px;
    font-weight: 700;
    letter-spacing: -0.015em;
    line-height: 1.35;
    margin: 0 0 6px;
  }
  .verdict-reason { font-size: 12.5px; color: var(--muted); margin: 0; }
  .verdict-foot {
    display: flex;
    flex-wrap: wrap;
    gap: 7px;
    align-items: center;
    justify-content: space-between;
  }
  .model-pills { display: flex; flex-wrap: wrap; gap: 6px; }
  .model-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 9px;
    border-radius: 8px;
    border: 1px solid var(--line-strong);
    background: var(--surface-2);
    color: var(--ink);
    font-size: 11.5px;
    cursor: pointer;
    transition: background-color .14s ease;
  }
  .model-chip:hover { background: var(--hover); }
  .chip-lbl { color: var(--muted); font-weight: 600; }

  /* 5-Tile Resource Strip */
  .vb-tiles {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 12px;
    margin-bottom: 14px;
  }
  .vb-tile {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 15px;
    box-shadow: var(--shadow);
    padding: 14px 15px;
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 9px;
  }
  .vb-tile > div { min-width: 0; }
  .vb-tile.tone-warn { border-color: var(--danger); }
  .tile-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 6px;
    flex-wrap: wrap;
    margin-bottom: 6px;
  }
  .tile-title { margin: 0; font-size: 12px; font-weight: 700; color: var(--ink-soft); }
  .tile-metric { font-size: 19px; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 6px; }
  .bar { height: 5px; background: var(--track); border-radius: 999px; overflow: hidden; margin-bottom: 7px; }
  .bar > div { height: 100%; border-radius: 999px; transition: width .35s ease; }
  .tile-detail { font-size: 11.5px; color: var(--muted); line-height: 1.4; overflow-wrap: anywhere; }
  .tile-actions { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }

  /* Bottom 2-Column Split */
  .vb-bottom {
    display: grid;
    grid-template-columns: 1.25fr 1fr;
    gap: 14px;
    margin-bottom: 18px;
  }
  .adv-list { display: flex; flex-direction: column; gap: 10px; }
  .adv-row {
    padding-bottom: 10px;
    border-bottom: 1px solid var(--line);
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
  }
  .adv-row:last-child { border-bottom: none; padding-bottom: 0; }
  .adv-title { font-size: 13px; font-weight: 700; margin: 4px 0 2px; }
  .adv-action { font-size: 12px; color: var(--muted); }
  .adv-cmds { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-top: 6px; }
  .inline-link { color: var(--info-ink); text-decoration: none; font-size: 11.5px; font-weight: 600; display: inline-flex; align-items: center; gap: 3px; }
  .inline-link:hover { text-decoration: underline; }

  .stack-list { display: flex; flex-direction: column; gap: 10px; }
  .stack-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 10px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--line);
  }
  .stack-row:last-child { border-bottom: none; padding-bottom: 0; }
  .stack-name { font-size: 13px; font-weight: 700; color: var(--ink); }
  .stack-detail { font-size: 11.5px; color: var(--muted); margin-top: 2px; }

  /* Governance & Accordions */
  .gate-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 10px;
  }
  .gate-label { font-size: 12.5px; font-weight: 700; color: var(--ink-soft); }
  .task-card {
    background: var(--surface);
    border: 1px solid var(--warn);
    border-radius: 15px;
    box-shadow: var(--shadow);
    padding: 15px 17px;
    margin-bottom: 12px;
  }
  .task-head { display: flex; align-items: center; gap: 9px; flex-wrap: wrap; margin-bottom: 6px; }
  .meta { font-size: 12px; color: var(--muted); margin: 4px 0 10px; overflow-wrap: anywhere; }
  pre {
    background: var(--surface-2);
    border: 1px solid var(--line);
    padding: 10px 12px;
    border-radius: 9px;
    font-size: 12px;
    overflow: auto;
    max-height: 220px;
    color: var(--ink-soft);
  }
  .actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-top: 12px; }
  .revise-form { display: flex; gap: 6px; flex: 1; min-width: 220px; }
  input[type=text], input[type=number], input[type=password] {
    width: 100%;
    padding: 7px 10px;
    border: 1px solid var(--line-strong);
    border-radius: 8px;
    background: var(--surface-2);
    color: var(--ink);
    font-size: 12.5px;
  }

  /* Modern Web Guidance: Semantic Accordion (<details>) */
  details.mwg-acc {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 13px;
    margin-bottom: 10px;
  }
  details.mwg-acc > summary {
    list-style: none;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 11px 15px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 700;
    color: var(--ink-soft);
  }
  details.mwg-acc > summary::-webkit-details-marker { display: none; }
  details.mwg-acc > summary .sum-left {
    display: flex;
    align-items: center;
    gap: 0.55ch;
  }
  details.mwg-acc > summary .sum-left::before {
    content: "";
    inline-size: 1em;
    block-size: 1em;
    flex-shrink: 0;
    background-color: currentColor;
    -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E") no-repeat center / contain;
    mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E") no-repeat center / contain;
    rotate: -90deg;
  }
  details.mwg-acc[open] > summary .sum-left::before { rotate: 0deg; }
  details.mwg-acc::details-content {
    interpolate-size: allow-keywords;
    overflow: clip;
    contain: layout;
  }
  details.mwg-acc:not([open])::details-content { block-size: 0; }
  @media (prefers-reduced-motion: no-preference) {
    details.mwg-acc > summary .sum-left::before { transition: rotate 0.2s; }
    details.mwg-acc::details-content {
      transition: block-size 0.28s ease-in-out, content-visibility 0.28s ease-in-out;
      transition-behavior: allow-discrete;
    }
  }
  .acc-body { padding: 0 15px 14px; }

  /* Modern Web Guidance: Container-Responsive Table */
  .table-wrap {
    overflow: auto;
    max-inline-size: 100%;
    max-block-size: 360px;
    container-type: inline-size;
    border: 1px solid var(--line);
    border-radius: 10px;
    background: var(--surface);
  }
  table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 12.5px;
    margin: 0;
  }
  thead {
    position: sticky;
    inset-block-start: 0;
    z-index: 1;
  }
  thead th {
    background: var(--surface-2);
    color: var(--ink-soft);
    font-weight: 600;
    text-align: left;
    padding: 8px 11px;
    border-bottom: 1px solid var(--line);
    white-space: nowrap;
  }
  td, tbody th {
    padding: 8px 11px;
    border-bottom: 1px solid var(--line);
    text-align: left;
    vertical-align: top;
  }
  tbody th { font-weight: 600; color: var(--ink); background: var(--surface); }
  tbody tr:last-child td, tbody tr:last-child th { border-bottom: none; }
  @container (width < 560px) {
    table, thead, tbody, tr, th, td { display: block; }
    thead { display: none; }
    tbody tr {
      margin-block-end: 10px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
    }
    tbody th {
      position: sticky;
      inset-block-start: 0;
      z-index: 2;
      background: var(--surface-2);
      border-bottom: 1px solid var(--line);
    }
    td::before {
      content: attr(data-col) ": ";
      font-weight: 600;
      color: var(--muted);
    }
  }

  .cockpit-footer {
    max-width: 1320px;
    margin: 16px auto 0;
    padding: 14px 4px 0;
    border-top: 1px solid var(--line);
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    font-size: 11.5px;
    color: var(--muted);
  }

  /* Light-Dismiss Modal Dialog */
  dialog {
    border: 1px solid var(--line-strong);
    border-radius: 16px;
    max-width: 640px;
    width: 92%;
    padding: 20px 22px;
    background: var(--surface);
    color: var(--ink);
    box-shadow: 0 24px 60px oklch(0 0 0 / 0.45);
  }
  dialog::backdrop {
    background: oklch(0.08 0.01 255 / 0.62);
    backdrop-filter: blur(4px);
  }
  .dlg-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 6px; }
  .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 11px; margin: 14px 0; }
  .form-grid .full { grid-column: 1 / -1; }
  .field label { display: block; font-size: 11.5px; font-weight: 600; margin-bottom: 4px; color: var(--ink-soft); }
  .presets { display: flex; gap: 7px; flex-wrap: wrap; align-items: center; margin: 10px 0 4px; font-size: 12px; color: var(--muted); }
  .notify-row { display: flex; gap: 8px; align-items: center; }

  .toast {
    position: fixed;
    right: 20px;
    bottom: 20px;
    z-index: 90;
    max-width: 440px;
    padding: 10px 14px;
    border-radius: 10px;
    font-size: 12.5px;
    font-weight: 600;
    background: var(--surface);
    color: var(--ink);
    border: 1px solid var(--line-strong);
    box-shadow: var(--shadow);
    display: none;
  }
  .toast.show { display: block; }
  .toast.ok { border-color: var(--ok); color: var(--ok); }
  .toast.err { border-color: var(--danger); color: var(--danger-ink); }

  /* Maturity-Gated Star Push Card (no topbar button; Spatial Observatory frosted card) */
  @keyframes starSlideIn {
    from { opacity: 0; transform: translateY(-10px) scale(.97); }
    to { opacity: 1; transform: translateY(0) scale(1); }
  }
  @keyframes starBadgePulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.14) rotate(-6deg); }
  }
  .star-prompt {
    position: fixed;
    top:62px;
    right: 20px;
    z-index: 95;
    width: min(388px, calc(100vw - 32px));
    background: var(--surface);
    color: var(--ink);
    border: 1px solid var(--warn);
    border-radius: 16px;
    padding: 15px 17px;
    box-shadow: var(--shadow);
    display: none;
  }
  .star-prompt.show { display: block; animation: starSlideIn .26s cubic-bezier(.16,1,.3,1); }
  .star-prompt.show .star-badge-icon { animation: starBadgePulse .9s ease 1; }
  .star-prompt.is-thanks { border-color: var(--ok); }
  .star-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; margin-bottom: 5px; }
  .star-title-wrap { display: flex; align-items: center; gap: 8px; font-size: 13.5px; line-height: 1.35; }
  .star-badge-icon {
    width: 24px;
    height: 24px;
    border-radius: 8px;
    flex-shrink: 0;
    display: grid;
    place-items: center;
    background: var(--warn-bg);
    color: var(--warn-ink);
  }
  .star-prompt.is-thanks .star-badge-icon { background: var(--ok-bg); color: var(--ok); }
  .star-close {
    background: transparent;
    border: none;
    color: var(--muted);
    cursor: pointer;
    padding: 2px;
    border-radius: 6px;
    display: inline-flex;
  }
  .star-close:hover { color: var(--ink); background: var(--track); }
  .star-desc { font-size: 12px; color: var(--muted); line-height: 1.45; margin-bottom: 11px; }
  .star-actions { display: flex; justify-content: flex-end; align-items: center; gap: 8px; flex-wrap: wrap; }
  .btn.star-cta { background: var(--warn); color: oklch(0.16 0.03 70); border-color: transparent; font-weight: 700; }
  .btn.star-cta:hover { filter: brightness(1.07); }

  .update-prompt {
    position: fixed;
    top:62px;
    right: 20px;
    z-index: 96;
    width: min(400px, calc(100vw - 32px));
    background: var(--surface);
    color: var(--ink);
    border: 1px solid var(--info);
    border-radius: 16px;
    padding: 15px 17px;
    box-shadow: var(--shadow);
    display: none;
  }
  .update-prompt.show { display: block; animation: starSlideIn .26s cubic-bezier(.16,1,.3,1); }
  .update-badge-icon {
    width: 24px;
    height: 24px;
    border-radius: 8px;
    flex-shrink: 0;
    display: grid;
    place-items: center;
    background: var(--info-bg);
    color: var(--info-ink);
  }
  .update-ver-pill {
    font-size: 11px;
    font-weight: 600;
    padding: 1px 7px;
    border-radius: 999px;
    background: var(--info-bg);
    color: var(--info-ink);
    white-space: nowrap;
  }
  .btn.update-cta { background: var(--info); color: var(--ok-ink); border-color: transparent; font-weight: 700; }
  .btn.update-cta:hover { filter: brightness(1.07); }
  .footer-right { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

  @media (max-width: 1120px) {
    .vb-tiles { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  }
  @media (max-width: 1000px) {
    .vb-hero, .vb-bottom { grid-template-columns: 1fr; }
  }
  @media (max-width: 760px) {
    .topbar { position: static; height: auto; padding: 8px 0; }
    .topbar-inner { flex-wrap: wrap; }
    .vb-gauges { grid-template-columns: 1fr; }
    .vb-tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .form-grid { grid-template-columns: 1fr; }
    .star-prompt, .update-prompt { top: 14px; right: 12px; left: 12px; width: auto; }
  }
  @media (max-width: 520px) {
    .vb-tiles { grid-template-columns: 1fr; }
  }
"""


_JS_TEMPLATE = """
const LOCAL_PAID_USD = __LOCAL_PAID_USD__;
const COPIED_LABEL = __COPIED_LABEL__;
const COPY_LABEL = __COPY_LABEL__;
const COPY_ERR_LABEL = __COPY_ERR_LABEL__;
const CSRF_TOKEN = __CSRF_TOKEN__;
const GITHUB_REPO_URL = __GITHUB_REPO_URL__;
const APP_VERSION = __APP_VERSION__;
const STAR_I18N = __STAR_I18N__;
const UPDATE_I18N = __UPDATE_I18N__;
const PAGE_LANG = __PAGE_LANG__;

function _sysScheme() {
  return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}
function _applyScheme(override) {
  const meta = document.querySelector('meta[name="color-scheme"]');
  if (override === 'light' || override === 'dark') {
    if (meta) meta.content = override;
    document.documentElement.setAttribute('data-theme', override);
  } else {
    if (meta) meta.content = 'light dark';
    document.documentElement.removeAttribute('data-theme');
  }
}
function toggleTheme() {
  let stored = null;
  try { stored = localStorage.getItem('color-scheme') || localStorage.getItem('fleet_theme'); } catch (e) {}
  const sys = _sysScheme();
  const current = (stored === 'light' || stored === 'dark') ? stored : sys;
  const target = current === 'dark' ? 'light' : 'dark';
  if (target === sys) {
    try {
      localStorage.removeItem('color-scheme');
      localStorage.removeItem('fleet_theme');
    } catch (e) {}
    _applyScheme(null);
  } else {
    try {
      localStorage.setItem('color-scheme', target);
      localStorage.removeItem('fleet_theme');
    } catch (e) {}
    _applyScheme(target);
  }
}
window.addEventListener('storage', (ev) => {
  if (ev.key === 'color-scheme') _applyScheme(ev.newValue);
});

function openSettingsModal() {
  const d = document.getElementById('settingsModal');
  if (d && !d.open && typeof d.showModal === 'function') d.showModal();
}
(function wireDialogLightDismiss() {
  const dlg = document.getElementById('settingsModal');
  if (!dlg) return;
  if (!('closedBy' in HTMLDialogElement.prototype)) {
    dlg.addEventListener('click', (event) => {
      if (event.target !== dlg) return;
      const rect = dlg.getBoundingClientRect();
      const inside = (
        rect.top <= event.clientY &&
        event.clientY <= rect.top + rect.height &&
        rect.left <= event.clientX &&
        event.clientX <= rect.left + rect.width
      );
      if (!inside) dlg.close();
    });
  }
})();

function setBudgetPreset(val) {
  document.getElementById('inp_budget').value = String(val);
  syncExternalFromRemaining();
}
function syncExternalFromRemaining() {
  const b = parseFloat(document.getElementById('inp_budget').value || '0');
  const remRaw = document.getElementById('inp_rem_quick').value;
  if (remRaw === '' || isNaN(b) || b <= 0) return;
  const rem = parseFloat(remRaw);
  if (isNaN(rem)) return;
  const ext = Math.max(0, b - rem - LOCAL_PAID_USD);
  document.getElementById('inp_ext').value = ext.toFixed(2);
}

let _toastTimer = null;
function showToast(text, ok) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = text;
  el.className = 'toast show ' + (ok ? 'ok' : 'err');
  if (_toastTimer) clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => { el.classList.remove('show'); }, 4500);
}
(function restoreFlashToast() {
  try {
    const raw = sessionStorage.getItem('fleet_flash');
    if (raw) {
      sessionStorage.removeItem('fleet_flash');
      const f = JSON.parse(raw);
      if (f && f.text) showToast(f.text, !!f.ok);
    }
  } catch (e) {}
})();

function _writeClipboard(text, onOk) {
  const onFallback = () => {
    try {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      const ok = document.execCommand('copy');
      document.body.removeChild(ta);
      if (ok) onOk(); else showToast(COPY_ERR_LABEL, false);
    } catch (e) {
      showToast(COPY_ERR_LABEL, false);
    }
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(onOk).catch(onFallback);
  } else {
    onFallback();
  }
}
function copyText(btn, text) {
  recordStarEngagement();
  _writeClipboard(text, () => {
    const orig = btn.innerHTML;
    btn.textContent = COPIED_LABEL;
    setTimeout(() => { btn.innerHTML = orig; }, 1500);
  });
}
function copyModelId(text) {
  if (!text) return;
  recordStarEngagement();
  _writeClipboard(text, () => showToast(COPIED_LABEL + ': ' + text, true));
}

async function sendTestAlert(btn, endpoint) {
  recordStarEngagement();
  const orig = btn.innerHTML;
  btn.disabled = true;
  try {
    const resp = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ csrf: CSRF_TOKEN }),
    });
    const data = await resp.json().catch(() => ({ ok: resp.ok, message: resp.statusText }));
    showToast(data.message || (data.ok ? 'OK' : 'Error'), !!data.ok);
  } catch (err) {
    showToast(String(err), false);
  } finally {
    btn.disabled = false;
    btn.innerHTML = orig;
  }
}

document.querySelectorAll('form[data-async="1"]').forEach((form) => {
  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    recordStarEngagement();
    const btn = form.querySelector('button[type="submit"]');
    const origHtml = btn ? btn.innerHTML : '';
    if (btn) {
      btn.disabled = true;
      const ico = btn.querySelector('svg');
      if (ico) ico.classList.add('spinning');
    }
    try {
      const payload = {};
      new FormData(form).forEach((v, k) => { payload[k] = v; });
      const resp = await fetch(form.action, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await resp.json().catch(() => ({ ok: resp.ok, message: resp.statusText }));
      const msgText = data.message || (data.ok ? 'Done' : 'Error');
      showToast(msgText, !!data.ok);
      if (data.ok) {
        try { sessionStorage.setItem('fleet_flash', JSON.stringify({ text: msgText, ok: true })); } catch (e) {}
        setTimeout(() => { window.location.reload(); }, 350);
      } else if (btn) {
        btn.disabled = false;
        btn.innerHTML = origHtml;
      }
    } catch (err) {
      showToast(String(err), false);
      if (btn) { btn.disabled = false; btn.innerHTML = origHtml; }
    }
  });
});

document.addEventListener('keydown', (ev) => {
  if (ev.metaKey || ev.ctrlKey || ev.altKey) return;
  const tgt = ev.target;
  if (tgt && (['INPUT', 'TEXTAREA', 'SELECT'].includes(tgt.tagName) || tgt.isContentEditable)) return;
  const dlg = document.getElementById('settingsModal');
  if (dlg && dlg.open) return;
  if (ev.key === 'r' || ev.key === 'R') {
    const btn = document.getElementById('btnRefresh');
    if (btn) btn.click();
  } else if (ev.key === 's' || ev.key === 'S') {
    openSettingsModal();
  }
});

const STAR_DISMISSED_KEY = 'ultra:star-v2:dismissed';
const STAR_DONE_KEY = 'ultra:star-v2:starred';
const STAR_ACTIONS_KEY = 'ultra:star-v2:actions';
const STAR_SESSIONS_KEY = 'ultra:star-v2:sessions';
const STAR_LAST_SESSION_KEY = 'ultra:star-v2:last_session_ts';
let _starAutoHideTimer = null;
let _confettiState = null;

function _starStorageGet(key) {
  try { return localStorage.getItem(key) === '1'; } catch (e) { return false; }
}
function _starStorageSet(key, val) {
  try {
    if (val) localStorage.setItem(key, '1');
    else localStorage.removeItem(key);
    return true;
  } catch (e) {
    return false;
  }
}
function _starGetInt(key) {
  try {
    const n = parseInt(localStorage.getItem(key) || '0', 10);
    return Number.isFinite(n) ? n : 0;
  } catch (e) {
    return 0;
  }
}
function _starSetInt(key, val) {
  try { localStorage.setItem(key, String(val)); return true; } catch (e) { return false; }
}
function recordStarEngagement() {
  _starSetInt(STAR_ACTIONS_KEY, _starGetInt(STAR_ACTIONS_KEY) + 1);
}
function _canPersistStar() {
  try {
    const probe = '__ultra_star_probe__';
    localStorage.setItem(probe, '1');
    localStorage.removeItem(probe);
    return true;
  } catch (e) {
    return false;
  }
}
const _settingsForm = document.querySelector('#settingsModal form');
if (_settingsForm) {
  _settingsForm.addEventListener('submit', () => recordStarEngagement());
}

function _ensureConfettiCanvas() {
  const w = window.innerWidth || 1280;
  const h = window.innerHeight || 720;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  if (_confettiState && document.body.contains(_confettiState.canvas)) {
    return _confettiState;
  }
  const canvas = document.createElement('canvas');
  canvas.setAttribute('aria-hidden', 'true');
  canvas.style.cssText = 'position:fixed;inset:0;width:100vw;height:100vh;pointer-events:none;z-index:9999;';
  canvas.width = Math.floor(w * dpr);
  canvas.height = Math.floor(h * dpr);
  document.body.appendChild(canvas);
  const ctx = canvas.getContext('2d');
  if (!ctx) { canvas.remove(); return null; }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  const state = { canvas, ctx, w, h, particles: [], rafId: 0, lastTs: 0, onResize: null };
  state.onResize = () => {
    const nw = window.innerWidth || 1280;
    const nh = window.innerHeight || 720;
    const ndpr = Math.min(window.devicePixelRatio || 1, 2);
    state.w = nw;
    state.h = nh;
    canvas.width = Math.floor(nw * ndpr);
    canvas.height = Math.floor(nh * ndpr);
    ctx.setTransform(ndpr, 0, 0, ndpr, 0, 0);
  };
  window.addEventListener('resize', state.onResize, { passive: true });
  _confettiState = state;
  return state;
}

function _spawnConfettiBurst(opts) {
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const state = _ensureConfettiCanvas();
  if (!state) return;

  const count = opts.particleCount || 80;
  const angleDeg = opts.angle !== undefined ? opts.angle : 90;
  const spreadDeg = opts.spread !== undefined ? opts.spread : 360;
  const startVel = opts.startVelocity || 45;
  const decay = opts.decay || 0.91;
  const gravity = (opts.gravity !== undefined ? opts.gravity : 1.0) * 3.0;
  const drift = opts.drift || 0;
  const ticks = opts.ticks || 200;
  const baseScalar = opts.scalar || 1.15;
  const shapes = opts.shapes || ['square', 'circle', 'star', 'streamer'];
  const palette = opts.colors || ['#f59e0b', '#fbbf24', '#10b981', '#34d399', '#3b82f6', '#60a5fa', '#ec4899', '#a855f7', '#f97316', '#ffffff'];

  const ox = opts.ox !== undefined ? opts.ox : state.w * (opts.x !== undefined ? opts.x : 0.5);
  const oy = opts.oy !== undefined ? opts.oy : state.h * (opts.y !== undefined ? opts.y : 0.5);
  const radAngle = angleDeg * (Math.PI / 180);
  const radSpread = spreadDeg * (Math.PI / 180);

  for (let i = 0; i < count; i++) {
    const scalar = baseScalar * (0.85 + Math.random() * 0.65);
    state.particles.push({
      x: ox,
      y: oy,
      wobble: Math.random() * 10,
      wobbleSpeed: Math.min(0.12, Math.random() * 0.1 + 0.05),
      velocity: startVel * 0.5 + Math.random() * startVel,
      angle2D: -radAngle + (0.5 * radSpread - Math.random() * radSpread),
      tiltAngle: (Math.random() * 0.5 + 0.25) * Math.PI,
      tiltSpeed: 0.08 + Math.random() * 0.06,
      color: palette[i % palette.length],
      shape: shapes[Math.floor(Math.random() * shapes.length)],
      tick: 0,
      totalTicks: ticks,
      decay,
      drift,
      gravity,
      scalar,
      ovalScalar: 0.65,
      random: Math.random() + 2,
      tiltSin: 0,
      tiltCos: 0,
      wobbleX: ox,
      wobbleY: oy,
    });
  }

  if (state.rafId) return;
  state.lastTs = performance.now();

  const drawStar = (c, rInner, rOuter) => {
    c.beginPath();
    let rot = (Math.PI / 2) * 3;
    const step = Math.PI / 5;
    for (let i = 0; i < 5; i++) {
      c.lineTo(Math.cos(rot) * rOuter, Math.sin(rot) * rOuter);
      rot += step;
      c.lineTo(Math.cos(rot) * rInner, Math.sin(rot) * rInner);
      rot += step;
    }
    c.closePath();
    c.fill();
  };

  const stepFrame = (now) => {
    const dt = Math.min(2.2, Math.max(0.25, (now - state.lastTs) / 16.6667));
    state.lastTs = now;
    const ctx = state.ctx;
    ctx.clearRect(0, 0, state.w, state.h);

    const alive = [];
    for (const p of state.particles) {
      p.tick += dt;
      if (p.tick >= p.totalTicks) continue;

      p.x += (Math.cos(p.angle2D) * p.velocity + p.drift) * dt;
      p.y += (Math.sin(p.angle2D) * p.velocity + p.gravity) * dt;
      p.velocity *= Math.pow(p.decay, dt);
      p.wobble += p.wobbleSpeed * dt;
      p.wobbleX = p.x + 11 * p.scalar * Math.cos(p.wobble);
      p.wobbleY = p.y + 11 * p.scalar * Math.sin(p.wobble);
      p.tiltAngle += p.tiltSpeed * dt;
      p.tiltSin = Math.sin(p.tiltAngle);
      p.tiltCos = Math.cos(p.tiltAngle);
      p.random = Math.random() + 2;

      const progress = p.tick / p.totalTicks;
      const alpha = progress > 0.58 ? Math.max(0, 1 - Math.pow((progress - 0.58) / 0.42, 1.4)) : 1;

      const x1 = p.x + p.random * p.tiltCos;
      const y1 = p.y + p.random * p.tiltSin;
      const x2 = p.wobbleX + p.random * p.tiltCos;
      const y2 = p.wobbleY + p.random * p.tiltSin;

      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.fillStyle = p.color;
      ctx.strokeStyle = p.color;

      if (p.shape === 'circle') {
        ctx.beginPath();
        const rx = Math.max(1.5, Math.abs(x2 - x1) * p.ovalScalar);
        const ry = Math.max(1.5, Math.abs(y2 - y1) * p.ovalScalar);
        ctx.ellipse(p.x, p.y, rx, ry, (Math.PI / 10) * p.wobble, 0, Math.PI * 2);
        ctx.fill();
      } else if (p.shape === 'star') {
        ctx.translate(p.x, p.y);
        ctx.rotate(p.tiltAngle);
        ctx.scale(1, Math.max(0.35, Math.abs(p.tiltCos)));
        drawStar(ctx, 4.5 * p.scalar, 9.5 * p.scalar);
      } else if (p.shape === 'streamer') {
        ctx.beginPath();
        ctx.lineWidth = Math.max(2, 2.8 * p.scalar);
        ctx.lineCap = 'round';
        ctx.moveTo(p.x, p.y);
        const mx = (p.x + p.wobbleX) * 0.5 + p.tiltSin * 7 * p.scalar;
        const my = (p.y + p.wobbleY) * 0.5 + p.tiltCos * 7 * p.scalar;
        ctx.quadraticCurveTo(mx, my, p.wobbleX + (p.wobbleX - p.x), p.wobbleY + (p.wobbleY - p.y));
        ctx.stroke();
      } else {
        ctx.beginPath();
        ctx.moveTo(Math.floor(p.x), Math.floor(p.y));
        ctx.lineTo(Math.floor(p.wobbleX), Math.floor(y1));
        ctx.lineTo(Math.floor(x2), Math.floor(y2));
        ctx.lineTo(Math.floor(x1), Math.floor(p.wobbleY));
        ctx.closePath();
        ctx.fill();
      }
      ctx.restore();
      alive.push(p);
    }
    state.particles = alive;
    if (alive.length > 0) {
      state.rafId = requestAnimationFrame(stepFrame);
    } else {
      window.removeEventListener('resize', state.onResize);
      state.canvas.remove();
      _confettiState = null;
    }
  };
  state.rafId = requestAnimationFrame(stepFrame);
}

function celebrateConfetti(anchorEl) {
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const w = window.innerWidth || 1280;
  const h = window.innerHeight || 720;
  let ox = w * 0.84;
  let oy = h * 0.16;
  if (anchorEl && typeof anchorEl.getBoundingClientRect === 'function') {
    const rect = anchorEl.getBoundingClientRect();
    if (rect.width > 0 || rect.height > 0) {
      ox = rect.left + rect.width * 0.5;
      oy = rect.top + rect.height * 0.45;
    }
  }
  _spawnConfettiBurst({
    ox, oy, particleCount: 180, angle: 90, spread: 360,
    startVelocity: 54, decay: 0.912, gravity: 1.05, ticks: 230, scalar: 1.28,
  });
  setTimeout(() => {
    _spawnConfettiBurst({
      x: 0.08, y: 0.68, particleCount: 70, angle: 58, spread: 64,
      startVelocity: 64, decay: 0.91, gravity: 1.0, drift: 0.2, ticks: 220, scalar: 1.22,
    });
    _spawnConfettiBurst({
      x: 0.92, y: 0.68, particleCount: 70, angle: 122, spread: 64,
      startVelocity: 64, decay: 0.91, gravity: 1.0, drift: -0.2, ticks: 220, scalar: 1.22,
    });
  }, 150);
  setTimeout(() => {
    _spawnConfettiBurst({
      ox, oy, particleCount: 45, angle: 90, spread: 360,
      startVelocity: 36, decay: 0.915, gravity: 0.85, ticks: 210, scalar: 1.38,
      shapes: ['star', 'circle'], colors: ['#fbbf24', '#fde047', '#f59e0b', '#fffbeb'],
    });
  }, 320);
}

function dismissStarPrompt(persist = true) {
  if (_starAutoHideTimer) { clearTimeout(_starAutoHideTimer); _starAutoHideTimer = null; }
  const box = document.getElementById('starPrompt');
  if (box) box.classList.remove('show');
  if (persist) {
    _starStorageSet(STAR_DISMISSED_KEY, true);
    fetch('/api/github-star-dismiss', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ csrf: CSRF_TOKEN }),
    }).catch(() => undefined);
  }
}

function resetStarPrompt() {
  if (_starAutoHideTimer) { clearTimeout(_starAutoHideTimer); _starAutoHideTimer = null; }
  const box = document.getElementById('starPrompt');
  const icon = document.getElementById('starPromptIcon');
  const title = document.getElementById('starPromptTitle');
  const desc = document.getElementById('starPromptDesc');
  const actions = document.getElementById('starPromptActions');
  if (box) box.classList.remove('is-thanks');
  if (icon) icon.innerHTML = STAR_I18N.starIcon;
  if (title) title.textContent = STAR_I18N.promptTitle;
  if (desc) desc.textContent = STAR_I18N.promptDesc;
  if (actions) {
    actions.innerHTML = '';
    const dismissBtn = document.createElement('button');
    dismissBtn.type = 'button';
    dismissBtn.className = 'btn xs ghost';
    dismissBtn.textContent = STAR_I18N.dismiss;
    dismissBtn.onclick = () => dismissStarPrompt(true);
    const ctaBtn = document.createElement('button');
    ctaBtn.type = 'button';
    ctaBtn.className = 'btn xs star-cta';
    ctaBtn.id = 'starActionBtn';
    ctaBtn.textContent = STAR_I18N.cta;
    ctaBtn.onclick = () => starInPlace();
    actions.append(dismissBtn, ctaBtn);
  }
}

function showThanksInPlace() {
  if (_starAutoHideTimer) clearTimeout(_starAutoHideTimer);
  const box = document.getElementById('starPrompt');
  const icon = document.getElementById('starPromptIcon');
  const title = document.getElementById('starPromptTitle');
  const desc = document.getElementById('starPromptDesc');
  const actions = document.getElementById('starPromptActions');
  if (box) { box.classList.add('show'); box.classList.add('is-thanks'); }
  if (icon) icon.innerHTML = STAR_I18N.sparkleIcon;
  if (title) title.textContent = STAR_I18N.thanksTitle;
  if (desc) desc.textContent = STAR_I18N.thanksDesc;
  if (actions) {
    actions.innerHTML = '';
    const link = document.createElement('a');
    link.className = 'btn xs ghost';
    link.href = GITHUB_REPO_URL;
    link.target = '_blank';
    link.rel = 'noreferrer';
    link.textContent = 'GitHub';
    actions.appendChild(link);
  }
  _starAutoHideTimer = setTimeout(() => dismissStarPrompt(false), 5000);
}

async function starInPlace() {
  const box = document.getElementById('starPrompt');
  const btn = document.getElementById('starActionBtn');
  if (btn) { btn.disabled = true; btn.textContent = STAR_I18N.starring; }
  try {
    const resp = await fetch('/api/github-star', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ csrf: CSRF_TOKEN }),
    });
    const data = await resp.json().catch(() => ({ ok: false, fallback_url: GITHUB_REPO_URL }));
    if (data.ok && data.starred) {
      _starStorageSet(STAR_DONE_KEY, true);
      _starStorageSet(STAR_DISMISSED_KEY, true);
      showThanksInPlace();
      celebrateConfetti(box);
      return;
    }
    const targetUrl = data.fallback_url || GITHUB_REPO_URL;
    const canPopup = !navigator.userActivation || navigator.userActivation.isActive !== false;
    const opened = canPopup ? window.open(targetUrl, '_blank', 'noopener,noreferrer') : null;
    if (opened) {
      _starStorageSet(STAR_DISMISSED_KEY, true);
      showThanksInPlace();
      celebrateConfetti(box);
      return;
    }
    if (btn) {
      btn.disabled = false;
      btn.textContent = STAR_I18N.openGh;
      btn.onclick = () => {
        window.open(targetUrl, '_blank', 'noopener,noreferrer');
        _starStorageSet(STAR_DISMISSED_KEY, true);
        showThanksInPlace();
        celebrateConfetti(box);
      };
    }
  } catch (err) {
    if (btn) {
      btn.disabled = false;
      btn.textContent = STAR_I18N.openGh;
      btn.onclick = () => {
        window.open(GITHUB_REPO_URL, '_blank', 'noopener,noreferrer');
        _starStorageSet(STAR_DISMISSED_KEY, true);
        showThanksInPlace();
        celebrateConfetti(box);
      };
    }
  }
}

function isMatureEnough(info) {
  const m = (info && info.maturity) || {};
  const ageHours = Number(m.age_hours || 0);
  const taskCount = Number(m.task_count || 0);
  const totalOps = Math.max(Number(m.server_ops || 0), _starGetInt(STAR_ACTIONS_KEY));
  const sessions = _starGetInt(STAR_SESSIONS_KEY);
  return (ageHours >= 0.25 && totalOps >= 5)
    || (ageHours >= 24 && (sessions >= 3 || taskCount >= 2 || totalOps >= 2))
    || (taskCount >= 3 && sessions >= 2);
}

function waitForVisibleAttention() {
  return new Promise((resolve) => {
    let calmTimer = null;
    let seenSignal = false;
    let done = false;
    const signals = ['pointermove', 'pointerdown', 'wheel', 'keydown', 'touchstart'];
    const isViewClear = () => {
      if (document.visibilityState !== 'visible' || !document.hasFocus()) return false;
      const dlg = document.getElementById('settingsModal');
      if (dlg && dlg.open) return false;
      const upd = document.getElementById('updatePrompt');
      if (upd && upd.classList.contains('show')) return false;
      const toast = document.getElementById('toast');
      if (toast && toast.classList.contains('show')) return false;
      return true;
    };
    const cleanup = () => {
      if (calmTimer) clearTimeout(calmTimer);
      signals.forEach((ev) => window.removeEventListener(ev, onSignal, true));
      document.removeEventListener('visibilitychange', scheduleCheck);
      window.removeEventListener('focus', scheduleCheck);
    };
    const scheduleCheck = () => {
      if (done) return;
      if (calmTimer) clearTimeout(calmTimer);
      if (!seenSignal || !isViewClear()) {
        if (seenSignal && document.visibilityState === 'visible' && document.hasFocus()) {
          calmTimer = setTimeout(scheduleCheck, 600);
        }
        return;
      }
      calmTimer = setTimeout(() => {
        if (done) return;
        if (!isViewClear()) {
          scheduleCheck();
          return;
        }
        done = true;
        cleanup();
        resolve();
      }, 1200);
    };
    const onSignal = () => {
      seenSignal = true;
      scheduleCheck();
    };
    signals.forEach((ev) => window.addEventListener(ev, onSignal, { capture: true, passive: true }));
    document.addEventListener('visibilitychange', scheduleCheck);
    window.addEventListener('focus', scheduleCheck);
  });
}

(function initStarPrompt() {
  const canPersist = _canPersistStar();
  if (canPersist) {
    const nowMs = Date.now();
    const lastMs = _starGetInt(STAR_LAST_SESSION_KEY);
    if (!lastMs || (nowMs - lastMs) > 30 * 60 * 1000) {
      _starSetInt(STAR_SESSIONS_KEY, _starGetInt(STAR_SESSIONS_KEY) + 1);
      _starSetInt(STAR_LAST_SESSION_KEY, nowMs);
    }
  }

  const params = new URLSearchParams(window.location.search || '');
  if (params.get('star_preview') === '1') {
    setTimeout(() => {
      resetStarPrompt();
      const box = document.getElementById('starPrompt');
      if (box) box.classList.add('show');
    }, 600);
    return;
  }

  fetch('/api/github-star')
    .then((r) => (r.ok ? r.json() : null))
    .then(async (info) => {
      if (!info) return;
      if (info.starred === true) {
        _starStorageSet(STAR_DONE_KEY, true);
        _starStorageSet(STAR_DISMISSED_KEY, true);
        return;
      }
      if (info.maturity && info.maturity.dismissed) {
        _starStorageSet(STAR_DISMISSED_KEY, true);
        return;
      }
      if (!canPersist || _starStorageGet(STAR_DISMISSED_KEY)) return;
      if (!isMatureEnough(info)) return;
      await waitForVisibleAttention();
      if (_starStorageGet(STAR_DISMISSED_KEY) || _starStorageGet(STAR_DONE_KEY)) return;
      resetStarPrompt();
      const box = document.getElementById('starPrompt');
      if (box) box.classList.add('show');
    })
    .catch(() => undefined);
})();

let _activeUpdateRef = '';
function _updDismissKey(ref) {
  return 'ultra:update-dismissed:' + String(ref || 'latest');
}
function dismissUpdatePrompt(persist = true) {
  const box = document.getElementById('updatePrompt');
  if (box) box.classList.remove('show');
  if (persist && _activeUpdateRef) {
    try { localStorage.setItem(_updDismissKey(_activeUpdateRef), '1'); } catch (e) {}
  }
}
function showUpdatePrompt(info) {
  const box = document.getElementById('updatePrompt');
  const pill = document.getElementById('updateVerPill');
  const desc = document.getElementById('updatePromptDesc');
  const diffLink = document.getElementById('updateDiffLink');
  const btn = document.getElementById('updateActionBtn');
  if (!box || !info) return;

  _activeUpdateRef = String(info.target_ref || info.remote_short_sha || '');
  const localLabel = 'v' + String(info.local_version || APP_VERSION);
  if (pill) {
    if (info.channel === 'release' && info.release_tag) {
      pill.textContent = localLabel + ' -> ' + info.release_tag;
    } else if (info.behind_count) {
      pill.textContent = UPDATE_I18N.behind.replace('{n}', String(info.behind_count));
    } else {
      pill.textContent = _activeUpdateRef || 'main';
    }
  }
  const summary = info.release_summary || info.commit_message || '';
  const blockMsg = PAGE_LANG === 'en' ? (info.block_reason_en || info.block_reason || '') : (info.block_reason || '');
  if (desc) {
    if (!info.can_auto_update && blockMsg) {
      desc.textContent = (summary ? summary + ' · ' : '') + blockMsg;
    } else {
      desc.textContent = summary || GITHUB_REPO_URL;
    }
  }
  if (diffLink) {
    diffLink.href = info.compare_url || GITHUB_REPO_URL;
  }
  if (btn) {
    btn.style.display = info.can_auto_update ? 'inline-flex' : 'none';
    btn.disabled = false;
    btn.textContent = UPDATE_I18N.now;
  }
  const starBox = document.getElementById('starPrompt');
  if (starBox) starBox.classList.remove('show');
  box.classList.add('show');
}

async function checkForUpdates(force = true) {
  const btn = document.getElementById('btnCheckUpdate');
  const origHtml = btn ? btn.innerHTML : '';
  if (btn) {
    btn.disabled = true;
    const lbl = btn.querySelector('span');
    if (lbl) lbl.textContent = UPDATE_I18N.checking;
  }
  try {
    const resp = await fetch('/api/update-status' + (force ? '?force=1' : ''));
    const info = await resp.json().catch(() => null);
    if (!info || !info.ok) {
      showToast(UPDATE_I18N.offline, false);
      return;
    }
    if (info.update_available) {
      try { localStorage.removeItem(_updDismissKey(info.target_ref || info.remote_short_sha)); } catch (e) {}
      showUpdatePrompt(info);
    } else {
      showToast(UPDATE_I18N.latest + ' (v' + String(info.local_version || APP_VERSION) + ')', true);
    }
  } catch (err) {
    showToast(UPDATE_I18N.offline, false);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = origHtml;
    }
  }
}

async function _pollHealthAndReload(msgText) {
  for (let i = 0; i < 20; i++) {
    await new Promise((r) => setTimeout(r, 800));
    try {
      const r = await fetch('/api/health', { cache: 'no-store' });
      if (r.ok) {
        try { sessionStorage.setItem('fleet_flash', JSON.stringify({ text: msgText, ok: true })); } catch (e) {}
        window.location.reload();
        return;
      }
    } catch (e) {}
  }
  window.location.reload();
}

async function runSelfUpdate() {
  const btn = document.getElementById('updateActionBtn');
  if (btn) { btn.disabled = true; btn.textContent = UPDATE_I18N.updating; }
  try {
    const resp = await fetch('/api/self-update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ csrf: CSRF_TOKEN }),
    });
    const data = await resp.json().catch(() => ({ ok: resp.ok, message: resp.statusText }));
    const msgText = data.message || (data.ok ? 'Updated' : 'Update failed');
    if (data.ok && data.restarting) {
      if (btn) btn.textContent = UPDATE_I18N.restarting;
      showToast(msgText, true);
      setTimeout(() => { _pollHealthAndReload(msgText); }, 900);
      return;
    }
    showToast(msgText, !!data.ok);
    if (data.ok) {
      dismissUpdatePrompt(false);
    } else if (btn) {
      btn.disabled = false;
      btn.textContent = UPDATE_I18N.now;
    }
  } catch (err) {
    showToast(String(err), false);
    if (btn) { btn.disabled = false; btn.textContent = UPDATE_I18N.now; }
  }
}

(function initUpdateCheck() {
  const params = new URLSearchParams(window.location.search || '');
  if (params.get('update_preview') === '1') {
    setTimeout(() => {
      showUpdatePrompt({
        ok: true,
        update_available: true,
        channel: 'release',
        target_ref: 'v3.1.0',
        release_tag: 'v3.1.0',
        release_summary: PAGE_LANG === 'en' ? 'Spatial Observatory & one-click GitHub self-update.' : 'Spatial Observatory 驾驶舱与一键自动检查更新上线。',
        compare_url: GITHUB_REPO_URL + '/releases',
        local_version: APP_VERSION,
        can_auto_update: true,
      });
    }, 450);
    return;
  }
  fetch('/api/update-status')
    .then((r) => (r.ok ? r.json() : null))
    .then((info) => {
      if (!info || !info.ok || !info.update_available) return;
      const ref = String(info.target_ref || info.remote_short_sha || '');
      try {
        if (ref && localStorage.getItem(_updDismissKey(ref)) === '1') return;
      } catch (e) {}
      showUpdatePrompt(info);
    })
    .catch(() => undefined);
})();
"""


def _render_gauge_panel(pool: dict[str, Any], is_en: bool) -> str:
    pool_id = str(pool.get("pool") or "")
    title = _pick_lang(pool, "title", is_en)
    windows = [w for w in (pool.get("windows") or []) if isinstance(w, dict)] if isinstance(pool.get("windows"), list) else []
    kicker = _pick_lang(pool, "kicker", is_en) or _pick_lang(pool, "detail", is_en)

    if len(windows) >= 2:
        w0, w1 = windows[0], windows[1]
        p0 = max(0.0, min(100.0, float(w0.get("pct") or 0.0)))
        p1 = max(0.0, min(100.0, float(w1.get("pct") or 0.0)))
        svg = _concentric_gauge_svg(p0, p1, _bar_color(pool_id, p0), _bar_color(pool_id, p1))
        win_rows = "".join(
            f'<div class="quota-win">'
            f'<div class="quota-win-row">'
            f'<span class="quota-win-lbl">{html.escape(_pick_lang(w, "label", is_en))}</span>'
            f'<span class="quota-win-val num">{max(0.0, min(100.0, float(w.get("pct") or 0.0))):.1f}%</span>'
            f'</div>'
            f'<div class="quota-win-sub">{html.escape(_pick_lang(w, "reset", is_en))}</div>'
            f'</div>'
            for w in windows
        )
        body = f'<div class="quota-windows">{win_rows}</div>'
    else:
        pct = pool.get("pct")
        p_val = max(0.0, min(100.0, float(pct))) if isinstance(pct, (int, float)) else None
        svg = _concentric_gauge_svg(
            p_val,
            None,
            _bar_color(pool_id, p_val if p_val is not None else 50.0),
            "var(--ok)",
        )
        body = f'<div class="quota-win-val num" style="font-size:17px;margin-bottom:3px;">{html.escape(_pick_lang(pool, "primary", is_en))}</div>'

    return (
        f'<div class="gauge-panel">'
        f'{svg}'
        f'<div class="gauge-info">'
        f'<div class="gauge-name">{html.escape(title)}</div>'
        f'{body}'
        f'<div class="gauge-kicker">{html.escape(kicker)}</div>'
        f'</div>'
        f'</div>'
    )


def render_cockpit_page(
    *,
    runtime: RuntimeSecrets,
    csrf_token: str,
    awaiting: list[dict[str, Any]],
    others: list[dict[str, Any]],
    pools: list[dict[str, Any]],
    advisor: list[dict[str, Any]],
    bridges: list[dict[str, Any]],
    repos: list[dict[str, Any]],
    routing: dict[str, Any] | None = None,
    lens: dict[str, Any] | None = None,
    capabilities: dict[str, Any] | None = None,
    msg: str = "",
    ok_flag: str = "",
    privacy: bool = False,
    lang: str = "zh",
) -> str:
    """Render the Spatial Observatory Telemetry & Governance Cockpit HTML page."""
    is_en = lang == "en"
    use_lang = "en" if is_en else "zh"
    t = STRINGS[use_lang]
    other_lang = "zh" if is_en else "en"
    lang_label = "中文" if is_en else "EN"
    next_privacy = "0" if privacy else "1"
    priv_val = "1" if privacy else "0"

    state_inputs = (
        f'<input type="hidden" name="csrf" value="{csrf_token}" />'
        f'<input type="hidden" name="lang" value="{use_lang}" />'
        f'<input type="hidden" name="privacy" value="{priv_val}" />'
    )

    banner_html = ""
    if msg:
        cls = "banner ok" if ok_flag == "1" else "banner err"
        icon = ICONS["check"] if ok_flag == "1" else "!"
        banner_html = f'<div class="{cls}">{icon}<span>{html.escape(msg)}</span></div>'

    caps = capabilities or {}
    wakeup_ready = bool(caps.get("wakeup_cli", True))
    gcp_sync_ready = bool(caps.get("gcp_sync_cli", True))

    agy_bridge = next((b for b in bridges if b.get("id") == "antigravity"), None)
    runtime_tag = t["runtime_fallback"]
    if agy_bridge:
        st_txt = _clean_badge(_pick_lang(agy_bridge, "status", is_en))
        runtime_tag = f"Antigravity 2.0 · {st_txt}" if st_txt else "Antigravity 2.0"

    # Split pools: 2 primary Antigravity pools -> Hero Gauges; rest -> 5-Tile Resource Strip
    agy_pools = [p for p in pools if str(p.get("pool") or "") in ("agy_gemini_weekly", "agy_claude_5h")]
    agy_pools.sort(key=lambda p: 0 if p.get("pool") == "agy_gemini_weekly" else 1)
    ext_pools = [p for p in pools if str(p.get("pool") or "") not in ("agy_gemini_weekly", "agy_claude_5h")]
    ext_pools.sort(key=lambda p: _EXT_POOL_ORDER.get(str(p.get("pool") or ""), 99))

    if agy_pools:
        gauges_html = "".join(_render_gauge_panel(p, is_en) for p in agy_pools)
    else:
        gauges_html = f'<div style="font-size:12.5px;color:var(--muted);">{html.escape(t["runtime_fallback"])}</div>'

    # Routing Verdict Plate
    roi_html = ""
    if isinstance(lens, dict) and float(lens.get("d7_usd") or 0) > 0:
        d7 = float(lens["d7_usd"])
        roi = d7 / 249.99
        roi_html = f'<span class="roi-stat num" title="Agy-Lens 7d API-equivalent value">7d ROI ${d7:,.0f} ({roi:.2f}×)</span>'

    if isinstance(routing, dict) and routing:
        mode = str(routing.get("mode") or "balanced")
        headline = str(routing.get("headline_en" if is_en else "headline_zh") or "")
        reason = str(routing.get("reason_en" if is_en else "reason_zh") or "")
        rec_code = str(routing.get("recommended_coding_model") or "")
        rec_triage = str(routing.get("recommended_triage_model") or "")
        mode_tone = "warn" if mode == "5h_harvest" else ("danger" if mode == "conserve_weekly" else "live")
        mode_label = {
            "5h_harvest": "5H HARVEST" if is_en else "5h 滚动收割",
            "conserve_weekly": "CONSERVE WEEKLY" if is_en else "周池保卫模式",
            "balanced": "BALANCED" if is_en else "双池均衡",
        }.get(mode, mode.upper())
        wakeup_btn = (
            f'<form method="POST" action="/api/wakeup" data-async="1" style="margin:0">'
            f"{state_inputs}"
            f'<button class="btn primary xs" type="submit">{ICONS["bolt"]} {html.escape(t["btn_wakeup"])}</button>'
            f"</form>"
            if wakeup_ready and bool(routing.get("wakeup_recommended"))
            else ""
        )
        verdict_plate_html = f"""
        <section class="vb-card verdict-plate">
          <div>
            <div class="plate-head" style="margin-bottom:8px;">
              <span class="source-badge {mode_tone}">{html.escape(mode_label)}</span>
              {roi_html}
            </div>
            <h2 class="verdict-headline">{html.escape(headline)}</h2>
            <p class="verdict-reason">{html.escape(reason)}</p>
          </div>
          <div class="verdict-foot">
            <div class="model-pills">
              <button type="button" class="model-chip" onclick="copyModelId({html.escape(json.dumps(rec_code))})" title="{html.escape(t['copy_model_tip'])}">
                <span class="chip-lbl">{html.escape(t['lbl_rec_coding'])}</span>
                <code>{html.escape(rec_code)}</code>
                {ICONS['copy']}
              </button>
              <button type="button" class="model-chip" onclick="copyModelId({html.escape(json.dumps(rec_triage))})" title="{html.escape(t['copy_model_tip'])}">
                <span class="chip-lbl">{html.escape(t['lbl_rec_triage'])}</span>
                <code>{html.escape(rec_triage)}</code>
                {ICONS['copy']}
              </button>
            </div>
            {wakeup_btn}
          </div>
        </section>
        """
    else:
        verdict_plate_html = f"""
        <section class="vb-card verdict-plate">
          <div>
            <div class="plate-head">
              <h2 class="plate-title">{html.escape(t['sec_routing'])}</h2>
              {roi_html}
            </div>
            <p class="verdict-reason">{html.escape(t['advisor_empty'])}</p>
          </div>
        </section>
        """

    # Middle 5-Tile Resource Strip + optional GCP grants table
    paid_local_used = 0.0
    grants_accordion_html = ""
    tile_cards: list[str] = []
    for p in ext_pools:
        pool_id = str(p.get("pool") or "")
        pct = p.get("pct")
        bar_html = ""
        if pct is not None:
            p_val = max(0.0, min(100.0, float(pct)))
            color = _bar_color(pool_id, p_val)
            bar_html = f'<div class="bar"><div style="width:{p_val:.1f}%;background:{color}"></div></div>'

        tone = html.escape(str(p.get("badge_tone", "muted")))
        p_title = _pick_lang(p, "title", is_en)
        p_badge = _clean_badge(_pick_lang(p, "badge", is_en))
        p_primary = _pick_lang(p, "primary", is_en)
        p_detail = _pick_lang(p, "detail", is_en)
        tile_warn_cls = " tone-warn" if tone == "warn" else ""

        tile_actions = ""
        if pool_id == "paid_gemini_api":
            paid_meta = p.get("meta") or {}
            paid_local_used = float(paid_meta.get("local_used_usd") or 0.0)
            grants = paid_meta.get("grants") or []
            if isinstance(grants, list) and grants:
                g_rows = "".join(
                    f"<tr><th class='num'>${float(g.get('remaining', 0)):.2f} / ${float(g.get('original', 0)):.2f}</th>"
                    f"<td data-col='{html.escape('已扣' if not is_en else 'Used')}' class='num'>-${float(g.get('used', 0)):.2f}</td>"
                    f"<td data-col='{html.escape('到期日' if not is_en else 'Expires')}' class='num'>{html.escape(str(g.get('end_date') or '-'))}</td></tr>"
                    for g in grants
                )
                grants_accordion_html = (
                    f'<details class="mwg-acc" style="margin-top:12px;">'
                    f'<summary><span class="sum-left">{html.escape(t["grants_summary"])}</span><span class="count-pill">{len(grants)}</span></summary>'
                    f'<div class="acc-body"><div class="table-wrap" tabindex="0" role="region" aria-label="{html.escape(t["grants_summary"])}">'
                    f'<table><thead><tr><th>{"剩余 / 总额" if not is_en else "Rem / Orig"}</th><th>{"已扣" if not is_en else "Used"}</th><th>{"到期日" if not is_en else "Expires"}</th></tr></thead>'
                    f'<tbody>{g_rows}</tbody></table></div></div></details>'
                )
            sync_btn = (
                f'<form method="POST" action="/api/sync-gcp-credits" data-async="1" style="margin:0">'
                f"{state_inputs}"
                f'<button type="submit" class="btn xs primary">{ICONS["refresh"]} {html.escape(t["sync_gcp"])}</button>'
                f"</form>"
                if gcp_sync_ready
                else ""
            )
            tile_actions = (
                f'<div class="tile-actions">'
                f"{sync_btn}"
                f'<a class="inline-link" href="https://console.cloud.google.com/billing/credits" target="_blank" rel="noreferrer">{html.escape(t["gcp_credits"])} {ICONS["arrow_up_right"]}</a>'
                f"</div>"
            )

        tile_cards.append(
            f"""
            <article class="vb-tile{tile_warn_cls}">
              <div>
                <div class="tile-top">
                  <h3 class="tile-title">{html.escape(p_title)}</h3>
                  <span class="source-badge {tone}">{html.escape(p_badge)}</span>
                </div>
                <div class="tile-metric num">{html.escape(p_primary)}</div>
                {bar_html}
                <div class="tile-detail">{html.escape(p_detail)}</div>
              </div>
              {tile_actions}
            </article>
            """
        )

    # Actionable Burn Advisor Rail (exclude redundant ROI card in UI)
    actionable_advisor = [
        item
        for item in advisor
        if item.get("kind") != "roi" and str(item.get("command") or "") != "agy-lens"
    ]
    advisor_rows: list[str] = []
    for item in actionable_advisor:
        sev = html.escape(str(item.get("severity", "info")))
        sev_badge = "warn" if sev == "urgent" else ("stale" if sev == "opportunity" else "local")
        cmd_hint = str(item.get("command") or "")
        run_btn = ""
        if cmd_hint == "ultra wakeup" and wakeup_ready:
            run_btn = (
                f'<form method="POST" action="/api/wakeup" data-async="1" style="margin:0">'
                f"{state_inputs}"
                f'<button type="submit" class="btn xs primary">{ICONS["bolt"]} {html.escape(t["run_now"])}</button></form>'
            )
        elif cmd_hint == "ultra sync-gcp-credits" and gcp_sync_ready:
            run_btn = (
                f'<form method="POST" action="/api/sync-gcp-credits" data-async="1" style="margin:0">'
                f"{state_inputs}"
                f'<button type="submit" class="btn xs primary">{ICONS["refresh"]} {html.escape(t["run_now"])}</button></form>'
            )

        if cmd_hint.startswith("https://"):
            cmd_html = f'<div class="adv-cmds"><a class="inline-link" href="{html.escape(cmd_hint)}" target="_blank" rel="noreferrer">{html.escape(cmd_hint)} {ICONS["arrow_up_right"]}</a></div>'
        elif cmd_hint:
            cmd_html = (
                f'<div class="adv-cmds">'
                f'<code>{html.escape(cmd_hint)}</code>'
                f'<button type="button" class="btn xs ghost" onclick="copyText(this, {html.escape(json.dumps(cmd_hint))})">{ICONS["copy"]} {html.escape(t["copy_cmd"])}</button>'
                f"{run_btn}</div>"
            )
        else:
            cmd_html = ""

        advisor_rows.append(
            f"""
            <div class="adv-row">
              <div style="min-width:0;flex:1;">
                <span class="source-badge {sev_badge}">{html.escape(_pick_lang(item, 'pool', is_en))}</span>
                <div class="adv-title">{html.escape(_pick_lang(item, 'title', is_en))}</div>
                <div class="adv-action">{html.escape(_pick_lang(item, 'action', is_en))}</div>
                {cmd_html}
              </div>
            </div>
            """
        )
    advisor_body = (
        f'<div class="adv-list">{"".join(advisor_rows)}</div>'
        if advisor_rows
        else f'<div style="font-size:12.5px;color:var(--muted);">{html.escape(t["advisor_empty"])}</div>'
    )

    # Native Antigravity Stack (Right Plate)
    stack_order = {"antigravity": 0, "agy_lens": 1, "agent_desktop": 2, "apprise": 3}
    ordered_bridges = sorted(bridges, key=lambda b: stack_order.get(str(b.get("id") or ""), 99))
    stack_rows: list[str] = []
    for b in ordered_bridges:
        tone = html.escape(str(b.get("tone", "muted")))
        b_name = _pick_lang(b, "name", is_en)
        b_status = _clean_badge(_pick_lang(b, "status", is_en))
        b_detail = _pick_lang(b, "detail", is_en)
        stack_rows.append(
            f"""
            <div class="stack-row">
              <div style="min-width:0;flex:1;">
                <div class="stack-name">{html.escape(b_name)}</div>
                <div class="stack-detail">{html.escape(b_detail)}</div>
              </div>
              <span class="source-badge {tone}">{html.escape(b_status)}</span>
            </div>
            """
        )

    # Yellow-Zone Approvals
    if awaiting:
        task_cards = []
        for tk in awaiting:
            wt_disp = redact_path(str(tk["worktree_path"] or ""), privacy=privacy)
            task_cards.append(
                f"""
                <div class="task-card">
                  <div class="task-head">
                    <span class="source-badge stale">{html.escape(tk['pool'])}</span>
                    <strong>[{html.escape(tk['project'])}] {html.escape(tk['title'])}</strong>
                    <code>{html.escape(tk['task_id'])}</code>
                  </div>
                  <p class="meta"><code>{html.escape(tk['branch_name'])}</code> @ <code>{html.escape(tk['head_sha'][:8])}</code> · Worktree: <code>{html.escape(wt_disp)}</code></p>
                  <details class="mwg-acc" open>
                    <summary><span class="sum-left">{html.escape(t['diff_verify'])}</span></summary>
                    <div class="acc-body"><pre>{html.escape(tk['diff_stat'] or '')}\n\n--- VERIFY ---\n{html.escape(tk['verify_output'] or '')}</pre></div>
                  </details>
                  <div class="actions">
                    <form method="POST" action="/api/approve" style="display:inline">
                      {state_inputs}
                      <input type="hidden" name="task_id" value="{html.escape(tk['task_id'])}" />
                      <button class="btn primary" type="submit">{ICONS['check']} {html.escape(t['btn_approve'])}</button>
                    </form>
                    <form method="POST" action="/api/revise" class="revise-form">
                      {state_inputs}
                      <input type="hidden" name="task_id" value="{html.escape(tk['task_id'])}" />
                      <input type="text" name="note" placeholder="{html.escape(t['placeholder_revise'])}" />
                      <button class="btn" type="submit">{html.escape(t['btn_revise'])}</button>
                    </form>
                  </div>
                </div>
                """
            )
        gate_section = f"""
        <section style="margin-bottom:14px;">
          <div class="gate-bar">
            <span class="gate-label">{html.escape(t['sec_awaiting'])}</span>
            <span class="count-pill warn">{len(awaiting)}</span>
          </div>
          {"".join(task_cards)}
        </section>
        """
    else:
        gate_section = f"""
        <div class="gate-bar">
          <span class="gate-label">{html.escape(t['sec_awaiting'])}</span>
          <span class="source-badge live">{html.escape(t['awaiting_clear'])}</span>
        </div>
        """

    repo_rows = "".join(
        f"<tr><th>{html.escape(r['project'])}</th>"
        f"<td data-col='{html.escape(t['th_path'])}'><code>{html.escape(redact_path(r['local_path'], privacy=privacy))}</code></td>"
        f"<td data-col='{html.escape(t['th_summary'])}'>{html.escape(r['summary'])}</td>"
        f"<td data-col='{html.escape(t['th_updated'])}' class='num'>{html.escape(r['updated'])}</td></tr>"
        for r in repos
    )
    history_rows = "".join(
        f"<tr><th><code>{html.escape(tk['task_id'])}</code></th>"
        f"<td data-col='{html.escape(t['th_proj'])}'>{html.escape(tk['project'])}</td>"
        f"<td data-col='{html.escape(t['th_title'])}'>{html.escape(tk['title'])}</td>"
        f"<td data-col='{html.escape(t['th_status'])}'><span class='source-badge muted'>{html.escape(tk['status'])}</span></td>"
        f"<td data-col='{html.escape(t['th_updated'])}' class='num'>{html.escape(tk['updated_at'])}</td></tr>"
        for tk in others[:12]
    )

    secret_placeholder = "已配置（留空保持不变）" if not is_en else "Configured (leave blank to keep)"
    empty_placeholder = "未设置（留空不改）" if not is_en else "Not set (optional)"
    budget_val = f"{runtime.paid_api_monthly_usd:g}" if runtime.paid_api_monthly_usd > 0 else ""

    test_alert_btn = (
        f'<button type="button" class="btn xs" onclick="sendTestAlert(this, \'/api/notify-test\')">{ICONS["bell"]} {html.escape(t["btn_test_push"])}</button>'
        if runtime.notify_enabled
        else ""
    )

    star_i18n_json = json.dumps(
        {
            "promptTitle": t["star_prompt_title"],
            "promptDesc": t["star_prompt_desc"],
            "cta": t["star_cta"],
            "starring": t["star_starring"],
            "openGh": t["star_open_gh"],
            "dismiss": t["star_dismiss"],
            "thanksTitle": t["star_thanks_title"],
            "thanksDesc": t["star_thanks_desc"],
            "starIcon": ICONS["star"],
            "sparkleIcon": ICONS["sparkle"],
        },
        ensure_ascii=False,
    )
    update_i18n_json = json.dumps(
        {
            "checking": t["upd_checking"],
            "now": t["upd_now"],
            "updating": t["upd_updating"],
            "restarting": t["upd_restarting"],
            "latest": t["upd_latest"],
            "offline": t["upd_offline"],
            "behind": t["upd_behind"],
        },
        ensure_ascii=False,
    )
    js_block = (
        _JS_TEMPLATE.replace("__LOCAL_PAID_USD__", f"{paid_local_used:.6f}")
        .replace("__COPIED_LABEL__", json.dumps(t["copied"], ensure_ascii=False))
        .replace("__COPY_LABEL__", json.dumps(t["copy_cmd"], ensure_ascii=False))
        .replace("__COPY_ERR_LABEL__", json.dumps(t["copy_err"], ensure_ascii=False))
        .replace("__CSRF_TOKEN__", json.dumps(csrf_token))
        .replace("__GITHUB_REPO_URL__", json.dumps(GITHUB_REPO_URL))
        .replace("__APP_VERSION__", json.dumps(__version__))
        .replace("__STAR_I18N__", star_i18n_json)
        .replace("__UPDATE_I18N__", update_i18n_json)
        .replace("__PAGE_LANG__", json.dumps(use_lang))
    )

    privacy_icon = ICONS["eye_off"] if privacy else ICONS["eye"]
    privacy_label = t["btn_privacy_off"] if privacy else t["btn_privacy_on"]

    return f"""<!doctype html>
<html lang="{ 'en' if is_en else 'zh-CN' }">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<meta name="color-scheme" content="light dark" />
<script>
(function(){{
  try {{
    var saved = localStorage.getItem('color-scheme');
    if (!saved) {{
      var legacy = localStorage.getItem('fleet_theme');
      if (legacy === 'light' || legacy === 'dark') saved = legacy;
    }}
    if (saved === 'light' || saved === 'dark') {{
      document.querySelector('meta[name="color-scheme"]').content = saved;
      document.documentElement.setAttribute('data-theme', saved);
    }}
  }} catch (e) {{}}
}})();
</script>
<title>{html.escape(t['page_title'])}</title>
<style>
{_CSS_BLOCK}
</style>
</head>
<body>
<header class="topbar">
  <div class="topbar-inner">
    <div class="brand">
      <div class="brand-mark">{ICONS['bolt']}</div>
      <h1>{html.escape(t['page_title'])}</h1>
      <span class="runtime-pill">{html.escape(runtime_tag)}</span>
    </div>
    <div class="toolbar">
      <form method="POST" action="/api/refresh-telemetry" data-async="1" style="margin:0">
        {state_inputs}
        <button id="btnRefresh" class="btn" type="submit">{ICONS['refresh']} <span>{html.escape(t['btn_refresh'])}</span></button>
      </form>
      <button class="btn" type="button" onclick="openSettingsModal()">{ICONS['sliders']} <span>{html.escape(t['btn_settings'])}</span></button>
      <a class="btn ghost" href="/?privacy={next_privacy}&lang={use_lang}">{privacy_icon} <span>{html.escape(privacy_label)}</span></a>
      <a class="btn ghost" href="/?privacy={priv_val}&lang={other_lang}">{ICONS['globe']} <span>{lang_label}</span></a>
      <button class="btn ghost" type="button" id="themeBtn" onclick="toggleTheme()" title="{html.escape(t['btn_theme_title'])}" aria-label="{html.escape(t['btn_theme_title'])}">{ICONS['sun']}{ICONS['moon']}</button>
    </div>
  </div>
</header>

<main class="wrap">
  {banner_html}

  <div class="vb-hero">
    <section class="vb-card">
      <div class="plate-head">
        <h2 class="plate-title">{html.escape(t['sec_gauges'])}</h2>
        <span style="font-size:11.5px;color:var(--muted);">{html.escape(runtime_tag)}</span>
      </div>
      <div class="vb-gauges">{gauges_html}</div>
    </section>
    {verdict_plate_html}
  </div>

  <section class="vb-tiles" aria-label="{html.escape(t['sec_pools'])}">
    {''.join(tile_cards)}
  </section>

  <div class="vb-bottom">
    <section class="vb-card">
      <div class="plate-head">
        <h2 class="plate-title">{html.escape(t['sec_advisor'])} <span class="count-pill">{len(actionable_advisor)}</span></h2>
      </div>
      {advisor_body}
      {grants_accordion_html}
    </section>

    <section class="vb-card">
      <div class="plate-head">
        <h2 class="plate-title">{html.escape(t['sec_wheels'])} <span class="count-pill">{len(ordered_bridges)}</span></h2>
      </div>
      <div class="stack-list">{''.join(stack_rows)}</div>
    </section>
  </div>

  {gate_section}

  <details class="mwg-acc" {'open' if others else ''}>
    <summary><span class="sum-left">{html.escape(t['sec_history'])}</span><span class="count-pill">{len(others)}</span></summary>
    <div class="acc-body">
      <div class="table-wrap" tabindex="0" role="region" aria-label="{html.escape(t['sec_history'])}">
        <table>
          <thead><tr><th>{html.escape(t['th_id'])}</th><th>{html.escape(t['th_proj'])}</th><th>{html.escape(t['th_title'])}</th><th>{html.escape(t['th_status'])}</th><th>{html.escape(t['th_updated'])}</th></tr></thead>
          <tbody>{history_rows or f'<tr><td colspan="5">{html.escape(t["no_rows"])}</td></tr>'}</tbody>
        </table>
      </div>
    </div>
  </details>

  <details class="mwg-acc">
    <summary><span class="sum-left">{html.escape(t['sec_matrix'])}</span><span class="count-pill">{len(repos)}</span></summary>
    <div class="acc-body">
      <div class="table-wrap" tabindex="0" role="region" aria-label="{html.escape(t['sec_matrix'])}">
        <table>
          <thead><tr><th>{html.escape(t['th_proj'])}</th><th>{html.escape(t['th_path'])}</th><th>{html.escape(t['th_summary'])}</th><th>{html.escape(t['th_updated'])}</th></tr></thead>
          <tbody>{repo_rows or f'<tr><td colspan="4">{html.escape(t["no_rows"])}</td></tr>'}</tbody>
        </table>
      </div>
    </div>
  </details>

  <footer class="cockpit-footer">
    <span>v{html.escape(__version__)} · {html.escape(t['footer_left'])}</span>
    <div class="footer-right">
      <button type="button" class="btn xs ghost" id="btnCheckUpdate" onclick="checkForUpdates(true)">{ICONS['download']} <span>{html.escape(t['btn_check_update'])}</span></button>
      <a class="inline-link" href="{html.escape(GITHUB_REPO_URL)}" target="_blank" rel="noreferrer">{html.escape(t['github_repo'])} {ICONS['arrow_up_right']}</a>
    </div>
  </footer>
</main>

<aside id="updatePrompt" class="update-prompt" role="region" aria-label="Update Available">
  <div class="star-head">
    <div class="star-title-wrap">
      <span class="update-badge-icon">{ICONS['download']}</span>
      <strong>{html.escape(t['upd_title'])}</strong>
      <span class="update-ver-pill num" id="updateVerPill"></span>
    </div>
    <button type="button" class="star-close" onclick="dismissUpdatePrompt(true)" aria-label="Close">{ICONS['close']}</button>
  </div>
  <div class="star-desc" id="updatePromptDesc"></div>
  <div class="star-actions">
    <a class="inline-link" id="updateDiffLink" href="{html.escape(GITHUB_REPO_URL)}" target="_blank" rel="noreferrer" style="margin-right:auto;">{html.escape(t['upd_view_diff'])} {ICONS['arrow_up_right']}</a>
    <button type="button" class="btn xs ghost" onclick="dismissUpdatePrompt(true)">{html.escape(t['upd_later'])}</button>
    <button type="button" class="btn xs update-cta" id="updateActionBtn" onclick="runSelfUpdate()">{html.escape(t['upd_now'])}</button>
  </div>
</aside>

<aside id="starPrompt" class="star-prompt" role="region" aria-label="GitHub Star">
  <div class="star-head">
    <div class="star-title-wrap">
      <span class="star-badge-icon" id="starPromptIcon">{ICONS['star']}</span>
      <strong id="starPromptTitle">{html.escape(t['star_prompt_title'])}</strong>
    </div>
    <button type="button" class="star-close" onclick="dismissStarPrompt()" aria-label="Close">{ICONS['close']}</button>
  </div>
  <div class="star-desc" id="starPromptDesc">{html.escape(t['star_prompt_desc'])}</div>
  <div class="star-actions" id="starPromptActions">
    <button type="button" class="btn xs ghost" onclick="dismissStarPrompt()">{html.escape(t['star_dismiss'])}</button>
    <button type="button" class="btn xs star-cta" id="starActionBtn" onclick="starInPlace()">{html.escape(t['star_cta'])}</button>
  </div>
</aside>

<div id="toast" class="toast" role="status"></div>

<dialog id="settingsModal" closedby="any" aria-labelledby="settingsModalTitle">
  <div class="dlg-head">
    <h2 id="settingsModalTitle" style="margin:0;font-size:16.5px;">{html.escape(t['modal_title'])}</h2>
    <button type="button" class="btn xs ghost" onclick="document.getElementById('settingsModal').close()" aria-label="{html.escape(t['btn_cancel'])}">{ICONS['close']}</button>
  </div>
  <div class="tile-detail">{html.escape(t['modal_desc'])}</div>
  <div class="presets">
    <span>{html.escape(t['preset_label'])}</span>
    <button type="button" class="btn xs" onclick="setBudgetPreset(10)">Pro ($10)</button>
    <button type="button" class="btn xs" onclick="setBudgetPreset(50)">Ultra ($50)</button>
    <button type="button" class="btn xs" onclick="setBudgetPreset(100)">Ultra 20x ($100)</button>
  </div>
  <form method="POST" action="/api/settings">
    {state_inputs}
    <div class="form-grid">
      <div class="field">
        <label>{html.escape(t['lbl_budget'])}</label>
        <input id="inp_budget" type="number" step="0.01" min="0" name="PAID_API_MONTHLY_USD" value="{html.escape(budget_val)}" placeholder="50" />
      </div>
      <div class="field">
        <label>{html.escape(t['lbl_ext_used'])}</label>
        <input id="inp_ext" type="number" step="0.01" min="0" name="PAID_API_EXTERNAL_USED_USD" value="{runtime.paid_api_external_used_usd:g}" />
      </div>
      <div class="field full">
        <label>{html.escape(t['lbl_rem_quick'])}</label>
        <input id="inp_rem_quick" type="number" step="0.01" min="0" placeholder="e.g. 50.00" oninput="syncExternalFromRemaining()" />
      </div>
      <div class="field">
        <label>{html.escape(t['lbl_flow_cap'])}</label>
        <input type="number" step="100" min="0" name="FLOW_MONTHLY_CREDITS" value="{runtime.flow_monthly_credits:g}" />
      </div>
      <div class="field">
        <label>{html.escape(t['lbl_colab_cap'])}</label>
        <input type="number" step="10" min="0" name="COLAB_MONTHLY_CU" value="{runtime.colab_monthly_cu:g}" />
      </div>
      <div class="field">
        <label>{html.escape(t['lbl_model'])}</label>
        <input type="text" name="GEMINI_TRIAGE_MODEL" value="{html.escape(runtime.gemini_triage_model)}" />
      </div>
      <div class="field">
        <label>{html.escape(t['lbl_proxy'])}</label>
        <input type="text" name="FLEET_PROXY" value="{html.escape(runtime.fleet_proxy)}" placeholder="http://127.0.0.1:1082" />
      </div>
      <div class="field full">
        <label>{html.escape(t['lbl_notify'])}</label>
        <div class="notify-row">
          <input type="text" name="FLEET_NOTIFY_URLS" value="{html.escape(runtime.fleet_notify_urls)}" placeholder="tgram://BOT_TOKEN/CHAT_ID" style="flex:1;" />
          {test_alert_btn}
        </div>
      </div>
      <div class="field full">
        <label>{html.escape(t['lbl_api_key'])}</label>
        <input type="password" name="GEMINI_PAID_API_KEY" value="" placeholder="{html.escape(secret_placeholder if runtime.paid_api_enabled else empty_placeholder)}" autocomplete="off" />
      </div>
      <div class="field">
        <label>{html.escape(t['lbl_tg_token'])}</label>
        <input type="password" name="TELEGRAM_BOT_TOKEN" value="" placeholder="{html.escape(secret_placeholder if runtime.telegram_bot_token else empty_placeholder)}" autocomplete="off" />
      </div>
      <div class="field">
        <label>{html.escape(t['lbl_tg_chat'])}</label>
        <input type="password" name="TELEGRAM_CHAT_ID" value="" placeholder="{html.escape(secret_placeholder if runtime.telegram_chat_id else empty_placeholder)}" autocomplete="off" />
      </div>
    </div>
    <div style="display:flex;justify-content:flex-end;gap:10px;margin-top:8px;">
      <button type="button" class="btn ghost" onclick="document.getElementById('settingsModal').close()">{html.escape(t['btn_cancel'])}</button>
      <button type="submit" class="btn primary">{html.escape(t['btn_save'])}</button>
    </div>
  </form>
</dialog>

<script>
{js_block}
</script>
</body>
</html>"""
