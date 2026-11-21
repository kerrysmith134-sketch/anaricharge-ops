#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""suppression.py — 统一抑制台账（ANARI-0094 轻量实现）

## 为什么需要
外联、培育、社区回复三条线各自维护"不要联系"的名单，早晚会漂：
Instantly 里有退信地址、Brevo 里有退订联系人、台账里有人被明确拒绝过——
只要有一条没同步，就会给明确说过"不要联系我"的人再发一次。那是真实的法律与声誉风险。

所以只保留**一个**台账 `ops/suppression.json`，发送前统一查。

## 用法
  python3 scripts/metrics/suppression.py list
  python3 scripts/metrics/suppression.py add someone@example.com --reason "明确拒绝" --source reply
  python3 scripts/metrics/suppression.py add example.org --type domain --reason "退信" --source bounce
  python3 scripts/metrics/suppression.py check someone@example.com     # 退出码 1 = 命中，必须 HOLD
  python3 scripts/metrics/suppression.py import-instantly             # 从 Instantly 拉抑制清单合并
"""
import argparse
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
LEDGER = os.path.join(WS, "ops", "suppression.json")


def load():
    try:
        return json.load(open(LEDGER, encoding="utf-8"))
    except (OSError, ValueError):
        return {"updated_at": "", "entries": []}


def save(d):
    d["updated_at"] = dt.date.today().isoformat()
    json.dump(d, open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def norm(v, kind="email"):
    v = (v or "").strip().lower()
    if kind == "email" and "@" in v:
        return v
    if kind == "domain":
        return v.lstrip("@").replace("www.", "")
    return v


def match(entries, value):
    """返回命中的 entry（邮箱精确 / 域名后缀 / 机构名包含）。"""
    v = norm(value)
    if not v:
        return None
    domain = v.split("@")[-1] if "@" in v else v
    for e in entries:
        t = e.get("type", "email")
        tgt = e.get("value", "")
        if t == "email" and v == tgt:
            return e
        if t == "domain" and (v == tgt or domain == tgt or domain.endswith("." + tgt)):
            return e
        if t == "org" and tgt and (tgt in v or v in tgt):
            return e
    return None


def cmd_add(a):
    d = load()
    val = norm(a.value, a.type)
    if any(e["value"] == val and e.get("type", "email") == a.type for e in d["entries"]):
        print("已在台账（幂等）:", val)
        return 0
    d["entries"].append({
        "value": val, "type": a.type, "reason": a.reason,
        "source": a.source, "added_at": dt.date.today().isoformat()})
    save(d)
    print(f"已加入：{a.type}:{val}（{a.reason}）→ 共 {len(d['entries'])} 条")
    return 0


def cmd_list(a):
    d = load()
    print(f"抑制台账：{len(d['entries'])} 条（更新于 {d.get('updated_at')}）")
    for e in d["entries"]:
        print(f"  {e.get('type','email'):7s} {e['value']:44s} {e.get('reason','')[:24]:26s} "
              f"src={e.get('source','')}")
    return 0


def cmd_check(a):
    d = load()
    hit = match(d["entries"], a.value)
    if hit:
        print(f"❌ HOLD — {a.value} 命中抑制台账：{hit.get('value')}（{hit.get('reason')}）")
        return 1
    print(f"✅ 可发送（未命中 {len(d['entries'])} 条抑制记录）：{a.value}")
    return 0


def cmd_import_instantly(a):
    """从 Instantly 拉 blocklist 合并（尽力而为；失败不阻塞）。"""
    sys.path.insert(0, os.path.join(WS, "scripts", "outbound"))
    try:
        import instantly_client as ic
        d = ic.call("/blocklist-entries", "GET")
        items = d if isinstance(d, list) else (d.get("items") or [])
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ 读取 Instantly 抑制清单失败（{type(e).__name__}: {str(e)[:80]}）")
        return 0
    ledger = load()
    added = 0
    for it in items:
        val = (it.get("email") or it.get("value") or "").strip().lower()
        if not val:
            continue
        if match(ledger["entries"], val):
            continue
        ledger["entries"].append({"value": val, "type": "email", "reason": "Instantly blocklist",
                                  "source": "instantly", "added_at": dt.date.today().isoformat()})
        added += 1
    save(ledger)
    print(f"从 Instantly 合并 {added} 条 → 台账共 {len(ledger['entries'])} 条")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p = sub.add_parser("add")
    p.add_argument("value")
    p.add_argument("--type", default="email", choices=["email", "domain", "org"])
    p.add_argument("--reason", required=True)
    p.add_argument("--source", default="manual")
    p = sub.add_parser("check")
    p.add_argument("value")
    sub.add_parser("import-instantly")
    a = ap.parse_args()
    return {"list": cmd_list, "add": cmd_add, "check": cmd_check,
            "import-instantly": cmd_import_instantly}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
