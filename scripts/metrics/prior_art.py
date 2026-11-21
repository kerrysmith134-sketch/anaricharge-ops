#!/usr/bin/env python3
"""prior_art.py — 做任何渠道工作前的"防重复劳动"检查。

## 为什么有这个东西
2026-11-07 实际教训：我把 UNGM 当成新机会重新盘点，而它在 10-22 就已注册（账号 #1290463）
并已明确决策「只作外链渠道、不做获客」；我又把"自助目录"当新发现，而 10-17 已做过
6 家字段级实测 + 12 家候选 + 4 家排除的完整复核。

**根因**：动手前没有搜 `05-records/`（历史记录）、`01-inventory/`（盘点）、`02-skills/`（技能）。
接管工作区里这些目录就是"记忆"，不查等于失忆。

## 用法
  python3 scripts/metrics/prior_art.py ungm
  python3 scripts/metrics/prior_art.py "directory" "wikidata"
输出：命中的文件 + 命中行摘要，供判断"这件事是否已经做过"。
"""
import os
import re
import sys

WS = "/Users/kerrychu/anari-charge-website"
SEARCH_DIRS = [
    "05-records", "01-inventory", "02-skills", "03-workflows", "04-suites",
    "08-execution",
]
SKIP = {"node_modules", ".git", "__pycache__"}
EXTS = (".md", ".json", ".jsonl", ".csv", ".yml", ".yaml")


def walk():
    for d in SEARCH_DIRS:
        root = os.path.join(WS, d)
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [x for x in dirnames if x not in SKIP]
            for fn in filenames:
                if fn.endswith(EXTS):
                    yield os.path.join(dirpath, fn)


def main():
    if len(sys.argv) < 2:
        print("用法: prior_art.py <关键词> [更多关键词]")
        return 2
    kws = [k.lower() for k in sys.argv[1:]]
    hits = {}
    for path in walk():
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except Exception:  # noqa: BLE001
            continue
        low = text.lower()
        if not all(k in low for k in kws):
            continue
        lines = []
        for i, line in enumerate(text.splitlines(), 1):
            if all(k in line.lower() for k in kws):
                lines.append((i, line.strip()[:180]))
        if lines:
            hits[os.path.relpath(path, WS)] = lines[:4]

    if not hits:
        print(f"未命中『{' + '.join(kws)}』→ 可能是新领域，可以推进（但仍要看同类词）")
        return 0
    print(f"命中 {len(hits)} 个文件 —— **先读这些，再决定是否重复做**：\n")
    for path, lines in sorted(hits.items()):
        print(f"  {path}")
        for i, line in lines:
            print(f"    L{i}: {line}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
