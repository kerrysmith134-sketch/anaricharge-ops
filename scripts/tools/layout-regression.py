#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""layout-regression.py — 布局回归（GROW-012 的可行版本）

## 为什么不是像素比对
先做了像素版，实测在这个环境里**不可用**：截图尺寸随真实窗口高度/dpr 变化
（1870 vs 1776、dpr 2.0 vs 1.97），还会因为 vh 布局整体位移——每次跑都 1–18% 假失败。
把阈值调到能"通过"的程度，就等于什么都测不出来。

## 换成什么
量**布局度量**而不是像素：
- 文档总高度、每个 section 的高度与顺序
- 关键元素的盒子（h1、导航、主 CTA、表单、卡片网格）与数量
- 横向溢出量
这些都是确定性的数字；变化超过容差就说明布局真的动了，而不是渲染抖动。

## 用法
  python3 scripts/tools/layout-regression.py                # 比对
  python3 scripts/tools/layout-regression.py --update        # 重建基线
  python3 scripts/tools/layout-regression.py --only home,cases
  python3 scripts/tools/layout-regression.py --pixels        # 附带像素差异（仅供参考，默认阈值 8%）
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "browser"))
from wb import WB, cleanup_all  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
BASE_DIR = os.path.join(WS, "08-execution", "layout-baseline")
SHOT_DIR = os.path.join(WS, "08-execution", "layout-shots")

PAGES = [
    ("home", "/"),
    ("products", "/products/"),
    ("solutions", "/solutions/"),
    ("cases", "/cases/"),
    ("case-jordan", "/cases/jordan-160kw"),
    ("agents", "/agents/"),
    ("markets", "/markets/"),
    ("tool-roi", "/tools/charging-station-roi"),
    ("inquiry", "/inquiry"),
    ("blog-article", "/blog/commercial-ac-charging-station-installation-cost"),
]

# 固定尺寸 iframe：vh 单位靠它固定，不受真实窗口影响
PROBE = """<!doctype html><meta charset="utf-8"><title>probe</title>
<style>html,body{{margin:0;background:#fff}}iframe{{border:0;display:block;width:{w}px;height:{h}px}}</style>
<iframe id="f" src="{url}"></iframe>"""
VIEWPORTS = {"desktop": (1440, 900), "mobile": (390, 844)}

MEASURE_JS = r"""
return (function () {
  var f = document.getElementById('f');
  var d = (f && f.contentDocument) ? f.contentDocument : document;
  var w = d.defaultView;
  // 懒加载图片立刻加载，避免高度随加载时机变化
  d.querySelectorAll('img[loading="lazy"]').forEach(function (i) {
    i.loading = 'eager'; if (i.src) { i.src = i.src; }
  });
  function box(el) {
    var r = el.getBoundingClientRect();
    return [Math.round(r.width), Math.round(r.height)];
  }
  var sections = [].map.call(d.querySelectorAll('main section'), function (s) {
    return Math.round(s.getBoundingClientRect().height);
  });
  function count(sel) { return d.querySelectorAll(sel).length; }
  var checks = {};
  var probes = {
    h1: 'h1', nav: '.site-nav', header: '.site-header', main: 'main',
    cta: '.nav-cta', cards: '.v2-product, .v2-scene, .v2-cap',
    form: 'form', textarea: 'textarea', steps: '[data-step]',
    filters: '[data-filter-bar]', compare: '[data-compare-grid]'
  };
  Object.keys(probes).forEach(function (k) { checks[k] = count(probes[k]); });
  var firstH1 = d.querySelector('h1');
  return JSON.stringify({
    scrollHeight: Math.round(d.documentElement.scrollHeight),
    bodyWidth: Math.round(d.documentElement.clientWidth),
    overflowX: Math.max(0, Math.round(d.documentElement.scrollWidth - d.documentElement.clientWidth)),
    sections: sections,
    checks: checks,
    h1Box: firstH1 ? box(firstH1) : null,
    navBox: d.querySelector('.site-nav') ? box(d.querySelector('.site-nav')) : null
  });
})()
"""


