#!/usr/bin/env python3
"""apply-pseo-batch-20261110.py — 把本批 30 个国别页接入站内入口。

做三件事（全部幂等，带 marker，可重复跑）：
  1. /markets/ hub：按区域追加 5 个「country guides」区段（30 条链接）
  2. 非本族入链：cases / journey / regulations / data / blog 页面各加一个
     「Market guides」related 区块（严格只加在相关语境里）
  3. 打印每页入链统计（hub + 非本族）供批次记录引用

用法：python3 scripts/site/apply-pseo-batch-20261110.py [--dry]
"""
import glob
import os
import re
import sys

WS = "/Users/kerrychu/anari-charge-website"
SITE = os.path.join(WS, "06-site", "anari-new-site", "site")
MARK = "pseo-batch-20261110"
DRY = "--dry" in sys.argv

# slug -> (显示名, hub 卡片一句话)
GUIDES = {
    # Middle East (delivered)
    "lebanon": ("Lebanon", "EDL shortfalls, generator economics and storage-first sites."),
    "israel": ("Israel", "45 °C summers, a capacity queue and a mature operator market."),
    "saudi-arabia": ("Saudi Arabia", "SEC capacity, 50 °C design points and SASO/SABER."),
    "uae": ("United Arab Emirates", "DEWA/ADDC areas, 45 °C+ heat and ESMA compliance."),
    "oman": ("Oman", "APSR rules, 45 °C+ heat and early corridor sites."),
    # Caucasus & Central Asia (delivered)
    "armenia": ("Armenia", "EAEU certification, 220 V grid and −25 °C winters."),
    "uzbekistan": ("Uzbekistan", "Chinese EV imports, GB/T and CCS2 side by side."),
    "kyrgyzstan": ("Kyrgyzstan", "EAEU rules, mountain corridors and −30 °C cold."),
    "tajikistan": ("Tajikistan", "Winter power deficits make storage the first decision."),
    # Europe (delivered)
    "bulgaria": ("Bulgaria", "CE + AFIR, KEVR and −20 °C winter operation."),
    "czechia": ("Czechia", "Delivered bus depot, AFIR timing and sub-zero nights."),
    "finland": ("Finland", "−30 °C design, high EV penetration and AFIR."),
    # Africa (delivered)
    "ethiopia": ("Ethiopia", "An ICE import ban, a hydro grid and weak reliability."),
    "ghana": ("Ghana", "GRIDCo/ECG reality, humidity and storage-first design."),
    # Target markets (market intelligence)
    "egypt": ("Egypt", "EEHC capacity, 40 °C+ heat and a young EV policy."),
    "nigeria": ("Nigeria", "DisCo reliability, generator economics and SONCAP."),
    "south-africa": ("South Africa", "Load-shedding history turns sites storage-first."),
    "morocco": ("Morocco", "ONEE grid, IMANOR rules and EU-adjacent supply."),
    "turkey": ("Türkiye", "CE via the customs union and a fast-growing EV base."),
    "india": ("India", "BIS IS 17017, 45 °C+ heat and Bharat DC-001 alongside CCS2."),
    "indonesia": ("Indonesia", "PLN capacity and a two-wheeler-led EV base."),
    "vietnam": ("Vietnam", "EVN grid, two-wheeler scale and CCS2/GB-T imports."),
    "pakistan": ("Pakistan", "NEPRA rules, outages and 45 °C+ summers."),
    "bangladesh": ("Bangladesh", "Easy-bike scale, BERC rules and monsoon humidity."),
    "sri-lanka": ("Sri Lanka", "CEB/PUCSL reality, 2022 crisis lessons and heat."),
    "thailand": ("Thailand", "Chinese OEM localisation, TISI and 230 V/50 Hz."),
    "philippines": ("Philippines", "A 230 V / 60 Hz grid — the only one in this set."),
    "malaysia": ("Malaysia", "TNB capacity, SIRIM approval and humid heat."),
    "iraq": ("Iraq", "50 °C+ summers, generator economy and storage-first sites."),
    "azerbaijan": ("Azerbaijan", "Azerenerji grid, Caspian corridor and AZSTAND."),
}

