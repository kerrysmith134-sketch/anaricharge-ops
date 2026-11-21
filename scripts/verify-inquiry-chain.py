#!/usr/bin/env python3
"""verify-inquiry-chain.py — 询盘链路端到端验证（可复跑，自动清理）。

## 为什么需要
2026-11-07 的教训：这条链路"看起来有"（表单、Worker、D1、Brevo 都在），
实际上 16 天零记录，而**没有任何报警**。原因不是链路坏，是前端一行 return。
靠人肉排查花了 6 轮。所以把验证做成一条命令。

## 验什么（四条）
1. Worker 可达 + Origin 白名单通过（POST /nurture）
2. D1 落库（consent=0 → status='stored'）
3. consent=1 → status='sent'（Brevo 同步成功）
4. audit_log 有对应留痕

## 用法
  python3 scripts/verify-inquiry-chain.py            # 全量验证（会写 2 条测试数据，结束自动删）
  python3 scripts/verify-inquiry-chain.py --dry      # 只看当前 D1 状态，不写入
"""
import argparse
import datetime as dt
import json
import os
import sys
import urllib.request

WS = "/Users/kerrychu/anari-charge-website"
sys.path.insert(0, os.path.join(WS, "scripts", "metrics"))
ENDPOINT = "https://api.anaricharge.com/nurture"
ORIGIN = "https://www.anaricharge.com"


def post(payload):
    req = urllib.request.Request(
        ENDPOINT, data=json.dumps(payload).encode(),
        headers={"Origin": ORIGIN, "Content-Type": "application/json",
                 "User-Agent": "Mozilla/5.0 (Macintosh) chain-verify"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except Exception as e:  # noqa: BLE001
        return 0, {"error": str(e)[:200]}


def q(sql):
    import d1_query
    return d1_query.query(sql)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--with-brevo", action="store_true",
                    help="同时验证 consent=1→Brevo（会在 Brevo 留下测试联系人，需人工删）")
    a = ap.parse_args()

    ts = int(dt.datetime.now().timestamp())
    e0 = "verify-consent0-%d@example.com" % ts
    e1 = "verify-consent1-%d@example.com" % ts
    fails = []

    total = (q("SELECT COUNT(*) AS n FROM submissions") or [{}])[0].get("n")
    print("当前 D1 submissions 行数: %s" % total)
    if a.dry:
        print("dry 模式：只读，不写入")
        return 0

    print("\n[1] consent=0 → 应落库且 status='stored'")
    st, body = post({"email": e0, "form_type": "inquiry", "consent": 0, "name": "verify"})
    print("   HTTP %s %s" % (st, json.dumps(body, ensure_ascii=False)[:100]))
    if st != 200:
        fails.append("Worker 不可达或 Origin 被拒")

    if a.with_brevo:
        print("[2] consent=1 → 应同步 Brevo 且 status='sent'")
        st2, body2 = post({"email": e1, "form_type": "inquiry", "consent": 1, "name": "verify"})
        print("   HTTP %s %s" % (st2, json.dumps(body2, ensure_ascii=False)[:100]))
    else:
        # 默认跳过：每跑一次就在 Brevo 留一个假联系人，会污染营销列表
        print("[2] consent=1→Brevo 测试已跳过（加 --with-brevo 才跑）")
        e1 = None

    print("\n[3] D1 校验")
    rows = q("SELECT email, consent, status, retry_count, "
             "substr(coalesce(last_error,''),1,80) AS err FROM submissions "
             "WHERE email IN ('%s','%s')" % (e0, e1))
    got = {r["email"]: r for r in rows}
    checks = [(e0, "stored")] + ([(e1, "sent")] if e1 else [])
    for em, want in checks:
        r = got.get(em)
        if not r:
            print("   ❌ %s 未落库" % em)
            fails.append("%s 未落库" % em)
        elif r["status"] != want:
            print("   ❌ %s status=%s（期望 %s）err=%s" % (em, r["status"], want, r["err"]))
            fails.append("%s status=%s 期望 %s" % (em, r["status"], want))
        else:
            print("   ✅ %s status=%s" % (em, r["status"]))

    print("\n[4] audit_log 留痕")
    logs = q("SELECT action FROM audit_log WHERE detail LIKE '%%verify-consent%%' ORDER BY ts DESC LIMIT 4")
    acts = [r["action"] for r in logs]
    print("   最近: %s" % acts)
    if "submission_stored" not in acts:
        fails.append("audit_log 缺 submission_stored")
    if a.with_brevo and "brevo_sent" not in acts:
        fails.append("audit_log 缺 brevo_sent")

    print("\n[5] 清理测试数据")
    q("DELETE FROM submissions WHERE email LIKE 'verify-consent%'")
    left = (q("SELECT COUNT(*) AS n FROM submissions") or [{}])[0].get("n")
    print("   清理后 submissions: %s" % left)
    if a.with_brevo:
        print("   ⚠️ Brevo 侧留 1 个测试联系人（verify-consent1-…），需人工删除")

    print("\n" + ("❌ 链路验证失败：" + "; ".join(fails) if fails else "✅ 询盘链路端到端验证通过"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
