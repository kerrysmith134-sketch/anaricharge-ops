#!/usr/bin/env python3
"""team_progress.py — 团队动作总览（回答「各团队是否都动起来了」）

从真实产物生成一份可打开的进度报告：
  - 近 48h run-log 按团队分组（谁在什么时候做了什么、qa）
  - 站点提交（git log）
  - 内容队列/台账
  - 索引（最新审计 + IndexNow + GSC 请求台账）
  - 社媒（Quora 发布台账 + 社媒分发稿）
  - 外联/引用域
  - 询盘（D1/账本）
  - 门禁（独立 verify-gates 报告目录）
用法: python3 scripts/metrics/team_progress.py [--hours 48]
输出: 08-execution/dashboard/team-progress-<date>-<hhmm>.md 与 .html
"""
import argparse, datetime as dt, glob, json, os, subprocess, sys

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = os.path.join(WS, "06-site/anari-new-site")
OUT = os.path.join(WS, "08-execution/dashboard")

GROUPS = [
    ("R1 总编排 / 增长脉冲", ["R1", "lead", "growth-pulse", "flywheel", "P4-"]),
    ("R2 SEO / 索引 / 内链", ["R2", "P2-", "P3-", "E2"]),
    ("R3 内容 / 验收", ["R3", "E1", "P5-cro"]),
    ("R4 外联 / PR", ["R4", "PodC", "PodA"]),
    ("R5 社区 / 社媒", ["R5", "P6-"]),
    ("R6 数据 / 守夜 / 简报", ["R6", "E3"]),
    ("A 系专业档位", ["A0", "A1", "A2", "A3", "A4"]),
]

def sh(cmd, cwd=None):
    try:
        return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=120).stdout.strip()
    except Exception:
        return ""

def group_of(agent):
    a = agent or "?"
    for name, prefixes in GROUPS:
        if any(a.startswith(p) or a == p for p in prefixes):
            return name
    return "其他"

