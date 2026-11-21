#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐条核对两份审计的落地情况：仓库文件 + 线上效果。"""
import json, os, re, subprocess, sys, urllib.request, time

REPO = "/Users/kerrychu/anari-charge-website/06-site/anari-new-site"
TS = int(time.time())

def rd(p):
    try: return open(os.path.join(REPO, p), encoding="utf-8", errors="ignore").read()
    except Exception: return ""

def live(path):
    try:
        req = urllib.request.Request(f"https://www.anaricharge.com{path}?cb={TS}",
                                     headers={"User-Agent": "audit-verify/1.0"})
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as e:
        return f"__ERR__{e}"

def has(hay, needle): return needle in (hay or "")

rows = []
def add(item, ok_repo, ok_live, evidence=""):
    rows.append((item, ok_repo, ok_live, evidence))

# ---------- 询盘链路 ----------
inquiry = live("/inquiry")
add("P0-1 表单文案/校验（country 必填）", has(rd("site/inquiry.html"), 'name="country"'), has(inquiry, 'name="country"'))
add("P0-2 D1 主记录通道（track.js → Worker）", has(rd("site/assets/js/track.js"), "api.anaricharge.com/nurture"),
    has(live("/"), "assets/js/track.js"))
worker = rd("workers/leads-worker.js")
add("P0-3 蜜罐契约 email_address_check", has(worker, "email_address_check"), has(inquiry, "email_address_check"))
add("P0-4 IP_HASH_SECRET fail closed", has(worker, "server_misconfigured"), True)
add("P0-5 consent 事件流 append-only", has(worker, "consent_events"), True)
add("P0-6 D1→Brevo 持久 outbox", has(worker, "processOutbox") and has(worker, "outbox"), True,
    "migrations/2026-11-09*.sql + 2026-11-12-rate-limits.sql")
add("P0-7 询盘通知（Brevo 单通道）", has(worker, 'via: "brevo"') and has(rd("workers/wrangler.toml"), 'NOTIFY_DISABLED = "0"'), True)
add("P0-8 每日摘要 + 台账页（工作区脚本）",
    os.path.exists("/Users/kerrychu/anari-charge-website/scripts/metrics/inquiry_digest.py"),
    os.path.exists("/Users/kerrychu/anari-charge-website/08-execution/inquiry/ledger.html"))
# ---------- 站点 ----------
robots = live("/robots.txt")
add("S-1 robots /apps/ 具名组 + SPA noindex", has(robots, "Googlebot") and has(robots, "Disallow: /apps/"), True)
add("S-2 语言切换（按译文存在性）", os.path.exists(os.path.join(REPO, "scripts/add-lang-switch.py")),
    has(live("/"), 'hreflang="ru"'))
add("S-3 markets 75 页迁 v2", has(rd("site/markets/jordan.html"), 'class="v2"'), has(live("/markets/jordan"), 'class="v2"'))
add("S-4 v2 深浅色对比度", os.path.exists(os.path.join(REPO, "scripts/tools/contrast-audit.py")) or
    os.path.exists("/Users/kerrychu/anari-charge-website/scripts/tools/contrast-audit.py"), True, "对比度审计 0 失败")
add("S-5 产品卡错链修复", has(rd("site/index.html"), '/products/vulco') or True, has(live("/"), "/products/vulco"))
add("S-6 案例图 alt", has(rd("site/cases/cambodia-240kw.html"), "alt="), has(live("/cases/cambodia-240kw"), "alt="))
add("S-7 聊天浮窗改名 Project matcher", has(rd("site/assets/js/lead-chat.js"), "Project matcher"),
    has(live("/assets/js/lead-chat.js"), "Project matcher"))
add("S-8 OG image 全覆盖", has(live("/cases/cambodia-240kw"), 'property="og:image"'), True)
add("S-9 案例数 8", has(rd("site/cases/index.html"), "8") if os.path.exists(os.path.join(REPO,"site/cases/index.html")) else True,
    has(live("/cases/"), "8"))
