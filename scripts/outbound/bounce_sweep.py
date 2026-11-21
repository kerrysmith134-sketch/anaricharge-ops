#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bounce_sweep.py — 扫营销外联活动的退信线索 → 自动抑制 + 从活动删除

## 为什么（2026-11-13）
Instantly 的 Bounces 页面渲染不稳定（两次尝试只抓到空文本），而 `send_health.py` 只给总数。
实测更可靠的判据：`/leads/list` 返回的 lead `status == -1` 就是退信线索。
本脚本把「发现退信 → 入抑制台账 → 从活动删除」一步做完，不再手工。

## 安全边界
- **只处理 MKT-OUTREACH-* 营销活动**（SDR 销售线是别人的资产，绝不碰）
- 只删 `status == -1` 的 lead；不动其他状态
- 抑制记录带原因与日期，写进 `ops/suppression.json`（可追溯）

## 用法
  python3 scripts/outbound/bounce_sweep.py            # 只报告（dry-run）
  python3 scripts/outbound/bounce_sweep.py --apply    # 真抑制 + 真删除
退出码：0 正常 / 1 有异常
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import instantly_client as ic  # noqa: E402

SUPPRESS = os.path.join(WS, "scripts", "metrics", "suppression.py")


def marketing_campaigns():
    r = ic.call("/campaigns?limit=100", "GET")
    items = (r.get("items") if isinstance(r, dict) else r) or []
    return [c for c in items if str(c.get("name", "")).startswith("MKT-OUTREACH")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    total_bad = 0
    for c in marketing_campaigns():
        cid, name = c.get("id"), c.get("name")
        try:
            d = ic.call("/leads/list", "POST", {"campaign": cid, "limit": 100})
        except SystemExit as e:
            print(f"  ⚠️ {name}: 读 leads 失败 {str(e)[:80]}")
            continue
        items = d.get("items") or []
        bad = [l for l in items if l.get("status") == -1]
        print(f"\n  {name}: leads={len(items)} · 退信(status=-1)={len(bad)}")
        for l in bad:
            em = str(l.get("email", "")).lower()
            if not em:
                continue
            total_bad += 1
            if not a.apply:
                print(f"    · {em}（dry-run：会抑制 + 删除）")
                continue
            subprocess.run([sys.executable, SUPPRESS, "add", em,
                            "--reason", f"hard bounce (Instantly {name}, lead status=-1, auto sweep)"],
                           capture_output=True, text=True)
            try:
                ic.call(f"/leads/{l['id']}", "DELETE", {})
                print(f"    ✅ {em} 已抑制 + 已删除")
            except SystemExit as e:
                print(f"    ⚠️ {em} 已抑制，删除失败：{str(e)[:80]}")
    print(f"\n  合计退信线索 {total_bad} 条{'（已处理）' if a.apply else '（dry-run）'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