GROUPS = [
    ("Middle East", "Delivered market", ["lebanon", "israel", "saudi-arabia", "uae", "oman"]),
    ("Caucasus & Central Asia", "Delivered market",
     ["armenia", "uzbekistan", "kyrgyzstan", "tajikistan"]),
    ("Europe", "Delivered market", ["bulgaria", "czechia", "finland"]),
    ("Africa", "Delivered market", ["ethiopia", "ghana"]),
    ("Market intelligence", "Not yet a delivered footprint", [
        "egypt", "nigeria", "south-africa", "morocco", "turkey", "india", "indonesia",
        "vietnam", "pakistan", "bangladesh", "sri-lanka", "thailand", "philippines",
        "malaysia", "iraq", "azerbaijan"]),
]

# 非本族页面 -> (区块标题, [(slug, 语境标签)])
INLINKS = {
    "cases/hot-climate.html": ("Hot-climate markets", [
        ("israel", "Israel — the deployment behind this case"),
        ("saudi-arabia", "Saudi Arabia — three-gun hot-climate sites"),
        ("uae", "United Arab Emirates — DEWA-era heat and capacity"),
        ("oman", "Oman — 45 °C+ sites on the same design basis"),
    ]),
    "cases/cold-climate.html": ("Cold-climate markets", [
        ("armenia", "Armenia — EAEU certification and −25 °C operation"),
        ("kyrgyzstan", "Kyrgyzstan — mountain corridors at −30 °C"),
        ("tajikistan", "Tajikistan — winter deficits and storage-first design"),
        ("uzbekistan", "Uzbekistan — GB/T imports and cold snaps"),
    ]),
    "cases/bus-depot-czechia.html": ("Market guide", [
        ("czechia", "Czechia — AFIR timing and sub-zero depot nights"),
    ]),
    "cases/emerging-markets.html": ("Market guides", [
        ("ethiopia", "Ethiopia — ICE import ban and a hydro grid"),
        ("bulgaria", "Bulgaria — CE + AFIR and KEVR"),
    ]),
    "journey/market-site.html": ("Market guides for step 2", [
        ("israel", "Israel"), ("lebanon", "Lebanon"),
        ("armenia", "Armenia"), ("ghana", "Ghana"),
    ]),
    "regulations/eu-afir.html": ("AFIR applies in these guides", [
        ("bulgaria", "Bulgaria"), ("czechia", "Czechia"), ("finland", "Finland"),
    ]),
    "data/findings-2026.html": ("Country briefs anchored on these findings", [
        ("israel", "Israel"), ("saudi-arabia", "Saudi Arabia"),
        ("czechia", "Czechia"), ("ethiopia", "Ethiopia"), ("bulgaria", "Bulgaria"),
    ]),
    "data/hot-climate-charging.html": ("Hot-climate market guides", [
        ("egypt", "Egypt"), ("iraq", "Iraq"), ("pakistan", "Pakistan"),
        ("indonesia", "Indonesia"), ("thailand", "Thailand"), ("malaysia", "Malaysia"),
    ]),
    "blog/buying-ev-chargers-from-china.html": ("Where those imports land", [
        ("vietnam", "Vietnam"), ("indonesia", "Indonesia"), ("thailand", "Thailand"),
        ("philippines", "Philippines"), ("malaysia", "Malaysia"),
        ("bangladesh", "Bangladesh"), ("sri-lanka", "Sri Lanka"),
        ("morocco", "Morocco"), ("turkey", "Türkiye"),
    ]),
    "blog/ev-charging-station-dealership-india.html": ("Market guide", [
        ("india", "India — certification, heat and policy"),
    ]),
    "blog/ev-charging-station-franchise-cost-india.html": ("Market guide", [
        ("india", "India — certification, heat and policy"),
    ]),
    "blog/india-vs-uae-ev-charging-franchise-roi.html": ("Market guides", [
        ("india", "India"), ("uae", "United Arab Emirates"),
    ]),
    "blog/ev-charging-franchise-kenya.html": ("African market guides", [
        ("nigeria", "Nigeria"), ("south-africa", "South Africa"),
        ("ghana", "Ghana"), ("ethiopia", "Ethiopia"),
    ]),
}