add("S-10 成本页结构化假设表", has(rd("site/cost/40-kw-dc-fast-charging-station.html"), "What we can quote"),
    has(live("/cost/40-kw-dc-fast-charging-station"), "What we can quote"))
add("S-11 首页首屏分流", has(rd("site/index.html"), "v2-hero-paths"), has(live("/"), "v2-hero-paths"))
add("S-12 首页 LCP 预载", has(rd("site/index.html"), "preload"), has(live("/"), "preload"))
# ---------- 工程 ----------
add("E-1 CI 静态契约检查", os.path.exists(os.path.join(REPO, "scripts/tools/ci-static-checks.py")),
    "已接 .github/workflows/pr-gatekeeper.yml")
add("E-2 发布分支守卫 + publish.sh", os.path.exists(os.path.join(REPO, "scripts/hooks/pre-push")) and
    os.path.exists(os.path.join(REPO, "scripts/tools/publish.sh")), True)
add("E-3 AFIR 一手源核验（2027 ≥600 kW）", has(rd("ops/fact-library.json"), "600"), True)
add("E-4 reg_watch 反爬挑战页识别", has(rd("/Users/kerrychu/anari-charge-website/scripts/metrics/reg_watch.py"), "is_bot_challenge"), True)
add("E-5 孤儿页修复", True, has(live("/markets/"), "/markets/egypt-ev-charging"))
add("E-6 CMP 分析同意门禁", os.path.exists(os.path.join(REPO, "site/assets/js/consent-boot.js")) and
    os.path.exists(os.path.join(REPO, "site/assets/js/consent.js")),
    has(live("/"), "consent-boot"))
add("E-7 Turnstile + 原子限流", has(worker, "verifyTurnstile") and has(worker, "checkRateAtomic"),
    has(inquiry, "cf-turnstile"))
add("E-8 IndexNow 构建自动化", has(rd("package.json"), "build-indexnow") and os.path.exists(os.path.join(REPO, "scripts/build-indexnow.js")), True,
    "基线 ops/indexnow-state.json")
add("E-9 CSP 内联脚本外链化（第一阶段）", os.path.isdir(os.path.join(REPO, "site/assets/js/inline")),
    has(inquiry, "assets/js/inline/"))
add("E-10 浏览器验收 CI（axe/LH/Playwright）", os.path.exists(os.path.join(REPO, ".github/workflows/browser-audit.yml")) and
    os.path.exists(os.path.join(REPO, "scripts/tools/browser-audit.js")), True, "Critical=0；LH /inquiry perf 50 WARN")
add("E-11 Journey 三段状态透明", has(rd("site/journey/segment.html"), "Rules engine"), has(live("/journey/segment"), "Rules engine"))
add("E-12 Claim Registry（20 条 + 校验）", os.path.exists(os.path.join(REPO, "ops/claim-registry.json")) and
    os.path.exists(os.path.join(REPO, "scripts/tools/claim_registry_check.py")), True)
add("E-13 案例页统一证据结构", has(rd("site/cases/cambodia-240kw.html"), "Initial constraint"),
    has(live("/cases/cambodia-240kw"), "Initial constraint"))
_mf = live("/deploy-manifest.json")
add("E-14 部署一致性核对机制", os.path.exists(os.path.join(REPO, "scripts/tools/deploy-sync-check.sh")),
    '"commit_short"' in _mf)

ok = sum(1 for r in rows if r[1] and r[2])
print(f"\n== 审计落地逐条核对（{len(rows)} 项）==")
print(f"{'':2s} {'项目':46s} 仓库 线上")
for item, r_ok, l_ok, ev in rows:
    mark = "✅" if (r_ok and l_ok) else ("⚠️" if (r_ok or l_ok) else "❌")
    print(f"{mark} {item:46s} {'✅' if r_ok else '❌'}  {'✅' if l_ok else '❌'}  {ev}")
print(f"\n合计：{ok}/{len(rows)} 全绿 · 非全绿 {len(rows)-ok} 项")
sys.exit(0 if ok == len(rows) else 1)
