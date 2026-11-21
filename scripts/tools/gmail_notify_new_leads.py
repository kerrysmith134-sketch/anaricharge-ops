#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gmail_notify_new_leads.py — 新询盘 → 用真实浏览器从 kerry@anaricharge.com 发出通知

## 为什么（2026-11-12 事故）
之前 Worker 用 Instantly `/emails/test` 代发通知，**信到了但正文是空的**（用户截图确认）。
用户明确要求："直接用浏览器操作我的 kerry@anaricharge.com 邮箱收和发就行了"。

## 做法
- 数据源：D1 `submissions`（唯一权威）
- 去重：`ops/gmail-notified.json` 记录已通知过的 submission_id
- 发送：调用 `scripts/tools/gmail_send.py`（真实 Gmail compose）
- 一次运行只发一封汇总（多条新询盘合并成一封），避免刷屏
- 保护：测试地址（含 example.com / ts- 前缀）不发；已通知过的不重复发

## 用法
  python3 scripts/tools/gmail_notify_new_leads.py            # 有新询盘就发
  python3 scripts/tools/gmail_notify_new_leads.py --dry      # 只打印
退出码：0 成功（含无新询盘）/ 1 失败
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(WS, "ops", "gmail-notified.json")
SEND = os.path.join(WS, "scripts", "tools", "gmail_send.py")
TO = "kerry@anaricharge.com"


def d1(sql):
    r = subprocess.run([sys.executable, os.path.join(WS, "scripts/metrics/d1_query.py"), "sql", sql],
                       capture_output=True, text=True, timeout=180)
    rows = []
    for line in (r.stdout or "").split("\n"):
        if line.strip().startswith("{"):
            try:
                rows.append(json.loads(line))
            except Exception:  # noqa: BLE001
                pass
    return rows


def outbox_status():
    """查每个 submission 的 notify outbox 状态（2026-11-12 方案 2）：
    Worker 已恢复 Brevo 即时通知；本 Gmail 档位只在 Brevo **没发成** 时才兜底，
    避免同一条询盘发两封。"""
    rows = d1("SELECT submission_id, kind, status, attempts FROM outbox WHERE kind='notify'")
    return {r["submission_id"]: r for r in rows}


def load_state():
    if os.path.exists(STATE):
        try:
            return json.load(open(STATE, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
    return {"notified": {}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    st = load_state()
    ob = outbox_status()
    rows = d1("SELECT submission_id, email, payload, created_at FROM submissions ORDER BY created_at DESC LIMIT 50")
    fresh = []
    for r in rows:
        sid = r["submission_id"]
        if sid in st["notified"]:
            continue
        email = (r.get("email") or "").lower()
        if "example.com" in email or email.startswith("ts-"):
            continue  # 测试地址不通知
        # 方案 2（用户 2026-11-12 拍板）：Brevo 即时通知是主通道，本 Gmail 档位只兜底。
        # 只有 Brevo 那封失败（outbox=dead/缺失）时才由这里补发，避免同一询盘发两封。
        rec = ob.get(sid)
        if rec and rec.get("status") == "sent":
            continue
        p = json.loads(r["payload"]) if isinstance(r.get("payload"), str) else (r.get("payload") or {})
        fresh.append((sid, r, p))
    if not fresh:
        print("  无新询盘需通知")
        return 0
    lines = ["有新询盘（来自网站）：", ""]
    for sid, r, p in fresh:
        when = dt.datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")).astimezone(
            dt.timezone(dt.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")
        lines += [
            f"· {p.get('FIRSTNAME') or '(无姓名)'} — {p.get('COMPANY') or '(无公司)'}",
            f"  国家/项目：{p.get('COUNTRY') or '-'} / {p.get('PRODUCT') or '-'}",
            f"  邮箱：{r['email']}",
            f"  描述：{(p.get('PROJECT') or '（空）')[:300]}",
            f"  时间：{when}（北京）· 同意营销：{'是' if str(p.get('consent')) == '1' else '否'}",
            f"  id：{sid}",
            "",
        ]
    lines += ["主记录：D1 anari-leads.submissions；销售跟进：Brevo CRM。", "—— 自动通知（Gmail 通道）"]
    body = "\n".join(lines)
    subj = f"新询盘 {len(fresh)} 条 · {fresh[0][2].get('COMPANY') or fresh[0][1]['email']}"
    print(f"  待发 {len(fresh)} 条 → {subj}")
    if a.dry:
        print(body[:500]); return 0
    tmp = "/tmp/gmail-notify-body.txt"
    open(tmp, "w", encoding="utf-8").write(body)
    rc = subprocess.run([sys.executable, SEND, "--to", TO, "--subject", subj, "--body-file", tmp],
                        cwd=WS, capture_output=True, text=True, timeout=600).returncode
    if rc != 0:
        print("  ❌ 发送失败")
        return 1
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    for sid, _r, _p in fresh:
        st["notified"][sid] = now
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"  ✅ 已发送并记录 {len(fresh)} 条")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