def hub_group_html(region, note, slugs):
    cards = "\n".join(
        '        <a class="v2-cap" href="/markets/%s"><b>%s</b><p>%s</p></a>'
        % (s, GUIDES[s][0], GUIDES[s][1]) for s in slugs)
    eyebrow = region if note == "Delivered market" else "Market intelligence"
    title = ("%s: country guides" % region) if note == "Delivered market" \
        else "Countries we are watching — %s" % region
    intro = ("Delivered markets in this region — each guide is anchored on what actually decided a "
             "project there." if note == "Delivered market" else
             "Market intelligence only — we have not delivered in these countries yet. The guides "
             "set out the constraint that would decide a first project.")
    return f'''  <!-- {MARK}-hub -->
  <section class="v2-section v2-section--alt">
    <div class="v2-wrap">
      <div class="v2-section-head">
        <p class="v2-eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
        <p>{intro}</p>
      </div>
      <div class="v2-capabilities">
{cards}
      </div>
    </div>
  </section>
'''


def related_block(title, items):
    lis = "\n".join('      <li><a href="/markets/%s">%s</a></li>' % (s, label)
                    for s, label in items)
    return f'''  <!-- {MARK} -->
  <section class="related wrap" aria-labelledby="{MARK}-h">
    <h2 id="{MARK}-h">{title}</h2>
    <ul>
{lis}
    </ul>
  </section>
'''


def main():
    ok = True
    # 1) hub
    hub = os.path.join(SITE, "markets", "index.html")
    s = open(hub, encoding="utf-8").read()
    if MARK + "-hub" not in s:
        blocks = "\n".join(hub_group_html(r, n, ss) for r, n, ss in GROUPS)
        anchor = '  <section class="v2-section">\n    <div class="v2-wrap">\n      <div class="v2-section-head">\n        <p class="v2-eyebrow">How to read a market</p>'
        if anchor not in s:
            print("✗ hub anchor not found"); ok = False
        else:
            new = s.replace(anchor, blocks + "\n" + anchor, 1)
            if DRY:
                print("[dry] hub: +%d sections" % len(GROUPS))
            else:
                open(hub, "w", encoding="utf-8").write(new)
                print("✓ hub updated: +%d sections (%d links)" % (
                    len(GROUPS), sum(len(g[2]) for g in GROUPS)))
    else:
        print("· hub already updated")

    # 2) non-family inlinks
    for rel, (title, items) in INLINKS.items():
        path = os.path.join(SITE, rel)
        if not os.path.isfile(path):
            print("✗ missing page:", rel); ok = False; continue
        s = open(path, encoding="utf-8").read()
        if MARK in s:
            print("· %s already linked" % rel); continue
        if "</main>" not in s:
            print("✗ no </main> in", rel); ok = False; continue
        if DRY:
            print("[dry] %s: +%d links" % (rel, len(items)))
            continue
        s = s.replace("</main>", related_block(title, items) + "</main>", 1)
        open(path, "w", encoding="utf-8").write(s)
        print("✓ %s: +%d links" % (rel, len(items)))

    if DRY:
        return 0 if ok else 1

    # 3) 入链统计
    print("\n=== 每页入链统计（hub 1 条 + 非本族）===")
    pages = [(f, open(f, encoding="utf-8", errors="replace").read())
             for f in glob.glob(os.path.join(SITE, "**", "*.html"), recursive=True)]
    for slug in GUIDES:
        target = "/markets/" + slug
        ins_other = 0
        for f, t in pages:
            rel = "/" + os.path.relpath(f, SITE).replace(os.sep, "/")
            if rel == target + ".html":
                continue
            if rel.startswith("/markets/"):
                continue  # 族内不算
            if ('href="%s"' % target) in t:
                ins_other += 1
        print("  %-18s hub=1  non-family=%d" % (slug, ins_other))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
