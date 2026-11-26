"""Precision Telemetry & Governance Cockpit UI (zero external dependencies, dual-theme, bilingual ZH/EN)."""

from __future__ import annotations

import html
import json
from typing import Any

from .config import RuntimeSecrets, redact_path

GITHUB_REPO_URL = "https://github.com/IMYin/google-ultra-maximizer"

STRINGS: dict[str, dict[str, str]] = {
    "zh": {
        "page_title": "Google AI Ultra Maximizer · 算力统筹驾驶舱",
        "subtitle": "核心双轮：T3 Code 移动编程/审批 (:3773) + Fleet-Hub 7 池遥测与合入闸门 (:7788) · 可选扩展：OpenMausBot (:8799)",
        "triage": "分诊",
        "triage_paid": "Paid Gemini",
        "triage_rules": "0-Token 规则",
        "notifier": "推送",
        "notifier_on": "Apprise 已通",
        "notifier_off": "未配置",
        "repos": "项目",
        "btn_refresh": "刷新探针",
        "btn_wakeup": "唤醒 5h 池",
        "btn_rebalance": "Bot 智能切池",
        "rebalance_tip": "将闲置 OpenMausBot 自动路由至当前推荐模型池",
        "copy_model_tip": "点击复制模型 ID",
        "btn_settings": "校准 / 设置",
        "btn_test_push": "测试推送",
        "btn_privacy_on": "截图脱敏",
        "btn_privacy_off": "取消脱敏",
        "open_maus": "OpenMausBot ↗",
        "open_t3": "T3 Code ↗",
        "sec_routing": "当下最优算力路由决策 (Next Best Move)",
        "lbl_rec_coding": "推荐编码模型",
        "lbl_rec_triage": "推荐调度/巡检",
        "sec_advisor": "Google Ultra 算力榨干参谋 (Burn Advisor)",
        "advisor_empty": "当前各算力池均处于健康平衡状态。",
        "sec_pools": "7 大独立算力池实测遥测",
        "sec_wheels": "AI 部门与开源栈协同面",
        "sec_awaiting": "黄区待拍板审批单",
        "awaiting_clear": "黄区清空 — 当前 0 个待合入工单，所有隔离 Agent 处于 0-Token 待命。",
        "diff_verify": "差异统计与验证输出",
        "btn_approve": "批准并合入 main",
        "btn_revise": "退回修改",
        "placeholder_revise": "输入修改意见...",
        "sec_history": "任务历史与事件流",
        "sec_matrix": "跨端同步项目矩阵（AI-Projects）",
        "th_id": "工单 ID",
        "th_proj": "项目",
        "th_title": "标题",
        "th_status": "状态",
        "th_updated": "更新时间",
        "th_path": "本地路径",
        "th_summary": "状态摘要",
        "open_ui": "打开控制台 ↗",
        "sync_gcp": "自动读取 GCP 赠金",
        "calibrate": "手动校准",
        "gcp_credits": "账单页 ↗",
        "grants_summary": "查看生效赠金明细（含 VPS 等扣费）",
        "modal_title": "设置与赠金额度校准",
        "modal_desc": "保存至本机 secrets.env（权限 600，绝不入库）。密钥框留空表示保持原有配置不变。",
        "preset_label": "一键填入月度赠金基数：",
        "lbl_budget": "Cloud / Gemini API 本月赠金总额 (USD)",
        "lbl_rem_quick": "按 GCP 账单页「当前剩余美元」快速校准（可选，填了自动反推外部已用）",
        "lbl_ext_used": "外部已消耗金额 (USD，比如在其它工具/Web控制台花掉的部分)",
        "lbl_flow_cap": "Flow 月度基础积分（用于进度条）",
        "lbl_colab_cap": "Colab 月度 CU 基数（用于进度条）",
        "lbl_model": "默认分诊模型",
        "lbl_t3": "T3 Code 控制台地址",
        "lbl_maus": "OpenMausBot Harness 地址",
        "lbl_vps": "BYO Linux VPS SSH 别名（OpenMausBot Self-hosted VPS）",
        "sync_maus_team": "同步 Ultra 部门包",
        "pair_maus": "免密配对 ↗",
        "rebalance_maus": "一键切至最优池",
        "lbl_proxy": "本地代理地址（可留空）",
        "lbl_notify": "Apprise 推送通道 URL（多个逗号分隔，如 tgram://... 或 bark://...）",
        "lbl_api_key": "Gemini Paid API Key（留空保持不变）",
        "lbl_tg_token": "Telegram Bot Token（可选快捷兼容，留空保持不变）",
        "lbl_tg_chat": "Telegram Chat ID（可选，留空保持不变）",
        "btn_save": "保存配置并立即刷新",
        "btn_cancel": "取消",
        "no_rows": "暂无记录",
        "copy_cmd": "复制",
        "copied": "已复制",
        "copy_err": "复制失败，请手动复制",
        "run_now": "立即执行",
        "shortcuts_hint": "快捷键：R 刷新 · S 校准 · Esc 关闭弹窗",
        "btn_star": "Star",
        "btn_starred": "已 Star",
        "star_prompt_title": "觉得 Google AI Ultra Maximizer 好用吗？",
        "star_prompt_desc": "给 GitHub 仓库点亮一颗 Star 支持开源迭代，点完有惊喜散花 ✨",
        "star_cta": "一键点亮 Star",
        "star_starring": "正在点亮…",
        "star_open_gh": "前往 GitHub 点 Star ↗",
        "star_dismiss": "暂不",
        "star_thanks_title": "感谢你的 Star 支持！🎉",
        "star_thanks_desc": "祝你每天榨干双 5h 池与全部 Ultra 算力额度！",
    },
    "en": {
        "page_title": "Google AI Ultra Maximizer · Telemetry & Governance Cockpit",
        "subtitle": "Core Stack: T3 Code Mobile Coding & Approvals (:3773) + Fleet-Hub 7-Pool Telemetry & Merge Gate (:7788) · Optional: OpenMausBot (:8799)",
        "triage": "Triage",
        "triage_paid": "Paid Gemini",
        "triage_rules": "0-Token Rules",
        "notifier": "Alerts",
        "notifier_on": "Apprise Ready",
        "notifier_off": "Unconfigured",
        "repos": "Repos",
        "btn_refresh": "Refresh",
        "btn_wakeup": "Wakeup 5h",
        "btn_rebalance": "Rebalance Bots",
        "rebalance_tip": "Route idle OpenMausBot bots to the recommended model pool",
        "copy_model_tip": "Click to copy model ID",
        "btn_settings": "Calibrate",
        "btn_test_push": "Test Alert",
        "btn_privacy_on": "Mask",
        "btn_privacy_off": "Unmask",
        "open_maus": "OpenMausBot ↗",
        "open_t3": "T3 Code ↗",
        "sec_routing": "Next Best Routing Move",
        "lbl_rec_coding": "Coding Model",
        "lbl_rec_triage": "Router / Triage",
        "sec_advisor": "Ultra Burn Advisor",
        "advisor_empty": "All quota pools are balanced.",
        "sec_pools": "Live 7-Pool Telemetry",
        "sec_wheels": "AI Department & Open-Source Stack",
        "sec_awaiting": "Yellow-Zone Approval Gate",
        "awaiting_clear": "Yellow Zone Clear — 0 pending merges · all isolated agents idle at 0 tokens.",
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
        "open_ui": "Open UI ↗",
        "sync_gcp": "Auto-Sync GCP Credits",
        "calibrate": "Calibrate",
        "gcp_credits": "GCP Console ↗",
        "grants_summary": "Inspect active grants & deductions (incl. VPS)",
        "modal_title": "Settings & Credit Calibration",
        "modal_desc": "Saved locally to secrets.env (chmod 600, never committed). Leave secret inputs blank to keep existing values.",
        "preset_label": "Quick-fill monthly Cloud credit tier:",
        "lbl_budget": "Monthly Cloud / Gemini Credit Budget (USD)",
        "lbl_rem_quick": "Quick-calibrate from GCP Remaining Balance USD (optional; auto-computes external spend)",
        "lbl_ext_used": "External Used USD (spend outside Fleet-Hub)",
        "lbl_flow_cap": "Flow Monthly Baseline Credits",
        "lbl_colab_cap": "Colab Monthly Baseline CU",
        "lbl_model": "Triage Model",
        "lbl_t3": "T3 Code URL",
        "lbl_maus": "OpenMausBot Harness URL",
        "lbl_vps": "BYO Linux VPS SSH Alias (OpenMausBot Self-hosted VPS)",
        "sync_maus_team": "Sync Ultra Bots",
        "pair_maus": "Auto-Pair ↗",
        "rebalance_maus": "Rebalance Idle Bots",
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
        "shortcuts_hint": "Shortcuts: R Refresh · S Calibrate · Esc Close Modal",
        "btn_star": "Star",
        "btn_starred": "Starred",
        "star_prompt_title": "Enjoying Google AI Ultra Maximizer?",
        "star_prompt_desc": "Give us a star on GitHub to help the project grow!",
        "star_cta": "Star on GitHub",
        "star_starring": "Starring…",
        "star_open_gh": "Open GitHub ↗",
        "star_dismiss": "Dismiss",
        "star_thanks_title": "Thanks for the star! 🎉",
        "star_thanks_desc": "It really helps Google AI Ultra Maximizer grow.",
    },
}

_POOL_ORDER: dict[str, int] = {
    "agy_gemini_weekly": 0,
    "agy_claude_5h": 1,
    "colab_cu": 2,
    "flow_credits": 3,
    "paid_gemini_api": 4,
    "gdrive_bus": 5,
    "ai_studio_daily": 6,
}

_POOL_SPAN: dict[str, str] = {
    "agy_gemini_weekly": "col-6 hero-pool",
    "agy_claude_5h": "col-6 hero-pool",
    "colab_cu": "col-4",
    "flow_credits": "col-4",
    "paid_gemini_api": "col-4",
    "gdrive_bus": "col-6 compact-pool",
    "ai_studio_daily": "col-6 compact-pool",
}


def _bar_color(pool_id: str, pct: float) -> str:
    if pool_id == "gdrive_bus":
        return "var(--info)"
    if pct >= 40.0:
        return "var(--ok)"
    if pct >= 15.0:
        return "var(--warn)"
    return "var(--danger)"


