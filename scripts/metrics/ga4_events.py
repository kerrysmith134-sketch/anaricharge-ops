#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ga4_events.py — 生命周期事件进 GA4（Growth OS GROW-004 的服务端补全）

## 为什么用 Measurement Protocol 而不是 GTM
站点的前端事件（page_view / form_submit / tool_complete）走 dataLayer → GTM → GA4，
这条路对**浏览器里发生的事**是对的。但 MQL / SAL / SAQO 不是浏览器事件 ——
它们是人在 CLI 里推状态（`lead_lifecycle.py set`），没有浏览器上下文。
所以服务端用 GA4 Measurement Protocol 直发，客户端零改动。

## 需要什么
GA4 → Admin → Data streams → 选站点数据流 → **Measurement Protocol API secrets** →
Create，得到 `api_secret`。存 `.secrets/ga4.json`：
    {"measurement_id": "G-MT63H5Q8EV", "api_secret": "..."}
（2026-11-08 实测：当前浏览器登录账号**没有该属性的管理权限**，
 页面显示 "Missing permissions"，因此 secret 需由属性管理员创建。）

## 没有 secret 时不会丢事件
事件先写队列 `08-execution/metrics/ga4-queue.jsonl`；
`ga4_events.py flush` 在有 secret 后一次性补发（带原始 event_time，GA4 接受 72h 内）。

## 用法
  python3 scripts/metrics/ga4_events.py emit --name lead_mql --sid <submission_id> --country Jordan
  python3 scripts/metrics/ga4_events.py sync                  # 把账本当前状态刷成事件（幂等：按 sid+status 去重）
  python3 scripts/metrics/ga4_events.py flush                 # 补发队列
  python3 scripts/metrics/ga4_events.py status
