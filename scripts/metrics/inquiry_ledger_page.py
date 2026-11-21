#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""inquiry_ledger_page.py — 生成第一方询盘台账页（不依赖 Brevo UI / 邮箱）

## 为什么有这个
2026-11-11 用户连续两处"看不到"询盘：邮箱（进垃圾箱）与 Brevo（CRM 未开通）。
询盘主记录其实一直在 D1。所以需要一个**零依赖**的查看入口：
本地 HTML 文件，双击即可看，数据全部来自 D1。

## 用法
  python3 scripts/metrics/inquiry_ledger_page.py            # 刷新台账页
输出：08-execution/inquiry/ledger.html（自包含，无外链资源）
"""
import datetime as dt
import html
import json
import os
import subprocess
import sys

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BJ = dt.timezone(dt.timedelta(hours=8))
OUT = os.path.join(WS, "08-execution", "inquiry", "ledger.html")


def d1(sql):
    r = subprocess.run([sys.executable, os.path.join(WS, "scripts/metrics/d1_query.py"), "sql", sql],
                       capture_output=True, text=True, timeout=180)
    rows = []
    for line in (r.stdout or "").split("\n"):
        if line.strip().startswith("{"):
            try:
                rows.append(json.loads(line))
            except Exception:  # noqa: BLE001
                pass
    return rows


def ledger():
    p = os.path.join(WS, "08-execution", "inquiry", "lifecycle.jsonl")
    out = {}
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            if line.strip():
                try:
                    rec = json.loads(line)
                    out[rec["submission_id"]] = rec
                except Exception:  # noqa: BLE001
                    pass
    return out


def main():
    subs = d1("SELECT submission_id, email, form_type, consent, status, payload, created_at "
              "FROM submissions ORDER BY created_at DESC LIMIT 200")
    led = ledger()
    rows_html = []
    for r in subs:
        p = json.loads(r["payload"]) if isinstance(r["payload"], str) else (r.get("payload") or {})
        rec = led.get(r["submission_id"], {})
        when = (dt.datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
                .astimezone(BJ).strftime("%Y-%m-%d %H:%M"))
        stage = rec.get("status", "未入账")
        badge = {"mql": "#1078F0", "sal": "#0B63CE", "saqo": "#0a7d33",
                 "won": "#0a7d33", "lost": "#8a8f98", "disqualified": "#8a8f98"}.get(stage, "#8a8f98")
        rows_html.append(f"""      <tr>
        <td class="mono">{when}</td>
        <td><b>{html.escape(p.get('FIRSTNAME') or '—')}</b><br><span class="sub">{html.escape(p.get('COMPANY') or '—')}</span></td>
        <td><a href="mailto:{html.escape(r['email'])}">{html.escape(r['email'])}</a></td>
        <td>{html.escape(p.get('COUNTRY') or '—')}</td>
        <td>{html.escape(p.get('PRODUCT') or '—')}</td>
        <td class="note">{html.escape(p.get('PROJECT') or '（空）')}</td>
        <td>{'是' if str(r.get('consent')) == '1' else '否'}</td>
        <td><span class="badge" style="background:{badge}">{html.escape(stage)}</span></td>
        <td class="mono small">{html.escape(r['submission_id'][:8])}…</td>
      </tr>""")
    now = dt.datetime.now(BJ).strftime("%Y-%m-%d %H:%M")
    doc = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>ANARI 询盘台账（{len(subs)} 条）</title>
<style>
  :root {{ --ink:#14161a; --sub:#6b7280; --line:#e5e7eb; --bg:#fff; }}
  body {{ font: 15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; color:var(--ink); background:#f7f8fa; margin:0; padding:32px; }}
  .wrap {{ max-width:1280px; margin:0 auto; }}
  h1 {{ font-size:22px; margin:0 0 6px; }}
  .meta {{ color:var(--sub); font-size:13px; margin-bottom:20px; }}
  table {{ width:100%; border-collapse:collapse; background:var(--bg); border:1px solid var(--line); border-radius:10px; overflow:hidden; }}
  th, td {{ text-align:left; padding:10px 12px; border-top:1px solid var(--line); vertical-align:top; font-size:14px; }}
  thead th {{ background:#fafbfc; font-size:12px; letter-spacing:.03em; text-transform:uppercase; color:var(--sub); }}
  .mono {{ font-variant-numeric: tabular-nums; }}
  .small {{ font-size:12px; color:var(--sub); }}
  .sub {{ color:var(--sub); font-size:12.5px; }}
  .note {{ max-width:280px; }}
  .badge {{ color:#fff; border-radius:999px; padding:2px 9px; font-size:12px; font-weight:600; }}
  .empty {{ padding:40px; text-align:center; color:var(--sub); background:#fff; border:1px solid var(--line); border-radius:10px; }}
  .hint {{ margin-top:16px; font-size:13px; color:var(--sub); }}
</style></head><body><div class="wrap">
<h1>ANARI 询盘台账</h1>
<div class="meta">数据源：Cloudflare D1 <code>anari-leads.submissions</code>（主记录）· 生成于 {now} 北京 · 共 {len(subs)} 条</div>
{'' if rows_html else '<div class="empty">还没有询盘</div>'}
{'<table><thead><tr><th>时间（北京）</th><th>客户</th><th>邮箱</th><th>国家</th><th>项目类型</th><th>项目描述</th><th>营销同意</th><th>账本状态</th><th>ID</th></tr></thead><tbody>' + ''.join(rows_html) + '</tbody></table>' if rows_html else ''}
<div class="hint">这份台账由 <code>scripts/metrics/inquiry_ledger_page.py</code> 从 D1 生成，不依赖邮箱或 Brevo 是否可用。每日摘要档位会顺带刷新它。</div>
</div></body></html>
"""
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(doc)
    print(f"  台账页已生成：{OUT}（{len(subs)} 条）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
