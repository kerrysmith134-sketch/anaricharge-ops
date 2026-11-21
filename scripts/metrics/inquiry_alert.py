#!/usr/bin/env python3
"""inquiry_alert.py — 新询盘告警（北极星最后一公里）。

## 为什么需要
北极星是询盘。但 2026-11-07 核查发现：询盘落地后**没有任何人被告知**——
- 表单主后端是 Web3Forms（邮件到 sales@），Worker 只写 D1 + Brevo 联系人
- 唯一的 D1 检查是每天 22:17 的监控档位
⇒ **09:00 来的询盘可能到次日 22:17 才被团队看见**（响应延迟最长 ~37 小时）。
B2B 工业品里，第一个回复的人赢一半。所以补一个可高频跑的告警。

## 判据
读 D1 `submissions`（唯一真实口径），与上次检查的状态比对：
- 出现新 `submission_id` → 新询盘，输出告警 + 记录延迟（created_at → 现在）
- 已在状态里 → 视为已看过：
  - 超过 `--stale-hours`（默认 24h）仍未升级为 acked → 再提醒一次（防"看到但没跟"）

## 用法
  python3 scripts/metrics/inquiry_alert.py            # 检查并输出告警
  python3 scripts/metrics/inquiry_alert.py --json     # 机器可读
  python3 scripts/metrics/inquiry_alert.py --mark-seen   # 把所有当前行标为已见
退出码：有新询盘或超时未处理 → 0（有内容可报）；无新询盘 → 0（输出"无新询盘"）。
"""
import argparse
import datetime as dt
import json
import os
import sys

WS = "/Users/kerrychu/anari-charge-website"
STATE = os.path.join(WS, "08-execution", "metrics", "inquiry-alert-state.json")
LOGDIR = os.path.join(WS, "08-execution", "inquiry")


def load_state():
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {"seen": {}, "last_check": None}


def save_state(s):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(s, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def fetch_rows():
    """读 D1；失败返回 (None, reason) —— 不抛，避免告警器自己成为故障点。"""
    sys.path.insert(0, os.path.join(WS, "scripts", "metrics"))
    try:
        import d1_query as d1q
        return d1q.query(
            "SELECT submission_id, email, form_type, consent, status, created_at, "
            "content_path FROM submissions ORDER BY created_at DESC LIMIT 50"), None
    except Exception as e:  # noqa: BLE001
        try:
            import d1_query as d1q
            c = d1q.cache_get("recent")
            if c:
                return c.get("rows") or [], "cache@%s" % c.get("at")
        except Exception:  # noqa: BLE001
            pass
        return None, "%s: %s" % (type(e).__name__, str(e)[:120])


def hours_since(iso, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    try:
        t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=dt.timezone.utc)
        return (now - t).total_seconds() / 3600.0
    except Exception:  # noqa: BLE001
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--mark-seen", action="store_true")
    ap.add_argument("--stale-hours", type=float, default=24.0)
    ap.add_argument("--sla-hours", type=float, default=4.0,
                    help="首次响应 SLA（小时）。超过即升级告警")
    ap.add_argument("--ack", default="", help="标记某条询盘已回信（submission_id 或 all）")
    a = ap.parse_args()

    rows, err = fetch_rows()
    st = load_state()
    seen = st.get("seen") or {}

    if rows is None:
        msg = "⚠️ 询盘告警无法检查 D1：%s" % err
        print(msg if not a.json else json.dumps({"ok": False, "error": msg}, ensure_ascii=False))
        return 0

    new, stale = [], []
    for r in rows:
        sid = r.get("submission_id") or ""
        if not sid:
            continue
        if sid not in seen:
            new.append(r)
        else:
            h = hours_since(r.get("created_at"))
            mark = seen.get(sid) or {}
            if h is not None and h >= a.stale_hours and not mark.get("acked"):
                stale.append({**r, "hours_open": round(h, 1)})

    for r in new:
        seen[r["submission_id"]] = {
            "first_seen": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "created_at": r.get("created_at"), "acked": False}

    if a.mark_seen:
        for r in rows:
            sid = r.get("submission_id")
            if sid and sid in seen:
                seen[sid]["acked"] = True

    # SLA 判定：未 ack 且超过 sla-hours
    sla_breached = []
    for r in rows:
        sid = r.get("submission_id") or ""
        rec = seen.get(sid) or {}
        if not sid or rec.get("acked"):
            continue
        h = hours_since(r.get("created_at"))
        if h is not None and h >= a.sla_hours:
            sla_breached.append({**r, "hours_open": round(h, 1)})

    # 人工确认回信
    if a.ack:
        tgt = [k for k in seen] if a.ack == "all" else [a.ack]
        n = 0
        for sid in tgt:
            if sid in seen:
                seen[sid]["acked"] = True
                seen[sid]["acked_at"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
                n += 1
        print("已标记 %d 条为已回信" % n)

    st["seen"] = seen
    st["last_check"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    save_state(st)

    # 落盘日志（有事件才写）
    if new or stale:
        os.makedirs(LOGDIR, exist_ok=True)
        p = os.path.join(LOGDIR, "alerts-%s.jsonl" % dt.date.today().isoformat())
        with open(p, "a", encoding="utf-8") as f:
            for r in new:
                f.write(json.dumps({"type": "new", **r,
                                    "alert_at": st["last_check"]}, ensure_ascii=False) + "\n")
            for r in stale:
                f.write(json.dumps({"type": "stale", **r}, ensure_ascii=False) + "\n")

    out = {"ok": True, "rows": len(rows), "new": new, "stale": stale,
           "checked_at": st["last_check"]}
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0

    if not new and not stale and not sla_breached:
        print("无新询盘（D1 共 %d 行，已全部看过，无 SLA 超时）" % len(rows))
        return 0

    print("🚨 询盘告警 · %s" % st["last_check"])
    for r in new:
        h = hours_since(r.get("created_at"))
        print("  新询盘 %s | %s | %s | consent=%s | %s"
              % (r.get("created_at"), r.get("email"), r.get("form_type"),
                 r.get("consent"), r.get("content_path") or "-"))
        if h is not None:
            print("    已等待 %.1f 小时未响应" % h)
    for r in stale:
        print("  ⏰ 超时未跟进 %s | %s | 已开 %.0f 小时"
              % (r.get("created_at"), r.get("email"), r.get("hours_open")))
    if sla_breached:
        print("\n  ⛔ SLA 已破（首次响应 SLA %.0fh）：" % a.sla_hours)
        for r in sla_breached:
            print("     %s | %s | 已开 %.1f 小时 → 需立即升级"
                  % (r.get("created_at"), r.get("email"), r.get("hours_open")))
    print("\n处理完请跑：python3 scripts/metrics/inquiry_alert.py --mark-seen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
