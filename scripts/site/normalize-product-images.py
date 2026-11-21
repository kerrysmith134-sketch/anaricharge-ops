#!/usr/bin/env python3
"""normalize-product-images.py — 产品主图统一白底 / 统一比例 / 统一视觉尺度。

## 为什么
用户决定 Products 页走「统一白底」。现有主图是**纯黑底渲染**（角落 RGB 0,0,0），
而颜色/裁切/产品占比各不相同 → 排成网格时参差不齐，这是"工业感"掉分的主要原因。

## 做法（纯 PIL，无 numpy/scipy 依赖）
1. **从四边泛洪**标记与边缘连通的近黑像素为背景 → 只去掉背景，
   产品内部的黑色部件（顶盖、线缆、机身黑条）因为不与边缘连通而被保留。
2. 对透明结果取内容外框（bbox）。
3. 统一画布 3:2（如 1800×1200），产品高度 = 画布高的 72%，水平居中，
   底部留固定基线边距 → 网格里每台机器看起来"同一台称上的东西"。
4. 输出 WebP 三档（master 1800 / 1024 / 640）+ 联络表供目视 QA。

## 用法
  python3 scripts/site/normalize-product-images.py --dry      # 只报告
  python3 scripts/site/normalize-product-images.py            # 生成到 products/v2/
  python3 scripts/site/normalize-product-images.py --sheet    # 额外出联络表
"""
import argparse
import glob
import os
import sys
from collections import deque

from PIL import Image, ImageDraw

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(WS, "06-site/anari-new-site/site/assets/img/products")
OUT = os.path.join(SRC, "v2")
SHEET = os.path.join(WS, "08-execution/materials/product-sheet.jpg")

# 10 个产品族的主图（不带 -640/-1024、不含 detail/scene）
SKIP_SUFFIX = ("-640", "-1024")
SKIP_WORDS = ("detail", "scene")

CANVAS_W, CANVAS_H = 1800, 1200     # 3:2
PRODUCT_H_RATIO = 0.72              # 产品高度占画布高
BG = (255, 255, 255)
THRESHOLD = 26                      # 近黑判定
MIN_BG_RATIO, MAX_BG_RATIO = 0.15, 0.97   # 超出范围 → 人工复核


def masters():
    out = []
    for p in sorted(glob.glob(os.path.join(SRC, "*.webp"))):
        name = os.path.splitext(os.path.basename(p))[0]
        if any(name.endswith(s) for s in SKIP_SUFFIX):
            continue
        if any(w in name for w in SKIP_WORDS):
            continue
        out.append((name, p))
    return out


def load_alpha_or_cut(im):
    """优先用源图自带 alpha；没有有效 alpha 才回退到泛洪抠图。"""
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        rgba = im.convert("RGBA")
        a = rgba.getchannel("A")
        hist = a.histogram()
        total = rgba.size[0] * rgba.size[1]
        transparent = sum(hist[:8])
        if transparent / total > 0.15:          # 有明显透明区 → 可信 alpha
            return rgba, transparent / total, "alpha"
    corner = im.convert("RGB").getpixel((2, 2))
    if all(c >= 246 for c in corner):
        rgba, ratio = cut_white_background(im)
        return rgba, ratio, "white-key"
    rgba, ratio = cut_background(im)
    return rgba, ratio, "black-key"


def cut_white_background(im):
    """白底源图：从四边泛洪掉近白像素，得到同样的透明主体。"""
    im = im.convert("RGB")
    w, h = im.size
    px = im.load()
    visited = bytearray(w * h)
    dq = deque()

    def push(x, y):
        i = y * w + x
        if visited[i]:
            return
        r, g, b = px[x, y]
        if r >= 246 and g >= 246 and b >= 246:      # 近白
            visited[i] = 1
            dq.append((x, y))

    for x in range(w):
        push(x, 0)
        push(x, h - 1)
    for y in range(h):
        push(0, y)
        push(w - 1, y)
    while dq:
        x, y = dq.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                push(nx, ny)
    alpha = Image.new("L", (w, h), 255)
    ap = alpha.load()
    for y in range(h):
        base = y * w
        for x in range(w):
            if visited[base + x]:
                ap[x, y] = 0
    out = im.convert("RGBA")
    out.putalpha(alpha)
    return out, sum(visited) / (w * h)


def cut_background(im):
    """从四边泛洪去掉与边缘连通的近黑背景，返回 RGBA。"""
    im = im.convert("RGB")
    w, h = im.size
    px = im.load()
    visited = bytearray(w * h)
    dq = deque()

    def push(x, y):
        i = y * w + x
        if visited[i]:
            return
        r, g, b = px[x, y]
        if r < THRESHOLD and g < THRESHOLD and b < THRESHOLD:
            visited[i] = 1
            dq.append((x, y))

    for x in range(w):
        push(x, 0)
        push(x, h - 1)
    for y in range(h):
        push(0, y)
        push(w - 1, y)
    while dq:
        x, y = dq.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                push(nx, ny)

    bg_ratio = sum(visited) / (w * h)
    alpha = Image.new("L", (w, h), 255)
    ap = alpha.load()
    for y in range(h):
        base = y * w
        for x in range(w):
            if visited[base + x]:
                ap[x, y] = 0
    out = im.convert("RGBA")
    out.putalpha(alpha)
    return out, bg_ratio


