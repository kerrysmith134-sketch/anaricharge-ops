#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""parallel_handover.py — 每天给并行团队（外部工作流）生成一份交接说明

## 为什么有这个
并行团队（kerrysmith134-sketch / AI Studio）已 5 次把 scripts/ 执行位剥成 100644，
两次带着红门禁推上 main（9a7a9c9 带 1 个失败测试、7e57db4 带 validate 断链）。
口头提醒没用，所以：**每天自动出一份带着当天事实的交接单**，写清
① 他们昨天推了什么 ② 我们替他们修了什么 ③ 他们今天必须做的一件事。

产物：08-execution/tech/handover/<日期>.md（同时追加一行到 handover.jsonl）

用法：python3 scripts/tools/parallel_handover.py [--date YYYY-MM-DD]
"""
import argparse, datetime as dt, json, os, subprocess, sys

WS = "/Users/kerrychu/anari-charge-website"
SITE = os.path.join(WS, "06-site/anari-new-site")
OUT_DIR = os.path.join(WS, "08-execution/tech/handover")


def run(args, cwd=SITE):
    try:
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=120)
        return p.stdout.strip()
    except Exception as e:
        return f"<failed: {e}>"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    a = ap.parse_args()
    day = a.date or dt.date.today().isoformat()

    # 1) 我们替他们做过的修复（提交信息里带 fix(...) 且提到 7e57/9a7a/执行位）
    # 用作者邮箱区分「我们」与「并行方」，不能靠提交信息猜
    OUR_EMAILS = {"ops@anaricharge.com"}
    log = run(["git", "log", "--since", f"{day} 00:00", "--until", f"{day} 23:59",
               "--format=%h|%ae|%s"])
    ours, theirs = [], []
    for line in log.splitlines():
        parts = line.split("|", 2)
        if len(parts) < 3:
            continue
        h, ae, s = parts
        if ae.strip().lower() in OUR_EMAILS:
            ours.append((h, s))
        else:
            theirs.append((h, s))

    # 2) 执行位现状
    perms = run(["git", "ls-files", "-s", "scripts/hooks/pre-push", "scripts/tools/publish.sh"])
    bad = [l for l in perms.splitlines() if l.startswith("100644")]
    perm_state = "100755 ✅" if not bad else "100644 ❌（pre-push 防线失效）"

    # 3) 部署同步
    sync = run(["bash", "scripts/tools/deploy-sync-check.sh"])
    synced = "✅ 已同步" if "已同步" in sync else "❌ 落后"

    # 4) 门禁快照（只跑最便宜的两条）
    tests = run(["node", "--test", "tests/site.test.js"])
    import re
    m_pass = re.search(r"^# pass (\d+)", tests, re.M)
    m_fail = re.search(r"^# fail (\d+)", tests, re.M)
    gate = f"{m_pass.group(1) if m_pass else '?'} pass / {m_fail.group(1) if m_fail else '?'} fail"

    head = run(["git", "rev-parse", "--short", "HEAD"])

    os.makedirs(OUT_DIR, exist_ok=True)
    md = [f"# 并行团队交接单 · {day}", "",
          f"- 我们的 HEAD：`{head}`", f"- 部署：{synced}",
          f"- 执行位：{perm_state}", f"- 门禁：{gate}", ""]

    md += ["## 一、你们今天推上来的", ""]
    md += [f"- `{h}` {s}" for h, s in theirs] or ["- （今天没有你们的提交）"]
    fixes = [(h, s) for h, s in ours if s.startswith("fix(") or "执行位" in s or "修 " in s]
    rest = [(h, s) for h, s in ours if (h, s) not in fixes]
    md += ["", "## 二、我们替你们修的", ""]
    md += [f"- `{h}` {s}" for h, s in fixes] or ["- （今天无需代修）"]
    if rest:
        md += ["", "我们自己的其它提交（无需你们处理）：", ""]
        md += [f"- `{h}` {s}" for h, s in rest]
    md += ["", "## 三、你们今天必须做的一件事", ""]
    if bad:
        md += ["> **执行位又掉了。**", "",
               "```bash",
               "cd 06-site/anari-new-site",
               "git config core.fileMode true",
               "chmod +x scripts/hooks/*.sh scripts/hooks/pre-push scripts/hooks/pre-commit \\",
               "         scripts/tools/*.sh scripts/tools/*.py scripts/site/*.py",
               "bash scripts/install-hooks.sh",
               "git add -A scripts/ && git commit -m 'chore: 恢复 scripts 执行位 100755'",
               "```"]
    else:
        md += ["> 执行位正常。推之前仍要跑：",
               "```bash",
               "cd 06-site/anari-new-site",
               "node --test tests/site.test.js && node validate.js && node scripts/check-facts.js",
               "```",
               "改了前端 css/js 的话，记得同步 `404.html` 与 `apps/*/index.html` 里的 hashed 引用（它们不由生成器覆盖）。"]

    md += ["", "## 四、常用判据", "",
           "| 判据 | 命令 | 期望 |", "|---|---|---|",
           "| 执行位 | `git ls-files -s scripts/hooks/pre-push` | `100755` |",
           "| 测试 | `node --test tests/site.test.js` | `fail 0` |",
           "| 页面契约 | `node validate.js` | `0 error(s)` |",
           "| 事实库 | `node scripts/check-facts.js` | `PASS` |",
           "| 线上是否同步 | `bash scripts/tools/deploy-sync-check.sh` | `已同步` |",
           "", "细则见仓内 `docs/PARALLEL-TEAM-HANDOVER.md`。"]

    out = os.path.join(OUT_DIR, f"{day}.md")
    open(out, "w", encoding="utf-8").write("\n".join(md) + "\n")
    with open(os.path.join(WS, "08-execution/tech/handover.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"date": day, "head": head, "synced": "已同步" in sync,
                            "perms_ok": not bad, "gate": gate,
                            "their_commits": len(theirs), "our_fixes": len([1 for _h, _s in ours if _s.startswith("fix(") or "执行位" in _s])},
                           ensure_ascii=False) + "\n")
    print(f"✅ 交接单已生成：{out}")
    print(f"   你们提交 {len(theirs)} 个 · 我们代修 {len(ours)} 个 · 执行位 {'正常' if not bad else '异常'} · {gate}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
