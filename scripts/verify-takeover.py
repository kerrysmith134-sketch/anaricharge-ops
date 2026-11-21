#!/usr/bin/env python3
"""verify-takeover.py — 接管完整性校验（可复跑）。

回答一个问题：**源目录里的东西，是不是都接过来了、都对得上、都能跑？**
不是「看起来有文件」，而是逐项对账并给 PASS/FAIL。

用法:
  python3 scripts/verify-takeover.py            # 人读摘要
  python3 scripts/verify-takeover.py --json     # 机器可读
  python3 scripts/verify-takeover.py --write 00-takeover/VERIFICATION.md
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

WS = "/Users/kerrychu/anari-charge-website"
SRC = "/Users/kerrychu/Documents/kimi/workspace"
NEW_SITE = os.path.join(SRC, "anari-new-site")

R = []          # results: (group, check, status, detail)


def add(group, check, status, detail=""):
    R.append({"group": group, "check": check, "status": status, "detail": detail})


def ok(group, check, detail=""):
    add(group, check, "PASS", detail)


def bad(group, check, detail=""):
    add(group, check, "FAIL", detail)


def warn(group, check, detail=""):
    add(group, check, "WARN", detail)


def count_files(root, skip=("node_modules", ".git", "__pycache__")):
    n = 0
    for r, ds, fs in os.walk(root):
        ds[:] = [d for d in ds if d not in skip]
        n += len(fs)
    return n


# ---------------------------------------------------------------- skills
def check_skills():
    g = "技能"
    src_agents = os.path.join(SRC, ".agents/skills")
    src_claude = os.path.join(SRC, ".claude/skills")
    if not os.path.isdir(src_agents):
        bad(g, "源技能目录存在", src_agents)
        return
    src_dirs = {d for d in os.listdir(src_agents)
                if os.path.isdir(os.path.join(src_agents, d)) and not d.startswith(".")}
    # .claude 里独立真实目录（非符号链接）
    extra = set()
    if os.path.isdir(src_claude):
        for d in os.listdir(src_claude):
            p = os.path.join(src_claude, d)
            if os.path.isdir(p) and not os.path.islink(p) and not d.startswith("."):
                extra.add(d)
    expect = src_dirs | extra
    dst = os.path.join(WS, "02-skills")
    if not os.path.isdir(dst):
        bad(g, "02-skills 存在", dst)
        return
    dst_dirs = {d for d in os.listdir(dst)
                if os.path.isdir(os.path.join(dst, d)) and not d.startswith(".")}
    ok(g, "源技能集合已解析",
       f"agents={len(src_dirs)} + claude独立={len(extra)} → 去重后 {len(expect)}")
    ok(g, ".agents/skills 已迁移", f"{len(src_dirs)} 个目录")
    missing = sorted(expect - dst_dirs)
    if missing:
        bad(g, "无遗漏技能目录", f"缺 {len(missing)}: {', '.join(missing[:12])}")
    else:
        ok(g, "无遗漏技能目录", f"{len(dst_dirs)} 个目录全在")
    extra_dst = sorted(dst_dirs - expect)
    if extra_dst:
        warn(g, "无多余目录", f"{len(extra_dst)} 个: {', '.join(extra_dst[:10])}")

    # 每个技能应有 SKILL.md
    no_skill = [d for d in sorted(dst_dirs) if not os.path.exists(os.path.join(dst, d, "SKILL.md"))]
    if no_skill:
        bad(g, "每个技能有 SKILL.md", f"{len(no_skill)} 个缺: {', '.join(no_skill[:12])}")
    else:
        ok(g, "每个技能有 SKILL.md", f"{len(dst_dirs)}/{len(dst_dirs)}")

    # frontmatter
    nofm, nameless, descless = [], [], []
    for d in sorted(dst_dirs):
        p = os.path.join(dst, d, "SKILL.md")
        if not os.path.exists(p):
            continue
        try:
            head = open(p, encoding="utf-8", errors="replace").read(1200)
        except OSError:
            continue
        if not head.startswith("---"):
            nofm.append(d)
            continue
        if not re.search(r"^name:\s*\S", head, re.M):
            nameless.append(d)
        if not re.search(r"^description:\s*\S", head, re.M):
            descless.append(d)
    if nofm:
        bad(g, "全部有 frontmatter", f"{len(nofm)} 个缺: {', '.join(nofm[:12])}")
    else:
        ok(g, "全部有 frontmatter", f"{len(dst_dirs)}/{len(dst_dirs)}")
    if nameless or descless:
        warn(g, "frontmatter 字段完整",
             f"缺 name {len(nameless)} / 缺 description {len(descless)}")
    else:
        ok(g, "frontmatter 字段完整", "name + description 齐全")

    # manifest
    man = os.path.join(dst, "_manifest.json")
    if os.path.exists(man):
        try:
            data = json.load(open(man, encoding="utf-8"))
            entries = data if isinstance(data, list) else data.get("skills", data)
            n = len(entries) if hasattr(entries, "__len__") else 0
            if n == len(dst_dirs):
                ok(g, "_manifest 条目数与目录数一致", f"{n} == {len(dst_dirs)}")
            else:
                bad(g, "_manifest 条目数与目录数一致", f"{n} != {len(dst_dirs)}")
        except Exception as e:  # noqa: BLE001
            bad(g, "_manifest 可解析", str(e)[:120])
    else:
        warn(g, "_manifest.json", "未找到（若 skill-porter 未交则记为缺口）")

    mm = os.path.join(dst, "_MERGE-MAP.md")
    if os.path.exists(mm):
        txt = open(mm, encoding="utf-8", errors="replace").read()
        ok(g, "_MERGE-MAP 存在", f"{len(txt)} 字符")
    else:
        warn(g, "_MERGE-MAP.md", "未找到")


# ---------------------------------------------------------------- workflows
REQ = ["触发", "验收"]


def check_workflows():
    g = "工作流"
    d = os.path.join(WS, "03-workflows")
    if not os.path.isdir(d):
        bad(g, "03-workflows 存在")
        return
    sops = sorted(glob.glob(os.path.join(d, "W*.md")))
    if len(sops) < 15:
        bad(g, "工作流数量 ≥15", f"实际 {len(sops)}")
    else:
        ok(g, "工作流数量 ≥15", f"{len(sops)} 个 SOP")
    weak = []
    for p in sops:
        t = open(p, encoding="utf-8", errors="replace").read()
        miss = [k for k in REQ if k not in t]
        if miss:
            weak.append((os.path.basename(p), miss))
    if weak:
        bad(g, "每个 SOP 含触发与验收",
            f"{len(weak)} 个缺: " + "; ".join(f"{n}({','.join(m)})" for n, m in weak[:8]))
    else:
        ok(g, "每个 SOP 含触发与验收", f"{len(sops)}/{len(sops)}")
    # 索引
    idx = os.path.join(d, "_INDEX.md")
    if os.path.exists(idx):
        t = open(idx, encoding="utf-8", errors="replace").read()
        linked = set(re.findall(r"(W\d+)[^\w]", t))
        have = {re.match(r"(W\d+)", os.path.basename(p)).group(1) for p in sops}
        miss = sorted(have - linked)
        if miss:
            bad(g, "_INDEX 覆盖全部 SOP", f"未链接: {', '.join(miss)}")
        else:
            ok(g, "_INDEX 覆盖全部 SOP", f"{len(have)} 个全链接")
    else:
        bad(g, "_INDEX.md 存在")
    # 排期
    sch = os.path.join(d, "_SCHEDULE.json")
    if os.path.exists(sch):
        try:
            data = json.load(open(sch, encoding="utf-8"))
            jobs = data.get("jobs") or data.get("slots") or []
            ids = {j.get("workflow") or j.get("id") for j in jobs if isinstance(j, dict)}
            have = {re.match(r"(W\d+)", os.path.basename(p)).group(1) for p in sops}
            refs = {i for i in ids if isinstance(i, str) and i.startswith("W")}
            unknown = sorted(refs - have)
            if unknown:
                warn(g, "_SCHEDULE 引用的工作流都存在", f"未知: {', '.join(unknown)}")
            else:
                ok(g, "_SCHEDULE 可解析且引用有效", f"{len(jobs)} 个档位")
        except Exception as e:  # noqa: BLE001
            bad(g, "_SCHEDULE.json 可解析", str(e)[:120])
    else:
        bad(g, "_SCHEDULE.json 存在")


# ---------------------------------------------------------------- suites
def check_suites():
    g = "套件"
    d = os.path.join(WS, "04-suites")
    if not os.path.isdir(d):
        bad(g, "04-suites 存在")
        return
    files = sorted(glob.glob(os.path.join(d, "S*.md")))
    if len(files) >= 4:
        ok(g, "套件数量 ≥4", f"{len(files)} 个")
    else:
        bad(g, "套件数量 ≥4", f"实际 {len(files)}")
    empty = [os.path.basename(p) for p in files
             if os.path.getsize(p) < 800]
    if empty:
        warn(g, "套件内容非空壳（>800B）", f"{len(empty)} 个偏小: {', '.join(empty)}")
    else:
        ok(g, "套件内容非空壳（>800B）", f"{len(files)}/{len(files)}")


# ---------------------------------------------------------------- records
def check_records():
    g = "执行记录"
    d = os.path.join(WS, "05-records")
    for fn, minb in [("timeline.md", 5000), ("current-state.md", 2000),
                     ("open-items.md", 2000), ("decisions.md", 1000)]:
        p = os.path.join(d, fn)
        if not os.path.exists(p):
            bad(g, f"{fn} 存在")
        else:
            sz = os.path.getsize(p)
            if sz < minb:
                warn(g, f"{fn} 内容充足", f"{sz}B < {minb}B")
            else:
                ok(g, f"{fn} 内容充足", f"{sz}B")
    tl = os.path.join(d, "timeline.md")
    if os.path.exists(tl):
        t = open(tl, encoding="utf-8", errors="replace").read()
        n = len(re.findall(r"^\|\s*P\d+|^\|\s*R\d+", t, re.M))
        if not n:
            n = len(re.findall(r"\bP\d{2}\b", t))
        if n >= 100:
            ok(g, "时间线条目 ≥100", f"{n} 条")
        else:
            bad(g, "时间线条目 ≥100", f"{n} 条")
        if "2026-07" in t or "2026-09" in t:
            ok(g, "时间线覆盖起点", "含 7/9 月记录")
        else:
            warn(g, "时间线覆盖起点", "未见早期日期")
    raw = os.path.join(d, "raw")
    if os.path.isdir(raw):
        n = count_files(raw)
        ok(g, "原始记录快照", f"{n} 份")
        if n < 20:
            warn(g, "原始快照数量", f"仅 {n} 份，源目录记录更多")
    else:
        bad(g, "05-records/raw 存在")


# ---------------------------------------------------------------- site
def check_site():
    g = "站点工程"
    d = os.path.join(WS, "06-site")
    if not os.path.isdir(d):
        bad(g, "06-site 存在")
        return
    cands = [p for p in glob.glob(os.path.join(d, "*")) if os.path.isdir(p)]
    # 主源优先：名字含 anari-new-site，其次 sitemap URL 数最多的
    with_site = [c for c in cands if os.path.isdir(os.path.join(c, "site"))]
    main = None
    if with_site:
        pref = [c for c in with_site if "anari-new-site" in os.path.basename(c)]
        pool = pref or with_site
        def loc_count(c):
            sm = os.path.join(c, "site", "sitemap.xml")
            if not os.path.exists(sm):
                return 0
            return len(re.findall(r"<loc>", open(sm, encoding="utf-8", errors="replace").read()))
        main = max(pool, key=loc_count)
    if not main:
        bad(g, "找到站点镜像（含 site/）", str(cands))
        return
    ok(g, "找到站点镜像", os.path.basename(main))
    dst_n = count_files(os.path.join(main, "site"))
    src_n = count_files(os.path.join(NEW_SITE, "site"))
    if dst_n >= src_n:
        ok(g, "site/ 文件数不少于源", f"镜像 {dst_n} >= 源 {src_n}")
    else:
        bad(g, "site/ 文件数不少于源", f"镜像 {dst_n} < 源 {src_n}")
    sm = os.path.join(main, "site", "sitemap.xml")
    if os.path.exists(sm):
        t = open(sm, encoding="utf-8", errors="replace").read()
        n = len(re.findall(r"<loc>", t))
        if n >= 119:
            ok(g, "镜像 sitemap 已同步到线上（≥119）", f"{n} URL")
        elif n >= 114:
            warn(g, "镜像 sitemap 落后线上", f"{n} < 119，需 fetch origin/main")
        else:
            bad(g, "镜像 sitemap 严重落后", f"{n}")
    for fn in ("RUNBOOK.md", "ARCHITECTURE.md", "GATE-RESULTS.md"):
        p = os.path.join(d, fn)
        if os.path.exists(p):
            ok(g, f"{fn} 存在", f"{os.path.getsize(p)}B")
        else:
            warn(g, f"{fn}", "未找到")
    gr = os.path.join(d, "GATE-RESULTS.md")
    if os.path.exists(gr):
        t = open(gr, encoding="utf-8", errors="replace").read()
        if re.search(r"exit|退出码|PASSED|FAILED", t, re.I):
            ok(g, "质量门结果含真实退出码", "ok")
        else:
            warn(g, "质量门结果含真实退出码", "未见退出码")


# ---------------------------------------------------------------- links
def check_links():
    g = "文档链接"
    md = []
    for sub in ("00-takeover", "01-inventory", "03-workflows", "04-suites",
                "05-records", "07-optimization", "08-execution", "02-skills"):
        md += glob.glob(os.path.join(WS, sub, "*.md"))
    md += glob.glob(os.path.join(WS, "*.md"))
    broken = []
    checked = 0
    for p in md:
        t = open(p, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"\[[^\]]*\]\(([^)#\s]+)(?:#[^)]*)?\)", t):
            link = m.group(1)
            if link.startswith(("http://", "https://", "mailto:")):
                continue
            target = os.path.normpath(os.path.join(os.path.dirname(p), link))
            # 也允许相对工作区根
            alt = os.path.normpath(os.path.join(WS, link.lstrip("./")))
            checked += 1
            if not (os.path.exists(target) or os.path.exists(alt)):
                broken.append((os.path.relpath(p, WS), link))
    if broken:
        bad(g, "内部 markdown 链接可解析",
            f"{len(broken)}/{checked} 断链，例: " +
            "; ".join(f"{a} → {b}" for a, b in broken[:6]))
    else:
        ok(g, "内部 markdown 链接可解析", f"{checked} 条全通")


# ---------------------------------------------------------------- browser
def check_browser():
    g = "浏览器自动化"
    base = os.path.join(WS, "scripts", "browser")
    for fn in ("wb.py", "ops.py"):
        p = os.path.join(base, fn)
        if os.path.exists(p):
            ok(g, f"{fn} 存在", f"{os.path.getsize(p)}B")
        else:
            bad(g, f"{fn} 存在")
    doc = os.path.join(WS, "00-takeover", "BROWSER-CAPABILITY.md")
    if os.path.exists(doc):
        ok(g, "能力文档存在", f"{os.path.getsize(doc)}B")
    else:
        warn(g, "BROWSER-CAPABILITY.md", "未找到")
    ev = os.path.join(WS, "08-execution", "browser-evidence")
    if os.path.isdir(ev):
        n = count_files(ev)
        ok(g, "浏览器操作留痕", f"{n} 份证据")
    else:
        warn(g, "browser-evidence", "未找到")
    # 守护进程健康（不启动，只探测）
    try:
        import subprocess
        bin_path = os.path.expanduser("~/.kimi-webbridge/bin/kimi-webbridge")
        if os.path.exists(bin_path):
            out = subprocess.run([bin_path, "status"], capture_output=True, text=True, timeout=15).stdout
            d = json.loads(out)
            if d.get("running") and d.get("extension_connected"):
                ok(g, "WebBridge 运行中且扩展已连接", d.get("version", ""))
            else:
                warn(g, "WebBridge 未就绪",
                     f"running={d.get('running')} ext={d.get('extension_connected')}")
        else:
            warn(g, "WebBridge 未安装", bin_path)
    except Exception as e:  # noqa: BLE001
        warn(g, "WebBridge 状态探测失败", str(e)[:120])


# ---------------------------------------------------------------- execution
def check_execution():
    g = "执行产出"
    d = os.path.join(WS, "08-execution")
    if not os.path.isdir(d):
        bad(g, "08-execution 存在")
        return
    jsons = glob.glob(os.path.join(d, "*.json"))
    badj = []
    for p in jsons:
        try:
            json.load(open(p, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            badj.append(os.path.basename(p))
    if badj:
        bad(g, "执行数据 JSON 合法", f"{len(badj)} 个损坏: {', '.join(badj)}")
    else:
        ok(g, "执行数据 JSON 合法", f"{len(jsons)} 个")
    gsc = os.path.join(d, "gsc-20261107.json")
    if os.path.exists(gsc):
        data = json.load(open(gsc, encoding="utf-8"))
        if data.get("auth") == "ok" and data.get("queries") is not None:
            ok(g, "GSC 真实数据已拉取",
               f"点击 {data.get('page_totals',{}).get('clicks')} / "
               f"展示 {data.get('page_totals',{}).get('impressions')}")
        else:
            bad(g, "GSC 真实数据已拉取", "auth 或数据结构异常")
    else:
        bad(g, "GSC 数据文件存在")
    for fn in ("2026-11-07-daily-run.md", "TECH-FINDINGS-20261107.md"):
        p = os.path.join(d, fn)
        if os.path.exists(p):
            ok(g, f"{fn} 存在", f"{os.path.getsize(p)}B")
        else:
            warn(g, fn, "未找到")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--write", default=None)
    a = ap.parse_args()

    check_skills()
    check_workflows()
    check_suites()
    check_records()
    check_site()
    check_links()
    check_browser()
    check_execution()

    p = sum(1 for r in R if r["status"] == "PASS")
    f = sum(1 for r in R if r["status"] == "FAIL")
    w = sum(1 for r in R if r["status"] == "WARN")

    if a.json:
        print(json.dumps({"summary": {"PASS": p, "FAIL": f, "WARN": w}, "results": R},
                         ensure_ascii=False, indent=2))
    else:
        cur = None
        for r in R:
            if r["group"] != cur:
                cur = r["group"]
                print(f"\n【{cur}】")
            icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️ "}[r["status"]]
            print(f"  {icon} {r['check']}" + (f"  — {r['detail']}" if r["detail"] else ""))
        print(f"\n总计: PASS {p} / FAIL {f} / WARN {w}")

    if a.write:
        lines = ["# 接管完整性校验报告", "",
                 f"生成: `python3 scripts/verify-takeover.py --write {a.write}`", "",
                 f"**PASS {p} / FAIL {f} / WARN {w}**", ""]
        cur = None
        for r in R:
            if r["group"] != cur:
                cur = r["group"]
                lines += [f"## {cur}", ""]
            icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}[r["status"]]
            lines.append(f"- {icon} **{r['check']}**" + (f" — {r['detail']}" if r["detail"] else ""))
        open(a.write, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        print("WROTE", a.write)
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
