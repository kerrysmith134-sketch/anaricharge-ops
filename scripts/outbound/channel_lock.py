#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""channel_lock.py — 外联/社媒频道的互斥锁（防并行会话撞车）

## 为什么需要
2026-11-10 发现：EcoMENA 编辑回复后，我方已经有一封"拒绝付费"的回信发出，
但那封信**不在 Instantly 的发件记录里** —— 说明有另一条路径（人工或并行会话）在操作同一个外联活动。
两边同时回信会给媒体留下极差印象（重复、口径冲突），比不发更糟。

## 机制
- 锁文件 `ops/locks/<channel>.json`：{owner, purpose, acquired_at, expires_at}
- `acquire` 前若有人持有且未过期 → 拒绝（退出码 3），并打印当前持有者
- `release` 只允许持有者释放（或 `--force`）
- TTL 默认 30 分钟，避免进程崩溃后锁死
- **凡是"对外发送/发布"动作（回信、发信、发帖、投稿），先 acquire 再动手**

## 用法
  python3 scripts/outbound/channel_lock.py status  outbound
  python3 scripts/outbound/channel_lock.py acquire outbound --owner lead --purpose "回复 EcoMENA"
  python3 scripts/outbound/channel_lock.py release outbound --owner lead
退出码：0 成功 / 3 已被他人持有 / 4 状态异常
"""
import argparse
import datetime as dt
import json
import os
import sys

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOCK_DIR = os.path.join(WS, "ops", "locks")
TTL_MIN = 30


def path_for(channel):
    return os.path.join(LOCK_DIR, f"{channel}.json")


def read_lock(channel):
    p = path_for(channel)
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {"owner": "?", "corrupt": True}


def is_live(lock):
    if not lock or lock.get("corrupt"):
        return bool(lock and lock.get("corrupt"))
    try:
        expires = dt.datetime.fromisoformat(lock["expires_at"])
    except Exception:  # noqa: BLE001
        return True
    return dt.datetime.now(dt.timezone.utc) < expires


def cmd_status(channel):
    lock = read_lock(channel)
    if not lock:
        print(f"🔓 {channel}: 未加锁")
        return 0
    state = "🔒 持有中" if is_live(lock) else "⏳ 已过期（可接管）"
    print(f"{state} {channel}: owner={lock.get('owner')} purpose={lock.get('purpose')} "
          f"acquired={lock.get('acquired_at')} expires={lock.get('expires_at')}")
    return 0


def cmd_acquire(channel, owner, purpose, force):
    lock = read_lock(channel)
    if is_live(lock) and not force and lock.get("owner") != owner:
        print(f"❌ {channel} 已被 {lock.get('owner')} 持有（{lock.get('purpose')}，"
              f"至 {lock.get('expires_at')}）。")
        print("   不要抢：先确认对方在做什么，或等锁过期（30 分钟）。")
        return 3
    now = dt.datetime.now(dt.timezone.utc)
    rec = {"channel": channel, "owner": owner, "purpose": purpose,
           "acquired_at": now.isoformat(timespec="seconds"),
           "expires_at": (now + dt.timedelta(minutes=TTL_MIN)).isoformat(timespec="seconds")}
    os.makedirs(LOCK_DIR, exist_ok=True)
    json.dump(rec, open(path_for(channel), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"🔒 已加锁 {channel} → {owner}（{TTL_MIN} 分钟）purpose={purpose}")
    return 0


def cmd_release(channel, owner, force):
    lock = read_lock(channel)
    if not lock:
        print(f"🔓 {channel} 本来就没锁")
        return 0
    if lock.get("owner") != owner and not force:
        print(f"❌ {channel} 由 {lock.get('owner')} 持有，你不能释放（用 --force 强制）")
        return 3
    os.remove(path_for(channel))
    print(f"🔓 已释放 {channel}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["status", "acquire", "release"])
    ap.add_argument("channel", help="outbound / community / brevo / social ...")
    ap.add_argument("--owner", default="lead")
    ap.add_argument("--purpose", default="")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.action == "status":
        return cmd_status(a.channel)
    if a.action == "acquire":
        return cmd_acquire(a.channel, a.owner, a.purpose, a.force)
    return cmd_release(a.channel, a.owner, a.force)


if __name__ == "__main__":
    raise SystemExit(main())