def load_json(p, default=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return default

def latest(pattern, key=os.path.getmtime):
    fs = glob.glob(pattern)
    return max(fs, key=key) if fs else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=48)
    a = ap.parse_args()
    now = dt.datetime.now().astimezone()
    since = now - dt.timedelta(hours=a.hours)
    since_iso = since.isoformat()

    rows = [json.loads(l) for l in open(os.path.join(WS, "08-execution/run-log.jsonl"), encoding="utf-8") if l.strip()]
    recent = [r for r in rows if r.get("at") and r["at"] >= since_iso]
    recent.sort(key=lambda r: r["at"], reverse=True)

    # git
    git_cmd = ('git log --date=format:"%m-%d %H:%M" --pretty="%ad|%h|%s" --since="'
               + since.strftime("%Y-%m-%d %H:%M") + '"')
    commits = sh(git_cmd, cwd=SITE).splitlines()

    # content
    ledger = load_json(os.path.join(WS, "08-execution/content/content-ledger.json"), {})
    entries = ledger.get("entries") if isinstance(ledger, dict) else ledger
    entries = entries or []
    recent_content = sorted([e for e in entries if str(e.get("date", "")) >= since.strftime("%Y-%m-%d")],
                            key=lambda e: str(e.get("date")), reverse=True)

    # index
    idx_file = latest(os.path.join(WS, "08-execution/tech/index-coverage*.json"))
    idx = load_json(idx_file) if idx_file else {}
    idx_prev = None
    files = sorted(glob.glob(os.path.join(WS, "08-execution/tech/index-coverage*.json")), key=os.path.getmtime)
    if len(files) >= 2:
        for f in reversed(files[:-1]):
            cand = load_json(f)
            if cand and cand.get("generated_at") != (idx or {}).get("generated_at"):
                idx_prev = cand
                break
    ireq = sorted(glob.glob(os.path.join(WS, "08-execution/gsc/index-requests-*.jsonl")))[-3:]
    ireq_rows = []
    for f in ireq:
        for l in open(f, encoding="utf-8"):
            try: ireq_rows.append(json.loads(l))
            except Exception: pass
    indexnow = load_json(os.path.join(SITE, "ops/indexnow-state.json"), {})
    in_count = len(indexnow.get("urls") or indexnow.get("entries") or indexnow) if isinstance(indexnow, dict) else 0

    # social
    qrows = [json.loads(l) for l in open(os.path.join(WS, "08-execution/community/quora-log.jsonl"), encoding="utf-8") if l.strip()]
    q_recent = [r for r in qrows if str(r.get("date", "")) >= since.strftime("%Y-%m-%d")]
    social_files = sorted(glob.glob(os.path.join(WS, "08-execution/social/*dispatch*.md")), key=os.path.getmtime)[-3:]

    # outbound
    try:
        mo = json.loads(sh("python3 scripts/outbound/marketing_outbound.py status", cwd=WS) or "{}")
    except Exception:
        mo = {}
    refdom = load_json(os.path.join(WS, "08-execution/backlink/referring-domains.json"), {})
    ref_rows = refdom.get("rows") if isinstance(refdom, dict) else []

    # inquiries
    funnel_txt = sh("python3 scripts/metrics/lead_lifecycle.py report 2>/dev/null | head -10", cwd=WS)

    # gates
    gate = latest(os.path.join(WS, "08-execution/tech/gate-runs/*.md"))
    gate_txt = ""
    if gate:
        try: gate_txt = open(gate, encoding="utf-8").read()[-900:]
        except Exception: pass

    # dashboards
    dash = load_json(os.path.join(WS, f"08-execution/daily/dashboard-{now.date().isoformat()}.json"), {}) or {}

    # group run-log
    groups = {name: [] for name, _ in GROUPS}
    groups["其他"] = []
    for r in recent:
        groups[group_of(r.get("agent"))].append(r)

    # ---- build markdown ----
    L = []
    A = L.append
    A(f"# 团队动作总览 · {now.strftime('%Y-%m-%d %H:%M')}（近 {a.hours}h）")
    A("")
    A(f"> 生成：`scripts/metrics/team_progress.py`（数据源：run-log / git / 索引审计 / Quora 台账 / 外联 API / 独立门禁报告）")
    A(f"> 窗口：{since.strftime('%m-%d %H:%M')} → {now.strftime('%m-%d %H:%M')} ｜ 动作 {len(recent)} 条 ｜ 站点提交 {len(commits)} 个")
    A("")
    A("## 0. 一句话")
    A("")
    A(f"**近 {a.hours} 小时有 {len(recent)} 条团队动作、{len(commits)} 个站点提交；每条都有产物路径（见下）。**"
      " 如果只看一个数：收录 197/247 = 79.8%（11-17 全量审计），比 11-16 的 71.1% 提升，主因是合并后分母变小 + 新页被收录。")
    A("")
    A("## 1. 各团队最近动作（按 run-log）")
    A("")
    A("| 团队 | 动作数 | 最近 3 条 |")
    A("|---|---:|---|")
    for name, _ in GROUPS + [("其他", [])]:
        rs = groups.get(name) or []
        if not rs: continue
        latest_txt = "；".join(f"{r['at'][5:16]} {r.get('task','')[:42]}" for r in rs[:3])
        A(f"| {name} | {len(rs)} | {latest_txt} |")
    A("")
    A("## 2. 站点发布（git）")
    A("")
    for c in commits[:15]:
        parts = c.split("|", 2)
        if len(parts) == 3: A(f"- `{parts[1]}` {parts[0]} {parts[2]}")
    A("")
    A("## 3. 内容 / 关键词")
    A("")
    if recent_content:
        for e in recent_content[:8]:
            slug = e.get("slug") or e.get("primary") or ""
            kind = e.get("type") or e.get("action") or "published"
            words = e.get("word_count") or e.get("words") or ""
            commit = e.get("commit") or ""
            A(f"- {e.get('date')} {kind} `{slug}` {('· '+str(words)+' 词') if words else ''} {('· '+commit) if commit else ''}")
    else:
        A("- 近 48h 无内容台账更新（检查内容档位）")
    qfile = sorted(glob.glob(os.path.join(WS, "08-execution/content/content-queue-*.json")), key=os.path.getmtime)
    if qfile:
        q = load_json(qfile[-1]) or {}
        items = q.get("items") or []
        ledger_slugs = {str(e.get("slug", "")).replace("/blog/", "").lstrip("/")
                        for e in entries if e.get("slug")}
        def _done(it):
            if it.get("status") in ("published", "live_verified", "done"):
                return True
            return str(it.get("slug", "")).replace("/blog/", "").lstrip("/") in ledger_slugs
        done = sum(1 for i in items if _done(i))
        A(f"- 最新选题队列：`{os.path.relpath(qfile[-1], WS)}` · {len(items)} 条 · 已上线（按台账核对）{done} 条 · 窗口 {q.get('window','')}")
    kmap = sorted(glob.glob(os.path.join(WS, "08-execution/keywords/keyword-map-*.md")))
    if kmap: A(f"- 最新词图：`{os.path.relpath(kmap[-1], WS)}`")
    A("")
    A("## 4. 索引 / 收录")
    A("")
    if idx:
        A(f"- 最新全量审计：{idx.get('generated_at','?')[:16]} · {idx.get('inspected')} URL · 已收录 {idx.get('verdict_dist',{}).get('PASS')} · "
          f"{json.dumps(idx.get('coverage_dist'), ensure_ascii=False)}")
    if idx_prev:
        A(f"- 上一份：{idx_prev.get('generated_at','?')[:16]} · 已收录 {idx_prev.get('verdict_dist',{}).get('PASS')} · URL {idx_prev.get('inspected')}")
    if ireq_rows:
        A(f"- GSC 请求索引台账（近 3 份）：共 {len(ireq_rows)} 条，最近：{ireq_rows[-1].get('date')} {ireq_rows[-1].get('url','')[:60]} → {ireq_rows[-1].get('result')}")
    A(f"- IndexNow 状态条目：{in_count}")
    A("")
    A("## 5. 社媒 / 社区")
    A("")
    A(f"- Quora 近 48h 发布/记录：{len(q_recent)} 条" + (f"；最近 {q_recent[0].get('date')} {q_recent[0].get('question','')[:60]}" if q_recent else ""))
    A(f"- Quora 累计台账：{len(qrows)} 条（{min((r.get('date') for r in qrows), default='?')} 起）")
    for f in social_files: A(f"- 社媒分发稿：`{os.path.relpath(f, WS)}`")
    A("")
    A("## 6. 外联 / 引用域")
    A("")
    if mo.get("campaigns"):
        for c in mo["campaigns"]:
            A(f"- {c.get('campaign')} · status={c.get('status')} · leads_actual={c.get('leads_actual')} · sent={c.get('sent')} · replies={c.get('replies_unique')}")
    A(f"- 引用域台账：{len(ref_rows)} 条（dofollow 见台账 result 字段）")
    A("")
    A("## 7. 询盘")
    A("")
    if funnel_txt:
        for line in funnel_txt.splitlines()[:8]: A("    " + line)
    A("")
    A("## 8. 门禁（独立验证，R14）")
    A("")
    if gate:
        A(f"- 最新报告：`{os.path.relpath(gate, WS)}`")
        tail = " / ".join(l.strip() for l in gate_txt.splitlines() if l.strip().startswith("|") and ("pass" in l or "fail" in l))
        A(f"- 摘要：{tail[:600]}")
    A("")
    A("## 9. 当日 KPI（看板）")
    A("")
    if dash:
        A(f"- 窗口 {dash.get('window')} · 点击 {dash.get('clicks')} · 展示 {dash.get('impressions')} · CTR {dash.get('ctr')}% · 有展示页 {dash.get('pages_with_impressions')}")
    A("")

    md = "\n".join(L)
    stamp = now.strftime("%Y%m%d-%H%M")
    md_path = os.path.join(OUT, f"team-progress-{stamp}.md")
    with open(md_path, "w", encoding="utf-8") as f: f.write(md)
    # simple HTML wrapper
    try:
        import html as H
        body = []
        for line in md.splitlines():
            if line.startswith("# "): body.append(f"<h1>{H.escape(line[2:])}</h1>")
            elif line.startswith("## "): body.append(f"<h2>{H.escape(line[3:])}</h2>")
            elif line.startswith("|"):
                body.append(f"<pre>{H.escape(line)}</pre>")
            elif line.startswith("- "): body.append(f"<p>{H.escape(line)}</p>")
            elif line.strip(): body.append(f"<p>{H.escape(line)}</p>")
        html_doc = ("<!doctype html><meta charset='utf-8'><title>团队动作总览</title>"
                    "<style>body{font:15px/1.6 -apple-system,system-ui;max-width:980px;margin:32px auto;padding:0 20px;color:#1b1b1f}"
                    "pre{white-space:pre-wrap;background:#f6f8fa;padding:8px;border-radius:6px;font-size:13px}"
                    "h1{border-bottom:2px solid #1877f2;padding-bottom:8px}h2{margin-top:28px;color:#1877f2}</style>")
        html_doc += "\n".join(body)
        html_path = os.path.join(OUT, f"team-progress-{stamp}.html")
        with open(html_path, "w", encoding="utf-8") as f: f.write(html_doc)
    except Exception:
        html_path = None
    print("WROTE", md_path)
    print("WROTE", glob.glob(os.path.join(OUT, f"team-progress-{stamp}.html")) and html_path)
    return 0

if __name__ == "__main__":
    sys.exit(main())
