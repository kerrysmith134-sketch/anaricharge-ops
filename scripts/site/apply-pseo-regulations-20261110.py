#!/usr/bin/env python3
"""apply-pseo-regulations-20261110.py — 把 14 个法规页接入站内入口。

做三件事（幂等，带 marker）：
  1. /regulations/ hub 新增「Country approval paths」区段（14 张卡，按区域排序）
  2. /journey/compliance 加「Country approval paths」related 区块（14 条）
  3. /regulations/eu-afir 加「AFIR member states in this set」related 区块（3 条）
  4. 打印每页入链统计（hub=1 + 非本族）
用法：python3 scripts/site/apply-pseo-regulations-20261110.py [--dry]
"""
import glob
import json
import os
import re
import sys

WS = "/Users/kerrychu/anari-charge-website"
SITE = os.path.join(WS, "06-site", "anari-new-site", "site")
SPECS = [
    "scripts/site/pseo/regulations-me.json",
    "scripts/site/pseo/regulations-cca.json",
    "scripts/site/pseo/regulations-eu-af.json",
]
MARK = "pseo-regs-20261110"
DRY = "--dry" in sys.argv

REGION_ORDER = ["Middle East", "Caucasus & Central Asia", "Europe", "Africa"]
REGION_LABEL = {"Middle East": "Middle East", "Caucasus & Central Asia": "Caucasus & Central Asia",
                "Europe": "Europe", "Africa": "Africa"}


def load_pages():
    pages = []
    for sp in SPECS:
        fam = json.load(open(os.path.join(WS, sp), encoding="utf-8"))
        pages.extend(fam["pages"])
    return pages


def card(p):
    tldr = re.split(r"(?<=[.!?])\s+", p.get("tldr", "").strip())[0]
    if len(tldr) > 105:
        tldr = tldr[:102].rsplit(" ", 1)[0] + "…"
    return ('        <div class="card">\n'
            '          <h3>%s</h3>\n'
            '          <p>%s</p>\n'
            '          <a class="card-link" href="/regulations/%s">Approval path for %s</a>\n'
            '        </div>' % (p["country"], tldr, p["slug"], p["country"]))


def main():
    pages = load_pages()
    by_region = {r: [] for r in REGION_ORDER}
    for p in pages:
        by_region.setdefault(p.get("region", "Other"), []).append(p)

    # 1) hub
    hub = os.path.join(SITE, "regulations", "index.html")
    s = open(hub, encoding="utf-8").read()
    if MARK + "-hub" not in s:
        blocks = []
        for r in REGION_ORDER:
            if not by_region.get(r):
                continue
            blocks.append('          <p class="eyebrow" style="grid-column:1/-1;margin:8px 0 0">%s</p>' % r)
            blocks.extend(card(p) for p in sorted(by_region[r], key=lambda x: x["country"]))
        section = f'''  <!-- {MARK}-hub -->
  <section class="section">
    <div class="wrap">
      <div class="section-head">
        <p class="eyebrow">Country approval paths</p>
        <h2>What a charging site has to clear, country by country</h2>
        <p>Fourteen delivered markets, each mapped as an approval sequence: who approves, what they ask for, and where the schedule usually dies. These pages are engineering and permitting experience, not legal advice — confirm against the regulator in writing before you sign.</p>
      </div>
      <div class="grid grid-3">
{chr(10).join(blocks)}
      </div>
    </div>
  </section>

'''
        anchor = '  <section class="section">\n    <div class="wrap">\n      <div class="section-head">\n        <p class="eyebrow">Related reading</p>\n        <h2>Go deeper</h2>'
        if anchor not in s:
            print("✗ hub anchor not found"); return 1
        s = s.replace(anchor, section + anchor, 1)
        if DRY:
            print("[dry] hub: +%d cards" % len(pages))
        else:
            open(hub, "w", encoding="utf-8").write(s)
            print("✓ hub: +%d country cards" % len(pages))
    else:
        print("· hub already updated")

    # 2) journey/compliance
    comp = os.path.join(SITE, "blog", "ev-charging-grid-connection-requirements.html")
    s = open(comp, encoding="utf-8").read()
    if MARK + "-gridblog" not in s:
        lis = "\n".join('      <li><a href="/regulations/%s">%s — %s</a></li>'
                        % (p["slug"], p["country"], "%s" % p.get("regulator", "approval path"))
                        for p in sorted(pages, key=lambda x: (REGION_ORDER.index(x.get("region", "Europe"))
                                                             if x.get("region") in REGION_ORDER else 9, x["country"])))
        block = f'''  <!-- {MARK}-gridblog -->
  <section class="related wrap">
    <h2>Country approval paths</h2>
    <ul>
{lis}
    </ul>
  </section>
'''
        if "</main>" not in s:
            print("✗ grid-connection blog has no </main>"); return 1
        s = s.replace("</main>", block + "</main>", 1)
        if DRY:
            print("[dry] grid-connection blog: +%d links" % len(pages))
        else:
            open(comp, "w", encoding="utf-8").write(s)
            print("✓ grid-connection blog: +%d links" % len(pages))
    else:
        print("· grid-connection blog already linked")

    # 3) eu-afir
    afir = os.path.join(SITE, "regulations", "eu-afir.html")
    s = open(afir, encoding="utf-8").read()
    if MARK + "-afir" not in s:
        eu = [p for p in pages if p["slug"] in ("bulgaria", "czechia", "finland")]
        lis = "\n".join('      <li><a href="/regulations/%s">%s — national approval path</a></li>'
                        % (p["slug"], p["country"]) for p in eu)
        block = f'''  <!-- {MARK}-afir -->
  <section class="related wrap">
    <h2>AFIR member states in this set</h2>
    <ul>
{lis}
    </ul>
  </section>
'''
        s = s.replace("</main>", block + "</main>", 1)
        if DRY:
            print("[dry] eu-afir: +%d links" % len(eu))
        else:
            open(afir, "w", encoding="utf-8").write(s)
            print("✓ eu-afir: +%d links" % len(eu))
    else:
        print("· eu-afir already linked")

    if DRY:
        return 0

    # 4) 入链统计
    print("\n=== 法规页入链统计（hub + 非本族）===")
    allp = [(f, open(f, encoding="utf-8", errors="replace").read())
            for f in glob.glob(os.path.join(SITE, "**", "*.html"), recursive=True)]
    for p in pages:
        target = "/regulations/" + p["slug"]
        nonfam = 0
        for f, t in allp:
            rel = "/" + os.path.relpath(f, SITE).replace(os.sep, "/")
            if rel == target + ".html" or rel.startswith("/regulations/"):
                continue
            if ('href="%s"' % target) in t:
                nonfam += 1
        print("  %-18s hub=1  non-family=%d" % (p["slug"], nonfam))
    return 0


if __name__ == "__main__":
    sys.exit(main())
