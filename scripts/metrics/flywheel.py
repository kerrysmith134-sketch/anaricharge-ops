#!/usr/bin/env python3
"""flywheel.py — 数据飞轮：快照 → 评估假设 → 识别能力缺口 → 提出下一步。

## 这个脚本解决什么
没有飞轮时，团队是「一轮一轮凭感觉改」。有飞轮后，循环是机械的：
    数据快照 → KPI 达成率 → 假设裁决 → 能力缺口排名 → 下一步建议 → 记录决策
下一次循环读上一次的决策，于是能看出"改了什么、有没有用"。

## 四层状态（都落 JSON，可追溯）
- `state.json`        KPI 定义 + 假设台账 + 决策日志 + 能力缺口
- `snapshot-<日期>.json` 当期数据快照（每次跑都新增，构成时间序列）
- `hypotheses.json`   待验假设（每个都有可证伪的判据）
- `decisions.jsonl`   决策流水（谁改了什么、依据哪条数据）

## 用法
  python3 scripts/metrics/flywheel.py snapshot     # 抓当期数据 + 更新 KPI 现值
  python3 scripts/metrics/flywheel.py evaluate     # 用新数据裁决假设
  python3 scripts/metrics/flywheel.py gaps         # 按 KPI 缺口排能力优先级
  python3 scripts/metrics/flywheel.py propose      # 生成下一轮建议（含"需要新建什么"）
  python3 scripts/metrics/flywheel.py status       # 一屏总览
"""
import argparse
import datetime as dt
import glob
import json
import os
import re
import sys

WS = "/Users/kerrychu/anari-charge-website"
FW = os.path.join(WS, "08-execution", "flywheel")
STATE = os.path.join(FW, "state.json")
HYPO = os.path.join(FW, "hypotheses.json")
DECISIONS = os.path.join(FW, "decisions.jsonl")

# ---------------------------------------------------------------- 口径常量（2026-11-09）
# 为什么改（别回退）：本轮飞轮复审判定 C.social_drafts_ready 与 B.high_intent_conversations
# 的**度量口径错配**，用户 2026-11-09 裁定「按新口径保留，不删除」。具体：
#  · C.social_drafts_ready：Quora 自 2026-11-08 起已获直发授权（R6 批量授权），
#    它的待发件不需要人工确认 → 再算进"待人工确认草稿数"就是虚高；
#  · B.high_intent_conversations：只靠人手填 conversations.jsonl，实际从未有人填
#    → 恒 0 被误判"落后"，真相是**不可测** → 改为自动源优先 + 人工兜底。
# 若看到这里被改回"全部 pending 草稿"或"只读 conversations.jsonl"，是被回退了。
AUTHORIZED_CHANNELS = {"quora"}       # 已授权直发、无需逐条人工确认的渠道
AUTHORIZED_SINCE = "2026-11-08"       # Quora 直发授权生效日


def today():
    return dt.date.today().isoformat()


def load(p, default):
    if not os.path.exists(p):
        return default
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return default


