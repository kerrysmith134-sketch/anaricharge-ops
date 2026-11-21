#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""postprocess-specs.py — 对生成后的 v2 页面规格做**幂等后处理**

为什么不直接改 gen-*.py：
  本轮我三次手工往生成脚本里插代码，两次插错层级（缩进/位置）导致
  SyntaxError 或 section 缺 type。生成脚本里的内容字典已经很大，
  再手工插行风险高。所以把「补充/修正」统一放到这里：读 JSON → 改 → 写回，
  幂等且可验证。

当前处理：
  1. RU/ES 案例中心页补齐全部 9 个案例卡（此前只有 6 个 → 3 个本地化案例页成孤儿）
"""
import json
import os

PAGES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pages")

CASES = [
    ("hot-climate", "scene-hotclimate-640.webp",
     ("Жара и влажность: непрерывная работа", "Calor y humedad: servicio continuo"),
     ("Термоуправление и защита от воды в сезон муссонов.",
      "Gestión térmica y control de agua en temporada de monzón.")),
    ("ac-wallbox-deployments", "scene-destination-640.webp",
     ("AC 22 кВт в пяти странах", "AC de 22 kW en cinco países"),
     ("Одно изделие для Омана, Кипра, Перу, Италии и Турции.",
      "Un producto para Omán, Chipre, Perú, Italia y Türkiye.")),
    ("emerging-markets", "scene-commercial-640.webp",
     ("Политика раньше сети", "La política antes que la red"),
     ("Эфиопия, Болгария, Сальвадор: спрос есть, инфраструктуры нет.",
      "Etiopía, Bulgaria, El Salvador: demanda sí, infraestructura no.")),
]

changed = 0
for loc, idx in (("ru", 0), ("es", 1)):
    p = os.path.join(PAGES, loc, "cases.json")
    d = json.load(open(p, encoding="utf-8"))
    grid = next((s for s in d["sections"] if s.get("type") == "sceneGrid"), None)
    if not grid:
        print(f"{loc}/cases.json 没有 sceneGrid，跳过")
        continue
    have = {i["href"] for i in grid["items"]}
    added = 0
    for slug, img, titles, texts in CASES:
        href = f"/{loc}/cases/{slug}"
        if href in have:
            continue
        grid["items"].append({
            "href": href,
            "image": f"/assets/img/v2/{img}",
            "title": titles[idx],
            "text": texts[idx],
        })
        added += 1
    if added:
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        changed += 1
    print(f"  {loc}/cases.json: 补 {added} 个案例卡（现有 {len(grid['items'])}）")

print(f"\n后处理完成：{changed} 个规格被修改")

# ---------------------------------------------------------------------------
# 2026-11-08：AC 全线下架（用户决策"只保留直流"）→ 22 kW 落地机案例同步下架
# 案例册里留着 AC 交付，等于在产品页说只做 DC、在案例里说我们交付 AC，自相矛盾。
# ---------------------------------------------------------------------------
DROP_CASES = {"ac-wallbox-deployments"}
for _loc in ("en", "ru", "es"):
    _p = os.path.join(PAGES, "cases.json") if _loc == "en" else os.path.join(PAGES, _loc, "cases.json")
    if not os.path.exists(_p):
        continue
    _d = json.load(open(_p, encoding="utf-8"))
    _n = 0
    for _s in _d.get("sections", []):
        if _s.get("type") != "sceneGrid":
            continue
        _keep = [i for i in _s["items"] if i["href"].rstrip("/").split("/")[-1] not in DROP_CASES]
        _n += len(_s["items"]) - len(_keep)
        _s["items"] = _keep
        if "nol" in (_s.get("h2") or "").lower():       # "nine cases" 一类文案
            _s["h2"] = _s["h2"].replace("Nine", "Eight").replace("nine", "eight")
            _s["h2"] = _s["h2"].replace("Девять", "Восемь").replace("Nueve", "Ocho")
    if _n:
        with open(_p, "w", encoding="utf-8") as _f:
            json.dump(_d, _f, ensure_ascii=False, indent=2)
        print(f"  {_p}: 下架 {_n} 个 AC 案例卡")