def _bot_model_badge_class(instance: str, model: str) -> str:
    low = f"{instance}/{model}".lower()
    if "claude" in low or "codex" in low or "gpt-oss" in low:
        return "bot-pill-5h"
    if "gemini-4" in low or "gemini-3" in low:
        return "bot-pill-weekly"
    return "bot-pill-std"


def _pick_lang(item: dict[str, Any], key: str, is_en: bool) -> str:
    if is_en:
        en_val = item.get(f"{key}_en")
        if en_val is not None and str(en_val) != "":
            return str(en_val)
    return str(item.get(key) or "")


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
    """Render the responsive Telemetry & Governance Cockpit HTML page."""
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
        icon = "✓" if ok_flag == "1" else "!"
        banner_html = f'<div class="{cls}"><span class="banner-dot">{icon}</span><span>{html.escape(msg)}</span></div>'

    caps = capabilities or {}
    wakeup_ready = bool(caps.get("wakeup_cli", True))
    gcp_sync_ready = bool(caps.get("gcp_sync_cli", True))

    maus_bridge = next((b for b in bridges if b.get("id") == "openmausbot"), None)
    maus_live = bool(maus_bridge and maus_bridge.get("tone") == "live")
    maus_cli_live = bool(maus_live and maus_bridge.get("cli_installed", True))
    maus_rebalance_ready = bool(maus_cli_live and maus_bridge.get("bot_count") != 0)

    t3_bridge = next((b for b in bridges if b.get("id") == "t3code"), None)
    t3_live = bool(t3_bridge and t3_bridge.get("tone") == "live")

    roi_pill = ""
    if isinstance(lens, dict) and float(lens.get("d7_usd") or 0) > 0:
        d7 = float(lens["d7_usd"])
        roi = d7 / 249.99
        roi_label = f"7d ROI ${d7:,.0f} ({roi:.2f}×)"
        roi_pill = (
            f'<span class="pill pill-emerald" title="Agy-Lens 7-day API-equivalent savings vs $249.99/mo Ultra">'
            f'{html.escape(roi_label)}</span>'
        )

    # Routing Verdict Hero Strip
    routing_html = ""
    if isinstance(routing, dict) and routing:
        mode = str(routing.get("mode") or "balanced")
        headline = str(routing.get("headline_en" if is_en else "headline_zh") or "")
        reason = str(routing.get("reason_en" if is_en else "reason_zh") or "")
        rec_code = str(routing.get("recommended_coding_model") or "")
        rec_triage = str(routing.get("recommended_triage_model") or "")
        mode_cls = "mode-harvest" if mode == "5h_harvest" else ("mode-warn" if mode == "conserve_weekly" else "mode-balanced")
        mode_label = {
            "5h_harvest": "5H HARVEST" if is_en else "5h 滚动收割",
            "conserve_weekly": "CONSERVE WEEKLY" if is_en else "周池保卫模式",
            "balanced": "BALANCED" if is_en else "双池均衡",
        }.get(mode, mode.upper())
        verdict_action_btns: list[str] = []
        if maus_rebalance_ready:
            verdict_action_btns.append(
                f'<form method="POST" action="/api/rebalance" data-async="1" style="margin:0">'
                f"{state_inputs}"
                f'<button class="btn primary sm" type="submit" title="{html.escape(t["rebalance_tip"])}">⚖️ {html.escape(t["btn_rebalance"])}</button>'
                f"</form>"
            )
            if wakeup_ready:
                verdict_action_btns.append(
                    f'<form method="POST" action="/api/wakeup" data-async="1" style="margin:0">'
                    f"{state_inputs}"
                    f'<button class="btn sm" type="submit">⚡ {html.escape(t["btn_wakeup"])}</button>'
                    f"</form>"
                )
        elif wakeup_ready and bool(routing.get("wakeup_recommended")):
            verdict_action_btns.append(
                f'<form method="POST" action="/api/wakeup" data-async="1" style="margin:0">'
                f"{state_inputs}"
                f'<button class="btn primary sm" type="submit">⚡ {html.escape(t["btn_wakeup"])}</button>'
                f"</form>"
            )
            if t3_live:
                verdict_action_btns.append(
                    f'<a class="btn sm" href="{html.escape(runtime.t3code_url)}" target="_blank" rel="noreferrer">📱 {html.escape(t["open_t3"])}</a>'
                )
        else:
            if t3_live:
                verdict_action_btns.append(
                    f'<a class="btn primary sm" href="{html.escape(runtime.t3code_url)}" target="_blank" rel="noreferrer">📱 {html.escape(t["open_t3"])}</a>'
                )
            if wakeup_ready:
                verdict_action_btns.append(
                    f'<form method="POST" action="/api/wakeup" data-async="1" style="margin:0">'
                    f"{state_inputs}"
                    f'<button class="btn sm" type="submit">⚡ {html.escape(t["btn_wakeup"])}</button>'
                    f"</form>"
                )
        verdict_actions_html = f'<div class="verdict-actions">{"".join(verdict_action_btns)}</div>' if verdict_action_btns else ""

        routing_html = f"""
        <section class="verdict-card {mode_cls}">
          <div class="verdict-main">
            <div class="verdict-kicker">
              <span class="verdict-badge">{html.escape(mode_label)}</span>
              <span>{html.escape(t['sec_routing'])}</span>
            </div>
            <div class="verdict-title">{html.escape(headline)}</div>
            <div class="verdict-reason">{html.escape(reason)}</div>
          </div>
          <div class="verdict-side">
            <div class="model-chips">
              <button type="button" class="model-chip" onclick="copyModelId({html.escape(json.dumps(rec_code))})" title="{html.escape(t['copy_model_tip'])}">
                <span class="chip-lbl">{html.escape(t['lbl_rec_coding'])}</span>
                <code>{html.escape(rec_code)}</code>
              </button>
              <button type="button" class="model-chip" onclick="copyModelId({html.escape(json.dumps(rec_triage))})" title="{html.escape(t['copy_model_tip'])}">
                <span class="chip-lbl">{html.escape(t['lbl_rec_triage'])}</span>
                <code>{html.escape(rec_triage)}</code>
              </button>
            </div>
            {verdict_actions_html}
          </div>
        </section>
        """

    # 7-Pool Bento Cards (ordered 6+6, 4+4+4, 6+6 for zero orphan gaps)
    paid_local_used = 0.0
    ordered_pools = sorted(pools, key=lambda p: _POOL_ORDER.get(str(p.get("pool") or ""), 99))
    pool_cards = []
    for p in ordered_pools:
        pool_id = str(p.get("pool", ""))
        span_cls = _POOL_SPAN.get(pool_id, "col-4")
        pct = p.get("pct")
        bar_html = ""
        if pct is not None:
            p_val = max(0.0, min(100.0, float(pct)))
            color = _bar_color(pool_id, p_val)
            bar_html = (
                f'<div class="bar-wrap">'
                f'<div class="bar"><div style="width:{p_val:.1f}%;background:{color}"></div></div>'
                f'<span class="pct-num">{p_val:.0f}%</span></div>'
            )
        tone = html.escape(str(p.get("badge_tone", "muted")))
        p_title = _pick_lang(p, "title", is_en)
        p_badge = _pick_lang(p, "badge", is_en)
        p_primary = _pick_lang(p, "primary", is_en)
        p_detail = _pick_lang(p, "detail", is_en)

        extra_actions = ""
        if pool_id == "paid_gemini_api":
            paid_meta = p.get("meta") or {}
            paid_local_used = float(paid_meta.get("local_used_usd") or 0.0)
            grants = paid_meta.get("grants") or []
            grants_html = ""
            if isinstance(grants, list) and grants:
                g_rows = "".join(
                    f"<tr><td>${float(g.get('remaining', 0)):.2f} / ${float(g.get('original', 0)):.2f}</td>"
                    f"<td>-${float(g.get('used', 0)):.2f}</td>"
                    f"<td>{html.escape(str(g.get('end_date') or '-'))}</td></tr>"
                    for g in grants
                )
                grants_html = (
                    f'<details class="grants-details">'
                    f'<summary>📋 {html.escape(t["grants_summary"])} ({len(grants)})</summary>'
                    f'<div class="table-wrap"><table class="mini-table">'
                    f'<thead><tr><th>{"剩余 / 总额" if not is_en else "Rem / Orig"}</th><th>{"已扣" if not is_en else "Used"}</th><th>{"到期日" if not is_en else "Expires"}</th></tr></thead>'
                    f"<tbody>{g_rows}</tbody></table></div></details>"
                )
            sync_gcp_btn = (
                f'<form method="POST" action="/api/sync-gcp-credits" data-async="1" style="margin:0">'
                f"{state_inputs}"
                f'<button type="submit" class="btn xs primary">🔄 {html.escape(t["sync_gcp"])}</button>'
                f"</form>"
                if gcp_sync_ready
                else ""
            )
            extra_actions = (
                f'<div class="card-actions">'
                f"{sync_gcp_btn}"
                f'<button type="button" class="btn xs" onclick="openSettingsModal()">✏️ {html.escape(t["calibrate"])}</button>'
                f'<a class="btn xs" href="https://console.cloud.google.com/billing/credits" target="_blank" rel="noreferrer">{html.escape(t["gcp_credits"])}</a>'
                f"</div>{grants_html}"
            )
        valid_windows = [w for w in (p.get("windows") or []) if isinstance(w, dict)] if isinstance(p.get("windows"), list) else []
        if len(valid_windows) >= 2:
            win_boxes: list[str] = []
            for w in valid_windows:
                w_pct = max(0.0, min(100.0, float(w.get("pct") or 0.0)))
                w_color = _bar_color(pool_id, w_pct)
                w_label = _pick_lang(w, "label", is_en)
                w_reset = _pick_lang(w, "reset", is_en)
                win_boxes.append(
                    f'<div class="quota-win">'
                    f'<div class="quota-win-head">'
                    f'<span class="quota-win-lbl">{html.escape(w_label)}</span>'
                    f'<span class="quota-win-val num">{w_pct:.1f}%</span>'
                    f'</div>'
                    f'<div class="bar"><div style="width:{w_pct:.1f}%;background:{w_color}"></div></div>'
                    f'<div class="quota-win-sub">{html.escape(w_reset)}</div>'
                    f'</div>'
                )
            body_html = f'<div class="quota-windows">{"".join(win_boxes)}</div>'
            kicker_txt = _pick_lang(p, "kicker", is_en) or p_detail
        else:
            body_html = f'<div class="metric num">{html.escape(p_primary)}</div>{bar_html}'
            kicker_txt = p_detail

        pool_cards.append(
            f"""
            <article class="card pool-card tone-{tone} {span_cls}">
              <div class="card-top">
                <h3 class="card-title">{html.escape(p_title)}</h3>
                <span class="source-badge {tone}">{html.escape(p_badge)}</span>
              </div>
              {body_html}
              <div class="kicker">{html.escape(kicker_txt)}</div>
              {extra_actions}
            </article>
            """
        )

    # Burn Advisor Cards
    advisor_cards = []
    for item in advisor:
        sev = html.escape(str(item.get("severity", "info")))
        cmd_hint = str(item.get("command") or "")
        action_btn = ""
        if cmd_hint == "ultra wakeup" and wakeup_ready:
            action_btn = (
                f'<form method="POST" action="/api/wakeup" data-async="1" style="margin:0">'
                f'{state_inputs}'
                f'<button type="submit" class="btn xs primary">⚡ {html.escape(t["run_now"])}</button></form>'
            )
        elif cmd_hint == "ultra sync-gcp-credits" and gcp_sync_ready:
            action_btn = (
                f'<form method="POST" action="/api/sync-gcp-credits" data-async="1" style="margin:0">'
                f'{state_inputs}'
                f'<button type="submit" class="btn xs primary">🔄 {html.escape(t["run_now"])}</button></form>'
            )

        if cmd_hint.startswith("https://"):
            cmd_html = f'<div class="adv-foot"><a class="inline-link" href="{html.escape(cmd_hint)}" target="_blank" rel="noreferrer">{html.escape(cmd_hint)} ↗</a></div>'
        elif cmd_hint:
            cmd_html = (
                f'<div class="adv-foot">'
                f'<code class="cmd-code">{html.escape(cmd_hint)}</code>'
                f'<button type="button" class="btn xs copy-btn" onclick="copyText(this, {html.escape(json.dumps(cmd_hint))})">{html.escape(t["copy_cmd"])}</button>'
                f'{action_btn}</div>'
            )
        else:
            cmd_html = ""
        advisor_cards.append(
            f"""
            <div class="adv-card sev-{sev}">
              <div class="adv-head">
                <span class="adv-pool">{html.escape(_pick_lang(item, 'pool', is_en))}</span>
                <span class="sev-dot sev-{sev}"></span>
              </div>
              <div class="adv-title">{html.escape(_pick_lang(item, 'title', is_en))}</div>
              <div class="adv-action">{html.escape(_pick_lang(item, 'action', is_en))}</div>
              {cmd_html}
            </div>
            """
        )
    advisor_block = (
        f'<div class="adv-grid">{"".join(advisor_cards)}</div>'
        if advisor_cards
        else f'<div class="empty-inline">{html.escape(t["advisor_empty"])}</div>'
    )

    # Ecosystem Wheels (symmetrical 6+6 + 4+4+4 bento; demote optional OpenMausBot when off)
    if maus_live:
        wheel_order = {"t3code": 0, "openmausbot": 1, "agy_lens": 2, "agent_desktop": 3, "apprise": 4}
        wide_wheels = {"t3code", "openmausbot"}
    else:
        wheel_order = {"t3code": 0, "agy_lens": 1, "agent_desktop": 2, "apprise": 3, "openmausbot": 4}
        wide_wheels = {"t3code", "agy_lens"}
    ordered_bridges = sorted(bridges, key=lambda b: wheel_order.get(str(b.get("id") or ""), 99))
    bridge_cards = []
    for b in ordered_bridges:
        tone = html.escape(str(b.get("tone", "muted")))
        b_id = str(b.get("id") or "")
        span_cls = "col-6" if b_id in wide_wheels else "col-4"
        link_html = (
            f'<a class="btn xs" href="{html.escape(b["action_url"])}" target="_blank" rel="noreferrer">{html.escape(t["open_ui"])}</a>'
            if b.get("action_url")
            else ""
        )
        roster_html = ""
        bridge_extra = ""
        if b_id == "openmausbot":
            bots = b.get("bots") or []
            if isinstance(bots, list) and bots:
                bot_chips = []
                for bot in bots:
                    b_name = str(bot.get("name") or "")
                    inst = str(bot.get("instance") or "")
                    mod = str(bot.get("model") or "")
                    busy = bool(bot.get("busy"))
                    pill_cls = _bot_model_badge_class(inst, mod)
                    dot_cls = "dot-busy" if busy else "dot-idle"
                    mod_txt = f"{inst}/{mod}" if inst and mod else (mod or "default")
                    bot_chips.append(
                        f'<div class="bot-chip {pill_cls}">'
                        f'<span class="bot-dot {dot_cls}"></span>'
                        f'<span class="bot-name">{html.escape(b_name)}</span>'
                        f'<code>{html.escape(mod_txt)}</code>'
                        f'</div>'
                    )
                roster_html = f'<div class="bot-roster">{"".join(bot_chips)}</div>'

            if maus_cli_live:
                rebalance_btn = (
                    f'<form method="POST" action="/api/rebalance" data-async="1" style="margin:0">'
                    f"{state_inputs}"
                    f'<button type="submit" class="btn xs">⚖️ {html.escape(t["rebalance_maus"])}</button>'
                    f"</form>"
                    if maus_rebalance_ready
                    else ""
                )
                bridge_extra = (
                    f'<div class="card-actions">'
                    f'<form method="POST" action="/api/maus-pair" target="_blank" style="margin:0">'
                    f"{state_inputs}"
                    f'<button type="submit" class="btn xs primary">🔑 {html.escape(t["pair_maus"])}</button>'
                    f"</form>"
                    f"{rebalance_btn}"
                    f'<form method="POST" action="/api/sync-maus-team" data-async="1" style="margin:0">'
                    f"{state_inputs}"
                    f'<button type="submit" class="btn xs">🤖 {html.escape(t["sync_maus_team"])}</button>'
                    f"</form></div>"
                )
        elif b_id == "t3code" and b.get("tone") == "live" and b.get("cli_installed", True):
            bridge_extra = (
                f'<div class="card-actions">'
                f'<form method="POST" action="/api/t3-pair" target="_blank" style="margin:0">'
                f'{state_inputs}'
                f'<button type="submit" class="btn xs primary">🔑 {html.escape(t["pair_maus"])}</button>'
                f"</form></div>"
            )
        bridge_cards.append(
            f"""
            <article class="card wheel-card tone-{tone} {span_cls}">
              <div class="card-top">
                <span class="source-badge {tone}">{html.escape(_pick_lang(b, 'status', is_en))}</span>
                {link_html}
              </div>
              <h3 class="card-title">{html.escape(_pick_lang(b, 'name', is_en))}</h3>
              <div class="kicker">{html.escape(_pick_lang(b, 'detail', is_en))}</div>
              {roster_html}
              {bridge_extra}
            </article>
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
                    <span class="source-badge warn">{html.escape(tk['pool'])}</span>
                    <strong>[{html.escape(tk['project'])}] {html.escape(tk['title'])}</strong>
                    <code>{html.escape(tk['task_id'])}</code>
                  </div>
                  <p class="meta"><code>{html.escape(tk['branch_name'])}</code> @ <code>{html.escape(tk['head_sha'][:8])}</code> · Worktree: <code>{html.escape(wt_disp)}</code></p>
                  <details open>
                    <summary>{html.escape(t['diff_verify'])}</summary>
                    <pre>{html.escape(tk['diff_stat'] or '')}\n\n--- VERIFY ---\n{html.escape(tk['verify_output'] or '')}</pre>
                  </details>
                  <div class="actions">
                    <form method="POST" action="/api/approve" style="display:inline">
                      {state_inputs}
                      <input type="hidden" name="task_id" value="{html.escape(tk['task_id'])}" />
                      <button class="btn primary" type="submit">✅ {html.escape(t['btn_approve'])}</button>
                    </form>
                    <form method="POST" action="/api/revise" class="revise-form">
                      {state_inputs}
                      <input type="hidden" name="task_id" value="{html.escape(tk['task_id'])}" />
                      <input type="text" name="note" placeholder="{html.escape(t['placeholder_revise'])}" />
                      <button class="btn" type="submit">🔄 {html.escape(t['btn_revise'])}</button>
                    </form>
                  </div>
                </div>
                """
            )
        awaiting_section = f"""
        <section class="section">
          <div class="section-head">
            <h2>🟡 {html.escape(t['sec_awaiting'])} <span class="count-pill warn">{len(awaiting)}</span></h2>
          </div>
          {"".join(task_cards)}
        </section>
        """
    else:
        awaiting_section = f"""
        <section class="clear-strip">
          <span class="clear-dot"></span>
          <span>{html.escape(t['awaiting_clear'])}</span>
        </section>
        """

    repo_rows = "".join(
        f"<tr><td><strong>{html.escape(r['project'])}</strong></td><td><code>{html.escape(redact_path(r['local_path'], privacy=privacy))}</code></td><td>{html.escape(r['summary'])}</td><td>{html.escape(r['updated'])}</td></tr>"
        for r in repos
    )
    history_rows = "".join(
        f"<tr><td><code>{html.escape(tk['task_id'])}</code></td><td>{html.escape(tk['project'])}</td><td>{html.escape(tk['title'])}</td><td><span class='source-badge muted'>{html.escape(tk['status'])}</span></td><td>{html.escape(tk['updated_at'])}</td></tr>"
        for tk in others[:12]
    )

    secret_placeholder = "已配置（留空保持不变）" if not is_en else "Configured (leave blank to keep)"
    empty_placeholder = "未设置（留空不改）" if not is_en else "Not set (optional)"
    budget_val = f"{runtime.paid_api_monthly_usd:g}" if runtime.paid_api_monthly_usd > 0 else ""

    return f"""<!doctype html>
<html lang="{ 'en' if is_en else 'zh-CN' }" data-theme="dark">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>{html.escape(t['page_title'])}</title>
<script>
(function(){{
  try {{
    var th = localStorage.getItem('fleet_theme');
    if (th === 'light' || th === 'dark') document.documentElement.setAttribute('data-theme', th);
  }} catch(e) {{}}
}})();
</script>
<style>
  :root, :root[data-theme="dark"] {{
    --bg:#080a0f; --bg-elev:#0e121a; --card:#121722; --card-hover:#171d2b;
    --ink:#f1f5f9; --ink-soft:#cbd5e1; --muted:#8c98ac;
    --line:rgba(255,255,255,.08); --line-strong:rgba(255,255,255,.16);
    --ok:#10b981; --ok-bg:rgba(16,185,129,.14); --ok-ink:#6ee7b7;
    --warn:#f59e0b; --warn-bg:rgba(245,158,11,.15); --warn-ink:#fcd34d;
    --danger:#ef4444; --danger-bg:rgba(239,68,68,.15); --danger-ink:#fca5a5;
    --info:#3b82f6; --info-bg:rgba(59,130,246,.14); --info-ink:#93c5fd;
    --muted-bg:rgba(148,163,184,.12); --muted-ink:#94a3b8;
    --code-bg:rgba(255,255,255,.06); --header-bg:rgba(8,10,15,.82);
    --shadow:0 8px 28px rgba(0,0,0,.35);
  }}
  :root[data-theme="light"] {{
    --bg:#f6f4ee; --bg-elev:#ece8de; --card:#ffffff; --card-hover:#fcfbf7;
    --ink:#111827; --ink-soft:#374151; --muted:#6b7280;
    --line:#e4dfd2; --line-strong:#cfc7b4;
    --ok:#15803d; --ok-bg:#dcfce7; --ok-ink:#14532d;
    --warn:#d97706; --warn-bg:#fef3c7; --warn-ink:#92400e;
    --danger:#dc2626; --danger-bg:#fee2e2; --danger-ink:#991b1b;
    --info:#2563eb; --info-bg:#dbeafe; --info-ink:#1e40af;
    --muted-bg:#e5e7eb; --muted-ink:#4b5563;
    --code-bg:#f2efe6; --header-bg:rgba(246,244,238,.88);
    --shadow:0 4px 16px rgba(17,24,39,.06);
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0;
    background:radial-gradient(1100px 440px at 10% -8%, rgba(16,185,129,.08), transparent 60%),
               radial-gradient(900px 420px at 92% -10%, rgba(59,130,246,.08), transparent 55%),
               var(--bg);
    color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","Inter","PingFang SC",sans-serif;
    -webkit-font-smoothing:antialiased;
    line-height:1.45;
  }}
  code, .num {{ font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace; font-variant-numeric:tabular-nums; }}
  code {{ background:var(--code-bg); padding:1px 6px; border-radius:5px; font-size:.86em; }}

  .topbar {{
    position:sticky; top:0; z-index:40;
    background:var(--header-bg); backdrop-filter:blur(16px); -webkit-backdrop-filter:blur(16px);
    border-bottom:1px solid var(--line);
  }}
  .topbar-inner {{
    max-width:1320px; margin:0 auto; padding:10px 20px;
    display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap;
  }}
  .brand {{ display:flex; align-items:center; gap:10px; min-width:0; }}
  .brand-mark {{
    width:28px; height:28px; border-radius:8px; flex-shrink:0;
    background:linear-gradient(135deg,#10b981 0%,#3b82f6 100%);
    display:grid; place-items:center; font-weight:800; color:#fff; font-size:14px;
    box-shadow:0 0 16px rgba(16,185,129,.25);
  }}
  .brand h1 {{ margin:0; font-size:15px; font-weight:700; letter-spacing:-.02em; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .pill {{
    font-size:11px; font-weight:600; padding:2px 8px; border-radius:999px;
    background:var(--code-bg); color:var(--ink-soft); border:1px solid var(--line); white-space:nowrap;
  }}
  .pill-emerald {{ background:var(--ok-bg); color:var(--ok-ink); border-color:rgba(16,185,129,.3); }}
  .toolbar {{ display:flex; gap:6px; flex-wrap:wrap; align-items:center; }}

  .btn {{
    padding:5px 10px; border-radius:8px; border:1px solid var(--line-strong);
    background:var(--card); color:var(--ink); cursor:pointer;
    font-weight:600; font-size:12px; text-decoration:none; white-space:nowrap;
    display:inline-flex; align-items:center; gap:5px; transition:all .14s ease;
  }}
  .btn:hover {{ background:var(--card-hover); border-color:var(--muted); }}
  .btn:disabled {{ opacity:.6; cursor:wait; }}
  .btn.primary {{ background:var(--ok); color:#041b11; border-color:transparent; font-weight:700; }}
  :root[data-theme="light"] .btn.primary {{ color:#fff; }}
  .btn.primary:hover {{ filter:brightness(1.08); }}
  .btn.ghost {{ background:transparent; border-color:var(--line); }}
  .btn.xs {{ padding:3px 8px; font-size:11px; border-radius:6px; }}

  .wrap {{ max-width:1320px; margin:0 auto; padding:14px 20px 44px; }}
  .sub-strip {{
    font-size:11.5px; color:var(--muted); margin-bottom:14px;
    display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap;
  }}
  .sub-pills {{ display:flex; gap:6px; flex-wrap:wrap; align-items:center; }}

  .banner {{
    padding:10px 14px; border-radius:10px; margin-bottom:14px;
    font-weight:600; font-size:13px; display:flex; align-items:center; gap:9px;
    border:1px solid var(--line);
  }}
  .banner.ok {{ background:var(--ok-bg); color:var(--ok-ink); border-color:rgba(16,185,129,.3); }}
  .banner.err {{ background:var(--danger-bg); color:var(--danger-ink); border-color:rgba(239,68,68,.3); }}
  .banner-dot {{ width:18px; height:18px; border-radius:999px; display:grid; place-items:center; font-size:11px; background:rgba(255,255,255,.15); flex-shrink:0; }}

  .verdict-card {{
    background:var(--card); border:1px solid var(--line-strong); border-radius:14px;
    padding:16px 18px; margin-bottom:20px; box-shadow:var(--shadow);
    display:flex; justify-content:space-between; align-items:center; gap:16px; flex-wrap:wrap;
  }}
  .verdict-card.mode-harvest {{ border-left:4px solid var(--warn); }}
  .verdict-card.mode-warn {{ border-left:4px solid var(--danger); }}
  .verdict-card.mode-balanced {{ border-left:4px solid var(--ok); }}
  .verdict-kicker {{ display:flex; align-items:center; gap:8px; font-size:11px; font-weight:700; color:var(--muted); text-transform:uppercase; letter-spacing:.04em; margin-bottom:6px; }}
  .verdict-badge {{ padding:2px 8px; border-radius:999px; background:var(--warn-bg); color:var(--warn-ink); }}
  .mode-balanced .verdict-badge {{ background:var(--ok-bg); color:var(--ok-ink); }}
  .mode-warn .verdict-badge {{ background:var(--danger-bg); color:var(--danger-ink); }}
  .verdict-title {{ font-size:16px; font-weight:700; letter-spacing:-.01em; margin-bottom:4px; }}
  .verdict-reason {{ font-size:12.5px; color:var(--muted); max-width:680px; }}
  .verdict-side {{ display:flex; flex-direction:column; gap:10px; align-items:flex-end; }}
  .model-chips {{ display:flex; gap:8px; flex-wrap:wrap; }}
  .model-chip {{ background:var(--bg-elev); border:1px solid var(--line); border-radius:9px; padding:5px 10px; display:flex; flex-direction:column; gap:2px; align-items:flex-start; color:var(--ink); text-align:left; font:inherit; cursor:pointer; transition:border-color .14s ease, background .14s ease; }}
  .model-chip:hover {{ border-color:var(--line-strong); background:var(--card-hover); }}
  .chip-lbl {{ font-size:10px; color:var(--muted); font-weight:600; text-transform:uppercase; }}
  .verdict-actions {{ display:flex; gap:8px; flex-wrap:wrap; }}

  .section {{ margin-bottom:22px; }}
  .section-head {{ display:flex; justify-content:space-between; align-items:center; gap:12px; margin:0 0 11px; flex-wrap:wrap; }}
  .section-head h2 {{ margin:0; font-size:13.5px; font-weight:700; letter-spacing:.01em; color:var(--ink-soft); display:flex; align-items:center; gap:7px; }}
  .count-pill {{ font-size:11px; padding:1px 7px; border-radius:999px; background:var(--code-bg); color:var(--ink); }}
  .count-pill.warn {{ background:var(--warn-bg); color:var(--warn-ink); }}

  /* 12-Column Symmetrical Bento Grids */
  .bento {{ display:grid; grid-template-columns:repeat(12, minmax(0, 1fr)); gap:12px; margin-bottom:22px; }}
  .col-4 {{ grid-column:span 4; }}
  .col-6 {{ grid-column:span 6; }}
  .col-8 {{ grid-column:span 8; }}
  @media (max-width:1023px) {{
    .col-4, .col-6, .col-8 {{ grid-column:span 6; }}
    .bento-wheels .wheel-card:last-child,
    .bento-pools .pool-card:last-child {{ grid-column:span 12; }}
  }}
  @media (max-width:720px) {{
    .topbar {{ position:static; }}
    .col-4, .col-6, .col-8, .bento-wheels .col-8,
    .bento-pools .pool-card:last-child {{ grid-column:span 12; }}
    .form-grid {{ grid-template-columns:1fr !important; }}
    .verdict-side {{ align-items:flex-start; }}
  }}

  .card {{
    background:var(--card); border:1px solid var(--line); border-radius:13px;
    padding:14px 16px; transition:border-color .15s ease; min-width:0;
  }}
  .card:hover {{ border-color:var(--line-strong); }}
  .card.tone-warn {{ border-color:rgba(239,68,68,.42); }}
  .hero-pool {{ background:linear-gradient(180deg, rgba(255,255,255,.02), transparent), var(--card); }}
  .compact-pool {{ padding:12px 15px; }}
  .compact-pool .metric {{ font-size:18px; }}
  .card-top {{ display:flex; justify-content:space-between; align-items:flex-start; gap:8px; margin-bottom:8px; flex-wrap:wrap; }}
  .card-title {{ margin:0; font-size:13.5px; font-weight:700; color:var(--ink-soft); }}
  .wheel-card .card-title {{ margin:2px 0 6px; font-size:14.5px; color:var(--ink); }}
  .source-badge {{ display:inline-flex; align-items:center; font-size:11px; padding:2px 8px; border-radius:999px; font-weight:600; white-space:nowrap; max-width:100%; overflow:hidden; text-overflow:ellipsis; }}
  .source-badge.live {{ background:var(--ok-bg); color:var(--ok-ink); }}
  .source-badge.local {{ background:var(--info-bg); color:var(--info-ink); }}
  .source-badge.stale {{ background:var(--warn-bg); color:var(--warn-ink); }}
  .source-badge.warn {{ background:var(--danger-bg); color:var(--danger-ink); }}
  .source-badge.muted {{ background:var(--muted-bg); color:var(--muted-ink); }}
  .metric {{ font-size:22px; font-weight:700; letter-spacing:-.02em; margin-bottom:7px; }}
  .kicker {{ font-size:12px; color:var(--muted); line-height:1.45; overflow-wrap:anywhere; }}
  .bar-wrap {{ display:flex; align-items:center; gap:9px; margin:6px 0 8px; }}
  .bar {{ flex:1; height:7px; background:var(--code-bg); border-radius:999px; overflow:hidden; }}
  .hero-pool .bar {{ height:8px; }}
  .bar div {{ height:100%; border-radius:999px; transition:width .35s ease; }}
  .pct-num {{ font-size:11.5px; font-weight:700; color:var(--ink-soft); font-family:ui-monospace,SFMono-Regular,monospace; }}
  .quota-windows {{ display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:10px; margin:6px 0 10px; }}
  .quota-win {{ background:var(--bg-elev); border:1px solid var(--line); border-radius:10px; padding:9px 11px; min-width:0; }}
  .quota-win-head {{ display:flex; justify-content:space-between; align-items:baseline; gap:8px; margin-bottom:6px; }}
  .quota-win-lbl {{ font-size:11.5px; font-weight:700; color:var(--ink-soft); white-space:nowrap; }}
  .quota-win-val {{ font-size:19px; font-weight:700; letter-spacing:-.02em; color:var(--ink); }}
  .quota-win .bar {{ height:7px; margin-bottom:6px; }}
  .quota-win-sub {{ font-size:11px; color:var(--muted); line-height:1.35; overflow-wrap:anywhere; }}
  @media (max-width:960px) {{ .quota-windows {{ grid-template-columns:1fr; }} }}
  .card-actions {{ display:flex; gap:6px; margin-top:11px; flex-wrap:wrap; }}

  .adv-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:11px; margin-bottom:22px; }}
  .adv-card {{
    background:var(--card); border:1px solid var(--line); border-left:3px solid var(--info);
    border-radius:12px; padding:13px 14px; display:flex; flex-direction:column; gap:5px; min-width:0;
  }}
  .adv-card.sev-urgent {{ border-left-color:var(--danger); }}
  .adv-card.sev-opportunity {{ border-left-color:var(--warn); }}
  .adv-head {{ display:flex; justify-content:space-between; align-items:center; }}
  .adv-pool {{ font-size:11px; font-weight:700; color:var(--muted); text-transform:uppercase; letter-spacing:.03em; }}
  .sev-dot {{ width:7px; height:7px; border-radius:999px; background:var(--info); }}
  .sev-dot.sev-urgent {{ background:var(--danger); box-shadow:0 0 8px var(--danger); }}
  .sev-dot.sev-opportunity {{ background:var(--warn); }}
  .adv-title {{ font-size:13.5px; font-weight:700; line-height:1.35; }}
  .adv-action {{ font-size:12px; color:var(--muted); line-height:1.45; }}
  .adv-foot {{ display:flex; align-items:center; gap:6px; flex-wrap:wrap; margin-top:4px; }}
  .cmd-code {{ font-size:11px; word-break:break-all; }}
  .inline-link {{ color:var(--info-ink); text-decoration:none; font-size:11.5px; font-weight:600; word-break:break-all; }}

  .bot-roster {{ display:flex; flex-wrap:wrap; gap:7px; margin-top:11px; }}
  .bot-chip {{
    display:inline-flex; align-items:center; gap:6px; padding:4px 9px; border-radius:8px;
    border:1px solid var(--line); background:var(--bg-elev); font-size:11.5px; max-width:100%;
  }}
  .bot-chip.bot-pill-5h {{ border-color:rgba(16,185,129,.28); }}
  .bot-chip.bot-pill-weekly {{ border-color:rgba(245,158,11,.35); }}
  .bot-dot {{ width:6px; height:6px; border-radius:999px; flex-shrink:0; }}
  .dot-idle {{ background:var(--ok); }}
  .dot-busy {{ background:var(--warn); box-shadow:0 0 6px var(--warn); }}
  .bot-name {{ font-weight:600; color:var(--ink); }}

  .grants-details {{ margin-top:10px; font-size:12px; }}
  .grants-details summary {{ cursor:pointer; color:var(--ink-soft); font-weight:600; }}
  .mini-table {{ margin-top:0; font-size:11px; }}

  .clear-strip {{
    display:flex; align-items:center; gap:9px; padding:10px 14px; border-radius:11px;
    background:var(--card); border:1px solid var(--line); color:var(--muted);
    font-size:12.5px; margin-bottom:16px;
  }}
  .clear-dot {{ width:8px; height:8px; border-radius:999px; background:var(--ok); flex-shrink:0; }}

  .task-card {{
    background:var(--card); border:1px solid var(--line); border-left:4px solid var(--warn);
    border-radius:12px; padding:15px 16px; margin-bottom:12px;
  }}
  .task-head {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:6px; }}
  .meta {{ font-size:12px; color:var(--muted); margin:4px 0 10px; overflow-wrap:anywhere; }}
  pre {{ background:var(--bg-elev); border:1px solid var(--line); padding:10px 12px; border-radius:8px; font-size:12px; overflow:auto; max-height:240px; color:var(--ink-soft); }}
  .actions {{ display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-top:12px; }}
  .revise-form {{ display:flex; gap:6px; flex:1; min-width:220px; }}
  input[type=text], input[type=number], input[type=password] {{
    width:100%; padding:8px 10px; border:1px solid var(--line-strong); border-radius:8px;
    background:var(--bg-elev); color:var(--ink); font-size:13px;
  }}
  input:focus {{ outline:none; border-color:var(--info); }}

  details.drawer {{
    background:var(--card); border:1px solid var(--line); border-radius:12px;
    padding:11px 15px; margin-bottom:12px; min-width:0;
  }}
  details.drawer summary {{
    cursor:pointer; font-size:13.5px; font-weight:700; color:var(--ink-soft);
    display:flex; align-items:center; justify-content:space-between; list-style:none;
  }}
  details.drawer summary::-webkit-details-marker {{ display:none; }}
  .table-wrap {{
    width:100%; overflow-x:auto; margin-top:10px;
    border:1px solid var(--line); border-radius:10px; background:var(--card);
  }}
  table {{ width:100%; border-collapse:collapse; font-size:12.5px; margin:0; }}
  th, td {{ text-align:left; padding:8px 11px; border-bottom:1px solid var(--line); vertical-align:top; }}
  tr:last-child td {{ border-bottom:none; }}
  th {{ background:var(--bg-elev); font-weight:600; color:var(--ink-soft); white-space:nowrap; }}
  .empty-inline {{ padding:14px; background:var(--card); border:1px dashed var(--line); border-radius:12px; color:var(--muted); font-size:12.5px; margin-bottom:20px; }}

  dialog {{
    border:1px solid var(--line-strong); border-radius:15px; max-width:650px; width:92%;
    padding:20px 22px; background:var(--card); color:var(--ink); box-shadow:0 24px 60px rgba(0,0,0,.45);
  }}
  dialog::backdrop {{ background:rgba(5,7,11,.68); backdrop-filter:blur(4px); }}
  .form-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin:14px 0; }}
  .form-grid .full {{ grid-column:1 / -1; }}
  .field label {{ display:block; font-size:11.5px; font-weight:600; margin-bottom:4px; color:var(--ink-soft); }}
  .presets {{ display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin:10px 0 4px; font-size:12px; color:var(--muted); }}
  .toast {{
    position:fixed; right:20px; bottom:20px; z-index:90; max-width:440px;
    padding:10px 14px; border-radius:10px; font-size:12.5px; font-weight:600;
    background:var(--card); color:var(--ink); border:1px solid var(--line-strong);
    box-shadow:var(--shadow); display:none;
  }}
  .toast.show {{ display:block; }}
  .toast.ok {{ border-color:var(--ok); color:var(--ok-ink); }}
  .toast.err {{ border-color:var(--danger); color:var(--danger-ink); }}

  .star-pill {{ border-color:rgba(245,158,11,.35); }}
  .star-pill:hover {{ border-color:var(--warn); }}
  .star-pill.is-starred {{ background:var(--warn-bg); color:var(--warn-ink); border-color:rgba(245,158,11,.45); }}
  @keyframes starSlideIn {{
    from {{ opacity:0; transform:translateY(-10px) scale(.97); }}
    to {{ opacity:1; transform:translateY(0) scale(1); }}
  }}
  @keyframes starBadgePulse {{
    0%, 100% {{ transform:scale(1); }}
    50% {{ transform:scale(1.16) rotate(-6deg); }}
  }}
  .star-prompt {{
    position:fixed; top:62px; right:20px; z-index:95;
    width:min(392px, calc(100vw - 32px));
    background:var(--card); color:var(--ink);
    border:1px solid rgba(245,158,11,.38); border-left:4px solid var(--warn);
    border-radius:14px; padding:14px 16px;
    box-shadow:0 20px 50px rgba(0,0,0,.48), 0 0 28px rgba(245,158,11,.14);
    display:none;
  }}
  :root[data-theme="light"] .star-prompt {{
    box-shadow:0 14px 36px rgba(17,24,39,.14), 0 0 0 1px rgba(217,119,6,.25);
  }}
  .star-prompt.show {{ display:block; animation:starSlideIn .26s cubic-bezier(.16,1,.3,1); }}
  .star-prompt.show .star-badge-icon {{ animation:starBadgePulse .9s ease 1; }}
  .star-prompt.is-thanks {{ border-color:rgba(16,185,129,.4); border-left-color:var(--ok); }}
  .star-head {{ display:flex; align-items:flex-start; justify-content:space-between; gap:10px; margin-bottom:5px; }}
  .star-title-wrap {{ display:flex; align-items:center; gap:8px; font-size:13.5px; line-height:1.35; }}
  .star-badge-icon {{
    width:22px; height:22px; border-radius:7px; flex-shrink:0;
    display:grid; place-items:center; font-size:12px;
    background:var(--warn-bg); color:var(--warn-ink);
  }}
  .star-prompt.is-thanks .star-badge-icon {{ background:var(--ok-bg); color:var(--ok-ink); }}
  .star-close {{
    background:transparent; border:none; color:var(--muted); cursor:pointer;
    font-size:17px; line-height:1; padding:0 2px; border-radius:5px;
  }}
  .star-close:hover {{ color:var(--ink); background:var(--code-bg); }}
  .star-desc {{ font-size:12px; color:var(--muted); line-height:1.45; margin-bottom:11px; }}
  .star-actions {{ display:flex; justify-content:flex-end; align-items:center; gap:8px; flex-wrap:wrap; }}
  .btn.star-cta {{ background:var(--warn); color:#1a1202; border-color:transparent; font-weight:700; }}
  .btn.star-cta:hover {{ filter:brightness(1.07); border-color:transparent; }}
  @media (max-width:720px) {{
    .star-prompt {{ top:14px; right:12px; left:12px; width:auto; }}
  }}
</style>
</head>
<body>
<header class="topbar">
  <div class="topbar-inner">
    <div class="brand">
      <div class="brand-mark">⚡</div>
      <h1>{html.escape(t['page_title'])}</h1>
      {roi_pill}
    </div>
    <div class="toolbar">
      <button class="btn star-pill" type="button" id="btnTopStar" onclick="onTopStarClick()">
        <span id="topStarIcon">☆</span> <span id="topStarLabel">{html.escape(t['btn_star'])}</span>
      </button>
      {(f'<a class="btn ghost" href="{html.escape(runtime.openmausbot_url)}" target="_blank" rel="noreferrer">🤖 {html.escape(t["open_maus"])}</a>' if maus_live else '')}
      {(f'<a class="btn ghost" href="{html.escape(runtime.t3code_url)}" target="_blank" rel="noreferrer">📱 {html.escape(t["open_t3"])}</a>' if t3_live else '')}
      <form method="POST" action="/api/refresh-telemetry" data-async="1" style="margin:0">
        {state_inputs}
        <button id="btnRefresh" class="btn" type="submit">🔄 {html.escape(t['btn_refresh'])}</button>
      </form>
      <button class="btn" type="button" onclick="openSettingsModal()">⚙️ {html.escape(t['btn_settings'])}</button>
      {(f'<form method="POST" action="/api/notify-test" data-async="1" style="margin:0">{state_inputs}<button class="btn ghost" type="submit">🔔 {html.escape(t["btn_test_push"])}</button></form>' if runtime.notify_enabled else '')}
      <a class="btn ghost" href="/?privacy={next_privacy}&lang={use_lang}">{'🔓' if privacy else '🕶️'} {html.escape(t['btn_privacy_off'] if privacy else t['btn_privacy_on'])}</a>
      <a class="btn ghost" href="/?privacy={priv_val}&lang={other_lang}">🌐 {lang_label}</a>
      <button class="btn ghost" type="button" id="themeBtn" onclick="toggleTheme()" title="Toggle Theme">◐</button>
    </div>
  </div>
</header>

<main class="wrap">
  <div class="sub-strip">
    <span>{html.escape(t['subtitle'])}</span>
    <div class="sub-pills">
      <span class="pill">{html.escape(t['triage'])}: {html.escape(t['triage_paid'] if runtime.paid_api_enabled else t['triage_rules'])}</span>
      <span class="pill">{html.escape(t['notifier'])}: {html.escape(t['notifier_on'] if runtime.notify_enabled else t['notifier_off'])}</span>
      <span class="pill">{html.escape(t['repos'])}: {len(repos)}</span>
      <span>{html.escape(t['shortcuts_hint'])}</span>
    </div>
  </div>

  {banner_html}
  {routing_html}

  <section class="section">
    <div class="section-head">
      <h2>📊 {html.escape(t['sec_pools'])} <span class="count-pill">{len(pools)}</span></h2>
    </div>
    <div class="bento bento-pools">{''.join(pool_cards)}</div>
  </section>

  <section class="section">
    <div class="section-head">
      <h2>🔥 {html.escape(t['sec_advisor'])} <span class="count-pill">{len(advisor)}</span></h2>
    </div>
    {advisor_block}
  </section>

  <section class="section">
    <div class="section-head">
      <h2>🧩 {html.escape(t['sec_wheels'])} <span class="count-pill">{len(bridges)}</span></h2>
    </div>
    <div class="bento bento-wheels">{''.join(bridge_cards)}</div>
  </section>

  {awaiting_section}

  <details class="drawer" {'open' if others else ''}>
    <summary><span>🗂️ {html.escape(t['sec_history'])}</span><span class="count-pill">{len(others)}</span></summary>
    <div class="table-wrap"><table><thead><tr><th>{html.escape(t['th_id'])}</th><th>{html.escape(t['th_proj'])}</th><th>{html.escape(t['th_title'])}</th><th>{html.escape(t['th_status'])}</th><th>{html.escape(t['th_updated'])}</th></tr></thead><tbody>{history_rows or f'<tr><td colspan="5">{html.escape(t["no_rows"])}</td></tr>'}</tbody></table></div>
  </details>

  <details class="drawer">
    <summary><span>🔗 {html.escape(t['sec_matrix'])}</span><span class="count-pill">{len(repos)}</span></summary>
    <div class="table-wrap"><table><thead><tr><th>{html.escape(t['th_proj'])}</th><th>{html.escape(t['th_path'])}</th><th>{html.escape(t['th_summary'])}</th><th>{html.escape(t['th_updated'])}</th></tr></thead><tbody>{repo_rows or f'<tr><td colspan="4">{html.escape(t["no_rows"])}</td></tr>'}</tbody></table></div>
  </details>
</main>

<aside id="starPrompt" class="star-prompt" role="region" aria-label="GitHub Star">
  <div class="star-head">
    <div class="star-title-wrap">
      <span class="star-badge-icon" id="starPromptIcon">⭐</span>
      <strong id="starPromptTitle">{html.escape(t['star_prompt_title'])}</strong>
    </div>
    <button type="button" class="star-close" onclick="dismissStarPrompt()" aria-label="Close">×</button>
  </div>
  <div class="star-desc" id="starPromptDesc">{html.escape(t['star_prompt_desc'])}</div>
  <div class="star-actions" id="starPromptActions">
    <button type="button" class="btn xs ghost" onclick="dismissStarPrompt()">{html.escape(t['star_dismiss'])}</button>
    <button type="button" class="btn xs star-cta" id="starActionBtn" onclick="starInPlace()">⭐ {html.escape(t['star_cta'])}</button>
  </div>
</aside>

<div id="toast" class="toast" role="status"></div>

<dialog id="settingsModal">
  <h2 style="margin:0 0 6px;font-size:17px;">⚙️ {html.escape(t['modal_title'])}</h2>
  <div class="kicker">{html.escape(t['modal_desc'])}</div>
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
        <label>{html.escape(t['lbl_t3'])}</label>
        <input type="text" name="T3CODE_URL" value="{html.escape(runtime.t3code_url)}" />
      </div>
      <div class="field">
        <label>{html.escape(t['lbl_maus'])}</label>
        <input type="text" name="OPENMAUSBOT_URL" value="{html.escape(runtime.openmausbot_url)}" />
      </div>
      <div class="field">
        <label>{html.escape(t['lbl_vps'])}</label>
        <input type="text" name="VPS_SSH_ALIAS" value="{html.escape(runtime.vps_ssh_alias)}" placeholder="my-gcp-vps" />
      </div>
      <div class="field full">
        <label>{html.escape(t['lbl_proxy'])}</label>
        <input type="text" name="FLEET_PROXY" value="{html.escape(runtime.fleet_proxy)}" placeholder="http://127.0.0.1:1082" />
      </div>
      <div class="field full">
        <label>{html.escape(t['lbl_notify'])}</label>
        <input type="text" name="FLEET_NOTIFY_URLS" value="{html.escape(runtime.fleet_notify_urls)}" placeholder="tgram://BOT_TOKEN/CHAT_ID" />
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
      <button type="button" class="btn" onclick="document.getElementById('settingsModal').close()">{html.escape(t['btn_cancel'])}</button>
      <button type="submit" class="btn primary">{html.escape(t['btn_save'])}</button>
    </div>
  </form>
</dialog>

<script>
const LOCAL_PAID_USD = {paid_local_used:.6f};
const COPIED_LABEL = {repr(t['copied'])};
const COPY_LABEL = {repr(t['copy_cmd'])};
const COPY_ERR_LABEL = {repr(t['copy_err'])};
const CSRF_TOKEN = {json.dumps(csrf_token)};
const GITHUB_REPO_URL = {json.dumps(GITHUB_REPO_URL)};
const STAR_I18N = {json.dumps({
    "star": t["btn_star"],
    "starred": t["btn_starred"],
    "promptTitle": t["star_prompt_title"],
    "promptDesc": t["star_prompt_desc"],
    "cta": t["star_cta"],
    "starring": t["star_starring"],
    "openGh": t["star_open_gh"],
    "dismiss": t["star_dismiss"],
    "thanksTitle": t["star_thanks_title"],
    "thanksDesc": t["star_thanks_desc"],
}, ensure_ascii=False)};

function toggleTheme() {{
  const cur = document.documentElement.getAttribute('data-theme') || 'dark';
  const next = cur === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  try {{ localStorage.setItem('fleet_theme', next); }} catch(e) {{}}
}}
function openSettingsModal() {{
  const d = document.getElementById('settingsModal');
  if (d && !d.open && typeof d.showModal === 'function') d.showModal();
}}
function setBudgetPreset(val) {{
  document.getElementById('inp_budget').value = String(val);
  syncExternalFromRemaining();
}}
function syncExternalFromRemaining() {{
  const b = parseFloat(document.getElementById('inp_budget').value || '0');
  const remRaw = document.getElementById('inp_rem_quick').value;
  if (remRaw === '' || isNaN(b) || b <= 0) return;
  const rem = parseFloat(remRaw);
  if (isNaN(rem)) return;
  const ext = Math.max(0, b - rem - LOCAL_PAID_USD);
  document.getElementById('inp_ext').value = ext.toFixed(2);
}}
let _toastTimer = null;
function showToast(text, ok) {{
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = text;
  el.className = 'toast show ' + (ok ? 'ok' : 'err');
  if (_toastTimer) clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => {{ el.classList.remove('show'); }}, 4500);
}}
(function restoreFlashToast() {{
  try {{
    const raw = sessionStorage.getItem('fleet_flash');
    if (raw) {{
      sessionStorage.removeItem('fleet_flash');
      const f = JSON.parse(raw);
      if (f && f.text) showToast(f.text, !!f.ok);
    }}
  }} catch(e) {{}}
}})();
function _writeClipboard(text, onOk) {{
  const onFallback = () => {{
    try {{
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      const ok = document.execCommand('copy');
      document.body.removeChild(ta);
      if (ok) onOk(); else showToast(COPY_ERR_LABEL, false);
    }} catch(e) {{
      showToast(COPY_ERR_LABEL, false);
    }}
  }};
  if (navigator.clipboard && navigator.clipboard.writeText) {{
    navigator.clipboard.writeText(text).then(onOk).catch(onFallback);
  }} else {{
    onFallback();
  }}
}}
function copyText(btn, text) {{
  recordStarEngagement();
  _writeClipboard(text, () => {{
    btn.textContent = COPIED_LABEL;
    setTimeout(() => {{ btn.textContent = COPY_LABEL; }}, 1500);
  }});
}}
function copyModelId(text) {{
  if (!text) return;
  recordStarEngagement();
  _writeClipboard(text, () => showToast(COPIED_LABEL + ': ' + text, true));
}}
document.querySelectorAll('form[data-async="1"]').forEach((form) => {{
  form.addEventListener('submit', async (ev) => {{
    ev.preventDefault();
    recordStarEngagement();
    const btn = form.querySelector('button[type="submit"]');
    const origText = btn ? btn.textContent : '';
    if (btn) {{ btn.disabled = true; btn.textContent = '⏳ ...'; }}
    try {{
      const payload = {{}};
      new FormData(form).forEach((v, k) => {{ payload[k] = v; }});
      const resp = await fetch(form.action, {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(payload),
      }});
      const data = await resp.json().catch(() => ({{ ok: resp.ok, message: resp.statusText }}));
      const msgText = data.message || (data.ok ? 'Done' : 'Error');
      showToast(msgText, !!data.ok);
      if (data.ok) {{
        try {{ sessionStorage.setItem('fleet_flash', JSON.stringify({{ text: msgText, ok: true }})); }} catch(e) {{}}
        setTimeout(() => {{ window.location.reload(); }}, 350);
      }} else if (btn) {{
        btn.disabled = false;
        btn.textContent = origText;
      }}
    }} catch (err) {{
      showToast(String(err), false);
      if (btn) {{ btn.disabled = false; btn.textContent = origText; }}
    }}
  }});
}});
document.addEventListener('keydown', (ev) => {{
  if (ev.metaKey || ev.ctrlKey || ev.altKey) return;
  const tgt = ev.target;
  if (tgt && (['INPUT', 'TEXTAREA', 'SELECT'].includes(tgt.tagName) || tgt.isContentEditable)) return;
  const dlg = document.getElementById('settingsModal');
  if (dlg && dlg.open) return;
  if (ev.key === 'r' || ev.key === 'R') {{
    const btn = document.getElementById('btnRefresh');
    if (btn) btn.click();
  }} else if (ev.key === 's' || ev.key === 'S') {{
    openSettingsModal();
  }}
}});

const STAR_DISMISSED_KEY = 'ultra:star-v2:dismissed';
const STAR_DONE_KEY = 'ultra:star-v2:starred';
const STAR_ACTIONS_KEY = 'ultra:star-v2:actions';
const STAR_SESSIONS_KEY = 'ultra:star-v2:sessions';
const STAR_LAST_SESSION_KEY = 'ultra:star-v2:last_session_ts';
let _starAutoHideTimer = null;
let _confettiState = null;

function _starStorageGet(key) {{
  try {{ return localStorage.getItem(key) === '1'; }} catch (e) {{ return false; }}
}}
function _starStorageSet(key, val) {{
  try {{
    if (val) localStorage.setItem(key, '1');
    else localStorage.removeItem(key);
    return true;
  }} catch (e) {{
    return false;
  }}
}}
function _starGetInt(key) {{
  try {{
    const n = parseInt(localStorage.getItem(key) || '0', 10);
    return Number.isFinite(n) ? n : 0;
  }} catch (e) {{
    return 0;
  }}
}}
function _starSetInt(key, val) {{
  try {{ localStorage.setItem(key, String(val)); return true; }} catch (e) {{ return false; }}
}}
function recordStarEngagement() {{
  _starSetInt(STAR_ACTIONS_KEY, _starGetInt(STAR_ACTIONS_KEY) + 1);
}}
function _canPersistStar() {{
  try {{
    const probe = '__ultra_star_probe__';
    localStorage.setItem(probe, '1');
    localStorage.removeItem(probe);
    return true;
  }} catch (e) {{
    return false;
  }}
}}
const _settingsForm = document.querySelector('#settingsModal form');
if (_settingsForm) {{
  _settingsForm.addEventListener('submit', () => recordStarEngagement());
}}
function setTopStarredUI(isStarred) {{
  const btn = document.getElementById('btnTopStar');
  const icon = document.getElementById('topStarIcon');
  const lbl = document.getElementById('topStarLabel');
  if (btn) btn.classList.toggle('is-starred', !!isStarred);
  if (icon) icon.textContent = isStarred ? '★' : '☆';
  if (lbl) lbl.textContent = isStarred ? STAR_I18N.starred : STAR_I18N.star;
}}
function _ensureConfettiCanvas() {{
  const w = window.innerWidth || 1280;
  const h = window.innerHeight || 720;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  if (_confettiState && document.body.contains(_confettiState.canvas)) {{
    return _confettiState;
  }}
  const canvas = document.createElement('canvas');
  canvas.setAttribute('aria-hidden', 'true');
  canvas.style.cssText = 'position:fixed;inset:0;width:100vw;height:100vh;pointer-events:none;z-index:9999;';
  canvas.width = Math.floor(w * dpr);
  canvas.height = Math.floor(h * dpr);
  document.body.appendChild(canvas);
  const ctx = canvas.getContext('2d');
  if (!ctx) {{ canvas.remove(); return null; }}
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  const state = {{ canvas, ctx, w, h, particles: [], rafId: 0, lastTs: 0, onResize: null }};
  state.onResize = () => {{
    const nw = window.innerWidth || 1280;
    const nh = window.innerHeight || 720;
    const ndpr = Math.min(window.devicePixelRatio || 1, 2);
    state.w = nw;
    state.h = nh;
    canvas.width = Math.floor(nw * ndpr);
    canvas.height = Math.floor(nh * ndpr);
    ctx.setTransform(ndpr, 0, 0, ndpr, 0, 0);
  }};
  window.addEventListener('resize', state.onResize, {{ passive: true }});
  _confettiState = state;
  return state;
}}
function _spawnConfettiBurst(opts) {{
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

  for (let i = 0; i < count; i++) {{
    const scalar = baseScalar * (0.85 + Math.random() * 0.65);
    state.particles.push({{
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
    }});
  }}

  if (state.rafId) return;
  state.lastTs = performance.now();

  const drawStar = (c, rInner, rOuter) => {{
    c.beginPath();
    let rot = (Math.PI / 2) * 3;
    const step = Math.PI / 5;
    for (let i = 0; i < 5; i++) {{
      c.lineTo(Math.cos(rot) * rOuter, Math.sin(rot) * rOuter);
      rot += step;
      c.lineTo(Math.cos(rot) * rInner, Math.sin(rot) * rInner);
      rot += step;
    }}
    c.closePath();
    c.fill();
  }};

  const stepFrame = (now) => {{
    const dt = Math.min(2.2, Math.max(0.25, (now - state.lastTs) / 16.6667));
    state.lastTs = now;
    const ctx = state.ctx;
    ctx.clearRect(0, 0, state.w, state.h);

    const alive = [];
    for (const p of state.particles) {{
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

      if (p.shape === 'circle') {{
        ctx.beginPath();
        const rx = Math.max(1.5, Math.abs(x2 - x1) * p.ovalScalar);
        const ry = Math.max(1.5, Math.abs(y2 - y1) * p.ovalScalar);
        ctx.ellipse(p.x, p.y, rx, ry, (Math.PI / 10) * p.wobble, 0, Math.PI * 2);
        ctx.fill();
      }} else if (p.shape === 'star') {{
        ctx.translate(p.x, p.y);
        ctx.rotate(p.tiltAngle);
        ctx.scale(1, Math.max(0.35, Math.abs(p.tiltCos)));
        drawStar(ctx, 4.5 * p.scalar, 9.5 * p.scalar);
      }} else if (p.shape === 'streamer') {{
        ctx.beginPath();
        ctx.lineWidth = Math.max(2, 2.8 * p.scalar);
        ctx.lineCap = 'round';
        ctx.moveTo(p.x, p.y);
        const mx = (p.x + p.wobbleX) * 0.5 + p.tiltSin * 7 * p.scalar;
        const my = (p.y + p.wobbleY) * 0.5 + p.tiltCos * 7 * p.scalar;
        ctx.quadraticCurveTo(mx, my, p.wobbleX + (p.wobbleX - p.x), p.wobbleY + (p.wobbleY - p.y));
        ctx.stroke();
      }} else {{
        ctx.beginPath();
        ctx.moveTo(Math.floor(p.x), Math.floor(p.y));
        ctx.lineTo(Math.floor(p.wobbleX), Math.floor(y1));
        ctx.lineTo(Math.floor(x2), Math.floor(y2));
        ctx.lineTo(Math.floor(x1), Math.floor(p.wobbleY));
        ctx.closePath();
        ctx.fill();
      }}
      ctx.restore();
      alive.push(p);
    }}
    state.particles = alive;
    if (alive.length > 0) {{
      state.rafId = requestAnimationFrame(stepFrame);
    }} else {{
      window.removeEventListener('resize', state.onResize);
      state.canvas.remove();
      _confettiState = null;
    }}
  }};
  state.rafId = requestAnimationFrame(stepFrame);
}}
function celebrateConfetti(anchorEl) {{
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const w = window.innerWidth || 1280;
  const h = window.innerHeight || 720;
  let ox = w * 0.84;
  let oy = h * 0.16;
  if (anchorEl && typeof anchorEl.getBoundingClientRect === 'function') {{
    const rect = anchorEl.getBoundingClientRect();
    if (rect.width > 0 || rect.height > 0) {{
      ox = rect.left + rect.width * 0.5;
      oy = rect.top + rect.height * 0.45;
    }}
  }}
  _spawnConfettiBurst({{
    ox,
    oy,
    particleCount: 180,
    angle: 90,
    spread: 360,
    startVelocity: 54,
    decay: 0.912,
    gravity: 1.05,
    ticks: 230,
    scalar: 1.28,
  }});
  setTimeout(() => {{
    _spawnConfettiBurst({{
      x: 0.08,
      y: 0.68,
      particleCount: 70,
      angle: 58,
      spread: 64,
      startVelocity: 64,
      decay: 0.91,
      gravity: 1.0,
      drift: 0.2,
      ticks: 220,
      scalar: 1.22,
    }});
    _spawnConfettiBurst({{
      x: 0.92,
      y: 0.68,
      particleCount: 70,
      angle: 122,
      spread: 64,
      startVelocity: 64,
      decay: 0.91,
      gravity: 1.0,
      drift: -0.2,
      ticks: 220,
      scalar: 1.22,
    }});
  }}, 150);
  setTimeout(() => {{
    _spawnConfettiBurst({{
      ox,
      oy,
      particleCount: 45,
      angle: 90,
      spread: 360,
      startVelocity: 36,
      decay: 0.915,
      gravity: 0.85,
      ticks: 210,
      scalar: 1.38,
      shapes: ['star', 'circle'],
      colors: ['#fbbf24', '#fde047', '#f59e0b', '#fffbeb'],
    }});
  }}, 320);
}}
function dismissStarPrompt(persist = true) {{
  if (_starAutoHideTimer) {{ clearTimeout(_starAutoHideTimer); _starAutoHideTimer = null; }}
  const box = document.getElementById('starPrompt');
  if (box) box.classList.remove('show');
  if (persist) {{
    _starStorageSet(STAR_DISMISSED_KEY, true);
    fetch('/api/github-star-dismiss', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ csrf: CSRF_TOKEN }}),
    }}).catch(() => undefined);
  }}
}}
function resetStarPrompt() {{
  if (_starAutoHideTimer) {{ clearTimeout(_starAutoHideTimer); _starAutoHideTimer = null; }}
  const box = document.getElementById('starPrompt');
  const icon = document.getElementById('starPromptIcon');
  const title = document.getElementById('starPromptTitle');
  const desc = document.getElementById('starPromptDesc');
  const actions = document.getElementById('starPromptActions');
  if (box) box.classList.remove('is-thanks');
  if (icon) icon.textContent = '⭐';
  if (title) title.textContent = STAR_I18N.promptTitle;
  if (desc) desc.textContent = STAR_I18N.promptDesc;
  if (actions) {{
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
    ctaBtn.textContent = '⭐ ' + STAR_I18N.cta;
    ctaBtn.onclick = () => starInPlace();
    actions.append(dismissBtn, ctaBtn);
  }}
}}
function showThanksInPlace() {{
  if (_starAutoHideTimer) clearTimeout(_starAutoHideTimer);
  const box = document.getElementById('starPrompt');
  const icon = document.getElementById('starPromptIcon');
  const title = document.getElementById('starPromptTitle');
  const desc = document.getElementById('starPromptDesc');
  const actions = document.getElementById('starPromptActions');
  if (box) {{ box.classList.add('show'); box.classList.add('is-thanks'); }}
  if (icon) icon.textContent = '🎉';
  if (title) title.textContent = STAR_I18N.thanksTitle;
  if (desc) desc.textContent = STAR_I18N.thanksDesc;
  if (actions) {{
    actions.innerHTML = '';
    const link = document.createElement('a');
    link.className = 'btn xs ghost';
    link.href = GITHUB_REPO_URL;
    link.target = '_blank';
    link.rel = 'noreferrer';
    link.textContent = 'GitHub ↗';
    actions.appendChild(link);
  }}
  _starAutoHideTimer = setTimeout(() => dismissStarPrompt(false), 5000);
}}
async function starInPlace() {{
  const box = document.getElementById('starPrompt');
  const btn = document.getElementById('starActionBtn');
  if (btn) {{ btn.disabled = true; btn.textContent = '⏳ ' + STAR_I18N.starring; }}
  try {{
    const resp = await fetch('/api/github-star', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ csrf: CSRF_TOKEN }}),
    }});
    const data = await resp.json().catch(() => ({{ ok: false, fallback_url: GITHUB_REPO_URL }}));
    if (data.ok && data.starred) {{
      _starStorageSet(STAR_DONE_KEY, true);
      _starStorageSet(STAR_DISMISSED_KEY, true);
      setTopStarredUI(true);
      showThanksInPlace();
      celebrateConfetti(box);
      return;
    }}
    const targetUrl = data.fallback_url || GITHUB_REPO_URL;
    const canPopup = !navigator.userActivation || navigator.userActivation.isActive !== false;
    const opened = canPopup ? window.open(targetUrl, '_blank', 'noopener,noreferrer') : null;
    if (opened) {{
      _starStorageSet(STAR_DISMISSED_KEY, true);
      showThanksInPlace();
      celebrateConfetti(box);
      return;
    }}
    if (btn) {{
      btn.disabled = false;
      btn.textContent = '⭐ ' + STAR_I18N.openGh;
      btn.onclick = () => {{
        window.open(targetUrl, '_blank', 'noopener,noreferrer');
        _starStorageSet(STAR_DISMISSED_KEY, true);
        showThanksInPlace();
        celebrateConfetti(box);
      }};
    }}
  }} catch (err) {{
    if (btn) {{
      btn.disabled = false;
      btn.textContent = '⭐ ' + STAR_I18N.openGh;
      btn.onclick = () => {{
        window.open(GITHUB_REPO_URL, '_blank', 'noopener,noreferrer');
        _starStorageSet(STAR_DISMISSED_KEY, true);
        showThanksInPlace();
        celebrateConfetti(box);
      }};
    }}
  }}
}}
function onTopStarClick() {{
  const btn = document.getElementById('btnTopStar');
  if (btn && btn.classList.contains('is-starred')) {{
    showThanksInPlace();
    celebrateConfetti(btn);
    return;
  }}
  resetStarPrompt();
  const box = document.getElementById('starPrompt');
  if (box) box.classList.add('show');
}}
function isMatureEnough(info) {{
  const m = (info && info.maturity) || {{}};
  const ageHours = Number(m.age_hours || 0);
  const taskCount = Number(m.task_count || 0);
  const totalOps = Math.max(Number(m.server_ops || 0), _starGetInt(STAR_ACTIONS_KEY));
  const sessions = _starGetInt(STAR_SESSIONS_KEY);
  return (ageHours >= 0.25 && totalOps >= 5)
    || (ageHours >= 24 && (sessions >= 3 || taskCount >= 2 || totalOps >= 2))
    || (taskCount >= 3 && sessions >= 2);
}}
function waitForVisibleAttention() {{
  return new Promise((resolve) => {{
    let calmTimer = null;
    let seenSignal = false;
    let done = false;
    const signals = ['pointermove', 'pointerdown', 'wheel', 'keydown', 'touchstart'];
    const isViewClear = () => {{
      if (document.visibilityState !== 'visible' || !document.hasFocus()) return false;
      const dlg = document.getElementById('settingsModal');
      if (dlg && dlg.open) return false;
      const toast = document.getElementById('toast');
      if (toast && toast.classList.contains('show')) return false;
      return true;
    }};
    const cleanup = () => {{
      if (calmTimer) clearTimeout(calmTimer);
      signals.forEach((ev) => window.removeEventListener(ev, onSignal, true));
      document.removeEventListener('visibilitychange', scheduleCheck);
      window.removeEventListener('focus', scheduleCheck);
    }};
    const scheduleCheck = () => {{
      if (done) return;
      if (calmTimer) clearTimeout(calmTimer);
      if (!seenSignal || !isViewClear()) {{
        if (seenSignal && document.visibilityState === 'visible' && document.hasFocus()) {{
          calmTimer = setTimeout(scheduleCheck, 600);
        }}
        return;
      }}
      calmTimer = setTimeout(() => {{
        if (done) return;
        if (!isViewClear()) {{
          scheduleCheck();
          return;
        }}
        done = true;
        cleanup();
        resolve();
      }}, 1200);
    }};
    const onSignal = () => {{
      seenSignal = true;
      scheduleCheck();
    }};
    signals.forEach((ev) => window.addEventListener(ev, onSignal, {{ capture: true, passive: true }}));
    document.addEventListener('visibilitychange', scheduleCheck);
    window.addEventListener('focus', scheduleCheck);
  }});
}}
(function initStarPrompt() {{
  const canPersist = _canPersistStar();
  if (_starStorageGet(STAR_DONE_KEY)) setTopStarredUI(true);

  if (canPersist) {{
    const nowMs = Date.now();
    const lastMs = _starGetInt(STAR_LAST_SESSION_KEY);
    if (!lastMs || (nowMs - lastMs) > 30 * 60 * 1000) {{
      _starSetInt(STAR_SESSIONS_KEY, _starGetInt(STAR_SESSIONS_KEY) + 1);
      _starSetInt(STAR_LAST_SESSION_KEY, nowMs);
    }}
  }}

  const params = new URLSearchParams(window.location.search || '');
  if (params.get('star_preview') === '1') {{
    setTimeout(() => {{
      resetStarPrompt();
      const box = document.getElementById('starPrompt');
      if (box) box.classList.add('show');
    }}, 600);
    return;
  }}

  fetch('/api/github-star')
    .then((r) => (r.ok ? r.json() : null))
    .then(async (info) => {{
      if (!info) return;
      if (info.starred === true) {{
        _starStorageSet(STAR_DONE_KEY, true);
        _starStorageSet(STAR_DISMISSED_KEY, true);
        setTopStarredUI(true);
        return;
      }}
      if (info.maturity && info.maturity.dismissed) {{
        _starStorageSet(STAR_DISMISSED_KEY, true);
        return;
      }}
      if (!canPersist || _starStorageGet(STAR_DISMISSED_KEY)) return;
      if (!isMatureEnough(info)) return;
      await waitForVisibleAttention();
      if (_starStorageGet(STAR_DISMISSED_KEY) || _starStorageGet(STAR_DONE_KEY)) return;
      resetStarPrompt();
      const box = document.getElementById('starPrompt');
      if (box) box.classList.add('show');
    }})
    .catch(() => undefined);
}})();
</script>
</body>
</html>"""
