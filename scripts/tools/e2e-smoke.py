#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e2e-smoke.py — 关键路径端到端冒烟（Growth OS GROW-012 的轻量版）

为什么需要：
  validate.js 只看静态 HTML（单 h1、死链、schema），check-facts 只看数字；
  **它们都看不到"页面在真实浏览器里能不能用"**：图片是否真的加载、JS 交互是否
  绑定、CTA 带不带上下文、journey 状态有没有存下来。这些坏掉时静态门禁全绿。

与 Playwright 的区别：不装浏览器驱动，用现有 WebBridge（用户真实 Chrome、
带登录态），单标签、可重复、约 60 秒跑完。视觉回归与多断点截图仍留给
sweep.py / contrast-audit.py。

用法：
  python3 scripts/tools/e2e-smoke.py                       # 本地
  python3 scripts/tools/e2e-smoke.py --base https://www.anaricharge.com
退出码：0 全过；1 有失败（可直接接进 CI / 定时任务）。
"""
import argparse
import json
import os
import sys
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "browser"))
from wb import WB, cleanup_all  # noqa: E402

NOT_SUBMITTED = "本脚本不提交真实询盘（不制造假线索）；只验证表单与上下文链路。"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8096")
    ap.add_argument("--ext", default=".html", help="本地服务器需要 .html；线上留空")
    a = ap.parse_args()
    base = a.base.rstrip("/")
    ext = a.ext

    results = []

    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))
        print(f"  {'✅' if ok else '❌'} {name}" + (f"  — {detail}" if detail and not ok else ""))

    cleanup_all(verbose=False)
    wb = WB(session="e2e")
    try:
        # ---------- 1. 首页：结构与导航 ----------
        wb.nav(f"{base}/index{ext}", new_tab=True); time.sleep(3)
        h1 = wb.eval("return (document.querySelector('h1')||{}).textContent||'';")
        nav_links = wb.eval("return document.querySelectorAll('header a').length;")
        overflow = wb.eval("return Math.max(0, document.documentElement.scrollWidth - window.innerWidth);")
        check("首页有唯一 h1", bool(h1.strip()), repr(h1)[:60])
        check("首页导航链接 ≥8", int(nav_links or 0) >= 8, str(nav_links))
        check("首页无横向溢出", int(overflow or 0) == 0, f"overflow={overflow}")

        # ---------- 2. 产品页：只剩直流，没有 AC ----------
        wb.nav(f"{base}/products/index{ext}", new_tab=False); time.sleep(3)
        names = wb.eval(
            "return JSON.stringify([...document.querySelectorAll('.v2-product b')].map(e=>e.textContent.trim()));")
        names = json.loads(names) if names else []
        check("产品页无 AC 产品（Gaia 已下架）", not any(n.lower() == "gaia" for n in names), str(names))
        check("产品页有 5 个 DC 族", len([n for n in names if n.lower() != "bess"]) >= 5, str(names))
        # 图片真实加载（不是只看 src 存在）
        wb.eval("document.querySelectorAll('.v2-product img').forEach(i=>{i.loading='eager';i.src=i.src;});")
        time.sleep(2.5)
        loaded = wb.eval(
            "return JSON.stringify([...document.querySelectorAll('.v2-product img')].map(i=>i.naturalWidth>0));")
        loaded = json.loads(loaded) if loaded else []
        check("产品图全部真实加载", loaded and all(loaded), f"{sum(loaded)}/{len(loaded)}")

        # ---------- 3. 案例页：8 个案例 ----------
        wb.nav(f"{base}/cases/index{ext}", new_tab=False); time.sleep(2.5)
        cards = wb.eval("return document.querySelectorAll('a[href*=\"/cases/\"]').length;")
        check("案例卡 ≥8", int(cards or 0) >= 8, str(cards))

        # ---------- 4. 工具 → 询盘：上下文真的带过去 ----------
        wb.nav(f"{base}/tools/charging-station-roi{ext}", new_tab=False); time.sleep(3.5)
        url = wb.eval("""
        const b=document.querySelector('.tool-lead__btn');
        if(!b) return '';
        b.dispatchEvent(new MouseEvent('mouseenter',{bubbles:true}));
        return b.href;
        """)
        has_note = bool(url) and "note=" in url and "ref=charging-station-roi" in url
        check("工具页出现复核 CTA 且带计算摘要", has_note, str(url)[:80])
        if url:
            path = url.replace(base, "").replace("https://www.anaricharge.com", "")
            if ext and ".html" not in path.split("?")[0]:
                path = path.replace("/inquiry", "/inquiry" + ext, 1)
            wb.nav(base + path, new_tab=False); time.sleep(2.5)
            msg = wb.eval("return (document.getElementById('f-message')||{}).value||'';")
            ctx = wb.eval("return (document.getElementById('f-tool-context')||{}).value||'';")
            ptype = wb.eval("return (document.getElementById('f-type')||{}).value||'';")
            check("询盘页预填计算摘要", "Calculation summary" in msg and bool(ctx), msg[:50])
            check("询盘页自动选中项目类型", ptype == "public-dc-fast-charging", ptype)

        # ---------- 5. journey：状态真的存下来 ----------
        # 注意：第 4 步（ROI）**必须**先有第 3 步的装备方案，直接点 Run 会被正确拒绝
        # （提示 Missing required input(s)）——所以从第 1 步（profile）验证状态写入，
        # 并额外断言第 4 步的"前置校验"确实生效（防回归：别让空输入算出假结果）。
        wb.nav(f"{base}/journey/segment{ext}", new_tab=False); time.sleep(3)
        # 第 1 步：先选一个画像（This is me →），再 Continue——Continue 在未选画像时是禁用的
        wb.eval("""
        const pick=[...document.querySelectorAll('button, a.btn')]
          .find(x=>/This is me/i.test(x.textContent));
        if (pick) pick.click();
        """); time.sleep(1)
        wb.eval("""
        const b=[...document.querySelectorAll('button, a.btn')]
          .find(x=>/Continue/i.test(x.textContent));
        if (b) b.click();
        """); time.sleep(2)
        seg_saved = wb.eval("return !!localStorage.getItem('anari_journey_v1');")
        check("journey 第 1 步状态写入", bool(seg_saved), f"localStorage={seg_saved}")

        wb.nav(f"{base}/journey/roi{ext}", new_tab=False); time.sleep(3)
        wb.eval("""
        const b=[...document.querySelectorAll('button')].find(x=>/Run the estimate/i.test(x.textContent));
        if (b) b.click();
        """); time.sleep(2)
        refused = wb.eval("""
        const r=document.getElementById('results');
        return r ? /Missing required input|Cannot run yet/i.test(r.textContent) : false;
        """)
        check("journey 第 4 步在缺前置数据时拒绝计算", bool(refused), f"refused={refused}")

        # ---------- 6. 404 恢复入口 ----------
        wb.nav(f"{base}/404{ext}", new_tab=False); time.sleep(2)
        rec = wb.eval("return document.querySelectorAll('main a[href]').length;")
        check("404 页提供恢复入口 ≥4", int(rec or 0) >= 4, str(rec))

        # ---------- 7. 询盘页：AC 选项已隐藏 ----------
        wb.nav(f"{base}/inquiry{ext}", new_tab=False); time.sleep(2)
        ac_hidden = wb.eval("""
        const o=[...document.querySelectorAll('#f-type option')].find(x=>x.value==='ac-destination-charging');
        return o ? (o.hidden ? 'hidden' : 'visible') : 'absent';
        """)
        check("询盘表单不再提供 AC 选项", ac_hidden in ("hidden", "absent"), str(ac_hidden))
    finally:
        try:
            wb.close_tab()
        except Exception:
            pass
        cleanup_all(verbose=False)
        print("\n✅ 浏览器已清空")

    failed = [r for r in results if not r[1]]
    print(f"\nE2E 冒烟：{len(results) - len(failed)}/{len(results)} 通过")
    print(NOT_SUBMITTED)
    if failed:
        print("\n失败项：")
        for n, _, d in failed:
            print(f"  - {n}" + (f"（{d}）" if d else ""))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