"""
import argparse
import datetime as dt
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SECRETS = os.path.join(WS, ".secrets", "ga4.json")
QUEUE = os.path.join(WS, "08-execution", "metrics", "ga4-queue.jsonl")
SENT = os.path.join(WS, "08-execution", "metrics", "ga4-sent.json")
ENDPOINT = "https://www.google-analytics.com/mp/collect"
DEBUG_ENDPOINT = "https://www.google-analytics.com/debug/mp/collect"

EVENT_FOR_STATUS = {
    "mql": "lead_mql",
    "sal": "lead_sal",
    "saqo": "opportunity_created",
    "won": "closed_won",
    "lost": "closed_lost",
    "disqualified": "lead_disqualified",
}


def secrets():
    try:
        d = json.load(open(SECRETS, encoding="utf-8"))
    except FileNotFoundError:
        return None
    if not d.get("measurement_id") or not d.get("api_secret"):
        return None
    return d


def now_iso():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def enqueue(name, params, sid):
    """无 secret 时先落盘，保证不丢。幂等键：sid + name。"""
    os.makedirs(os.path.dirname(QUEUE), exist_ok=True)
    sent = load_sent()
    if f"{sid}:{name}" in sent:
        return "dup"
    with open(QUEUE, "a", encoding="utf-8") as f:
        f.write(json.dumps({"name": name, "params": params, "sid": sid,
                            "queued_at": now_iso()}, ensure_ascii=False) + "\n")
    return "queued"


def load_queue():
    if not os.path.exists(QUEUE):
        return []
    out = []
    for line in open(QUEUE, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def load_sent():
    try:
        return json.load(open(SENT, encoding="utf-8"))
    except FileNotFoundError:
        return {}


def save_sent(d):
    os.makedirs(os.path.dirname(SENT), exist_ok=True)
    json.dump(d, open(SENT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def post(text, dry_run=False):
    """直接发一条（带 event_time 以便补发时保留时间）。"""
    s = secrets()
    params = {"measurement_id": s["measurement_id"], "api_secret": s["api_secret"]}
    body = {
        "client_id": text["params"].pop("client_id", "server." + text["sid"][:24]),
        "events": [{"name": text["name"],
                    "params": {**text["params"], "event_time": text["queued_at"]}}],
    }
    if dry_run:
        return 200, {"dry": True, "body": body}
    req = urllib.request.Request(
        ENDPOINT + "?" + urllib.parse.urlencode(params),
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, {}
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read(300).decode("utf-8", "ignore")}
    except Exception as e:  # noqa: BLE001
        return 0, {"error": f"{type(e).__name__}: {str(e)[:160]}"}


def cmd_emit(a):
    params = {"submission_id": a.sid, "session_id": a.sid[:24]}
    if a.country:
        params["country"] = a.country
    if a.stage:
        params["stage"] = a.stage
    if a.value:
        params["value"] = a.value
    params["currency"] = "USD"
    if not secrets():
        r = enqueue(a.name, params, a.sid)
        print(f"{r}: {a.name} 已入队（缺 api_secret）→ 建好 secret 后跑 flush")
        return 0
    code, err = post({"name": a.name, "params": params, "sid": a.sid, "queued_at": now_iso()})
    if code in (200, 204):
        sent = load_sent(); sent[f"{a.sid}:{a.name}"] = now_iso(); save_sent(sent)
        print(f"✅ {a.name} → GA4 ({a.sid[:16]})")
        return 0
    print(f"❌ GA4 HTTP {code} {err.get('error', '')[:160]} → 已入队")
    enqueue(a.name, params, a.sid)
    return 1


def cmd_sync(a):
    """把账本里每条记录按当前状态补齐事件（幂等，不重复发）。"""
    import lead_lifecycle as L
    recs = list(L.load().values())
    if not recs:
        print("账本为空，无需同步。")
        return 0
    n = 0
    for r in recs:
        st = r.get("status")
        name = EVENT_FOR_STATUS.get(st)
        if not name:
            continue
        params = {"submission_id": r["submission_id"], "stage": st,
                  "country": r.get("country") or "", "currency": "USD"}
        if r.get("pipeline_value"):
            params["value"] = r["pipeline_value"]
        if not secrets():
            if enqueue(name, params, r["submission_id"]) == "queued":
                n += 1
        else:
            sent = load_sent()
            if f"{r['submission_id']}:{name}" in sent:
                continue
            code, err = post({"name": name, "params": params,
                              "sid": r["submission_id"], "queued_at": now_iso()})
            if code in (200, 204):
                sent[f"{r['submission_id']}:{name}"] = now_iso(); save_sent(sent); n += 1
            else:
                enqueue(name, params, r["submission_id"])
    print(f"sync 完成：新增/更新事件 {n} 条（队列总计 {len(load_queue())}）")
    return 0


def cmd_flush(a):
    if not secrets():
        print("仍缺 api_secret：GA4 → Admin → Data streams → Measurement Protocol API secrets")
        print(f"当前积压 {len(load_queue())} 条（不会丢）")
        return 1
    q = load_queue()
    if not q:
        print("队列为空。")
        return 0
    sent = load_sent()
    ok = fail = 0
    keep = []
    for item in q:
        code, err = post(item, dry_run=a.dry)
        if code in (200, 204):
            sent[f"{item['sid']}:{item['name']}"] = now_iso()
            ok += 1
        else:
            fail += 1
            keep.append(item)
        time.sleep(0.15)   # 别把 MP 打出限流
    save_sent(sent)
    with open(QUEUE, "w", encoding="utf-8") as f:
        for it in keep:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(f"flush：成功 {ok} · 失败 {fail} · 剩余 {len(keep)}")
    return 0 if fail == 0 else 1


def cmd_status(a):
    s = secrets()
    q = load_queue()
    print(f"api_secret: {'✅ 已配置' if s else '❌ 缺失'}"
          + (f"（{s['measurement_id']}）" if s else ""))
    print(f"待发队列: {len(q)} 条" + (f"，最早 {q[0]['queued_at']}" if q else ""))
    print(f"已发记录: {len(load_sent())} 条")
    if not s:
        print("\n拿到 secret 的步骤：GA4 → Admin → Data streams → 站点数据流 → "
              "Measurement Protocol API secrets → Create → 存 .secrets/ga4.json")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("emit")
    p.add_argument("--name", required=True)
    p.add_argument("--sid", required=True)
    p.add_argument("--country", default="")
    p.add_argument("--stage", default="")
    p.add_argument("--value", type=int)
    sub.add_parser("sync")
    p = sub.add_parser("flush"); p.add_argument("--dry", action="store_true")
    sub.add_parser("status")
    a = ap.parse_args()
    return {"emit": cmd_emit, "sync": cmd_sync, "flush": cmd_flush,
            "status": cmd_status}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
