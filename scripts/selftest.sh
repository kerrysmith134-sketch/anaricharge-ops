#!/usr/bin/env bash
# selftest.sh — 全链路冒烟测试：任何"改了 A 却弄崩 B"的回归，跑它一遍就能发现。
#
# 由来：2026-11-07 geo-citations.json 从裸数组改成 {"rows":[]}，
# geo_check.py 兼容了，但 north_star.py 没兼容 → 每日看板直接崩。
# 这类问题不该靠人记得检查。
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
FAIL=0
run() {
  local name="$1"; shift
  if "$@" >/tmp/selftest.out 2>&1; then
    printf "  ✅ %-40s\n" "$name"
  else
    printf "  ❌ %-40s\n" "$name"
    sed 's/^/       /' /tmp/selftest.out | tail -6
    FAIL=1
  fi
}

echo "=== 度量链路 ==="
run "north_star.py（每日看板）"      python3 scripts/metrics/north_star.py
run "flywheel.py status（KPI）"      python3 scripts/metrics/flywheel.py status
run "flywheel.py propose（下一步）"  python3 scripts/metrics/flywheel.py propose
run "opportunity_rank.py（机会）"    python3 scripts/metrics/opportunity_rank.py
run "geo_check.py（GEO 基线）"       python3 scripts/metrics/geo_check.py summary
run "lead_lifecycle.py（SAQO 账本）"  python3 scripts/metrics/lead_lifecycle.py report
run "evidence-report.py（证据台账）"  python3 scripts/tools/evidence-report.py   
run "brevo_crm.py（Brevo 对账）"   python3 scripts/metrics/brevo_crm.py verify
run "ga4_events.py（GA4 队列）"  python3 scripts/metrics/ga4_events.py status
run "ga4_query.py（GA4 实时）"  python3 scripts/metrics/ga4_query.py realtime
run "run_log_autolog（run 记录）"  python3 scripts/metrics/run_log_autolog.py --dry
run "team 覆盖率与权限"  python3 scripts/team/coverage.py
run "send_health（外联体检）"  python3 scripts/outbound/send_health.py 2>&1 | tail -2
run "policy_check（动作策略）"  python3 scripts/team/policy_check.py check --action instantly.lead.import --actor-type agent --actor-id selftest --capability connector.instantly.write --consent --not-suppressed
run "suppression（抑制台账）"  python3 scripts/metrics/suppression.py list
run "prospect_discovery.py（目标池）" python3 scripts/outbound/prospect_discovery.py report
run "marketing_outbound.py（外联）"   python3 scripts/outbound/marketing_outbound.py status

echo
echo "=== 全渠道覆盖审计（技能/任务/KPI）==="
if python3 scripts/metrics/coverage_audit.py >/dev/null 2>&1; then
  printf "  ✅ %-40s\n" "coverage_audit.py（11 渠道）"
else
  printf "  ❌ %-40s\n" "coverage_audit.py 失败"
fi

echo
echo "=== 浏览器卫生（R10）==="
TABS=$(python3 scripts/browser/wb.py tabs-all 2>/dev/null | python3 -c "
import sys,json
raw=sys.stdin.read(); i=raw.find('[')
try: d=json.loads(raw[i:]); print(sum(s['count'] for s in d))
except Exception: print(0)")
if [ "${TABS:-0}" -le 3 ]; then
  printf "  ✅ %-40s\n" "浏览器标签 ${TABS} 个（≤3）"
else
  printf "  ⚠️  %-40s\n" "浏览器标签 ${TABS} 个（>3，需 hygiene）"
fi

echo
echo "=== 每日询盘摘要（可发信，仅 dry）==="
if python3 scripts/metrics/inquiry_digest.py --dry >/dev/null 2>&1; then
  OK "inquiry_digest.py（dry）"
else
  BAD "inquiry_digest.py"
fi

echo "=== 外联频道互斥锁 ==="
if python3 scripts/outbound/channel_lock.py status outbound >/dev/null 2>&1; then
  OK "channel_lock（并行会话互斥）"
else
  BAD "channel_lock"
fi

echo "=== 工作区对账 ==="
run "verify-inquiry-chain.py --dry"   python3 scripts/verify-inquiry-chain.py --dry
run "verify-takeover.py"             python3 scripts/verify-takeover.py

echo
echo "=== 发布纪律（分支守卫）==="
if [ -x 06-site/anari-new-site/scripts/hooks/pre-push ] && [ -x 06-site/anari-new-site/scripts/tools/publish.sh ]; then
  OK "pre-push 分支守卫 + publish.sh（唯一发布入口）"
else
  BAD "发布纪律脚本缺失或不可执行"
fi

echo "=== 站点质量门 ==="
cd 06-site/anari-new-site || { echo "  ❌ 站点目录不存在"; exit 1; }
run "validate.js"                    node validate.js
run "check-facts.js"                 node scripts/check-facts.js
run "audit-inbound-links.js"         node scripts/audit-inbound-links.js --min 3

echo
if [ "$FAIL" = "0" ]; then
  echo "全链路冒烟测试通过。"
else
  echo "有环节失败（见上）。"
fi
exit "$FAIL"
