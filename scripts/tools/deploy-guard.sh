#!/usr/bin/env bash
# deploy-guard.sh — 部署守卫（2026-11-21 加）
#
# 为什么需要：GitHub push **不会**自动触发 Cloudflare 上线。
# 上线靠 publish.sh 第 5 步调 wrangler deploy。若有人直接 git push，
# 代码在 GitHub、线上却是旧的，而且没人会发现。
#
# 本脚本：比对「本地已提交的 site/sitemap.xml」与「线上 sitemap」的 sha256
#   - 一致 → 静默退出（exit 0，不输出，避免刷屏）
#   - 不一致 → 自动 deploy-site.sh → 复核 → 写台账 → 输出 3 行报告
#
# 用法：
#   bash scripts/tools/deploy-guard.sh          # 检查并在需要时部署
#   bash scripts/tools/deploy-guard.sh --check   # 只检查不部署
# 退出码：0 已同步或已成功补齐 / 1 部署后仍不一致（需人看）
set -uo pipefail
WS="/Users/kerrychu/anari-charge-website"
SITE="$WS/06-site/anari-new-site"
LOG="$WS/08-execution/tech/deploy-guard.jsonl"
MODE="${1:-}"

mkdir -p "$(dirname "$LOG")"
# 0) 远端是否领先本地（有人 push 但本地没拉 → 比对本地 sitemap 会误判"已同步"）
BEHIND="$({ cd "$SITE" && git fetch -q origin main 2>/dev/null; git rev-list --count HEAD..origin/main 2>/dev/null; } || echo 0)"
export BEHIND

before="$(cd "$SITE" && bash scripts/tools/deploy-sync-check.sh 2>&1)"
if echo "$before" | grep -q "线上已同步"; then
  # 一致：静默（L1 档位不该刷屏），只在台账留痕
  python3 - "$before" <<'PY' >/dev/null 2>&1
import json,sys,datetime as dt
rec={"ts":dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
     "action":"noop","detail":sys.argv[1].strip()[:200]}
open("/Users/kerrychu/anari-charge-website/08-execution/tech/deploy-guard.jsonl","a",encoding="utf-8").write(json.dumps(rec,ensure_ascii=False)+"\n")
PY
  if [ "${BEHIND:-0}" -gt 0 ] 2>/dev/null; then
    echo "⚠️ 线上与本地已同步，但远端领先本地 ${BEHIND} 个提交（有人 push 未拉取）"
    echo "   处理：cd 06-site/anari-new-site && git pull --ff-only origin main && bash scripts/tools/deploy-site.sh"
  fi
  exit 0
fi

if [ "$MODE" = "--check" ]; then
  echo "⚠️ 线上与仓库不一致（--check 模式不部署）"
  echo "$before" | tail -3
  exit 1
fi

echo "⚠️ 检测到线上落后，开始部署…"
cd "$SITE"
deploy_out="$(bash scripts/tools/deploy-site.sh 2>&1 | tail -4)"
after="$(bash scripts/tools/deploy-sync-check.sh 2>&1)"
ok="no"; echo "$after" | grep -q "线上已同步" && ok="yes"

python3 - "$ok" "$before" "$after" "$deploy_out" <<'PY'
import json,sys,datetime as dt
ok,before,after,deploy=sys.argv[1:5]
rec={"ts":dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
     "action":"deploy" if ok=="yes" else "deploy_failed",
     "before":before.strip()[:200],"after":after.strip()[:200],"deploy_tail":deploy.strip()[:300]}
open("/Users/kerrychu/anari-charge-website/08-execution/tech/deploy-guard.jsonl","a",encoding="utf-8").write(json.dumps(rec,ensure_ascii=False)+"\n")
PY

if [ "$ok" = "yes" ]; then
  echo "✅ 部署守卫：线上已补齐（原落后 → 现已同步）"
  echo "$after" | tail -1
  exit 0
else
  echo "❌ 部署守卫：部署后仍不一致，需要人看"
  echo "$after" | tail -3
  exit 1
fi