def save(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(obj, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


# ---------------------------------------------------------------- 数据抓取
def gsc_latest():
    fs = sorted(glob.glob(os.path.join(WS, "08-execution", "gsc-*.json")))
    return json.load(open(fs[-1], encoding="utf-8")) if fs else None


def sitemap_count():
    """页面数要反映**线上状态**，不是本地检出分支的状态。

    本地镜像会切到各种分支（chore/content/seo），sitemap.xml 随之变化。
    若直接读工作区，同一个 KPI 在不同分支上会给出不同数字 → 飞轮数据失真。
    所以优先读 origin/main 的版本（= 线上已合并状态），读不到才回退工作区。
    """
    repo = os.path.join(WS, "06-site", "anari-new-site")
    try:
        import subprocess
        out = subprocess.run(["git", "-C", repo, "show", "origin/main:site/sitemap.xml"],
                             capture_output=True, text=True, timeout=20)
        if out.returncode == 0 and out.stdout:
            return out.stdout.count("<loc>")
    except Exception:  # noqa: BLE001
        pass
    p = os.path.join(repo, "site", "sitemap.xml")
    if os.path.exists(p):
        return open(p, encoding="utf-8").read().count("<loc>")
    return None


def opportunity():
    p = os.path.join(WS, "08-execution", "dashboard", "opportunity-rank.json")
    return load(p, None)


def outbound_stats():
    """只看营销线（MKT-OUTREACH-*），SDR 一律不碰。"""
    try:
        sys.path.insert(0, os.path.join(WS, "scripts", "outbound"))
        import instantly_client as ic
    except Exception:  # noqa: BLE001
        return {"error": "instantly_client 不可用"}
    try:
        camps = [c for c in ic.list_campaigns()
                 if (c.get("name") or "").startswith("MKT-OUTREACH")]
        rows = {c.get("campaign_id"): c for c in (ic.analytics() or [])}
        leads = sent = replies = 0
        for c in camps:
            items = (ic.call("/leads/list", "POST",
                             {"campaign": c.get("id"), "limit": 100}).get("items") or [])
            leads += len(items)
            a = rows.get(c.get("id"), {})
            sent += int(a.get("emails_sent_count") or 0)
            replies += int(a.get("reply_count_unique") or 0)
        return {"campaigns": len(camps), "leads": leads, "sent": sent, "replies": replies,
                "reply_rate_pct": round(replies / sent * 100, 2) if sent else None}
    except SystemExit as e:  # noqa: BLE001
        return {"error": str(e)[:200]}


def pool_stats():
    p = os.path.join(WS, "08-execution", "marketing-outbound", "prospect-pool.jsonl")
    if not os.path.exists(p):
        return {"total": 0, "ready": 0}
    rows = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    return {"total": len(rows),
            "ready": sum(1 for r in rows if r.get("status") == "ready"),
            "loaded": sum(1 for r in rows if r.get("status") == "loaded")}


def geo_stats():
    """geo-citations.json 既可能是 {"rows":[...]} 也可能是裸数组，两种都兼容。"""
    p = os.path.join(WS, "08-execution", "geo", "geo-citations.json")
    d = load(p, None)
    if d is None:
        return {"checked": 0, "cited": 0, "layer": None}
    rows = d.get("rows") if isinstance(d, dict) else d
    rows = rows or []
    return {"checked": len(rows),
            "cited": sum(1 for r in rows if r.get("cited")),
            "layer": d.get("layer") if isinstance(d, dict) else "unknown"}


def ga4_proxy():
    """D1 拿不到时的**代理口径**：GA4 前端事件。

    明确标注为代理 —— 它包含测试提交，不是真实询盘数。
    但"完全没有数"和"有个会骗人的数"，对 Pod B 的可管理性差别很大：
    前者无法判断方向，后者至少能看趋势（并在事件归零时立刻发现问题）。
    """
    g = gsc_latest()
    if not g:
        return {"available": False, "reason": "无 GSC/GA4 数据文件"}
    ev = {}
    for e in (g.get("ga4_events") or []):
        if isinstance(e, dict) and e:
            ev[list(e.keys())[0]] = list(e.values())[0]
    return {"available": bool(ev), "events": ev,
            "generate_lead": ev.get("generate_lead"),
            "form_submit": ev.get("form_submit"),
            "form_start": ev.get("form_start"),
            "note": "代理口径：GA4 事件含测试提交，真实询盘以 D1 为准"}


def d1_inquiries():
    """询盘唯一真实口径：D1 submissions。

    2026-11-07 起可用（wrangler OAuth 指向正确账号 db81cefb…）。
    自动回退顺序：OAuth → API token。
    """
    try:
        sys.path.insert(0, os.path.join(WS, "scripts", "metrics"))
        import d1_query as d1q
    except Exception as e:  # noqa: BLE001
        return {"available": False, "reason": "d1_query 不可用: %s" % e}
    try:
        rows = d1q.query(
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN consent=1 THEN 1 ELSE 0 END) AS consent_1, "
            "SUM(CASE WHEN consent=0 THEN 1 ELSE 0 END) AS consent_0, "
            "SUM(CASE WHEN status='stored' THEN 1 ELSE 0 END) AS stored, "
            "SUM(CASE WHEN status='sent' THEN 1 ELSE 0 END) AS sent, "
            "SUM(CASE WHEN status='dead' THEN 1 ELSE 0 END) AS dead "
            "FROM submissions")
        r = rows[0] if rows else {}
        try:
            d1q.cache_put("counts", rows)      # 成功时留一份缓存，供卡住时降级
        except Exception:  # noqa: BLE001
            pass
        return {"available": True, "count": r.get("total", 0),
                "consent_1": r.get("consent_1") or 0,
                "consent_0": r.get("consent_0") or 0,
                "stored": r.get("stored") or 0,
                "sent": r.get("sent") or 0,
                "dead": r.get("dead") or 0,
                "source": "D1 submissions（wrangler OAuth）"}
    except Exception as e:  # noqa: BLE001  —— 含 subprocess.TimeoutExpired：wrangler 卡住不能拖垮看板
        # 降级：用上一次成功的缓存（标明时间，不假装是实时值）
        try:
            import d1_query as _d1q
            c = _d1q.cache_get("counts")
            if c:
                rows = c.get("rows") or []
                r = rows[0] if rows else {}
                return {"available": True, "stale": True,
                        "source": "cache@%s（本次查询失败：%s）" % (c.get("at"), type(e).__name__),
                        "count": r.get("total") or 0,
                        "consent_1": r.get("consent_1") or 0,
                        "consent_0": r.get("consent_0") or 0,
                        "stored": r.get("stored") or 0,
                        "sent": r.get("sent") or 0,
                        "dead": r.get("dead") or 0}
        except Exception:  # noqa: BLE001
            pass
        return {"available": False, "reason": "%s: %s" % (type(e).__name__, str(e)[:180])}


def _parse_dt(v):
    """把 Brevo 可能给的时间值（ISO 字符串 / epoch 秒 / epoch 毫秒）解析成 UTC datetime。"""
    import datetime as _dt
    if v in (None, ""):
        return None
    if isinstance(v, (int, float)) or (isinstance(v, str) and v.strip().isdigit()):
        try:
            ts = float(v)
        except Exception:  # noqa: BLE001
            return None
        if ts > 1e11:                      # 毫秒时间戳
            ts /= 1000.0
        try:
            return _dt.datetime.fromtimestamp(ts, _dt.timezone.utc)
        except Exception:  # noqa: BLE001
            return None
    try:
        d = _dt.datetime.fromisoformat(str(v).strip().replace("Z", "+00:00"))
    except Exception:  # noqa: BLE001
        return None
    return d if d.tzinfo else d.replace(tzinfo=_dt.timezone.utc)


def _deal_created_at(deal):
    """尽量从 Brevo deal 里取创建时间，返回 (datetime|None, 字段名|None)。

    `/v3/crm/deals` 的返回里 created_at 落在哪里没有公开契约保证（顶层 / attributes /
    驼峰都可能），所以逐个候选尝试；都不认识就返回 None，上层据此判"无日期"而**不是猜**。
    """
    at = deal.get("attributes") or {}
    for field, v in (("created_at", deal.get("created_at")),
                     ("createdAt", deal.get("createdAt")),
                     ("attributes.created_at", at.get("created_at")),
                     ("attributes.createdAt", at.get("createdAt")),
                     ("created", deal.get("created")),
                     ("attributes.created", at.get("created"))):
        got = _parse_dt(v)
        if got is not None:
            return got, field
    return None, None


def _manual_high_intent():
    """人工台账 conversations.jsonl（D1 之外对话的兜底来源）。

    available 只表示**台账文件在**；count 是真实登记条数（空文件 = 0 条登记，不是假 0）。
    """
    import datetime as _dt
    path = os.path.join(WS, "08-execution", "inquiry", "conversations.jsonl")
    if not os.path.exists(path):
        return {"available": False, "count": None, "reason": "尚无 conversations.jsonl"}
    cut = _dt.date.today() - _dt.timedelta(days=30)
    n = 0
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
            d = _dt.date.fromisoformat(str(r.get("date") or "")[:10])
        except Exception:  # noqa: BLE001
            continue
        if d >= cut:
            n += 1
    return {"available": True, "count": n, "reason": ""}


def _brevo_high_intent():
    """Brevo CRM deals → 近 30 天、**非 D1 同步**的高意向商机数（自动源）。

    排重逻辑：brevo_crm.py 推送时把 D1 的 submission_id 写进 deal_description，
    所以带 `submission_id=` / `lead_lifecycle` 标记的 deal 视为"已在 B.inquiries 计过"
    → 排除并记 excluded_from_d1，避免同一个询盘被算两次。
    """
    import datetime as _dt
    try:
        sys.path.insert(0, os.path.join(WS, "scripts", "metrics"))
        import brevo_crm as bc
    except Exception as e:  # noqa: BLE001
        return {"available": False, "reason": "brevo_crm 不可用: %s: %s" % (type(e).__name__, str(e)[:120])}
    try:
        deals = bc.all_deals()
    except SystemExit as e:      # brevo_crm 用 SystemExit 报"缺 key / HTTP 失败"
        return {"available": False, "reason": "Brevo API 不可用: %s" % str(e)[:160]}
    except Exception as e:  # noqa: BLE001
        return {"available": False, "reason": "%s: %s" % (type(e).__name__, str(e)[:160])}

    cut = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=30)
    counted = excluded = undated = 0
    for d in deals:
        at = d.get("attributes") or {}
        desc = str(at.get("deal_description") or "")
        name = str(at.get("deal_name") or d.get("name") or "")
        blob = (desc + "\n" + name).lower()
        if bc.sid_of(d) or "submission_id=" in blob or "lead_lifecycle" in blob:
            excluded += 1
            continue
        when, _field = _deal_created_at(d)
        if when is None:
            undated += 1
            continue
        if when >= cut:
            counted += 1
    base = {"total": len(deals), "excluded_from_d1": excluded, "undated": undated}
    if not deals:
        # API 通、确实是空表 → 真实的 0（不是"拿不到"）
        return dict(base, available=True, count_30d=0, reason="")
    if undated == len(deals):
        # 有 deal 但取不到任何日期 → 不做 30 天过滤，直接报不可测（不猜）
        return dict(base, available=False, count_30d=None,
                    reason="Brevo 有 %d 个 deal，但返回里取不到 created_at → 无法按 30 天过滤（不猜）" % len(deals))
    return dict(base, available=True, count_30d=counted, reason="")


