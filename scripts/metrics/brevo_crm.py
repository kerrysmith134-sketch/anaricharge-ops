#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""brevo_crm.py — SAQO 账本 → Brevo CRM Deals 同步（GROW-005 完整版）

## 为什么这么做
本地账本（`08-execution/inquiry/lifecycle.jsonl`）解决了"有没有把线索当机会看"，
但销售不在这里工作。Brevo 已经有账号、有联系人，**自带 CRM Deals**，
所以用它做销售侧的共同界面，比再引入一个 HubSpot 合理。

## 关键事实（2026-11-08 实测，别再猜）
- `POST /v3/crm/deals` 可用；返回 `{id}`
- deal 的 attributes 里：`deal_name`、`deal_description`、`amount`、
  `deal_stage`、`pipeline`、`deal_owner` 由服务端补默认值
- **没有公开的 pipeline / stage 列表端点**（`/v3/crm/pipelines` 404 等）
  ⇒ 本脚本不猜 stage id：**stage 留给销售在 UI 里推进**，
  我们在 `deal_name` 与 `deal_description` 里写清楚状态、六条件进度与 submission_id。

## 幂等
按 `deal_description` 里的 `submission_id=` 匹配已有 deal：
有则 PATCH，无则 POST。重复跑不会产生重复商机。

## 用法
  python3 scripts/metrics/brevo_crm.py whoami
  python3 scripts/metrics/brevo_crm.py deals                 # 列出现有 deals
  python3 scripts/metrics/brevo_crm.py push --dry            # 预览要推什么
  python3 scripts/metrics/brevo_crm.py push                  # 真推
  python3 scripts/metrics/brevo_crm.py verify                # 对账：账本 vs Brevo
  python3 scripts/metrics/brevo_crm.py delete --sid <sid>    # 删测试残留（默认 dry-run）
  python3 scripts/metrics/brevo_crm.py delete --sid <sid> --yes   # 真删（不可逆）

## 删除护栏（2026-11-09 加）
DELETE 是不可逆动作（R6）。本命令只用于清理**测试残留**：
- 默认 dry-run，必须显式 `--yes` 才真删；
- 若 `--sid` 命中本地账本里的记录 → **直接拒绝**（真实商机只能人工在 UI 处理）。
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SECRETS = os.path.join(WS, ".secrets", "brevo.json")
API = "https://api.brevo.com/v3"
STATUS_LABEL = {
    "new": "New inquiry", "mql": "MQL", "sal": "SAL",
    "saqo": "SAQO", "won": "Won", "lost": "Lost", "disqualified": "Disqualified",
}
PUSH_STATUSES = {"mql", "sal", "saqo", "won", "lost"}   # new 不推：还没被当机会


