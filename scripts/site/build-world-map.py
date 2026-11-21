#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build-world-map.py — 从 Natural Earth（公有领域）生成站点用的世界地图 SVG

为什么要自己生成：
  1. 授权干净 —— Natural Earth 是 public domain，不引入 CC BY-SA 的传染与署名义务
  2. 投影自己定 —— 用等距圆柱投影（plate carrée），再用同一个投影算国家坐标点，
     **圆点与海岸线必然对齐**（现成地图底图无法保证这点）

输出：
  - site/assets/img/world-map-v2.svg   陆地轮廓（单 path，坐标取整，体积小）
  - 同时打印 22 个运营国的投影像素坐标，供页面组件摆放热点

用法：python3 scripts/site/build-world-map.py /tmp/ne110.geojson
"""
import json
import os
import sys

W, H = 1000, 500          # 2:1 等距圆柱，正好 -180..180 / -90..90
PREC = 0                  # 坐标小数位（1 位足够 1000px 宽，体积减半）

OUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "06-site/anari-new-site/site/assets/img/world-map-v2.svg",
)

# 运营国（22 国口径，来源：fact-library / 站点 AGENTS.md）
COUNTRIES = {
    "Jordan": (31.0, 36.0), "Lebanon": (33.9, 35.9), "Israel": (31.0, 34.9),
    "Oman": (21.5, 55.9), "Saudi Arabia": (24.0, 45.0), "United Arab Emirates": (24.0, 54.0),
    "Georgia": (42.0, 43.5), "Armenia": (40.1, 45.0), "Kazakhstan": (48.0, 67.0),
    "Uzbekistan": (41.4, 64.6), "Kyrgyzstan": (41.2, 74.8), "Tajikistan": (38.9, 71.3),
    "Romania": (45.9, 24.9), "Bulgaria": (42.7, 25.5), "Czechia": (49.8, 15.5),
    "Finland": (61.9, 25.7), "Cambodia": (12.6, 104.9), "Nepal": (28.4, 84.1),
    "Kenya": (-0.02, 37.9), "Ethiopia": (9.1, 40.5), "Ghana": (7.9, -1.0),
    "El Salvador": (13.8, -88.9),
}


def project(lon, lat):
    x = (lon + 180.0) / 360.0 * W
    y = (90.0 - lat) / 180.0 * H
    return round(x, PREC), round(y, PREC)


def polygon_ring(coords):
    pts = " ".join(f"{project(lon, lat)[0]},{project(lon, lat)[1]}" for lon, lat in coords)
    return f"M{pts}Z"


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ne110.geojson"
    data = json.load(open(src, encoding="utf-8"))
    parts = []
    for feat in data["features"]:
        # 南极洲跨 180° 经线，在等距圆柱投影里会被拉成一条横带（视觉像故障）；
        # 我们在南极没有业务，直接排除。
        if (feat.get("properties") or {}).get("ADMIN") == "Antarctica":
            continue
        geom = feat.get("geometry") or {}
        gtype = geom.get("type")
        coords = geom.get("coordinates")
        if not coords:
            continue
        rings = []
        if gtype == "Polygon":
            rings = coords
        elif gtype == "MultiPolygon":
            for poly in coords:
                rings.extend(poly)
        for ring in rings:
            if len(ring) < 5:
                continue
            # 顶点抽稀：1000px 画布上每 2 点取 1 点，视觉几乎无差，体积减半
            if len(ring) > 40:
                ring = ring[::2] + [ring[-1]]
            parts.append(polygon_ring(ring))
    path = "".join(parts)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'role="img" aria-label="World map">'
        f"<title>World map</title>"
        f'<path fill="#DCE4EE" fill-rule="evenodd" d="{path}"/>'
        f"</svg>"
    )
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"写出 {os.path.normpath(OUT)}  {len(svg) // 1024} KB  （{len(parts)} 个多边形环）")
    print("\n国家投影坐标（viewBox %d×%d，页面里按百分比摆放）：" % (W, H))
    for name, (lat, lon) in COUNTRIES.items():
        x, y = project(lon, lat)
        print(f'  {name:18s} x={x / W * 100:.1f}%  y={y / H * 100:.1f}%')


if __name__ == "__main__":
    main()