def high_intent_conversations():
    """高意向对话（近 30 天，D1 之外）——**自动采集优先，人工台账兜底**。

    2026-11-09 口径改造（用户裁定「按新口径保留，不删除」）：
    - 旧口径只读 `08-execution/inquiry/conversations.jsonl` 的人工登记。实际没有任何人
      往里面写 → 恒 0，看起来"落后"，真相是**不可测**（度量口径错配）。
    - 新口径：① Brevo CRM deals 近 30 天（自动源，销售真实在用的界面）；
              ② Brevo 不可用 → 退回人工台账。
              ③ 两路都不可用 → available=False / count_30d=None / reason 写明原因，
                 让飞轮判 no_data 而不是 behind。**绝不写 0 冒充有数据。**
    - D1 账本同步来的商机（带 submission_id= 标记）排除，记 excluded_from_d1，
      否则与 B.inquiries 重复计数。
    - caveat：Brevo 里"无 submission_id 标记"的 deal 才被算作 D1 之外 → 人工在 UI 手建
      时若漏标会**高估**（上限估计）；WhatsApp/直邮/来电没进 CRM 时会**低估**。
      所以这是约值，判定达标前需人工复核。
    """
    manual = _manual_high_intent()
    bv = _brevo_high_intent()
    out = {
        "available": False,
        "count_30d": None,
        "source": "none",
        "manual_count": manual.get("count"),
        "manual_available": manual.get("available"),
        "brevo_deals_30d": bv.get("count_30d"),
        "brevo_total": bv.get("total"),
        "excluded_from_d1": bv.get("excluded_from_d1"),
        "undated_deals": bv.get("undated"),
        "reason": "",
        "caveat": "",
    }
    if bv.get("available"):
        out.update(available=True, count_30d=bv.get("count_30d"),
                   source="Brevo CRM deals（近30天，已排除 D1 同步）")
        out["caveat"] = ("Brevo 中无 submission_id 标记的 deal 视为 D1 之外：人工手建漏标会高估，"
                         "未进 CRM 的 WhatsApp/直邮/来电会低估 → 约值，达标前需人工复核")
        if manual.get("available") and (manual.get("count") or 0) > (bv.get("count_30d") or 0):
            out["caveat"] += "；人工台账另有 %s 条未计入（Brevo 优先）" % manual.get("count")
        if bv.get("undated"):
            out["caveat"] += "；%d 个 deal 无日期未计入" % bv.get("undated")
    elif manual.get("available"):
        out.update(available=True, count_30d=manual.get("count"),
                   source="08-execution/inquiry/conversations.jsonl（人工台账；Brevo 不可用兜底）")
        out["reason"] = "Brevo 不可用：%s；已退回人工台账" % (bv.get("reason") or "未知")
    else:
        out["reason"] = "两路都不可用：Brevo=%s；人工台账=%s" % (
            bv.get("reason") or "未知", manual.get("reason") or "未知")
    return out


def inquiry_alert_latency():
    """询盘告警延迟：从提交落库到**任一通道首次通知**的时长（小时）。

    2026-11-12 口径修正（重要）：
    - 旧口径只数 `08-execution/inquiry/alerts-*.jsonl`，那是 **4 次/天的人工巡检档**。
      巡检间隔本身在夜间有 ~12 小时空档，于是把「等档位」当成了「告警慢」——
      实测 9.46h 里大部分是巡检节奏，不是通知通道。
    - 真实第一通知通道：Worker 落库后写 D1 `outbox(kind='notify')` → Brevo 即时邮件。
      实测 Novekta 那条：submission 19:12:06.497Z → outbox sent_at 19:12:09.345Z = **2.8 秒**。
    - 新口径 = **多通道取最早**：① outbox notify ② 巡检 alerts 日志。每条询盘取最早一次，
      并记录用了哪个通道、是否超 4h 目标。
    - 诚实边界：n<3 时不下结论（本工作区既有纪律），返回里带 caveat。
    """
    import datetime as _dt

    def _p(v):
        if not v:
            return None
        try:
            d = _dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        except Exception:  # noqa: BLE001
            return None
        return d if d.tzinfo else d.replace(tzinfo=_dt.timezone.utc)

    # ① 主通道：D1 submissions × outbox(kind=notify)
    subs, chans = {}, {}
    try:
        sys.path.insert(0, os.path.join(WS, "scripts", "metrics"))
        import d1_query as d1q
        rows = d1q.query(
            "SELECT s.submission_id AS sid, s.created_at AS sub_at, "
            "o.sent_at AS o_sent, o.created_at AS o_created, o.status AS o_status "
            "FROM submissions s LEFT JOIN outbox o "
            "ON o.submission_id = s.submission_id AND o.kind = 'notify' "
            "ORDER BY s.created_at DESC LIMIT 50")
        for r in rows:
            sid = r.get("sid")
            if not sid:
                continue
            subs.setdefault(sid, _p(r.get("sub_at")))
            t = _p(r.get("o_sent")) or _p(r.get("o_created"))
            if t and (r.get("o_status") in (None, "sent", "pending", "retry")):
                chans.setdefault(sid, []).append(("outbox_notify", t))
    except Exception:  # noqa: BLE001
        pass

    # ② 兜底：4×/天巡检日志
    import glob as _glob
    for f in sorted(_glob.glob(os.path.join(WS, "08-execution", "inquiry", "alerts-*.jsonl")))[-30:]:
        try:
            for line in open(f, encoding="utf-8"):
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                if r.get("type") != "new":
                    continue
                sid, c, a = r.get("submission_id"), _p(r.get("created_at")), _p(r.get("alert_at"))
                if sid and c and a:
                    subs.setdefault(sid, c)
                    chans.setdefault(sid, []).append(("monitor_alert", a))
        except Exception:  # noqa: BLE001
            continue

    items = []
    for sid, c in subs.items():
        if not c or not chans.get(sid):
            continue
        chan, t = min(chans[sid], key=lambda x: x[1])
        h = (t - c).total_seconds() / 3600.0
        if h < 0:                      # 时钟/时区异常，跳过而不是记负数
            continue
        items.append({"submission_id": sid, "created_at": c.isoformat(),
                      "first_notice_at": t.isoformat(), "channel": chan,
                      "latency_h": round(h, 3),
                      "over_target": h > 4.0})
    if not items:
        return {"available": False, "reason": "尚无询盘通知记录（D1 无询盘或 outbox 无 notify）"}

    vals = [i["latency_h"] for i in items]
    by_ch = {}
    for i in items:
        by_ch[i["channel"]] = by_ch.get(i["channel"], 0) + 1
    out = {"available": True,
           "avg_h": round(sum(vals) / len(vals), 2),
           "max_h": round(max(vals), 2),
           "min_h": round(min(vals), 2),
           "n": len(items),
           "over_target": sum(1 for i in items if i["over_target"]),
           "by_channel": by_ch,
           "source": "多通道取最早：D1 outbox(kind=notify) ∪ 巡检 alerts 日志",
           "items": items}
    if len(items) < 3:
        out["caveat"] = "n=%d <3，样本不足，均值不作考核结论（团队既有纪律）" % len(items)
    return out