def compose(rgba):
    """按统一尺度把产品摆进白底画布。"""
    bbox = rgba.getbbox()
    if not bbox:
        return None
    obj = rgba.crop(bbox)
    target_h = int(CANVAS_H * PRODUCT_H_RATIO)
    scale = target_h / obj.height
    new_w = max(1, int(obj.width * scale))
    obj = obj.resize((new_w, target_h), Image.LANCZOS)

    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), BG)
    x = (CANVAS_W - new_w) // 2
    # 底部基线：所有产品底部对齐到同一留白
    bottom_margin = int(CANVAS_H * 0.14)
    y = CANVAS_H - bottom_margin - target_h

    # 接触阴影：椭圆形径向渐变，让白底产品"落地"而不是漂浮。
    # 只在基线上方一点点，宽度略窄于产品，透明度很低——过重会显脏。
    sh_w = max(60, int(new_w * 0.86))
    sh_h = max(14, int(target_h * 0.045))
    shadow = Image.new("L", (sh_w, sh_h), 0)
    for yy in range(sh_h):
        for xx in range(sh_w):
            nx = (xx - sh_w / 2) / (sh_w / 2)
            ny = (yy - sh_h / 2) / (sh_h / 2)
            d = (nx * nx + ny * ny) ** 0.5
            v = max(0.0, 1.0 - d)
            shadow.putpixel((xx, yy), int(255 * (v ** 2.2) * 0.22))
    shade = Image.new("RGB", (sh_w, sh_h), (38, 38, 43))
    canvas.paste(shade, (x + (new_w - sh_w) // 2,
                         y + target_h - sh_h // 2), shadow)

    canvas.paste(obj, (x, y), obj)
    return canvas


def save_variants(img, name):
    os.makedirs(OUT, exist_ok=True)
    paths = []
    for suffix, width in (("", 1800), ("-1024", 1024), ("-640", 640)):
        im = img if width == CANVAS_W else img.resize(
            (width, round(width * CANVAS_H / CANVAS_W)), Image.LANCZOS)
        p = os.path.join(OUT, f"{name}{suffix}.webp")
        im.save(p, "WEBP", quality=90, method=6)
        paths.append(p)
    return paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--sheet", action="store_true")
    a = ap.parse_args()

    ms = masters()
    print(f"主图 {len(ms)} 张 → 画布 {CANVAS_W}×{CANVAS_H}（3:2），产品高 {PRODUCT_H_RATIO:.0%}")
    review, done = [], []
    for name, path in ms:
        im = Image.open(path)
        # 源图是 RGBA 渲染（自带高质量 alpha）→ 直接用，不要抠图。
        # 早期版本把 RGBA 压平后当成"纯黑底"去泛洪，会把机身黑色部件（线缆、侧板）
        # 一起吃掉——这才是产品看起来"缺一块"的原因。
        rgba, bg_ratio, src_kind = load_alpha_or_cut(im)
        if not (MIN_BG_RATIO <= bg_ratio <= MAX_BG_RATIO):
            review.append((name, round(bg_ratio * 100, 1),
                           "背景占比异常（黑底/白底都不匹配）"))
            continue
        canvas = compose(rgba)
        if canvas is None:
            review.append((name, round(bg_ratio * 100, 1), "内容框为空"))
            continue
        if a.dry:
            print(f"  [dry] {name:28s} 透明 {bg_ratio*100:5.1f}% ({src_kind}) → 将输出 3 档")
        else:
            save_variants(canvas, name)
            print(f"  ✅ {name:28s} 透明 {bg_ratio*100:5.1f}% ({src_kind})")
        done.append((name, canvas if canvas else None))

    if review:
        print("\n需要人工复核：")
        for n, r, why in review:
            print(f"  ⚠️ {n}  {r}%  {why}")

    if a.sheet and done and not a.dry:
        cols, rows = 5, 2
        tw, th = 360, 240
        sheet = Image.new("RGB", (cols * tw, rows * th), "#f6f8fb")
        d = ImageDraw.Draw(sheet)
        for i, (name, canvas) in enumerate(done[:cols * rows]):
            if canvas is None:
                continue
            thumb = canvas.copy()
            thumb.thumbnail((tw - 12, th - 34))
            x = (i % cols) * tw + 6
            y = (i // cols) * th + 26
            sheet.paste(thumb, (x, y))
            d.text((x, y - 16), name, fill="#26262b")
        os.makedirs(os.path.dirname(SHEET), exist_ok=True)
        sheet.save(SHEET, "JPEG", quality=88)
        print(f"\n联络表 → {SHEET}")
    print(f"\n完成 {len(done)} / {len(ms)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
