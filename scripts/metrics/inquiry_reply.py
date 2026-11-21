#!/usr/bin/env python3
"""inquiry_reply.py — 为新询盘生成「首封回复草稿」并登记高意向对话。

## 为什么
SLA 规定 T2（首次回复客户）≤4 工作小时，但团队不代发（R6）。
实际瓶颈不是"发"，是"写"——工程师忙着，一拖就是一天。
所以把可预填的部分全部预填好，人只剩"看一眼 → 复制 → 发送"。

## 做两件事
1. `draft`：读 D1 新询盘 → 按表单内容生成个性化回复草稿 → 写 `08-execution/inquiry/pending/<id>.md`
2. `log`：登记 D1 之外的高意向对话（WhatsApp/直邮/来电）→ `conversations.jsonl`

## 用法
  python3 scripts/metrics/inquiry_reply.py draft            # 为所有未处理询盘生成草稿
  python3 scripts/metrics/inquiry_reply.py draft --id <sid> # 指定一条
  python3 scripts/metrics/inquiry_reply.py log --channel whatsapp --note "问 240kW 报价"
  python3 scripts/metrics/inquiry_reply.py list             # 看待发草稿
"""
import argparse
import datetime as dt
import json
import os
import sys

WS = "/Users/kerrychu/anari-charge-website"
PEND = os.path.join(WS, "08-execution", "inquiry", "pending")
CONV = os.path.join(WS, "08-execution", "inquiry", "conversations.jsonl")


def d1_rows(limit=50):
    sys.path.insert(0, os.path.join(WS, "scripts", "metrics"))
    import d1_query as d1q
    return d1q.query(
        "SELECT submission_id, email, form_type, consent, status, created_at, "
        "payload, content_path FROM submissions ORDER BY created_at DESC LIMIT %d" % limit)


def parse_payload(raw):
    """payload 是表单字段的 JSON 文本；解析失败就原样返回，不编造。"""
    try:
        d = json.loads(raw or "{}")
        return d if isinstance(d, dict) else {}
    except Exception:  # noqa: BLE001
        return {"_raw": raw}


def pick(p, *keys):
    for k in keys:
        for kk in (k, k.lower(), k.upper()):
            v = p.get(kk)
            if v not in (None, ""):
                return str(v).strip()
    return ""


def build_draft(r):
    p = parse_payload(r.get("payload"))
    name = pick(p, "name", "full_name", "first_name") or "there"
    company = pick(p, "company", "organization")
    country = pick(p, "country", "location", "market")
    power = pick(p, "power", "kw", "power_kw")
    site = pick(p, "site_type", "use_case", "application")
    msg = pick(p, "message", "comments", "notes", "requirement")
    landing = r.get("content_path") or ""

    # 按客户给了什么，决定推荐哪一条「约束」→ 与站内定位一致（按约束选型，不按功率）
    # 客户面语言必须与站点主语言一致（英文）——正文里不能出现中文
    rec = []
    if power:
        rec.append("- At %s two of our platforms overlap. Whether you need dual standard "
                   "(CCS2 + GB/T) is what decides between them." % power)
    if site:
        rec.append("- For a %s site the binding constraint is usually maintenance access or "
                   "transformer headroom, not the charger rating — I can send a one-pager." % site)
    if "hot" in (msg or "").lower() or "temperature" in (msg or "").lower():
        rec.append("- On high ambient: we publish what we actually measured at 45 °C+, "
                   "including what we could not measure (DOI below).")
    if country:
        rec.append("- Noted on %s — if the grid connection is the slow part there, say so "
                   "and I will size to what the grid can deliver." % country)

    subject = "Re: your enquiry — one question before we size it"
    body = """Hi {name},

Thanks for reaching out{co}.

I have your enquiry. Before I send specs, one question that decides most of the
work:

  What is the available capacity at the site — the kVA you can actually draw?

With that number I can tell you what is realistic at your power level, and what
would force a different platform. Without it I would just be sending a brochure.

{recs}

Useful meanwhile: our measured hot-climate and monsoon field data is public and
citable (CC BY 4.0, DOI 10.5281/zenodo.24039549) — including the four things we
could not measure:
  https://www.anaricharge.com/data/findings-2026

I will follow up within one business day.

Best regards,
<YOUR NAME>
Anari Energy · Shenzhen
kerry@anaricharge.com · WhatsApp +86 188 6620 5186

---
auto-draft · submitted {created} · form {ftype} · landing {landing}
{msgline}""".format(
        name=name,
        co=(" at %s" % company) if company else "",
        recs="\n".join(rec),
        created=r.get("created_at") or "",
        ftype=r.get("form_type") or "",
        landing=landing or "-",
        msgline=("Customer note: %s" % msg) if msg else "Customer left no note",
    )
    meta = {"platform": "email", "to": r.get("email"), "submission_id": r.get("submission_id"),
            "subject": subject, "created": dt.date.today().isoformat(),
            "country": country, "power": power, "site_type": site}
    return meta, body