def key():
    try:
        d = json.load(open(SECRETS, encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"缺少 {SECRETS}（Brevo API key，600 权限）")
    k = (os.environ.get("BREVO_API_KEY") or d.get("api_key") or "").strip()
    if not k.startswith("xkeysib-"):
        raise SystemExit("Brevo API key 格式不对（应以 xkeysib- 开头）")
    return k


def call(method, path, body=None, timeout=30):
    req = urllib.request.Request(
        API + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"api-key": key(), "Content-Type": "application/json",
                 "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "ignore")
        return e.code, {"error": raw[:300]}
    except Exception as e:  # noqa: BLE001
        return 0, {"error": f"{type(e).__name__}: {str(e)[:200]}"}


def ledger():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import lead_lifecycle as L
    return list(L.load().values())


def all_deals(limit=100):
    out, offset = [], 0
    while True:
        code, d = call("GET", f"/crm/deals?limit={limit}&offset={offset}")
        if code != 200:
            raise SystemExit(f"读取 deals 失败 HTTP {code}: {d.get('error')}")
        items = d.get("items") or []
        out.extend(items)
        offset += limit
        if len(items) < limit or offset > 1000:
            break
    return out


def sid_of(deal):
    desc = (deal.get("attributes") or {}).get("deal_description") or ""
    for part in desc.replace("|", ";").split(";"):
        part = part.strip()
        if part.startswith("submission_id="):
            return part.split("=", 1)[1].strip()
    return ""


def deal_payload(rec):
    status = rec.get("status", "new")
    q = rec.get("qualification") or {}
    qn = sum(1 for v in q.values() if v)
    desc = (f"submission_id={rec['submission_id']}; status={status}; "
            f"qualification={qn}/6; country={rec.get('country') or '-'}; "
            f"project_type={rec.get('project_type') or '-'}; "
            f"source={(rec.get('attr_first') or rec.get('content_path') or '-')[:120]}")
    name = f"{STATUS_LABEL.get(status, status)} · {rec.get('country') or 'Unknown market'} · " \
           f"{rec.get('project_type') or 'project'}"
    attrs = {"deal_name": name[:120], "deal_description": desc[:1000]}
    # 2026-11-21 修：pipeline 被清零（180k→0）时，原逻辑因 falsy 不清空 Brevo 的 amount，
    # 导致 CRM 里仍显示 180,000（与账本不一致）。只要账本有该字段就同步，包括 0。
    if "pipeline_value" in rec:
        attrs["amount"] = rec.get("pipeline_value") or 0
    return {"name": name[:120],
            "attributes": attrs,
            "linkedContactsIds": [],
            "linkedCompaniesIds": []}


def cmd_whoami(a):
    code, d = call("GET", "/account")
    if code != 200:
        print(f"❌ HTTP {code}: {d}"); return 1
    plan = (d.get("plan") or [{}])[0]
    print(f"✅ {d.get('email')} · {d.get('companyName')} · plan={plan.get('type')} "
          f"credits={plan.get('credits')}")
    code2, deals = call("GET", "/crm/deals?limit=1")
    print(f"   CRM deals 端点: HTTP {code2} · 现有 {((deals.get('pager') or {}).get('total'))} 个")
    return 0


def cmd_deals(a):
    ds = all_deals()
    if not ds:
        print("Brevo 里还没有 deal。")
        return 0
    print(f"{'submission_id':<16} {'amount':>10}  name")
    for d in ds:
        at = d.get("attributes") or {}
        print(f"{sid_of(d)[:16]:<16} {str(at.get('amount') or 0):>10}  {at.get('deal_name','')[:60]}")
    print(f"\n共 {len(ds)} 个")
    return 0


def cmd_push(a):
    recs = [r for r in ledger() if r.get("status") in PUSH_STATUSES]
    if not recs:
        print("账本里没有 mql/sal/saqo/won/lost 的记录（new 不推）——先 qualify 再 push。")
        return 0
    existing = {sid_of(d): d for d in all_deals()}
    created = updated = failed = 0
    for rec in recs:
        sid = rec["submission_id"]
        payload = deal_payload(rec)
        if sid in existing:
            did = existing[sid].get("id")
            if a.dry:
                print(f"  [dry] UPDATE {sid} → {payload['attributes']['deal_name'][:60]}")
                updated += 1
                continue
            code, d = call("PATCH", f"/crm/deals/{did}", {"attributes": payload["attributes"]})
            ok = code in (200, 204)
            updated += ok
            failed += not ok
            print(f"  {'✅' if ok else '❌'} UPDATE {sid} HTTP {code}")
        else:
            if a.dry:
                print(f"  [dry] CREATE {sid} → {payload['attributes']['deal_name'][:60]}")
                created += 1
                continue
            code, d = call("POST", "/crm/deals", payload)
            ok = code in (200, 201)
            created += ok
            failed += not ok
            print(f"  {'✅' if ok else '❌'} CREATE {sid} HTTP {code} {'' if ok else d.get('error','')[:120]}")
    print(f"\n{'预览' if a.dry else '完成'}：新建 {created} · 更新 {updated} · 失败 {failed}")
    return 1 if failed else 0


def cmd_verify(a):
    """两侧对账。**网络不通 ≠ 数据不一致**：连不上时只告警并返回 0，
    避免把"Brevo 暂时不可达"误报成数据漂移（这个坑在 D1 上踩过一次）。"""
    recs = ledger()
    try:
        ds = all_deals()
    except SystemExit as e:
        print(f"⚠ 无法连接 Brevo，本次跳过对账（不判失败）：{str(e)[:120]}")
        return 0
    pushed = {r["submission_id"] for r in recs if r.get("status") in PUSH_STATUSES}
    in_brevo = {sid_of(d) for d in ds if sid_of(d)}
    missing = pushed - in_brevo
    orphan = in_brevo - {r["submission_id"] for r in recs}
    print(f"账本里该推的 {len(pushed)} 条 · Brevo 有 {len(in_brevo)} 条")
    if missing:
        print(f"  ⚠ 账本有但 Brevo 没有 {len(missing)} 条：{sorted(missing)[:5]}")
    if orphan:
        print(f"  ⚠ Brevo 有但账本没有 {len(orphan)} 条（可能是人工建的）：{sorted(orphan)[:5]}")
    if not missing and not orphan:
        print("  ✅ 两侧一致")
    return 0 if not missing else 1


def cmd_delete(a):
    """删测试残留 deal。默认 dry-run；账本里的真实商机拒绝删除（护栏）。

    为什么要有这个命令：11-08 的 GA4 e2e 自测在 Brevo 留了 1 条
    `TEST-ga4-e2e-001`，对账时长期报「Brevo 有但账本没有」——噪声会让
    真正的异常淹没。清理动作必须可复跑、可审计，不能靠一次性脚本。
    """
    target = a.sid.strip()
    try:
        ds = all_deals()
    except SystemExit as e:
        print(f"⚠ 连不上 Brevo，本次无法删除：{str(e)[:120]}")
        return 1
    hit = [d for d in ds if sid_of(d) == target]
    if not hit:
        print(f"❌ Brevo 里没有 submission_id={target} 的 deal（未做任何事）")
        return 1
    # 护栏：真实商机只能人工处理
    if target in {r["submission_id"] for r in ledger()}:
        print(f"⛔ {target} 在本地账本里，拒绝删除（真实商机必须人工在 Brevo UI 处理）")
        return 2
    for d in hit:
        at = d.get("attributes") or {}
        print(f"  目标：id={d.get('id')} · {at.get('deal_name')} · {at.get('deal_description','')[:80]}")
        if not a.yes:
            print("  [dry-run] 未删除。确认要删请加 --yes（不可逆）")
            continue
        code, body = call("DELETE", f"/crm/deals/{d.get('id')}")
        ok = code in (200, 204)
        print(f"  {'✅ 已删除' if ok else '❌ 删除失败'} HTTP {code} {'' if ok else body.get('error','')[:160]}")
        if not ok:
            return 1
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("whoami"); sub.add_parser("deals"); sub.add_parser("verify")
    p = sub.add_parser("push"); p.add_argument("--dry", action="store_true")
    p = sub.add_parser("delete")
    p.add_argument("--sid", required=True, help="submission_id（如 TEST-ga4-e2e-001）")
    p.add_argument("--yes", action="store_true", help="真删（不可逆，必须显式）")
    a = ap.parse_args()
    return {"whoami": cmd_whoami, "deals": cmd_deals,
            "push": cmd_push, "verify": cmd_verify,
            "delete": cmd_delete}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
