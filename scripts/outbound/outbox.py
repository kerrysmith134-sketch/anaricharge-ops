#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""outbox.py — D1→Brevo outbox 运维工具（状态 / 主动排空 / 重放死信）

## 背景
2026-11-10 审计 P1：原来 D1 落库后 `ctx.waitUntil(deliverWithRetry(...))` 直连 Brevo，
请求结束即无保障，失败只留 dead 行、无重放工具。
现改为 outbox：任务落 `outbox` 表，由 cron（每分钟）或本脚本的 `tick` 主动排空，
失败按 2^n 分钟退避重试，超过 max_attempts 才 dead，可 `replay` 重放。

## 用法
  python3 scripts/outbound/outbox.py status     # pending / sending / dead 计数 + 最老的 pending
  python3 scripts/outbound/outbox.py tick       # 调 Worker /admin/outbox/tick 主动处理
  python3 scripts/outbound/outbox.py replay [--submission-id <sid>]
退出码：0 正常 / 1 发现 dead（需要人看）
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API = "https://api.anaricharge.com"
SECRETS = os.path.join(WS, ".secrets")


def admin_token():
    """运维 token = Worker 的 IP_HASH_SECRET；从 wrangler 的 secret 无法读出，
    这里用同一份部署文档记录的密钥来源：环境变量优先，其次 .secrets/worker-admin.json。"""
    tok = os.environ.get("ANARI_ADMIN_TOKEN", "")
    if tok:
        return tok
    p = os.path.join(SECRETS, "worker-admin.json")
    if os.path.exists(p):
        try:
            return json.load(open(p, encoding="utf-8")).get("token", "")
        except Exception:  # noqa: BLE001
            return ""
    return ""


def d1(sql):
    r = subprocess.run([sys.executable, os.path.join(WS, "scripts/metrics/d1_query.py"), "sql", sql],
                       capture_output=True, text=True, timeout=180)
    out = (r.stdout or "").strip()
    rows = []
    for line in out.split("\n"):
        line = line.strip()
        if line.startswith("{"):
            try:
                rows.append(json.loads(line))
            except Exception:  # noqa: BLE001
                pass
    return rows


def cmd_status():
    rows = d1("SELECT status, COUNT(*) AS n FROM outbox GROUP BY status")
    counts = {r.get("status"): r.get("n") for r in rows}
    print("outbox 状态:", counts or "（空）")
    oldest = d1("SELECT id, submission_id, attempts, next_attempt_at FROM outbox WHERE status='pending' ORDER BY id LIMIT 3")
    for r in oldest:
        print(f"  pending id={r['id']} sid={r['submission_id']} attempts={r['attempts']} next={r['next_attempt_at']}")
    dead = d1("SELECT id, submission_id, attempts, substr(last_error,1,80) AS err FROM outbox WHERE status='dead' ORDER BY id LIMIT 5")
    for r in dead:
        print(f"  DEAD id={r['id']} sid={r['submission_id']} attempts={r['attempts']} err={r['err']}")
    return 1 if dead else 0


def call(path):
    tok = admin_token()
    if not tok:
        print("❌ 缺少 admin token：设 ANARI_ADMIN_TOKEN，或写 .secrets/worker-admin.json {token:...}")
        return 2
    req = urllib.request.Request(API + path, method="POST",
                                 headers={"Origin": "https://www.anaricharge.com",
                                          "x-admin-token": tok, "Content-Type": "text/plain"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(r.read().decode()[:300])
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"❌ 调用失败：{e}")
        return 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["status", "tick", "replay"])
    ap.add_argument("--submission-id", default="")
    a = ap.parse_args()
    if a.action == "status":
        return cmd_status()
    if a.action == "tick":
        return call("/admin/outbox/tick")
    q = ("?submission_id=" + a.submission_id) if a.submission_id else ""
    return call("/admin/outbox/replay" + q)


if __name__ == "__main__":
    raise SystemExit(main())
