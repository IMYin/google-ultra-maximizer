"""Task triage & monthly quota harvester (Zero-Token rules + optional Paid Gemini API)."""

from __future__ import annotations

import json
import re
import shutil
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any

from .config import RuntimeSecrets
from .db import FleetDB

RED_ZONE_KEYWORDS = (
    "pg_dump",
    "drop table",
    "terraform apply",
    "gh workflow run",
    "app store 正式提审",
    "正式发布",
    "公众号群发",
    "quantx 实盘",
)

COLAB_KEYWORDS = ("f5-tts", "voice-clone", "whisper", "sdxl", "prender", "colab", "gpu", "批量渲染")
FLOW_KEYWORDS = ("veo", "genie", "gflow", "短剧", "nano banana")


def detect_red_zone_warnings(raw_markdown: str) -> list[str]:
    lowered = raw_markdown.lower()
    return [kw for kw in RED_ZONE_KEYWORDS if kw in lowered]


def extract_context_guardrails(context_md: str) -> list[str]:
    lines: list[str] = []
    for line in context_md.splitlines():
        s = line.strip()
        if re.match(r"^(\d+\.|-)\s+\*\*", s) and any(
            k in s for k in ("红线", "禁", "规范", "迁移", "同改", "本地化", "CI", "dev-external")
        ):
            lines.append(s)
    return lines[:8]


def rule_based_triage(project: str, title: str, raw_markdown: str, context_md: str) -> dict[str, Any]:
    """Deterministic zero-token classifier and brief compiler."""
    lowered = f"{title}\n{raw_markdown}".lower()
    if any(k in lowered for k in COLAB_KEYWORDS):
        pool = "colab_cu"
    elif any(k in lowered for k in FLOW_KEYWORDS):
        pool = "flow_credits"
    else:
        pool = "agy_core"

    red_hits = detect_red_zone_warnings(raw_markdown)
    zone = "RED" if red_hits else "YELLOW"
    guardrails = extract_context_guardrails(context_md)

    return {
        "mode": "zero_token_rules",
        "pool": pool,
        "zone": zone,
        "red_zone_hits": red_hits,
        "summary": title,
        "guardrails": guardrails,
        "estimated_usd": 0.0,
    }


def paid_api_triage(
    project: str,
    title: str,
    raw_markdown: str,
    context_md: str,
    secrets: RuntimeSecrets,
) -> dict[str, Any]:
    """Call Paid Gemini API to classify, assess red-zones, and produce an execution brief."""
    prompt = (
        "你是个人研发军团的参谋分诊官。请只输出 JSON，字段："
        '{"pool":"agy_core|colab_cu|flow_credits|ai_studio_daily",'
        '"zone":"GREEN|YELLOW|RED",'
        '"summary":"不超过80字的中文执行摘要",'
        '"red_zone_hits":["触发的红线关键词"],'
        '"guardrails":["需注入给执行Agent的项目约束"]}\n\n'
        f"项目：{project}\n标题：{title}\n\n"
        f"--- CONTEXT.md 节选 ---\n{context_md[:2500]}\n\n"
        f"--- INBOX 需求 ---\n{raw_markdown[:3500]}"
    )
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{secrets.gemini_triage_model}:generateContent?key={secrets.gemini_paid_api_key}"
    )
    body = json.dumps(
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1},
        }
    ).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
        usage = payload.get("usageMetadata", {})
        p_tok = int(usage.get("promptTokenCount", 0) or 0)
        o_tok = int(usage.get("candidatesTokenCount", 0) or 0)
        # Gemini 2.5 Flash standard published blended rate estimate ($0.30/1M in, $2.50/1M out)
        real_usd = (p_tok * 0.30 + o_tok * 2.50) / 1_000_000.0
        parsed = json.loads(text)
        parsed["mode"] = f"paid_api:{secrets.gemini_triage_model}"
        parsed["estimated_usd"] = real_usd
        parsed["prompt_tokens"] = p_tok
        parsed["output_tokens"] = o_tok
        return parsed
    except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError):
        fallback = rule_based_triage(project, title, raw_markdown, context_md)
        fallback["mode"] = "zero_token_rules_fallback"
        return fallback


def triage_task(
    db: FleetDB,
    project: str,
    title: str,
    raw_markdown: str,
    context_md: str,
    secrets: RuntimeSecrets,
) -> dict[str, Any]:
    if secrets.paid_api_enabled:
        result = paid_api_triage(project, title, raw_markdown, context_md, secrets)
        if result.get("estimated_usd", 0) > 0 or result.get("prompt_tokens", 0) > 0:
            db.increment_quota("paid_gemini_api", float(result.get("estimated_usd", 0)))
            calls = int(db.get_meta("paid_api_calls", "0") or 0) + 1
            p_tok = int(db.get_meta("paid_api_prompt_tokens", "0") or 0) + int(result.get("prompt_tokens", 0))
            o_tok = int(db.get_meta("paid_api_output_tokens", "0") or 0) + int(result.get("output_tokens", 0))
            db.set_meta("paid_api_calls", str(calls))
            db.set_meta("paid_api_prompt_tokens", str(p_tok))
            db.set_meta("paid_api_output_tokens", str(o_tok))
        return result
    return rule_based_triage(project, title, raw_markdown, context_md)


def check_monthly_harvesters(db: FleetDB, secrets: RuntimeSecrets) -> list[str]:
    """Check day-of-month triggers only when real quota/CLI tools are configured."""
    now = datetime.now()
    day = now.day
    month = now.strftime("%Y-%m")
    alerts: list[str] = []
    ledger = {row["pool"]: row for row in db.get_quota_ledger(month)}

    gflow_ready = bool(shutil.which("gflow") or shutil.which("gflow-cli"))
    if day >= 22 and gflow_ready:
        flow = ledger.get("flow_credits", {})
        if flow.get("last_harvester_run") != f"{month}-22":
            db.mark_harvester_run("flow_credits", f"{month}-22", month)
            msg = "每月22日 Flow 积分清零哨兵：gflow-cli 已就绪，请检查本月剩余 Flow 积分并启动批量素材渲染。"
            db.add_event("harvester", "FLOW_QUOTA_HARVEST_DUE", msg)
            alerts.append(msg)

    if day >= 24 and secrets.paid_api_enabled and secrets.paid_api_monthly_usd > 0:
        api = ledger.get("paid_gemini_api", {})
        total_used = float(api.get("used_units", 0)) + float(secrets.paid_api_external_used_usd)
        remaining = max(0.0, float(secrets.paid_api_monthly_usd) - total_used)
        if remaining > 5 and api.get("last_harvester_run") != f"{month}-24":
            db.mark_harvester_run("paid_gemini_api", f"{month}-24", month)
            msg = f"每月24日 API 赠金收割哨兵：记录尚余约 ${remaining:.2f}，建议跑 Batch API 批量生产下月小游戏关卡与 SEO 词条。"
            db.add_event("harvester", "API_QUOTA_HARVEST_DUE", msg)
            alerts.append(msg)

    return alerts
