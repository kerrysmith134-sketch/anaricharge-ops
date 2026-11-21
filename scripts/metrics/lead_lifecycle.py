#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lead_lifecycle.py — 询盘生命周期账本（北极星 SAQO 的落地件）

## 为什么需要（对应 Growth OS 计划 GROW-005）
计划把北极星从「询盘数」升级为 **SAQO（Sales-Accepted Qualified Project
Opportunity，销售接受的合格项目机会）及其 pipeline value**。
而我们现在的度量只到「D1 收到一条询盘」——没有 MQL / SAL / SAQO 任何一层，
也看不到丢失原因。于是：
  - 询盘数 = 0 时看不出是「没人来」还是「来了没被当机会」；
  - 销售拒绝的样本无法反哺内容与 ICP 判断。

**为什么先不做 CRM 集成**：HubSpot 目前只出现在文档里，没有代码集成也没有确认订阅。
在账号和 API key 落地前，用**本地账本 + D1 为询盘系统记录**是正确的中间态：
不假装有 CRM，也不阻塞 P0。等 HubSpot 上线，按 submission_id 迁移即可。

## SAQO 六条件（按 Growth OS 计划收紧；用户 2026-11-08 确认"要有效询盘"）
进 `saqo` 必须**六项全部为真**，缺一项只能是 `sal`（销售接受）或留在 `mql`：
  1. `real_contact`  真实可联系的企业/项目联系人（非垃圾、非求职、非学生作业）
  2. `icp`           属 ICP：CPO / EPC / 车队 / 能源地产等资产方
  3. `market`        国家属已服务或明确接受的目标市场
  4. `need`          有可识别的项目类型、场景或设备/系统需求
  5. `trigger`       有真实采购/投资/工程触发点，或已表达明确下一步
  6. `accepted`      销售接受并愿意跟进（有人负责、有下一步时间点）
**不因为是"看起来像机会"就放行** —— 放宽标准等于制造漂亮假数字。

## 口径
- **能进账本的只有 D1 `submissions` 里的真实询盘**（D1 是询盘唯一真实口径）。
- 状态机：`new → mql → sal → saqo → won | lost`，`disqualified` 表示确认不是机会。
  只允许向前或在同层内改判；`lost`/`disqualified` 必须写原因。
- **pipeline_value** 只在 `saqo` 及以后有意义（未加权金额）。
- 每条变更写 `events`，带时间、操作人、理由——这是"可解释"的最低要求。

## 用法
  python3 scripts/metrics/lead_lifecycle.py sync            # 拉 D1，补齐账本里没有的询盘
  python3 scripts/metrics/lead_lifecycle.py list [--all]    # 列表（默认只看未结案）
  python3 scripts/metrics/lead_lifecycle.py set <sid> mql --by kerry --note "有明确项目"
  python3 scripts/metrics/lead_lifecycle.py set <sid> saqo --value 180000 --by kerry
  python3 scripts/metrics/lead_lifecycle.py set <sid> lost --reason "只买配件"
  python3 scripts/metrics/lead_lifecycle.py report [--days 30]