def index_coverage():
    """收录覆盖（GSC URL Inspection API 结果，样本或全量）。

    这是 Pod A 唯一能证明"页面工厂真的起作用"的直接指标 —— 页面数不等于被收录页数。
    数据由 `scripts/index_coverage.py` 产出；此处只读取最新一份。
    """
    import glob as _glob
    # 只信 scope=full 的那份。2026-11-07 踩过：我写了一份 20 条的抽检文件，
    # 按 mtime 取最新会让 KPI 变成"20 条样本的收录率"，看起来像全站数据。
    # 没有 scope 字段的历史文件按文件名判断（含 full）。
    cand = _glob.glob(os.path.join(WS, "08-execution", "tech", "index-coverage*.json"))
    if not cand:
        return {"available": False, "reason": "尚无 index-coverage*.json（跑 index_coverage.py）"}

    def is_full(path):
        d = load(path, None) or {}
        scope = d.get("scope")
        if scope:
            return scope == "full"
        return "full" in os.path.basename(path)

    full = [f for f in cand if is_full(f)] or sorted(cand, key=lambda f: os.path.getmtime(f))[-1:]
    files = sorted(full, key=lambda f: os.path.getmtime(f))
    d = load(files[-1], None) or {}
    inspected = int(d.get("inspected") or 0)
    dist = d.get("verdict_dist") or {}
    passed = int(dist.get("PASS") or 0)
    return {"available": inspected > 0,
            "file": os.path.basename(files[-1]),
            "inspected": inspected,
            "indexed": passed,
            "indexed_pct": round(passed / inspected * 100, 1) if inspected else None,
            "coverage_dist": d.get("coverage_dist"),
            "sitemap_urls": d.get("sitemap_urls")}


def referring_domains():
    """引用域（真实外链验证过的唯一域名数）。

    与 GEO 引用不同：这里只算**真的链到我们**的页面，逐页抓取验证。
    台账由 `scripts/metrics/referring_domains.py` 维护（add / verify / report）。
    """
    p = os.path.join(WS, "08-execution", "backlink", "referring-domains.json")
    d = load(p, None)
    if not d:
        return {"available": False, "reason": "尚无 referring-domains.json"}
    rows = d.get("rows") or []
    active = [r for r in rows if r.get("status") == "active"]
    follow = [r for r in active if (r.get("result") or {}).get("rel") != "nofollow"]
    return {"available": True,
            "entries": len(rows),
            "active": len(active),
            "domains": len({r["domain"] for r in active}),
            "follow_domains": len({r["domain"] for r in follow})}


def geo_ai_stats():
    """AI 引擎层的 GEO 可见度（Perplexity 等真实回答里是否引用我们）。

    与 search_proxy 层的区别：搜索结果是"排名位次"，AI 答案是"是否被当成来源引用"。
    GEO 的目标是后者，所以有 AI 层数据时 KPI 用 AI 层。
    """
    p = os.path.join(WS, "08-execution", "geo", "geo-citations-ai.json")
    d = load(p, None)
    if not d:
        return {"available": False, "reason": "尚无 geo-citations-ai.json"}
    rows = d.get("rows") or []
    return {"available": bool(rows), "engine": d.get("engine"),
            "checked": len(rows), "cited": sum(1 for r in rows if r.get("cited")),
            "checked_at": d.get("checked_at")}


def internal_health():
    """内链健康度：孤儿页数（站内入链为 0 的页面）。

    数据源是站仓库里的 `scripts/audit-inbound-links.js --json`（CI 里同一条门禁）。
    内链一直有工作流但没有 KPI —— 没有指标的工作流等于没人管。
    """
    import subprocess
    repo = os.path.join(WS, "06-site", "anari-new-site")
    try:
        out = subprocess.run(["node", "scripts/audit-inbound-links.js", "--json"],
                             cwd=repo, capture_output=True, text=True, timeout=90).stdout
        d = json.loads(out[:out.rindex("}") + 1])
        fams = d.get("families") or []
        return {"available": True, "orphans": len(d.get("orphans") or []),
                "families": len(fams),
                "min_inbound": min([f.get("inbound", 0) for f in fams], default=None)}
    except Exception as e:  # noqa: BLE001
        return {"available": False, "reason": "%s: %s" % (type(e).__name__, str(e)[:120])}


def _draft_channel(path):
    """草稿的渠道标记：approval.py 约定文件首行是 JSON meta（含 platform）。

    取不到/不是 JSON → 返回 "unmarked"（老格式草稿）。不能因为格式老就悄悄丢掉。
    """
    try:
        with open(path, encoding="utf-8") as f:
            first = f.readline().strip()
    except Exception:  # noqa: BLE001
        return "unmarked"
    try:
        meta = json.loads(first)
    except Exception:  # noqa: BLE001
        return "unmarked"
    if not isinstance(meta, dict):
        return "unmarked"
    ch = str(meta.get("platform") or meta.get("channel") or "").strip().lower()
    return ch or "unmarked"


