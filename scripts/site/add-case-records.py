#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""add-case-records.py — 给案例页注入「项目记录」证据面板（幂等）

对应 Growth OS 计划 §3：案例页至少要有
Site context / Configuration / Binding constraint / Commissioning /
Measured outcome / 限制与来源，而不是只讲故事。

数据在 `scripts/site/v2/cases-evidence.json`（只用页面已陈述的事实；
缺的写 Not published，不补编）。

幂等：页面里已有 `data-case-record` 就跳过。
"""
import html
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
SITE = os.path.join(WS, "06-site/anari-new-site/site")
DATA = json.load(open(os.path.join(HERE, "v2/cases-evidence.json"), encoding="utf-8"))

LABELS = [
    ("site_context", "Site context"),
    ("binding_constraint", "Binding constraint"),
    ("configuration", "Configuration"),
    ("commissioning", "Commissioning"),
    ("outcome", "Measured / stated outcome"),
]


def panel(slug, rec):
    rows = []
    for key, label in LABELS:
        val = rec.get(key) or "Not published."
        rows.append(
            f'          <div class="v2-rec-row"><dt>{html.escape(label)}</dt>'
            f"<dd>{html.escape(val)}</dd></div>"
        )
    limits = re.sub(r"\s+", " ", rec.get("limits") or "Not published.").strip()
    source = rec.get("source") or "Not published."
    return f"""  <section class="v2-section v2-section--alt" data-case-record>
    <div class="v2-wrap">
      <div class="v2-section-head">
        <p class="v2-eyebrow">Project record</p>
        <h2>What this project was, and what it does not prove</h2>
        <p>Fields are filled from the deployment record. Anything we cannot substantiate is marked
        as not published rather than estimated.</p>
      </div>
      <dl class="v2-record">
{chr(10).join(rows)}
          <div class="v2-rec-row v2-rec-row--limits"><dt>Limits</dt><dd>{html.escape(limits)}</dd></div>
          <div class="v2-rec-row"><dt>Source</dt><dd>{html.escape(source)}</dd></div>
      </dl>
    </div>
  </section>
"""


def inject(fp, slug):
    t = io.open(fp, encoding="utf-8").read()
    if "data-case-record" in t:
        return "skip"
    rec = DATA.get(slug)
    if not rec:
        return "nodata"
    # 插在 hero 之后：<main> 之后第一个 </section> 就是 hero 的收尾
    mi = t.find("<main")
    if mi < 0:
        return "noanchor"
    end = t.find("</section>", mi)
    if end < 0:
        return "noanchor"
    end += len("</section>")
    block = "\n\n" + panel(slug, rec)
    t = t[:end] + block + t[end:]
    io.open(fp, "w", encoding="utf-8").write(t)
    return "ok"


def main():
    n = {"ok": 0, "skip": 0, "nodata": 0, "noanchor": 0}
    for slug in DATA:
        if slug.startswith("_"):
            continue
        fp = os.path.join(SITE, "cases", f"{slug}.html")
        if not os.path.exists(fp):
            print(f"  缺失页面: {slug}")
            continue
        r = inject(fp, slug)
        n[r] += 1
        print(f"  {slug:22s} {r}")
    print(f"\n注入 {n['ok']} · 跳过 {n['skip']}（已有）· 无数据 {n['nodata']} · 找不到锚点 {n['noanchor']}")
    return 0 if n["noanchor"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