def cmd_draft(only_id=""):
    try:
        rows = d1_rows()
    except Exception as e:  # noqa: BLE001
        print("读 D1 失败：%s" % str(e)[:160])
        return 1
    if only_id:
        rows = [r for r in rows if r.get("submission_id") == only_id]
    if not rows:
        print("没有询盘可生成草稿（D1 为空）。")
        return 0
    os.makedirs(PEND, exist_ok=True)
    n = 0
    for r in rows:
        sid = r.get("submission_id") or "unknown"
        path = os.path.join(PEND, "%s.md" % sid)
        if os.path.exists(path):
            continue
        meta, body = build_draft(r)
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(meta, ensure_ascii=False) + "\n\n" + body)
        n += 1
        print("  已生成草稿: %s → %s" % (sid, r.get("email")))
    print("\n生成 %d 份 | 待发目录 %s" % (n, PEND))
    print("复制正文到邮件发出后，跑：python3 scripts/metrics/inquiry_alert.py --ack %s"
          % (rows[0].get("submission_id") if rows else "<id>"))
    return 0


def cmd_list():
    if not os.path.isdir(PEND):
        print("待发目录为空。")
        return 0
    files = [f for f in sorted(os.listdir(PEND)) if f.endswith(".md")]
    if not files:
        print("待发目录为空。")
        return 0
    print("待发询盘回复 %d 份：\n" % len(files))
    for f in files:
        raw = open(os.path.join(PEND, f), encoding="utf-8").read()
        line = raw.splitlines()[0] if raw else "{}"
        try:
            m = json.loads(line)
        except Exception:  # noqa: BLE001
            m = {}
        print("  [%s] → %s | %s" % (f[:-3], m.get("to"), m.get("subject")))
    return 0


def cmd_log(channel, note):
    rec = {"date": dt.date.today().isoformat(), "channel": channel,
           "note": note, "logged_at": dt.datetime.now().isoformat(timespec="seconds")}
    os.makedirs(os.path.dirname(CONV), exist_ok=True)
    with open(CONV, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    n = sum(1 for _ in open(CONV, encoding="utf-8")) if os.path.exists(CONV) else 1
    print("已登记高意向对话（%s）| 累计 %d 条" % (channel, n))
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    d = sub.add_parser("draft")
    d.add_argument("--id", default="")
    sub.add_parser("list")
    lg = sub.add_parser("log")
    lg.add_argument("--channel", default="other",
                    choices=["whatsapp", "email", "phone", "linkedin", "other"])
    lg.add_argument("--note", default="")
    a = ap.parse_args()
    if a.cmd == "draft":
        return cmd_draft(a.id)
    if a.cmd == "list":
        return cmd_list()
    if a.cmd == "log":
        return cmd_log(a.channel, a.note)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