"""
import argparse
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
LEDGER = os.path.join(WS, "08-execution", "inquiry", "lifecycle.jsonl")

STATES = ["new", "mql", "sal", "saqo", "won", "lost", "disqualified"]
ADVANCE = {"new", "mql", "sal", "saqo", "won"}   # 只这些会推进"历史最高阶段"
QUAL_KEYS = ["real_contact", "icp", "market", "need", "trigger", "accepted"]
ORDER = {s: i for i, s in enumerate(STATES)}
FORWARD = {"new": {"mql", "disqualified"},
           "mql": {"sal", "lost", "disqualified"},
           "sal": {"saqo", "lost"},
           "saqo": {"won", "lost"},
           "won": set(), "lost": set(), "disqualified": set()}


def now():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def load():
    if not os.path.exists(LEDGER):
        return {}
    out = {}
    with open(LEDGER, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            out[rec["submission_id"]] = rec
    return out


def save(recs):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "w", encoding="utf-8") as f:
        for r in sorted(recs.values(), key=lambda x: x.get("created_at") or ""):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def d1_submissions():
    """复用 d1_query 的取数（三级降级已在那边实现）。"""
    sys.path.insert(0, HERE)
    import d1_query  # noqa: WPS433
    # 真实 schema（PRAGMA table_info 核过）：没有 id / country / project_type 列，
    # 国家与项目类型在 payload JSON 里。别再猜列名 —— 猜错会表现为 D1 报错+清空账本。
    sql = ("SELECT submission_id, email, form_type, payload, consent, status, "
           "retry_count, created_at, attr_first, attr_last, content_path "
           "FROM submissions ORDER BY created_at DESC LIMIT 500")
    for via in ("wrangler", "auto"):      # token 常 403（账号权限），wrangler OAuth 可用
        try:
            rows = d1_query.query(sql, via=via)
            if rows is not None:
                return rows          # 注意：[] 是"成功但没有询盘"，不是失败
        except SystemExit as e:
            print(f"  via={via} 失败：{str(e)[:120]}")
        except Exception as e:
            print(f"  via={via} 异常：{type(e).__name__}: {str(e)[:120]}")
    return None



def pick_ci(d, key):
    """大小写不敏感地从 payload 里取字段（Worker 写大写键，旧代码读小写键导致字段全丢）。"""
    if not isinstance(d, dict):
        return ""
    for k, v in d.items():
        if str(k).lower() == key.lower() and isinstance(v, str) and v.strip():
            return v.strip()
    return ""

def cmd_sync(a):
    recs = load()
    rows = d1_submissions()
    if rows is None:
        print("D1 查询失败（网络或权限）。账本未改动。")
        return 1
    if not rows:
        print("D1 里 0 条询盘（查询成功）。账本保持不变；北极星为 0 时先看流量与转化。")
    added = 0
    for r in rows:
        sid = (r.get("submission_id") or "").strip()
        if not sid:
            continue
        if sid in recs:
            continue
        payload = r.get("payload") or ""
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}
        recs[sid] = {
            "submission_id": sid,
            "email": r.get("email") or (payload or {}).get("email") or "",
            # 2026-11-10 修：D1 submissions 表只存 payload JSON（没有 country/project_type 列），
            # 旧代码用小写 key 读 → 永远空。首条真实询盘（乌拉圭/商业车队）就是这样丢的字段。
            # Worker 的 normalize 写的是大写键（COUNTRY/PRODUCT/FIRSTNAME/COMPANY/PROJECT）。
            "country": pick_ci(payload, "country") or r.get("country") or "",
            "project_type": pick_ci(payload, "product") or pick_ci(payload, "project_type") or r.get("project_type") or "",
            "name": pick_ci(payload, "firstname") or r.get("firstname") or "",
            "company": pick_ci(payload, "company") or r.get("company") or "",
            "project_note": (pick_ci(payload, "project") or r.get("project") or "")[:400],
            "form_type": r.get("form_type") or "",
            "consent": r.get("consent"),
            "attr_first": r.get("attr_first") or "",
            "content_path": r.get("content_path") or "",
            "created_at": r.get("created_at") or "",
            "status": "new",
            "max_stage": ORDER["new"],
            "qualification": {},
            "pipeline_value": 0,
            "currency": "USD",
            "events": [{"at": now(), "from": None, "to": "new", "by": "sync", "reason": ""}],
        }
        added += 1
    save(recs)
    print(f"sync 完成：D1 询盘 {len(rows)} 条，本次新增 {added} 条（账本共 {len(recs)} 条）")
    if added:
        print("下一步：给每条打 mql / sal / saqo / disqualified —— 例：")
        new_sid = next(k for k, v in recs.items() if v["status"] == "new")
        print(f"  python3 scripts/metrics/lead_lifecycle.py set {new_sid} mql --note \"有明确项目\"")
    return 0


def cmd_list(a):
    recs = load()
    if not recs:
        print("账本为空。先跑 sync。")
        return 0
    rows = list(recs.values())
    if not a.all:
        rows = [r for r in rows if r["status"] not in ("won", "lost", "disqualified")]
    rows.sort(key=lambda r: ORDER.get(r["status"], 9))
    print(f"{'status':<13} {'qual':<6} {'country':<12} {'created':<12} {'value':>9}  submission_id / email")
    for r in rows:
        q = r.get("qualification") or {}
        qn = f"{sum(1 for k in QUAL_KEYS if q.get(k))}/6"
        print(f"{r['status']:<13} {qn:<6} {(r.get('country') or '-')[:11]:<12} "
              f"{(r.get('created_at') or '-')[:10]:<12} {r.get('pipeline_value') or 0:>9}  "
              f"{r['submission_id'][:14]} / {r.get('email', '')[:28]}")
    print(f"\n共 {len(rows)} 条" + ("" if a.all else "（未结案）"))
    return 0


def cmd_set(a):
    recs = load()
    rec = recs.get(a.submission_id)
    if not rec:
        print(f"账本里没有 {a.submission_id}。先 sync 或核对 ID。")
        return 1
    target = a.status
    cur = rec["status"]
    if target not in FORWARD.get(cur, set()):
        print(f"不允许 {cur} → {target}。允许：{sorted(FORWARD.get(cur, [])) or '无（已结案）'}")
        return 1
    if target in ("lost", "disqualified") and not a.reason:
        print(f"{target} 必须写 --reason（丢失原因要能反哺内容与 ICP 判断）。")
        return 1
    if target == "saqo":
        checks = rec.get("qualification") or {}
        missing = [k for k in QUAL_KEYS if not checks.get(k)]
        if missing:
            print(f"SAQO 需要六条件全部为真，缺：{', '.join(missing)}")
            print("  逐项确认：python3 scripts/metrics/lead_lifecycle.py qualify <sid> \\")
            print("            --real-contact --icp --market --need --trigger --accepted")
            print("  未满足就只能是 sal —— 不要为了让 SAQO 有数字而放宽标准。")
            return 1
    ev = {"at": now(), "from": cur, "to": target,
          "by": a.by, "reason": a.reason or "", "note": a.note or ""}
    if target == "saqo":
        ev["qualification"] = dict(rec.get("qualification") or {})
    rec["events"].append(ev)
    rec["status"] = target
    # 只有"前进路径"上的状态推进 max_stage；lost / disqualified 是结局，不是阶段。
    if target in ADVANCE:
        rec["max_stage"] = max(rec.get("max_stage") or 0, ORDER.get(target, 0))
    rec["updated_at"] = now()
    if a.value is not None:
        rec["pipeline_value"] = a.value
    if a.owner:
        rec["owner"] = a.owner
    save(recs)
    print(f"{a.submission_id}: {cur} → {target}"
          + (f"（pipeline {rec['pipeline_value']}）" if a.value is not None else ""))
    return 0



def cmd_revalue(a):
    """只改 pipeline_value（不改状态），用于纠正"未确认金额"——事件里留痕，可审计。

    为什么需要：FORWARD 只允许前进（saqo 之后只能 lost/won），所以发现 pipeline 是估算值时
    无法用 set 修正。硬改文件又不可审计。这里提供受控入口：状态不动，金额可改，
    每次改动写一条 from==to 的事件（by/reason/note 齐全）。
    """
    recs = load()
    rec = recs.get(a.submission_id)
    if not rec:
        print(f"账本里没有 {a.submission_id}。先 sync。")
        return 1
    if rec.get("status") not in ("saqo", "won"):
        print(f"只有 saqo/won 才有 pipeline 金额意义；当前是 {rec.get('status')}。")
        return 1
    old = rec.get("pipeline_value") or 0
    rec["events"].append({
        "at": now(), "from": rec["status"], "to": rec["status"], "by": a.by,
        "reason": "revalue", "note": a.note or "",
        "pipeline_before": old, "pipeline_after": int(a.value),
    })
    rec["pipeline_value"] = int(a.value)
    rec["updated_at"] = now()
    save(recs)
    print(f"{a.submission_id}: pipeline {old} → {int(a.value)}（状态仍为 {rec['status']}）")
    return 0

def cmd_qualify(a):
    """逐项确认 SAQO 六条件。全部为真才能 set saqo。"""
    recs = load()
    rec = recs.get(a.submission_id)
    if not rec:
        print(f"账本里没有 {a.submission_id}。先 sync。")
        return 1
    q = rec.setdefault("qualification", {})
    flags = {"real_contact": a.real_contact, "icp": a.icp, "market": a.market,
             "need": a.need, "trigger": a.trigger, "accepted": a.accepted}
    changed = [k for k, v in flags.items() if v is not None]
    if not changed:
        print("至少给一项：--real-contact / --icp / --market / --need / --trigger / --accepted")
        print("（对应 --no-real-contact 等可显式置假）")
        return 1
    for k in changed:
        q[k] = bool(flags[k])
    rec["updated_at"] = now()
    save(recs)
    missing = [k for k in QUAL_KEYS if not q.get(k)]
    print(f"{a.submission_id} 六条件：通过 {len(QUAL_KEYS) - len(missing)}/6"
          + (f"  缺：{', '.join(missing)}" if missing else "  ✅ 可 set saqo"))
    return 0


def cmd_show(a):
    recs = load()
    rec = recs.get(a.submission_id)
    print(json.dumps(rec, ensure_ascii=False, indent=2) if rec else "没有这条")
    return 0 if rec else 1


def cmd_report(a):
    recs = list(load().values())
    if not recs:
        print("账本为空。先跑 sync。")
        return 0
    cutoff = (dt.datetime.now().astimezone() - dt.timedelta(days=a.days)).isoformat()
    recent = [r for r in recs if (r.get("created_at") or "") >= cutoff]
    scope = recent or recs
    label = f"最近 {a.days} 天" if recent else "全部（窗口内无新询盘）"

    def stage(r):
        # 历史最高阶段；老记录没有 max_stage 时退回当前状态
        return r.get("max_stage") if r.get("max_stage") is not None else ORDER.get(r["status"], 0)

    def cnt(s):
        return sum(1 for r in scope if stage(r) >= ORDER[s])

    valid = len(scope)
    mql = cnt("mql")
    sal = cnt("sal")
    saqo = cnt("saqo")
    won = sum(1 for r in scope if r["status"] == "won")
    lost = [r for r in scope if r["status"] in ("lost", "disqualified")]
    pipeline = sum((r.get("pipeline_value") or 0) for r in scope
                   if r["status"] in ("saqo", "won"))
    print(f"=== 生命周期漏斗（{label}）===")
    print(f"  有效询盘 (D1)      {valid}")
    print(f"  MQL               {mql}" + (f"   {mql / valid * 100:.0f}%" if valid else ""))
    print(f"  SAL（销售接受）    {sal}" + (f"   {sal / valid * 100:.0f}%" if valid else ""))
    print(f"  SAQO（北极星）     {saqo}")
    print(f"  Won               {won}")
    print(f"  Pipeline (USD)    {pipeline:,}")
    if lost:
        print(f"\n  丢失 {len(lost)} 条，原因：")
        for r in lost:
            ev = [e for e in r.get("events", []) if e.get("reason")]
            print(f"    - {r['submission_id'][:14]} {r['status']}: "
                  f"{(ev[-1]['reason'] if ev else '（未填原因）')}")
    if valid == 0:
        print("\n  ⚠ 窗口内 0 条询盘——北极星为 0 时先看流量与转化，而不是继续加页面。")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sync")
    p = sub.add_parser("list")
    p.add_argument("--all", action="store_true")
    p = sub.add_parser("set")
    p.add_argument("submission_id")
    p.add_argument("status", choices=STATES)
    p.add_argument("--value", type=int)
    p.add_argument("--by", default=os.environ.get("USER", "unknown"))
    p.add_argument("--note", default="")
    p.add_argument("--reason", default="")
    p.add_argument("--owner", default="")
    p = sub.add_parser("qualify")
    p.add_argument("submission_id")
    for k in QUAL_KEYS:
        p.add_argument("--" + k.replace("_", "-"), dest=k, action="store_true", default=None)
        p.add_argument("--no-" + k.replace("_", "-"), dest=k, action="store_false", default=None)
    p = sub.add_parser("show")
    p.add_argument("submission_id")
    p = sub.add_parser("report")

    rv = sub.add_parser("revalue", help="只改 pipeline 金额（状态不变，留痕）")
    rv.add_argument("submission_id")
    rv.add_argument("--value", type=int, required=True)
    rv.add_argument("--by", default="kerry")
    rv.add_argument("--note", default="")
    rv.set_defaults(func=cmd_revalue)
    p.add_argument("--days", type=int, default=30)
    a = ap.parse_args()
    return {"sync": cmd_sync, "list": cmd_list, "set": cmd_set, "qualify": cmd_qualify,
            "show": cmd_show, "report": cmd_report, "revalue": cmd_revalue}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
