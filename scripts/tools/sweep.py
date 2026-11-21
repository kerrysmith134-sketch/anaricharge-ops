#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sweep.py — 单标签逐页巡检（R10 浏览器卫生的机制化）

问题：之前的写法每页 `new_tab=True`，用户窗口里会同时挂 6–11 个标签几分钟。
本脚本固定行为：
  1. 开始前先清残留
  2. **只开 1 个标签**，后续页面在同一标签里 `newTab:false` 导航
  3. 全程在 try/finally 里，无论成功失败都关闭该标签并复核
  4. 每页默认截图 + 打印页面度量（溢出、h1、fixed 元素）

用法：
  python3 scripts/tools/sweep.py --base http://127.0.0.1:8096 \
      --paths /index.html,/cases/index.html --out /tmp/shots --tag mob
  # 可选：--width 390 用同源探针模拟窄屏（需要 --probe 指向站点内的探针页）
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "browser"))
from wb import WB, cleanup_all  # noqa: E402


def measure(wb, probe=None, width=None):
    if probe and width:
        # 探针模式：把 iframe 指到目标页，量 iframe 内的布局
        return wb.eval("""
        return (function(){
          const f=document.getElementById('sweepFrame');
          if(!f||!f.contentDocument) return JSON.stringify({err:'no frame'});
          const d=f.contentDocument, w=f.contentWindow;
          const bar='class="contact-bar"';
          const fixed=[...d.querySelectorAll('body *')].filter(e=>{
            const cs=getComputedStyle(e);
            if(cs.position!=='fixed'||cs.display==='none') return false;
            const r=e.getBoundingClientRect(); return r.width>40&&r.height>20;
          }).map(e=>e.className.toString().slice(0,18));
          const h=d.querySelector('h1');
          return JSON.stringify({
            overflow: d.documentElement.scrollWidth - w.innerWidth,
            h1: h ? h.textContent.trim().slice(0,38) : null,
            h1px: h ? getComputedStyle(h).fontSize : null,
            fixed: fixed,
            footers: d.querySelectorAll('footer').length
          });
        })()
        """)
    return wb.eval("""
    return (function(){
      return JSON.stringify({
        overflow: document.documentElement.scrollWidth - innerWidth,
        h1: document.querySelector('h1') ? document.querySelector('h1').textContent.trim().slice(0,38) : null,
        v2: !!document.querySelector('main.v2')
      });
    })()
    """)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--paths", required=True, help="逗号分隔的相对路径")
    ap.add_argument("--out", default="/tmp/shots")
    ap.add_argument("--tag", default="sweep")
    ap.add_argument("--wait", type=float, default=4.0)
    ap.add_argument("--probe", default=None, help="探针页路径（同源 iframe 里量窄屏）")
    ap.add_argument("--width", type=int, default=None)
    ap.add_argument("--no-shot", action="store_true")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    paths = [p.strip() for p in a.paths.split(",") if p.strip()]
    results = []

    cleanup_all(verbose=False)          # 1) 先清残留
    wb = WB(session="sweep")
    tab_open = False
    try:
        if a.probe:
            wb.nav(a.base.rstrip("/") + a.probe + f"?w={a.width or 390}", new_tab=True)
        else:
            wb.nav(a.base.rstrip("/") + paths[0], new_tab=True)
        tab_open = True
        time.sleep(a.wait)

        for i, p in enumerate(paths):
            ts = int(time.time() * 1000)
            if a.probe:
                wb.eval("document.getElementById('sweepFrame').src='%s?v=%d'"
                        % (p if p.startswith("http") else p, ts))
            else:
                # 2) 关键：同一标签内导航，不再开新标签
                wb.nav(a.base.rstrip("/") + p, new_tab=False)
            time.sleep(a.wait)
            if not a.probe:
                # 截图前归零：必须用 instant，站点有 scroll-behavior:smooth，
                # 平滑滚动在 0.4s 内到不了顶 → 截图会拍到中途位置（本轮踩过）。
                wb.eval("window.scrollTo({top:0,left:0,behavior:'instant'});")
                time.sleep(0.8)
            info = measure(wb, a.probe, a.width)
            results.append({"path": p, "info": info})
            print(f"  {p:52s} {info}")
            if not a.no_shot:
                slug = p.strip("/").replace("/", "_").replace(".html", "") or "home"
                wb.screenshot(path=os.path.join(a.out, f"{a.tag}-{slug}.png"))
    finally:
        # 3) 无论成败都收尾
        try:
            if tab_open:
                wb.close_tab()
        except Exception:
            pass
        cleanup_all(verbose=False)      # 4) 复核
        print("\n✅ 单标签巡检结束，浏览器已清空")

    def ok(r):
        info = r.get("info")
        if not isinstance(info, str):
            return False
        return '"overflow": 0' in info.replace('"overflow":0', '"overflow": 0')

    bad = [r for r in results if not ok(r)]
    if bad:
        print(f"⚠️ 有 {len(bad)} 页存在横向溢出或度量失败：")
        for b in bad:
            print("   ", b["path"], b["info"])
        sys.exit(1)
    print(f"全部 {len(results)} 页：横向溢出 0")


if __name__ == "__main__":
    main()