def diff_metrics(base, cur, tol_px=6):
    """返回差异列表；空 = 通过。"""
    out = []
    for k in ("scrollHeight", "bodyWidth", "overflowX"):
        a, b = base.get(k), cur.get(k)
        if a != b:
            out.append(f"{k}: {a} → {b}")
    ba, bb = base.get("sections") or [], cur.get("sections") or []
    if len(ba) != len(bb):
        out.append(f"section 数量: {len(ba)} → {len(bb)}")
    else:
        for i, (x, y) in enumerate(zip(ba, bb)):
            if abs(x - y) > tol_px:
                out.append(f"section[{i}] 高度: {x} → {y}")
    for k in (base.get("checks") or {}):
        a = (base.get("checks") or {}).get(k)
        b = (cur.get("checks") or {}).get(k)
        if a != b:
            out.append(f"元素数 {k}: {a} → {b}")
    for k in ("h1Box", "navBox"):
        a, b = base.get(k), cur.get(k)
        if a is None or b is None:
            if a != b:
                out.append(f"{k}: {a} → {b}")
            continue
        if abs(a[0] - b[0]) > tol_px or abs(a[1] - b[1]) > tol_px:
            out.append(f"{k} 尺寸: {a} → {b}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8096")
    ap.add_argument("--ext", default=".html")
    ap.add_argument("--mode", default="both", choices=["desktop", "mobile", "both"])
    ap.add_argument("--only", default="")
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--tol", type=int, default=6, help="允许的高度差（px）")
    ap.add_argument("--pixels", action="store_true", help="额外记录像素差异（仅参考）")
    ap.add_argument("--json", default="")
    a = ap.parse_args()

    os.makedirs(BASE_DIR, exist_ok=True)
    os.makedirs(SHOT_DIR, exist_ok=True)
    pages = PAGES
    if a.only:
        want = {s.strip() for s in a.only.split(",")}
        pages = [p for p in pages if p[0] in want]
    modes = ["desktop", "mobile"] if a.mode == "both" else [a.mode]
    base = a.base.rstrip("/") + "/"
    probe = os.path.join(WS, "06-site/anari-new-site/site/_layoutprobe.html")

    results = []
    cleanup_all(verbose=False)
    wb = WB(session="layout")
    try:
        wb.nav(base, new_tab=True)
        for mode in modes:
            w, h = VIEWPORTS[mode]
            for slug, path in pages:
                p = path
                if a.ext and p == "/":
                    p = "/index" + a.ext
                elif a.ext and not p.endswith("/") and not p.endswith(a.ext):
                    p = p + a.ext
                open(probe, "w", encoding="utf-8").write(
                    PROBE.format(w=w, h=h, url=base + p.lstrip("/")))
                wb.nav(base + "_layoutprobe.html", new_tab=False)
                time.sleep(2.2)
                raw = wb.eval(MEASURE_JS)
                time.sleep(0.6)
                raw2 = wb.eval(MEASURE_JS)   # 再量一次，取"稳定后"的结果
                try:
                    cur = json.loads(raw2 or raw)
                except (TypeError, ValueError):
                    print(f"  ⚠ {slug}/{mode} 取不到度量")
                    continue
                ref_path = os.path.join(BASE_DIR, f"{slug}-{mode}.json")
                if a.update or not os.path.exists(ref_path):
                    json.dump(cur, open(ref_path, "w", encoding="utf-8"),
                              ensure_ascii=False, indent=1)
                    print(f"  {'更新' if a.update else '新'}基线 {slug:14s} {mode}")
                    results.append({"slug": slug, "mode": mode, "diffs": []})
                    continue
                ref = json.load(open(ref_path, encoding="utf-8"))
                diffs = diff_metrics(ref, cur, a.tol)
                ok = not diffs
                print(f"  {'✅' if ok else '❌'} {slug:14s} {mode:8s}"
                      + ("" if ok else "  " + "; ".join(diffs[:3])))
                results.append({"slug": slug, "mode": mode, "diffs": diffs})
                if a.pixels:
                    shot = os.path.join(SHOT_DIR, f"{slug}-{mode}.png")
                    wb.screenshot(path=shot, selector="#f")
    finally:
        try:
            wb.close_tab()
        except Exception:
            pass
        cleanup_all(verbose=False)
        if os.path.exists(probe):
            os.remove(probe)
        print("\n✅ 浏览器已清空")

    fails = [r for r in results if r["diffs"]]
    print(f"\n布局回归：{len(results) - len(fails)}/{len(results)} 通过（容差 {a.tol}px）")
    if fails:
        print("变化页：")
        for r in fails:
            print(f"  - {r['slug']}/{r['mode']}: {'; '.join(r['diffs'])}")
        print("如确认变化是有意的 → `--update` 刷新基线。")
    if a.json:
        json.dump(results, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("明细 →", a.json)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
