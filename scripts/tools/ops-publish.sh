#!/usr/bin/env bash
# ops-publish.sh — 工作区仓库（脚本/配置）发布入口
# 与站点仓库 publish.sh 同思路：分支检查 → 敏感文件扫描 → 提交 → 推送
# 用法：bash scripts/tools/ops-publish.sh "commit message" <paths...>
set -euo pipefail
WS="/Users/kerrychu/anari-charge-website"
cd "$WS"
MSG="${1:-chore(ops): update}"; shift || true
[ $# -eq 0 ] && { echo "用法: ops-publish.sh '<msg>' <path...>"; exit 2; }

branch="$(git rev-parse --abbrev-ref HEAD)"
[ "$branch" = "main" ] || { echo "❌ 只能在 main 发布（当前 $branch）"; exit 1; }

git fetch -q origin main 2>/dev/null || true
if [ -n "$(git rev-list --count HEAD..origin/main 2>/dev/null)" ] && [ "$(git rev-list --count HEAD..origin/main)" != "0" ]; then
  echo "❌ 落后 origin/main，先 git pull --rebase"; exit 1
fi

git add -A "$@"
if git diff --cached --quiet; then echo "没有需要提交的改动"; exit 0; fi

# 机密兜底（hook 之外再查一次，防 --no-verify）
if git diff --cached --name-only | grep -qE '(^|/)\.secrets/|\.env$|\.pem$'; then
  echo "❌ 暂存区含机密文件，拒绝提交"; exit 1
fi

git -c user.name="Anari AI Ops" -c user.email="ops@anaricharge.com" commit -q -m "$MSG"
git push origin main
echo "✅ ops 发布完成：$(git log --oneline -1)"