def social_posts():
    """近 30 天社媒/社区实际发布数 + 待人工确认草稿数（仅未授权渠道）。

    2026-11-09 口径改造（用户裁定「按新口径保留，不删除」）：
    - `drafts_ready`（KPI C.social_drafts_ready）旧口径数 pending/ 下**全部** *.md。
      但 Quora 自 2026-11-08 起已获直发授权（R6 批量授权），Quora 待发件不需要人工确认
      → 继续计入就是口径错配（数值虚高，还激励继续写 Quora 草稿）。
      新口径只数**未授权渠道**的待确认草稿，附 by_channel 明细；被排除的记在
      excluded_authorized 里（含说明，便于复核）。
    - 渠道取自草稿首行 JSON meta 的 platform（approval.py 的写入格式）；
      无 meta 的老草稿按 "unmarked" 计入（宁多不少，不能因格式悄悄漏计）。

    发布数口径不变：Quora/Reddit 以 quora-log.jsonl 为准（有 permalink 才算发布）；
    LinkedIn 等以 08-execution/social/*-dispatch.md 为准（当前无自动记录 → 只数文件）。
    """
    import datetime as _dt
    cut = _dt.date.today() - _dt.timedelta(days=30)
    n = 0
    details = {}
    log = os.path.join(WS, "08-execution", "community", "quora-log.jsonl")
    if os.path.exists(log):
        for line in open(log, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            if r.get("status") != "published":
                continue
            try:
                d = _dt.date.fromisoformat((r.get("date") or "")[:10])
            except Exception:  # noqa: BLE001
                continue
            if d >= cut:
                n += 1
        details["quora"] = n
    pend = os.path.join(WS, "08-execution", "community", "pending")
    files = sorted(f for f in os.listdir(pend) if f.endswith(".md")) if os.path.isdir(pend) else []
    by_channel, excl_by_channel, excl_files = {}, {}, []
    for fn in files:
        ch = _draft_channel(os.path.join(pend, fn))
        if ch in AUTHORIZED_CHANNELS:
            excl_by_channel[ch] = excl_by_channel.get(ch, 0) + 1
            excl_files.append(fn)
            continue
        by_channel[ch] = by_channel.get(ch, 0) + 1
    drafts_ready = sum(by_channel.values())
    details["pending_total"] = len(files)
    return {"available": True, "posts_30d": n, "drafts_ready": drafts_ready,
            "details": details,
            "by_channel": by_channel,
            "excluded_authorized": {
                "count": sum(excl_by_channel.values()),
                "by_channel": excl_by_channel,
                "files": excl_files,
                "note": "已授权直发渠道（%s，自 %s 起）不需逐条人工确认 → 不计入待确认草稿" % (
                    "/".join(sorted(AUTHORIZED_CHANNELS)), AUTHORIZED_SINCE)}}


# ---------------------------------------------------------------- 语种需求（2026-11-09 补的计量缺口）
# 为什么加：2026-11-09 做 RU/ES 诊断时发现"没有任何 KPI 能回答某个语种有没有需求"，
# 结论只能靠一次性 join，下一轮无法复现 → 按「计量缺口优先于能力缺口」补三个口子：
#   ① 需求：非英语查询的展示量（按语言拆）
#   ② 捕获：/ru /es 页自身的自然搜索展示（只从 GSC 页面维度取，免费）
#   ③ 使用：/ru /es 的 GA4 session（全渠道，带缓存，别每次命令都打 API）
LOCALE_PREFIX = {"ru": ("/ru",), "es": ("/es",)}
LOCALE_SESSION_CACHE = os.path.join(WS, "08-execution", "metrics", "ga4-locale-cache.json")
LOCALE_CACHE_TTL_H = 6

# 按文字体系判语种（可靠，不猜）；拉丁字母的非英语只能靠词表启发（标注 heuristic）。
_SCRIPT_RANGES = [
    ("ru", r"[\u0400-\u04FF]"),            # 西里尔
    ("he", r"[\u0590-\u05FF]"),            # 希伯来（以色列是 ICP 市场）
    ("ar", r"[\u0600-\u06FF]"),            # 阿拉伯
    ("zh", r"[\u4e00-\u9fff]"),
    ("ja", r"[\u3040-\u30ff]"),
    ("ko", r"[\uac00-\ud7af]"),
    ("el", r"[\u0370-\u03FF]"),
    ("th", r"[\u0E00-\u0E7F]"),
    ("hi", r"[\u0900-\u097F]"),
]
# 拉丁字母非英语：**宁可漏报，不可虚高**。只认"强特征词"（不在英文里出现的那种）+
# 有变音符；或 ≥2 个强特征词。第一版把 anariev.com 判成葡语（因为 "com"）、
# 把 "residential ev installation roi" 判成法语（because "installation"）——所以词表
# 剔掉了所有与英文重叠的词（installation/service/para/com/guide/...）。
_LATIN_STRONG = {
    "es": r"(c[oó]mo|cu[aá]nto|cu[aá]nta|precio|estaci[oó]n|cargador|bater[ií]a|instalaci[oó]n|d[oó]nde|mejor|gu[ií]a|cu[aá]l|recarga|carga\b|cargan)",
    "pt": r"(quanto|pre[cç]o|esta[cç][aã]o|carregador|bateria|instala[cç][aã]o|melhor|guia|recarga|carregamento|ponto de|fornecedor)",
    "fr": r"(combien|borne de recharge|recharge|entreprise|meilleur|pourquoi|comment installer)",
    "de": r"(wieviel|ladeger[aä]t|ladeinfrastruktur|unternehmen|preisvergleich|wie funktioniert)",
}
_DIACRITIC = r"[áéíóúñãõçàèêôûäöüßâîù]"


def _is_operator_query(s):
    """GSC 会把我们自己/工具发起的检索式也记成 query（如 "x" -site:...）。这些不是用户需求。"""
    low = s.lower()
    return ("-site:" in low) or low.startswith('"') or (" or " in low and "site:" in low)


def detect_query_language(q):
    """返回 (lang, method)。method: 'script'（可靠）/ 'latin-strong'（窄口径）/ None。

    设计原则：拉丁字母的误判会直接污染 KPI，所以只认窄口径强特征 + 变音符；
    拿不准就返回 None（当英文/未知），宁可漏报。
    """
    s = (q or "").strip()
    if not s or _is_operator_query(s):
        return None, None
    for lang, pat in _SCRIPT_RANGES:
        if re.search(pat, s):
            return lang, "script"
    low = s.lower()
    for lang in ("pt", "es", "fr", "de"):     # pt 先：'carga' 两语共用，pt 独有词更具体
        if re.search(_LATIN_STRONG[lang], low):
            return lang, "latin-strong"
    return None, None


def locale_of(path):
    """'/ru/agents/' → 'ru'；'/rules' 不会被误判成 ru。"""
    p = (path or "").split("?")[0]
    for loc in LOCALE_PREFIX:
        if p == "/" + loc or p.startswith("/" + loc + "/"):
            return loc
    return None


def non_english_demand():
    """非英语查询的可归因展示（28 天窗口，来自 GSC 查询维度）。

    口径警告：低流量站 GSC 会把约 60% 展示匿名化，查询维度是**下限**，不是总量。
    用途只有两个：① 有没有非英语需求；② 需求落在哪种语言。不能用来算总量。
    """
    g = gsc_latest()
    if not g:
        return {"available": False, "reason": "无 gsc-*.json"}
    rows = g.get("queries") or []
    by_lang, detail = {}, []
    total = 0
    for r in rows:
        q = r.get("query") or ""
        lang, method = detect_query_language(q)
        if not lang:
            continue
        imp = int(r.get("impressions") or 0)
        total += imp
        d = by_lang.setdefault(lang, {"queries": 0, "impressions": 0, "best_position": None,
                                      "methods": set()})
        d["queries"] += 1
        d["impressions"] += imp
        d["methods"].add(method)
        pos = r.get("position")
        if pos is not None:
            d["best_position"] = pos if d["best_position"] is None else min(d["best_position"], pos)
        detail.append({"query": q, "lang": lang, "method": method,
                       "impressions": imp, "position": round(pos, 1) if pos is not None else None})
    for v in by_lang.values():
        v["methods"] = sorted(v["methods"])
    return {"available": bool(rows),
            "window": g.get("window"),
            "impressions_lower_bound": total,
            "by_language": by_lang,
            "queries": sorted(detail, key=lambda x: -x["impressions"])[:40],
            "note": "查询维度因 GSC 匿名化丢约 60% 展示 → 这是下限；只判有无与语种，不算总量"}


def locale_organic():
    """/ru /es 页自身的自然搜索表现（GSC 页面维度，免费，无额外 API 调用）。"""
    g = gsc_latest()
    if not g:
        return {"available": False, "reason": "无 gsc-*.json"}
    by = {"ru": {"pages": 0, "impressions": 0, "clicks": 0},
          "es": {"pages": 0, "impressions": 0, "clicks": 0}}
    for r in (g.get("pages") or []):
        u = r.get("page") or ""
        path = u.split("anaricharge.com", 1)[-1] if "anaricharge.com" in u else u
        loc = locale_of(path)
        if not loc:
            continue
        by[loc]["pages"] += 1
        by[loc]["impressions"] += int(r.get("impressions") or 0)
        by[loc]["clicks"] += int(r.get("clicks") or 0)
    impr = by["ru"]["impressions"] + by["es"]["impressions"]
    return {"available": True, "impressions": impr,
            "clicks": by["ru"]["clicks"] + by["es"]["clicks"],
            "by_locale": by,
            "note": "只算 GSC 页面维度里出现过的语种页（有展示才在列）"}


def ga4_locale_sessions():
    """GA4 全渠道 session（/ru /es），带 6 小时缓存 —— 别让每条命令都打 API。"""
    import datetime as _dt
    try:
        c = load(LOCALE_SESSION_CACHE, None)
        if c and c.get("at"):
            age = (_dt.datetime.now() - _dt.datetime.fromisoformat(c["at"])).total_seconds() / 3600
            if age < LOCALE_CACHE_TTL_H:
                return c["data"]
    except Exception:  # noqa: BLE001
        pass
    try:
        sys.path.insert(0, os.path.join(WS, "scripts", "metrics"))
        import ga4_query as g4
        d = g4.post("runReport", {
            "dateRanges": [{"startDate": "28daysAgo", "endDate": "today"}],
            "dimensions": [{"name": "pagePath"}],
            "metrics": [{"name": "screenPageViews"}, {"name": "sessions"}],
            "limit": 500,
        })
        if d.get("error"):
            raise RuntimeError("GA4 %s: %s" % (d.get("error"), str(d.get("body"))[:120]))
        by = {"ru": {"sessions": 0, "views": 0}, "es": {"sessions": 0, "views": 0}}
        for r in (d.get("rows") or []):
            path = r["dimensionValues"][0]["value"]
            loc = locale_of(path)
            if not loc:
                continue
            by[loc]["views"] += int(r["metricValues"][0]["value"])
            by[loc]["sessions"] += int(r["metricValues"][1]["value"])
        out = {"available": True,
               "sessions": by["ru"]["sessions"] + by["es"]["sessions"],
               "views": by["ru"]["views"] + by["es"]["views"],
               "by_locale": by}
        save(LOCALE_SESSION_CACHE, {"at": _dt.datetime.now().isoformat(timespec="seconds"), "data": out})
        return out
    except SystemExit as e:                     # 缺凭证
        return {"available": False, "sessions": None, "reason": "缺 GA4 OAuth 凭证：%s" % str(e)[:120]}
    except Exception as e:                      # noqa: BLE001
        return {"available": False, "sessions": None,
                "reason": "%s: %s" % (type(e).__name__, str(e)[:150])}


def snapshot():
    g = gsc_latest()
    org = {}
    if g:
        pt = g.get("page_totals") or {}
        org = {"clicks": pt.get("clicks"), "impressions": pt.get("impressions"),
               "ctr_pct": pt.get("ctr"), "avg_position": pt.get("avg_position_weighted"),
               "window": g.get("window"), "pages_with_impressions": g.get("pages_with_impressions")}
    opp = opportunity() or {}
    snap = {
        "date": today(),
        "organic": org,
        "sitemap_urls": sitemap_count(),
        "opportunity_clicks_total": opp.get("total_opportunity_clicks"),
        "outbound": outbound_stats(),
        "pool": pool_stats(),
        "geo": geo_stats(),
        "geo_ai": geo_ai_stats(),
        "internal_health": internal_health(),
        "inquiry_alert": inquiry_alert_latency(),
        "high_intent": high_intent_conversations(),
        "social": social_posts(),
        "index_coverage": index_coverage(),
        "referring_domains": referring_domains(),
        "d1": d1_inquiries(),
        "conversion_proxy": ga4_proxy(),
        "non_en": non_english_demand(),
        "locale_organic": locale_organic(),
        "locale_ga4": ga4_locale_sessions(),
    }
    if org.get("impressions") and snap["sitemap_urls"]:
        snap["impressions_per_page_month"] = round(
            org["impressions"] / snap["sitemap_urls"] * 30 / 28, 1)
    _snap_path = os.path.join(FW, "snapshot-%s.json" % today())
    _prev = _prev_snapshot(_snap_path)          # 必须在 save 之前取上一份
    save(_snap_path, snap)
    return snap


# ---------------------------------------------------------------- KPI
def compute_kpis(snap, state):
    """把快照映射成 KPI 现值 + 达成判定。"""
    kpis = state["kpis"]
    out = {}
    org = snap.get("organic") or {}
    ob = snap.get("outbound") or {}
    proxy = snap.get("conversion_proxy") or {}
    d1 = snap.get("d1") or {}
    d1_count = d1.get("count") if d1.get("available") else None
    vals = {
        # Pod A 需求
        "A.org_clicks_28d": org.get("clicks"),
        "A.org_impressions_28d": org.get("impressions"),
        "A.indexable_pages": snap.get("sitemap_urls"),
        "A.impressions_per_page_month": snap.get("impressions_per_page_month"),
        "A.index_coverage_pct": (snap.get("index_coverage") or {}).get("indexed_pct"),
        "A.orphan_pages": (snap.get("internal_health") or {}).get("orphans"),
        "B.inquiry_alert_latency_h": (snap.get("inquiry_alert") or {}).get("avg_h"),
        "B.high_intent_conversations": (snap.get("high_intent") or {}).get("count_30d"),
        "C.social_posts_30d": (snap.get("social") or {}).get("posts_30d"),
        "C.social_drafts_ready": (snap.get("social") or {}).get("drafts_ready"),
        # Pod B 转化
        # D1 是唯一真实口径；拿不到时退到 GA4 代理（status 会标成 proxy，不冒充达标）
        "B.inquiries": d1_count if d1_count is not None else proxy.get("generate_lead"),
        # 2026-11-13：营销同意率 = consent=1 / 全部询盘。
        # 为什么：11-12 两条询盘都是 consent=0 → 进不了 Brevo 培育（consent 是独立断点，
        # 不是链路 bug，也绝不能预勾选）。没有这个 KPI 就无法判断改文案有没有用。
        "B.consent_optin_pct": (
            round((d1.get("consent_1") or 0) / d1_count * 100, 1)
            if (d1.get("available") and d1_count) else None),
        # Pod C 权威
        "C.outreach_sent": ob.get("sent"),
        "C.outreach_reply_rate_pct": ob.get("reply_rate_pct"),
        "C.prospect_pool_ready": (snap.get("pool") or {}).get("ready"),
        "C.geo_cited": ((snap.get("geo_ai") or {}).get("cited")
                        if (snap.get("geo_ai") or {}).get("available")
                        else (snap.get("geo") or {}).get("cited")),
        "C.referring_domains": (snap.get("referring_domains") or {}).get("domains"),
        # 语种需求三件套（2026-11-09 补的计量缺口）
        "A.non_en_impressions_28d": (snap.get("non_en") or {}).get("impressions_lower_bound"),
        "A.locale_impressions_28d": (snap.get("locale_organic") or {}).get("impressions"),
        "A.locale_sessions_28d": (snap.get("locale_ga4") or {}).get("sessions"),
    }
    for key, spec in kpis.items():
        v = vals.get(key)
        target = spec.get("target")
        status, detail = "no_data", ""
        is_proxy = (key == "B.inquiries" and d1_count is None
                    and proxy.get("generate_lead") is not None)
        if v is None:
            status = "no_data"
            detail = "无数据来源" if not spec.get("source_ready", True) else "本期无值"
        elif is_proxy:
            status = "proxy"
            detail = "代理口径（GA4 generate_lead，含测试）；D1 为准"
        elif target is None:
            status = "tracking"
        elif spec.get("direction") == "higher":
            status = "on_track" if v >= target else "behind"
            detail = "目标 ≥%s" % target
        else:
            status = "on_track" if v <= target else "behind"
            detail = "目标 ≤%s" % target
        # 2026-11-13：同意率样本 n<5 时只作观测，不判达标（0/2 这种比率毫无统计意义）
        if key == "B.consent_optin_pct" and d1_count is not None and d1_count < 5:
            status = "tracking"
            detail = "样本 n=%s <5，不判达标（同意率只作观测）" % d1_count
        # 2026-11-12：告警延迟改为多通道取最早后，n<3 时不许判达标（团队既有纪律）
        if key == "B.inquiry_alert_latency_h":
            ia = snap.get("inquiry_alert") or {}
            if ia.get("available") and (ia.get("n") or 0) < 3:
                status = "tracking"
                detail = "样本 n=%s <3，不判达标（%s）" % (ia.get("n"), ia.get("caveat") or "")
        out[key] = {"pod": spec["pod"], "name": spec["name"], "value": v,
                    "target": target, "status": status, "detail": detail,
                    "source": spec.get("source", "")}
    return out


# ---------------------------------------------------------------- 假设裁决
EVO = os.path.join(FW, "evolutions.jsonl")


def _prev_snapshot(today_file):
    """取上一份快照（用于比对 KPI 状态变化）。没有就返回 None。"""
    import glob as _glob
    files = sorted(_glob.glob(os.path.join(FW, "snapshot-*.json")))
    files = [f for f in files if f != today_file]
    if not files:
        return None
    return load(files[-1], None)


def evolution_append(change, because, evidence, kind="measurement_driven"):
    """把一条进化写进台账 —— 只有代码写进来的才算"机制"。

    此前 20 条 evolution 全是人手写的（grep 确认没有任何代码写这个文件），
    也就是说"自进化台账"只是一本日记。现在由 KPI 状态迁移自动产生。
    """
    rec = {"date": today(), "type": kind, "change": change,
           "because": because, "evidence": evidence, "generated_by": "flywheel.py"}
    try:
        with open(EVO, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return True
    except Exception:  # noqa: BLE001
        return False


def evolution_from_kpi_delta(prev, kpis):
    """比对上一份快照与当期 KPI 状态，状态迁移 → 自动写进化条目。

    这是自进化的"闭环出口"：没有它，KPI 变了也没人记录"我因此改了什么"。
    """
    if not prev:
        return []
    pk = prev.get("kpis") or {}
    out = []
    for key, cur in (kpis or {}).items():
        old = pk.get(key) or {}
        o, n = old.get("status"), cur.get("status")
        if not o or o == n:
            continue
        ov, nv = old.get("value"), cur.get("value")
        if o == "no_data" and n in ("on_track", "behind"):
            change = "%s 从不可测变为可测（%s）" % (key, cur.get("name"))
            why = "补上了数据源：%s" % (cur.get("source") or "见 state.json")
        elif o == "behind" and n == "on_track":
            change = "%s 由落后转为达标（%s → %s）" % (key, ov, nv)
            why = "按 KPI 判据达成，方法有效，可复制到同级指标"
        elif o == "on_track" and n == "behind":
            change = "%s 由达标退为落后（%s → %s）" % (key, ov, nv)
            why = "回归！先查是不是口径变了或数据源失效，再查执行"
        elif o in ("proxy", "no_data") and n == "behind":
            change = "%s 代理口径切换为正式口径（%s）" % (key, cur.get("name"))
            why = "计量缺口已补，此后该指标可用于判断达标"
        else:
            change = "%s 状态迁移 %s → %s（值 %s → %s）" % (key, o, n, ov, nv)
            why = "按 KPI 判据自动记录"
        evolution_append(change, why,
                         "flywheel snapshot 比对：上一份 %s" % (prev.get("date") or "?"))
        out.append(key)
    return out


def evolution_from_verdicts(changed_ids, hypos):
    """假设被裁决（证实/过期）→ 自动写进化条目。"""
    out = []
    _items = hypos.get("items") if isinstance(hypos, dict) else hypos
    for h in (_items or []):
        if h.get("id") not in changed_ids:
            continue
        verdict = h.get("verdict") or ""
        evolution_append(
            "假设 %s 裁决为 %s：%s" % (h.get("id"), h.get("status"), h.get("claim")),
            verdict or "判据满足",
            "hypotheses.json / %s" % (h.get("test") or ""), kind="hypothesis_verdict")
        out.append(h.get("id"))
    return out


def evaluate(snap, kpis):
    hypos = load(HYPO, {"items": []})
    # 兼容两种落盘结构：{"items":[...]} 与 直接 list（2026-11-21 发现 list 会让 evaluate 崩溃）
    hypo_items = hypos.get("items") if isinstance(hypos, dict) else hypos
    if not isinstance(hypo_items, list):
        hypo_items = []
    today_s = today()
    changed = []
    for h in hypo_items:
        if h.get("status") != "open":
            continue
        m = h.get("metric")
        if m in kpis and kpis[m]["status"] != "no_data":
            v = kpis[m]["value"]
            op, thr = h.get("op"), h.get("threshold")
            hit = (v >= thr) if op == ">=" else (v <= thr)
            h["last_value"] = v
            h["last_checked"] = today_s
            if hit:
                h["status"] = "confirmed"
                h["verdict"] = "判据满足：%s %s %s（实测 %s）" % (m, op, thr, v)
                changed.append(h["id"])
        if h.get("due") and h["due"] < today_s and h.get("status") == "open":
            h["status"] = "expired"
            h["verdict"] = "到期仍未满足判据，按未证实处理"
            changed.append(h["id"])
    save(HYPO, hypos)
    if changed:
        evolution_from_verdicts(changed, hypos)
    return changed


# ---------------------------------------------------------------- 缺口
GAP_RULES = {
    "no_data": ("计量缺口", "没有可信数据源 → 先补测量，否则这条 KPI 永远无法管理"),
    "proxy": ("计量缺口", "只有代理口径（GA4 事件，含测试）→ 真实结果仍不可知，必须补正式测量"),
    "behind": ("能力缺口", "有数据但未达标 → 需要加强该 Pod 的执行力或方法"),
}


def gaps(kpis):
    rows = []
    for key, k in kpis.items():
        if k["status"] in GAP_RULES:
            kind, why = GAP_RULES[k["status"]]
            rows.append({"kpi": key, "pod": k["pod"], "name": k["name"],
                         "status": k["status"], "kind": kind,
                         "value": k["value"], "target": k["target"], "why": why})
    order = {"no_data": 0, "behind": 1}
    rows.sort(key=lambda r: (order.get(r["status"], 9), r["pod"]))
    return rows


# ---------------------------------------------------------------- 建议
# KPI 依赖链：前一个不解决，后面的努力会被浪费。
# 飞轮只报**链上第一个断点**（根因），不把下游结果当成新问题。
CHAINS = {
    "Pod A": ["A.indexable_pages", "A.impressions_per_page_month",
              "A.org_impressions_28d", "A.org_clicks_28d"],
    "Pod C": ["C.prospect_pool_ready", "C.outreach_sent",
              "C.outreach_reply_rate_pct"],
}
STANDALONE = {"Pod B": ["B.inquiries"], "Pod C_geo": ["C.geo_cited"]}

FIX = {
    "A.indexable_pages": ("build", "扩下一个页面族（F3 场站场景 / F1 国别页），页面数是展示量的唯一量级杠杆"),
    "A.impressions_per_page_month": ("strengthen", "页均展示偏低 → 查收录率与位次，不是继续堆页"),
    "A.org_impressions_28d": ("strengthen", "展示不足 → 位次太远，需要外链/内链，不是改 title"),
    "A.org_clicks_28d": ("strengthen", "有点击但太少 → 先解决上游展示量，CTR 天花板已知仅 14.7"),
    "B.inquiries": ("observe", "P0 修复已上线（main 0168d8a，线上已无 consent 门）⇒ 询盘现在会真的落库。"
                              "当前 D1 仍 0 行。下一步：① 等第一条真实询盘并核对 D1+audit_log；"
                              "② 中期建议把 Worker 变主后端（现在主后端是 Web3Forms 第三方，Worker 只是 sendBeacon 副发）"),
    "C.prospect_pool_ready": ("build", "目标池 ready 为 0 → 跑每周三发现任务，并换路径补抓（/editorial 等）"),
    "C.outreach_sent": ("strengthen", "活动已 armed 但没发出去 → 检查 start_date 与发送窗口，不是加名单"),
    "C.outreach_reply_rate_pct": ("measure", "发了但回复率无数据 → 等首批发出后统计 unique reply"),
    "C.geo_cited": ("build", "GEO 基线 20 条查询 0 露出 → 不做泛化内容，先抢出现最多的位置："
                             "给 cost/grid 两簇各做一个可被引用的数据页（带可核对数字与日期）"),
}


def propose(kpis, gap_rows, snap):
    """按依赖链找根因，每个 Pod 只给 1–2 条可执行动作。"""
    sug = []
    seen = set()

    def add(pod, kpi):
        if kpi in seen:
            return
        seen.add(kpi)
        kind, action = FIX.get(kpi, ("strengthen", "未达标，需要加强"))
        k = kpis.get(kpi, {})
        sug.append({"type": kind, "pod": pod, "kpi": kpi,
                    "action": action,
                    "evidence": "现值 %s / 目标 %s（%s）" % (
                        k.get("value"), k.get("target"), k.get("status"))})

    # 1) 每条依赖链只报第一个断点
    for pod, chain in CHAINS.items():
        for kpi in chain:
            k = kpis.get(kpi)
            if not k:
                continue
            if k["status"] != "on_track":
                add(pod, kpi)
                break

    # 2) 独立 KPI
    for pod, keys in STANDALONE.items():
        for kpi in keys:
            k = kpis.get(kpi)
            if k and k["status"] != "on_track":
                add(pod.replace("_geo", ""), kpi)

    # 3) 外部事实型提示（数据说不通的地方）
    ob = snap.get("outbound") or {}
    if (ob.get("sent") or 0) >= 5 and (ob.get("replies") or 0) == 0:
        sug.append({"type": "strengthen", "pod": "Pod C", "kpi": "C.outreach_reply_rate_pct",
                    "action": "已发 %s 封但 0 回复 → 先改首句与名单质量，不要加量" % ob.get("sent"),
                    "evidence": "sent=%s replies=0" % ob.get("sent")})
    if (ob.get("sent") or 0) == 0 and (ob.get("leads") or 0) > 0:
        sug.append({"type": "note", "pod": "Pod C", "kpi": "C.outreach_sent",
                    "action": "19 条线索已 armed 但今天未到发送窗口（周一至周五 09:00–18:00）→ 等 11-10 起观察",
                    "evidence": "leads=19 sent=0"})
    return sug


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["snapshot", "evaluate", "gaps", "propose", "status"])
    a = ap.parse_args()
    state = load(STATE, None)
    if not state:
        raise SystemExit("缺 state.json（KPI 定义），先建。")

    if a.cmd == "snapshot":
        snap = snapshot()
        kpis = compute_kpis(snap, state)
        _prev_hist = (state.get("history") or [None])[-1]
        state["kpis_latest"] = {"date": today(), "values": kpis}
        state.setdefault("history", []).append({"date": today(),
            "kpis": {k: v["value"] for k, v in kpis.items()},
            "statuses": {k: v["status"] for k, v in kpis.items()}})
        save(STATE, state)
        # 自进化的闭环出口：KPI 状态迁移 → 自动写进化条目（此前只能手写）
        if _prev_hist:
            _old = {k: {"status": s, "name": (state["kpis"].get(k) or {}).get("name"),
                        "value": (_prev_hist.get("kpis") or {}).get(k),
                        "source": (state["kpis"].get(k) or {}).get("source")}
                    for k, s in (_prev_hist.get("statuses") or {}).items()}
            _moved = evolution_from_kpi_delta({"kpis": _old}, kpis)
            if _moved:
                print("→ 自动记录 %d 条 KPI 状态迁移到 evolutions.jsonl" % len(_moved))
        print(json.dumps(snap, ensure_ascii=False, indent=1))
        return 0

    if a.cmd == "evaluate":
        snap = snapshot()
        kpis = compute_kpis(snap, state)
        ch = evaluate(snap, kpis)
        print("本次裁决变化的假设:", ch or "无")
        return 0

    snap = snapshot()
    kpis = compute_kpis(snap, state)
    if a.cmd == "gaps":
        for g in gaps(kpis):
            print("  [%s] %-22s %-6s %s" % (g["status"], g["kpi"], g["pod"], g["name"]))
        return 0
    if a.cmd == "propose":
        rows = propose(kpis, gaps(kpis), snap)
        for s in rows:
            print("  → [%-10s|%s] %s\n      依据: %s" % (
                s["type"], s["pod"], s["action"], s.get("evidence", "")))
        print("\n共 %d 条动作（按依赖链根因给，不是把所有未达标都列一遍）" % len(rows))
        # 落盘：让每日/每周档位能消费"下一步该做什么"，而不是只停留在屏幕上
        try:
            import datetime as _dt
            _out = os.path.join(FW, "next-actions.json")
            _prev = load(_out, {}) or {}
            save(_out, {"generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
                        "actions": rows, "acked": _prev.get("acked") or []})
            print("（已落盘 %s，日报/周报复用）" % os.path.basename(_out))
        except Exception as e:  # noqa: BLE001
            print("（落盘失败：%s）" % str(e)[:80])
        return 0
    # status
    print("=== KPI 现状（%s）===" % today())
    for k, v in kpis.items():
        print("  %-28s %-8s 值=%-8s 目标=%-6s %s" % (
            k, v["pod"], v["value"], v["target"], v["status"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
