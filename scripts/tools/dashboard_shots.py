#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dashboard_shots.py — 把运营仪表盘 HTML 截成 PNG（light / dark / top）。

## 为什么需要
用户 2026-11-09 明确要「仪表盘那种格式」的日报。仪表盘是单文件 HTML，
聊天里要看图，所以每晚生成 HTML 后顺手截三张图：
  - `-light.png` 整页（浅色）
  - `-dark.png`  整页（深色，用仪表盘自带的 `?theme=dark`）
  - `-top.png`  顶部核心区裁剪（1440×1240，聊天里直接看）

## 实现
用 **headless Chrome**（`--headless=new`），不用 WebBridge：
浏览器扩展不允许 file:// 导航（实测报 "Cannot navigate to a file URL without
local file access"）；headless + 独立 `--user-data-dir` 既能读本地文件、
又完全不碰用户的 Chrome 配置（不产生标签，R10 卫生天然满足）。
截图后按背景色裁掉底部空白，得到真实整页高度；失败只报错，不假装成功。

## 用法
  python3 scripts/tools/dashboard_shots.py --date 2026-11-09
  python3 scripts/tools/dashboard_shots.py --html 08-execution/dashboard/site-dashboard-2026-11-09.html
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DASH = os.path.join(WS, "08-execution", "dashboard")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def shot(url, out, width, height, profile):
    cmd = [CHROME, "--headless=new", "--no-sandbox", "--disable-gpu",
           "--disable-dev-shm-usage", "--disable-crash-reporter",
           "--hide-scrollbars",
           "--no-first-run", "--no-default-browser-check",
           "--force-device-scale-factor=1",
           "--user-data-dir=" + profile,
           "--screenshot=" + out,
           "--window-size=%d,%d" % (width, height),
           "--virtual-time-budget=6000",
           url]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if not os.path.exists(out) or os.path.getsize(out) < 5000:
        raise RuntimeError("截图失败 rc=%s stderr=%s" % (r.returncode, (r.stderr or "")[-300:]))
    return out



def make_dark_variant(html):
    """仪表盘没有 ?theme= 参数（暗色只认 localStorage / prefers-color-scheme），
    所以复制一份把取主题的那段替换成固定 dark，仅用于截图，不改原文件。"""
    src = open(html, encoding="utf-8").read()
    needle = "localStorage.getItem('anari-dash-theme')||'system'"
    if needle not in src:
        raise RuntimeError("找不到主题读取片段，无法生成暗色变体")
    out = os.path.join(tempfile.mkdtemp(prefix="anari-dash-dark-"),
                       "dark-" + os.path.basename(html))
    open(out, "w", encoding="utf-8").write(src.replace(needle, "'dark'"))
    return out


def trim_bottom(path, pad=24):
    """按左上角背景色裁掉底部空白，返回 (w, h_cropped)。"""
    from PIL import Image
    im = Image.open(path).convert("RGB")
    w, h = im.size
    bg = im.getpixel((w - 3, h - 3))
    px = im.load()
    last = 0
    for y in range(h - 1, -1, -1):
        row_diff = False
        for x in range(0, w, max(1, w // 60)):
            p = px[x, y]
            if abs(p[0] - bg[0]) + abs(p[1] - bg[1]) + abs(p[2] - bg[2]) > 12:
                row_diff = True
                break
        if row_diff:
            last = y
            break
    new_h = min(h, last + pad)
    if new_h < h:
        im.crop((0, 0, w, new_h)).save(path)
    return w, new_h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="")
    ap.add_argument("--html", default="")
    ap.add_argument("--width", type=int, default=1440)
    ap.add_argument("--height", type=int, default=9000)
    ap.add_argument("--top-height", type=int, default=1850)
    a = ap.parse_args()

    html = a.html or (os.path.join(DASH, "site-dashboard-%s.html" % a.date) if a.date else "")
    if not html or not os.path.exists(html):
        print("HTML 不存在：%s（先跑 build_site_dashboard.py）" % (html or "(未指定)"))
        return 2
    date = a.date or os.path.basename(html).replace("site-dashboard-", "").replace(".html", "")
    prefix = os.path.join(DASH, "site-dashboard-%s" % date)
    base = "file://" + os.path.abspath(html)

    result = {"date": date, "html": os.path.relpath(html, WS), "shots": {}, "dims": {}}
    profile = tempfile.mkdtemp(prefix="anari-dash-chrome-")
    try:
        light = prefix + "-light.png"
        shot(base, light, a.width, a.height, profile)
        w, h = trim_bottom(light)
        result["shots"]["light"] = os.path.relpath(light, WS)
        result["dims"]["full"] = [w, h]

        dark_html = make_dark_variant(html)
        dark = prefix + "-dark.png"
        shot("file://" + os.path.abspath(dark_html), dark, a.width, a.height, profile)
        trim_bottom(dark)
        result["shots"]["dark"] = os.path.relpath(dark, WS)

        from PIL import Image
        top = prefix + "-top.png"
        Image.open(light).crop((0, 0, w, min(a.top_height, h))).save(top)
        result["shots"]["top"] = os.path.relpath(top, WS)
        result["dims"]["top"] = [w, min(a.top_height, h)]
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:300])},
                         ensure_ascii=False))
        return 1
    finally:
        subprocess.run(["rm", "-rf", profile], capture_output=True)

    result["ok"] = True
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
