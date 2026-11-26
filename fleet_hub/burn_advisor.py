"""Ultra Burn Advisor: actionable routing advice to maximize Google AI Ultra value before quota resets."""

from __future__ import annotations

import calendar
from datetime import datetime
from typing import Any


def build_burn_recommendations(
    cards: list[dict[str, Any]],
    lens_stats: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> list[dict[str, str]]:
    """Analyze live pool balances and emit concrete scheduling advice."""
    cur = now or datetime.now()
    last_day = calendar.monthrange(cur.year, cur.month)[1]
    days_left_inclusive = max(1, last_day - cur.day + 1)
    by_pool = {c.get("pool", ""): c for c in cards}
    advice: list[dict[str, str]] = []

    gem = by_pool.get("agy_gemini_weekly") or {}
    c5 = by_pool.get("agy_claude_5h") or {}
    gem_pct = gem.get("pct")
    c5_pct = c5.get("pct")
    gem_meta = gem.get("meta") or {}
    gem_is_5h = bool(
        gem_meta.get("is_rolling_5h")
        or (isinstance(gem_meta.get("hours_left"), (int, float)) and float(gem_meta["hours_left"]) <= 8.5)
    )

    if gem_is_5h and isinstance(gem_pct, (int, float)) and isinstance(c5_pct, (int, float)) and (gem_pct >= 50.0 or c5_pct >= 50.0):
        reset_txt = ((c5.get("meta") or {}).get("reset_text")) or "5小时内重置"
        hours_left = (c5.get("meta") or {}).get("hours_left")
        reset_en = f"{hours_left:.1f}h reset" if isinstance(hours_left, (int, float)) else "5h rolling reset"
        advice.append(
            {
                "severity": "opportunity",
                "pool": "AI Ultra 双 5h 滚动池",
                "pool_en": "AI Ultra Dual 5h Pools",
                "title": f"双 5h 滚动池满血（Gemini 4 {gem_pct:.0f}% · Claude 5.5 {c5_pct:.0f}%，{reset_txt}）",
                "title_en": f"Dual 5h Rolling Pools Ready (Gemini 4 {gem_pct:.0f}% · Claude 5.5 {c5_pct:.0f}% · {reset_en})",
                "action": "已解锁最高档双 5h 滚动池：在 T3 Code 里可并行跑 Gemini 4 Neon/Carbon 与 Claude Opus 5.5，每 5 小时各自回满。",
                "action_en": "Both Gemini 4 and Claude 5.5 refresh every 5 hours independently—run heavy parallel coding threads in T3 Code.",
                "command": "ultra wakeup",
            }
        )
    elif isinstance(c5_pct, (int, float)) and c5_pct >= 50.0:
        gem_note = f"（当前 Gemini 周池仅剩 {gem_pct:.1f}%）" if isinstance(gem_pct, (int, float)) and gem_pct < 45.0 else ""
        gem_note_en = f" (Gemini Weekly only {gem_pct:.1f}% left)" if isinstance(gem_pct, (int, float)) and gem_pct < 45.0 else ""
        reset_txt = ((c5.get("meta") or {}).get("reset_text")) or "5小时内重置"
        hours_left = (c5.get("meta") or {}).get("hours_left")
        reset_en = f"{hours_left:.1f}h reset" if isinstance(hours_left, (int, float)) else "5h rolling reset"
        advice.append(
            {
                "severity": "urgent" if isinstance(gem_pct, (int, float)) and gem_pct < 35.0 else "opportunity",
                "pool": "Claude 5.5 5h 滚动池",
                "pool_en": "Claude 5.5 5h Rolling Pool",
                "title": f"Claude Opus / Sonnet 5.5 还有 {c5_pct:.0f}% 空转（{reset_txt}）{gem_note}",
                "title_en": f"Claude Opus / Sonnet 5.5 is {c5_pct:.0f}% idle ({reset_en}){gem_note_en}",
                "action": "立即把编码、Review、重构线程在 T3 Code 或 Antigravity 切换到 Claude Opus 5.5，零损耗保护 Gemini 周池。",
                "action_en": "Switch coding, reviews, and threads in T3 Code / Antigravity to Claude 5.5 to protect Gemini Weekly.",
                "command": "ultra wakeup",
            }
        )

    flow = by_pool.get("flow_credits") or {}
    flow_meta = flow.get("meta") or {}
    flow_credits = flow_meta.get("credits")
    if isinstance(flow_credits, (int, float)) and flow_credits >= 100.0:
        per_day = flow_credits / days_left_inclusive
        clips_per_day = per_day / 27.0  # ~27 credits per 9s 720p omni-1.2-flash clip
        sev = "urgent" if days_left_inclusive <= 6 and flow_credits >= 2000 else "opportunity"
        advice.append(
            {
                "severity": sev,
                "pool": "Google Flow 月清零池",
                "pool_en": "Google Flow Monthly Expiring",
                "title": f"Flow 还剩 {flow_credits:,.0f} 积分（月底仅剩 {days_left_inclusive} 天，需日均烧 {per_day:,.0f} 点 ≈ {clips_per_day:.0f} 条 9s 720p 短片）",
                "title_en": f"Flow has {flow_credits:,.0f} credits ({days_left_inclusive}d left · target {per_day:,.0f}/day ≈ {clips_per_day:.0f} 9s clips)",
                "action": "月底过期不结转，建议批量投喂 `gflow video t2v / i2v`（2026-11 冲刺素材库或短剧母带）。",
                "action_en": "Credits expire at month-end with zero rollover; queue `gflow video t2v / i2v` batches.",
                "command": "gflow video t2v \"...\" --model omni-1.2-flash --duration 9 --aspect 9:16",
            }
        )

    colab = by_pool.get("colab_cu") or {}
    colab_bal = (colab.get("meta") or {}).get("balance")
    if isinstance(colab_bal, (int, float)) and colab_bal >= 100.0:
        cu_per_day = colab_bal / days_left_inclusive
        l4_hours = colab_bal / 1.94
        advice.append(
            {
                "severity": "opportunity",
                "pool": "Google Colab L4 GPU 池",
                "pool_en": "Google Colab L4 GPU Pool",
                "title": f"Colab 尚余 {colab_bal:.1f} CU（约合 {l4_hours:.0f} 小时 L4 算力，月末日均可用 {cu_per_day:.1f} CU）",
                "title_en": f"Colab has {colab_bal:.1f} CU (~{l4_hours:.0f}h L4 GPU · {cu_per_day:.1f} CU/day available)",
                "action": "重算力全数卸载云端：`colab run --gpu L4` 跑 F5-TTS 语音克隆、faster-whisper 对齐、SDXL 铜版画与多进程帧渲染。",
                "action_en": "Offload TTS, Whisper, and batch frame rendering to cloud L4 GPUs via `colab run --gpu L4`.",
                "command": "colab run --gpu L4 <script.py>",
            }
        )

    paid = by_pool.get("paid_gemini_api") or {}
    paid_meta = paid.get("meta") or {}
    if paid_meta.get("gcp_synced"):
        rem_usd = float(paid_meta.get("remaining_usd") or 0.0)
        bud_usd = float(paid_meta.get("budget_usd") or 0.0)
        used_usd = float(paid_meta.get("used_usd") or 0.0)
        eg = paid_meta.get("earliest_grant") or {}
        eg_rem = float(eg.get("remaining") or 0.0) if isinstance(eg, dict) else 0.0
        eg_end = str(eg.get("end_date") or "") if isinstance(eg, dict) else ""
        eg_days = eg.get("days_left") if isinstance(eg, dict) else None
        if isinstance(eg_days, int) and eg_days <= 21 and eg_rem >= 1.0:
            advice.append(
                {
                    "severity": "urgent",
                    "pool": "Google Cloud 赠金到期预警",
                    "pool_en": "GCP Grant Expiration Alert",
                    "title": f"一笔 ${eg_rem:.2f} 赠金将在 {eg_days} 天后（{eg_end}）过期",
                    "title_en": f"${eg_rem:.2f} GCP grant expires in {eg_days}d ({eg_end})",
                    "action": "建议优先把这部分额度用于 Gemini Batch API（半价）或 Cloud VM/存储开销，避免过期作废。",
                    "action_en": "Burn this grant on Gemini Batch API (50% off) or BYO Linux VPS / Cloud Storage before expiry.",
                    "command": "https://console.cloud.google.com/billing/credits",
                }
            )
        else:
            advice.append(
                {
                    "severity": "info",
                    "pool": "Google Cloud 赠金实测账本",
                    "pool_en": "GCP Billing Credits Ledger",
                    "title": f"GCP 赠金池实测可用 ${rem_usd:.2f} / ${bud_usd:.2f}（VPS 与云服务已扣 ${used_usd:.2f}）",
                    "title_en": f"GCP Credits: ${rem_usd:.2f} / ${bud_usd:.2f} left (${used_usd:.2f} spent on VPS/API)",
                    "action": (
                        f"最早一笔剩余 ${eg_rem:.2f} 到期日为 {eg_end}（有效期内可跨月抵扣 VPS/Gemini API）。"
                        if eg_end
                        else "可随时点卡片上的「自动读取 GCP 赠金」刷新最新扣费。"
                    ),
                    "action_en": (
                        f"Earliest tranche ${eg_rem:.2f} expires {eg_end} (covers VPS & Gemini Batch API)."
                        if eg_end
                        else "Click Auto-Sync GCP Credits on the card to refresh deductions."
                    ),
                    "command": "ultra sync-gcp-credits",
                }
            )
    elif paid.get("badge_tone") == "muted":
        advice.append(
            {
                "severity": "info",
                "pool": "Google Cloud / Gemini 赠金池",
                "pool_en": "Google Cloud / Gemini Credits",
                "title": "Developer Paid API 赠金池尚未同步",
                "title_en": "GCP / Developer Paid API credits not synced yet",
                "action": "点卡片上的「自动读取 GCP 赠金」自动汇总账单，或点 ⚙️ 手动设置总额（$10/$40/$50/$100）。",
                "action_en": "Click Auto-Sync GCP Credits on the card or open Calibrate to set your monthly credit grant.",
                "command": "ultra sync-gcp-credits",
            }
        )
    elif isinstance(paid_meta.get("remaining_usd"), (int, float)) and float(paid_meta["remaining_usd"]) >= 5.0:
        rem_usd = float(paid_meta["remaining_usd"])
        bud_usd = float(paid_meta.get("budget_usd") or 0.0)
        advice.append(
            {
                "severity": "urgent" if days_left_inclusive <= 6 else "opportunity",
                "pool": "Google Cloud / Gemini API 赠金池",
                "pool_en": "Google Cloud / Gemini Credits",
                "title": f"Paid API 赠金本月尚余 ${rem_usd:.2f} / ${bud_usd:.0f}（手动基数，建议点自动同步核实）",
                "title_en": f"Paid API credits: ${rem_usd:.2f} / ${bud_usd:.0f} left (manual baseline)",
                "action": "点击驾驶舱卡片上的「自动读取 GCP 赠金」可自动算出 VPS 等云消费后的真实可用余额。",
                "action_en": "Click Auto-Sync GCP Credits to verify real grant balances after VPS & cloud spend.",
                "command": "ultra sync-gcp-credits",
            }
        )
    elif paid.get("pool") == "paid_gemini_api" and paid_meta.get("budget_usd", 0) <= 0:
        advice.append(
            {
                "severity": "info",
                "pool": "Google Cloud / Gemini API 赠金池",
                "pool_en": "Google Cloud / Gemini Credits",
                "title": "Paid API Key 已接入，尚未同步 GCP 赠金总额",
                "title_en": "Paid API Key configured; GCP credit grants not synced",
                "action": "点击「自动读取 GCP 赠金」即可自动抓取所有生效赠金明细与剩余美元。",
                "action_en": "Click Auto-Sync GCP Credits to fetch active grant balances and expiration dates.",
                "command": "ultra sync-gcp-credits",
            }
        )

    if isinstance(lens_stats, dict) and float(lens_stats.get("d7_usd") or 0.0) > 0:
        d7_usd = float(lens_stats["d7_usd"])
        roi = d7_usd / 249.99
        advice.append(
            {
                "severity": "info",
                "pool": "Agy-Lens 算力回本统计",
                "pool_en": "Agy-Lens 7d ROI",
                "title": f"近 7 天本地实测等效 API 消耗 ${d7_usd:.2f}（{int(lens_stats.get('d7_calls') or 0):,} 次调用，7 天即回本 Ultra 月费的 {roi:.2f}×）",
                "title_en": f"7d API-equivalent value: ${d7_usd:.2f} ({int(lens_stats.get('d7_calls') or 0):,} calls · {roi:.2f}× of $249.99/mo Ultra)",
                "action": "终端执行 `agy-lens` 或在 Antigravity 右侧边栏打开 Agy Lens 查看各模型细粒度 tok/s 与上下文占比。",
                "action_en": "Run `agy-lens` or open the Agy Lens sidebar for per-model tok/s and context breakdown.",
                "command": "agy-lens",
            }
        )

    return advice


def compute_routing_verdict(
    cards: list[dict[str, Any]],
    lens_stats: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Produce a deterministic, zero-token routing verdict for OpenMausBot, T3 Code, and UI."""
    cur = now or datetime.now()
    last_day = calendar.monthrange(cur.year, cur.month)[1]
    days_left = max(1, last_day - cur.day + 1)
    by_pool = {c.get("pool", ""): c for c in cards}

    gem = by_pool.get("agy_gemini_weekly") or {}
    c5 = by_pool.get("agy_claude_5h") or {}
    flow = by_pool.get("flow_credits") or {}
    paid = by_pool.get("paid_gemini_api") or {}

    gem_pct = gem.get("pct")
    c5_pct = c5.get("pct")
    flow_credits = (flow.get("meta") or {}).get("credits")
    paid_meta = paid.get("meta") or {}
    eg = paid_meta.get("earliest_grant") or {}

    c5_val = float(c5_pct) if isinstance(c5_pct, (int, float)) else None
    gem_val = float(gem_pct) if isinstance(gem_pct, (int, float)) else None
    wakeup_needed = c5_val is not None and c5_val >= 99.0

    expiring_pools: list[str] = []
    if isinstance(flow_credits, (int, float)) and flow_credits >= 500.0 and days_left <= 7:
        expiring_pools.append(f"flow_credits ({flow_credits:,.0f} pts, {days_left}d left)")
    if isinstance(eg, dict) and isinstance(eg.get("days_left"), int) and eg["days_left"] <= 21 and float(eg.get("remaining") or 0) >= 1.0:
        expiring_pools.append(f"gcp_grant (${float(eg['remaining']):.2f}, {eg['days_left']}d left)")

    gem_meta = gem.get("meta") or {}
    gem_is_5h = bool(
        gem_meta.get("is_rolling_5h")
        or (isinstance(gem_meta.get("hours_left"), (int, float)) and float(gem_meta["hours_left"]) <= 8.5)
    )
    if gem_is_5h and gem_val is not None and gem_val >= 40.0 and c5_val is not None and c5_val >= 40.0:
        mode = "balanced"
        coding_model = "antigravity/claude-opus-5-5"
        triage_model = "antigravity/gemini-4-neon"
        headline_zh = f"AI Ultra 双 5h 滚动池全开（Gemini 4 {gem_val:.0f}% · Claude 5.5 {c5_val:.0f}%）"
        headline_en = f"AI Ultra Dual 5h Rolling Active (Gemini 4 {gem_val:.0f}% · Claude 5.5 {c5_val:.0f}%)"
        reason_zh = "两个主池均每 5 小时独立刷新：T3 Code 可自由并行使用 Claude Opus 5.5 与 Gemini 4 Neon/Carbon。"
        reason_en = "Both Gemini 4 and Claude 5.5 refresh every 5 hours independently—run heavy parallel threads in T3 Code."
    elif c5_val is not None and c5_val >= 40.0 and (gem_val is None or gem_val < 55.0):
        mode = "5h_harvest"
        coding_model = "antigravity/claude-opus-5-5"
        triage_model = "antigravity/claude-sonnet-5-5"
        gem_txt = f"{gem_val:.1f}%" if gem_val is not None else "n/a"
        headline_zh = f"优先切入 Claude 5.5 5h 滚动池（当前 {c5_val:.0f}% 空转 · Gemini 周池 {gem_txt}）"
        headline_en = f"Route to Claude 5.5 5h Pool ({c5_val:.0f}% idle · Gemini Weekly {gem_txt})"
        reason_zh = "5 小时池自动高频刷新且不消耗 Gemini 周池；建议将编码线程全部路由到 Claude Opus/Sonnet 5.5。"
        reason_en = "5h rolling quota resets multiple times daily without touching Gemini Weekly; route coding threads to Claude 5.5."
    elif c5_val is not None and c5_val >= 25.0:
        mode = "balanced"
        coding_model = "antigravity/claude-opus-5-5"
        triage_model = "antigravity/claude-sonnet-5-5"
        headline_zh = f"双池均衡（Claude 5h {c5_val:.0f}% · Gemini 周池 {gem_val:.1f}%）" if gem_val is not None else f"5h 滚动池可用 ({c5_val:.0f}%)"
        headline_en = f"Balanced Pools (Claude 5h {c5_val:.0f}% · Gemini Weekly {gem_val:.1f}%)" if gem_val is not None else f"Claude 5h Active ({c5_val:.0f}%)"
        reason_zh = "日常编码与 Review 优先走 Claude 5.5 5h 池，长上下文架构综合留给 Gemini 4 周池。"
        reason_en = "Use Claude 5.5 5h for coding/reviews; reserve Gemini 4 Weekly for deep long-context synthesis."
    elif gem_val is not None and gem_val < 20.0:
        mode = "conserve_weekly"
        coding_model = "antigravity/gemini-3.8-flash"
        triage_model = "antigravity/gemini-3.8-flash"
        headline_zh = f"主池警戒（Gemini 仅剩 {gem_val:.1f}%）· 建议切 Codex / 外部池或等待 5h 重置"
        headline_en = f"Primary Pool Low ({gem_val:.1f}%) · Prefer Codex / Paid Batch or Wait 5h Reset"
        reason_zh = "Gemini 与 5h 池当前余量均偏低；轻量任务切 Flash，重度编码可路由至 Codex 或等待下一轮 5h 窗口。"
        reason_en = "Both Antigravity buckets are constrained; route lightweight triage to Flash or heavy coding to Codex until the next 5h reset."
    else:
        mode = "balanced"
        coding_model = "antigravity/gemini-4-neon"
        triage_model = "antigravity/gemini-3.8-flash"
        headline_zh = "使用 Gemini 4 主池（5h 池冷却中）"
        headline_en = "Use Gemini 4 Primary Pool (Claude 5h cooling)"
        reason_zh = "Claude 5h 滚动池当前余量较少，重度架构可暂用 Gemini 4 主池并留意重置倒计时。"
        reason_en = "Claude 5h rolling window is cooling; use Gemini 4 until the next 5h reset."

    d7_usd = float((lens_stats or {}).get("d7_usd") or 0.0)
    roi_x = round(d7_usd / 249.99, 2) if d7_usd > 0 else 0.0

    return {
        "mode": mode,
        "recommended_coding_model": coding_model,
        "recommended_triage_model": triage_model,
        "headline_zh": headline_zh,
        "headline_en": headline_en,
        "reason_zh": reason_zh,
        "reason_en": reason_en,
        "wakeup_recommended": wakeup_needed,
        "gemini_weekly_pct": gem_val,
        "claude_5h_pct": c5_val,
        "expiring_pools": expiring_pools,
        "lens_d7_usd": round(d7_usd, 2),
        "lens_roi_x": roi_x,
    }
