#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contrast-audit.py — 全站文字对比度审计（WCAG 2.2 AA）

为什么需要：2026-11-07 用户指出 `/who-we-serve/` 里有整块**白底白字**——
根因是我把 `.v2-cap`（两列卡片）只写了深色皮肤，却在浅色区块复用。
这类错误肉眼要一页页翻才看得到，必须用机制查。

判定：
  - 普通文字     对比度 ≥ 4.5:1
  - 大字（≥24px 或 ≥18.66px 且 bold） ≥ 3:1
  - 背景是图片/渐变（hero）时跳过（无法用纯色判定，另行人工核对）

用法：
  python3 scripts/tools/contrast-audit.py --base http://127.0.0.1:8096 \
      --paths /who-we-serve/index.html,/solutions/index.html --json /tmp/contrast.json
  python3 scripts/tools/contrast-audit.py --base https://www.anaricharge.com --sitemap
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "browser"))
from wb import WB, cleanup_all  # noqa: E402

AUDIT_JS = r"""
return (function () {
  function parseColor(s) {
    const m = s.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(',').map(Number);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  }
  function lum(c) {
    const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b);
  }
  function ratio(a, b) {
    const l1 = lum(a), l2 = lum(b);
    return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
  }
  function blend(fg, bg) {  // fg 半透明时叠到 bg 上
    const a = fg.a;
    return { r: fg.r * a + bg.r * (1 - a), g: fg.g * a + bg.g * (1 - a), b: fg.b * a + bg.b * (1 - a), a: 1 };
  }
  function effectiveBg(el) {
    // 向上找到第一个不透明背景；遇到背景图/渐变则返回 null（无法判定）
    let node = el;
    while (node && node !== document.documentElement) {
      const cs = getComputedStyle(node);
      if (cs.backgroundImage && cs.backgroundImage !== 'none') return null;
      const c = parseColor(cs.backgroundColor);
      if (c && c.a > 0.95) return c;
      node = node.parentElement;
    }
    return parseColor(getComputedStyle(document.body).backgroundColor) || { r: 255, g: 255, b: 255, a: 1 };
  }

  const out = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = walker.nextNode())) {
    const txt = (n.textContent || '').trim();
    if (txt.length < 2) continue;
    const el = n.parentElement;
    if (!el) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.15) continue;
    // 跳过文字压在图片上的组件（.v2-scene 图片卡、hero、产品卡）：这些白字是有意的，
    // 真正要查的是"浅色背景上的浅色文字"。图片卡另行人工核对。
    if (el.closest('[aria-hidden="true"], script, style, .v2-hero, .skip-link, .v2-scene, .v2-product')) continue;
    const fg0 = parseColor(cs.color);
    if (!fg0) continue;
    // 祖先内有绝对定位 <img> 覆盖时，背景是图片，跳过
    let over = false, up = el;
    while (up && up !== document.body) {
      if (up.querySelector && up.querySelector(':scope > img')) { over = true; break; }
      up = up.parentElement;
    }
    if (over) continue;
    const bg = effectiveBg(el);
    if (!bg) continue;                                   // hero/图片背景：跳过
    const fg = fg0.a < 1 ? blend(fg0, bg) : fg0;
    const size = parseFloat(cs.fontSize);
    const bold = parseInt(cs.fontWeight, 10) >= 700;
    const large = size >= 24 || (size >= 18.66 && bold);
    const need = large ? 3 : 4.5;
    const r = ratio(fg, bg);
    if (r + 0.01 < need) {
      out.push({ text: txt.slice(0, 60), ratio: Math.round(r * 100) / 100, need: need,
                 fg: `rgba(${Math.round(fg.r)},${Math.round(fg.g)},${Math.round(fg.b)})`,
                 bg: `rgba(${Math.round(bg.r)},${Math.round(bg.g)},${Math.round(bg.b)})`,
                 cls: (el.className || el.tagName).toString().slice(0, 40), size: Math.round(size) });
    }
  }
  return JSON.stringify(out.slice(0, 40));
})()
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--paths", default=None, help="逗号分隔；与 --sitemap 二选一")
    ap.add_argument("--sitemap", action="store_true", help="用本地 sitemap 的全部 URL")
    ap.add_argument("--json", default=None)
    ap.add_argument("--wait", type=float, default=3.0)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    if a.sitemap:
        import re
        xml = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "06-site/anari-new-site/site/sitemap.xml"),
                   encoding="utf-8").read()
        paths = [u.replace("https://www.anaricharge.com", "") or "/" for u in re.findall(r"<loc>(.*?)</loc>", xml)]
    else:
        paths = [p.strip() for p in (a.paths or "/").split(",") if p.strip()]
    if a.limit:
        paths = paths[: a.limit]

    cleanup_all(verbose=False)
    wb = WB(session="contrast")
    problems = {}
    try:
        wb.nav(a.base.rstrip("/") + paths[0], new_tab=True)
        time.sleep(a.wait)
        for i, p in enumerate(paths):
            if i:
                wb.nav(a.base.rstrip("/") + p, new_tab=False)
                time.sleep(a.wait)
            wb.eval("window.scrollTo({top:0,behavior:'instant'})")
            title = (wb.eval("return document.title;") or "")
            if "Error response" in title or "404" in title[:20]:
                print(f"  ⚠ {p}  404（跳过）")
                continue
            try:
                raw = wb.eval(AUDIT_JS)
                issues = json.loads(raw) if isinstance(raw, str) else (raw or [])
            except Exception as e:
                issues = [{"error": str(e)[:120]}]
            if issues:
                problems[p] = issues
                print(f"  ✗ {p}  低对比度 {len(issues)} 处")
                for it in issues[:4]:
                    if "error" in it:
                        print(f"      ERR {it['error']}")
                    else:
                        print(f"      {it['ratio']:>5}:1 (需 {it['need']}) {it['cls']:<28} {it['text'][:44]!r}")
            else:
                print(f"  ✓ {p}")
    finally:
        try:
            wb.close_tab()
        except Exception:
            pass
        cleanup_all(verbose=False)
        print("\n✅ 审计结束，浏览器已清空")

    if a.json:
        json.dump(problems, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("明细 →", a.json)
    total = sum(len(v) for v in problems.values())
    print(f"\n合计：{len(problems)} 页有低对比度文字，共 {total} 处")
    if problems:
        sys.exit(1)


if __name__ == "__main__":
    main()
