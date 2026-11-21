#!/bin/bash
# sync-back.sh — 把接管成果回写到原 Kimi 工作区（只读沙箱外的唯一出口）
#
# 默认 dry-run；要真写必须显式 --apply。
# 原因：本会话写沙箱只允许写 /Users/kerrychu/anari-charge-website，
#      且原工作区是运行中业务的一部分，回写必须有意识、可回滚。
#
# 用法:
#   bash scripts/sync-back.sh                # 预览会写什么
#   bash scripts/sync-back.sh --apply        # 真正复制（先打 tar 备份）
#   bash scripts/sync-back.sh --apply --skills-only
#
set -euo pipefail

SRC="/Users/kerrychu/anari-charge-website"
DST="/Users/kerrychu/Documents/kimi/workspace"
APPLY=0
SKILLS_ONLY=0
for a in "$@"; do
  case "$a" in
    --apply) APPLY=1 ;;
    --skills-only) SKILLS_ONLY=1 ;;
    *) echo "unknown arg: $a" >&2; exit 2 ;;
  esac
done

say() { printf '%s\n' "$*"; }

say "src : $SRC"
say "dst : $DST"
say "mode: $([ $APPLY -eq 1 ] && echo APPLY || echo DRY-RUN)"
say ""

# 1) 可写性探测（不真写）
if ! touch "$DST/.sync-write-test" 2>/dev/null; then
  say "!! 目标工作区不可写（沙箱限制）。"
  say "!! 请在系统终端（Terminal.app）里执行本脚本，或临时放开写权限。"
  [ $APPLY -eq 1 ] && exit 3
  say "!! 继续仅预览。"
else
  rm -f "$DST/.sync-write-test"
  say "可写性: OK"
fi
say ""

# 2) 待回写清单
TARGETS=(
  "AGENTS.md:AGENTS-takeover.md"
  "00-takeover:takeover-00"
  "01-inventory:takeover-01-inventory"
  "03-workflows:takeover-03-workflows"
  "04-suites:takeover-04-suites"
  "05-records:takeover-05-records"
  "07-optimization:takeover-07-optimization"
  "08-execution:takeover-08-execution"
)
if [ $SKILLS_ONLY -eq 0 ]; then
  TARGETS+=("02-skills:.agents/skills-takeover")
fi

for t in "${TARGETS[@]}"; do
  s="${t%%:*}"; d="${t##*:}"
  if [ -e "$SRC/$s" ]; then
    n=$(find "$SRC/$s" -type f 2>/dev/null | wc -l | tr -d ' ')
    say "  $s  ->  $DST/$d   ($n files)"
  fi
done
say ""

# 3) 备份 + 复制
if [ $APPLY -eq 1 ]; then
  STAMP=$(date +%Y%m%d-%H%M%S)
  mkdir -p "$DST/.takeover-inbox"
  tar -czf "$DST/.takeover-inbox/backup-before-takeover-$STAMP.tar.gz" \
      -C "$DST" .agents .claude 2>/dev/null || true
  say "备份: $DST/.takeover-inbox/backup-before-takeover-$STAMP.tar.gz"
  for t in "${TARGETS[@]}"; do
    s="${t%%:*}"; d="${t##*:}"
    [ -e "$SRC/$s" ] || continue
    mkdir -p "$(dirname "$DST/$d")"
    cp -R "$SRC/$s" "$DST/$d"
    say "copied $s -> $d"
  done
  say ""
  say "完成。注意：02-skills 落到 .agents/skills-takeover，"
  say "要真正生效需要用户在 Kimi 侧把 skills 合并进 .agents/skills 或加软链。"
else
  say "（dry-run，未写入。加 --apply 执行。）"
fi
