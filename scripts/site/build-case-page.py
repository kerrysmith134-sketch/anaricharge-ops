#!/usr/bin/env python3
"""build-case-page.py — 案例页生成器。

为什么要有它：一个案例页 440 行，其中 ~200 行是 JSON-LD（Article / BreadcrumbList /
FAQPage / CaseStudy）。手抄必错，而且 validate.js 会校验「FAQ schema 必须与可见文案
逐字一致」——两边分别手写迟早漂移。本生成器让 FAQ、面包屑、meta 都从同一份数据渲染，
schema 与正文天然一致。

用法:
  python3 scripts/site/build-case-page.py --spec scripts/site/cases-data.json --slug hot-climate
  python3 scripts/site/build-case-page.py --spec scripts/site/cases-data.json --all --dry

输入 spec 关键字段见文件末尾 SAMPLE / scripts/site/cases-data.json。
输出：<repo>/site/cases/<slug>.html
"""
import argparse
import html
import json
import os
import re
import sys

WS = "/Users/kerrychu/anari-charge-website"
FRAG = os.path.join(WS, "scripts", "site", "fragments")
REPO = os.path.join(WS, "06-site", "anari-new-site")
BASE = "https://www.anaricharge.com"
ORG_CONTACT = """{
          "@type": "ContactPoint",
          "contactType": "sales",
          "url": "https://www.linkedin.com/showcase/shenzhen-anari-energy-co-ltd",
          "email": "kerry@anaricharge.com",
          "availableLanguage": ["en", "ru", "es"],
          "areaServed": "Worldwide"
        }"""


def esc(s):
    return html.escape(s, quote=False)


def jsonld_str(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2)


def stat_band(stats):
    out = []
    for num, label in stats:
        out.append('        <div class="stat"><span class="stat-num">%s</span>'
                   '<span class="stat-label">%s</span></div>' % (esc(num), esc(label)))
    return "\n".join(out)


def table_block(t):
    if not t:
        return ""
    head = "".join('<th scope="col">%s</th>' % esc(h) for h in t["head"])
    rows = []
    for r in t["rows"]:
        cells = "".join("<td>%s</td>" % c if not str(c).startswith('<') else "<td>%s</td>" % c
                        for c in r)
        rows.append("          <tr>%s</tr>" % cells)
    return """
    <div class="table-wrap">
      <table class="data">
        <caption>%(caption)s</caption>
        <thead>
          <tr>%(head)s</tr>
        </thead>
        <tbody>
%(rows)s
        </tbody>
      </table>
    </div>""" % {"caption": esc(t["caption"]), "head": head, "rows": "\n".join(rows)}


def faq_visible(faq):
    out = []
    for qa in faq:
        out.append("""      <details class="faq-item">
        <summary>%s</summary>
        <p>%s</p>
      </details>""" % (esc(qa["q"]), qa["a"]))
    return "\n".join(out)


def build(spec):
    slug = spec["slug"]
    url = "%s/cases/%s" % (BASE, slug)
    faq = spec["faq"]
    img = spec["hero_image"]
    hero_base = spec.get("hero_basename", slug)
    img_w, img_h = spec.get("hero_size", [1000, 667])
    og_img = spec.get("og_image", img)

    nav = open(os.path.join(FRAG, "nav.html"), encoding="utf-8").read()
    footer = open(os.path.join(FRAG, "footer.html"), encoding="utf-8").read()

    # ---------------- JSON-LD ----------------
    article_ld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": spec["og_title"],
        "description": spec["article_description"],
        "datePublished": spec.get("date_published", "2026-11-07"),
        "dateModified": spec.get("date_modified", "2026-11-07"),
        "inLanguage": "en",
        "about": {"@type": "Thing", "name": spec["article_about"]},
        "author": {
            "@type": "Organization",
            "telephone": "+8618866205186",
            "name": "Anari Energy",
            "url": BASE + "/",
            "logo": {"@type": "ImageObject",
                     "url": BASE + "/assets/img/anari-icon.webp",
                     "width": 512, "height": 512},
            "legalName": "Shenzhen Anari Energy Co., Ltd.",
            "image": BASE + "/assets/img/og/cases-jordan-station.jpg",
            "contactPoint": json.loads("[" + ORG_CONTACT + "]"),
            "sameAs": ["https://www.anariev.com/",
                       "https://www.linkedin.com/showcase/shenzhen-anari-energy-co-ltd"],
        },
        "mainEntityOfPage": url,
    }
    breadcrumb_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Cases", "item": BASE + "/cases/"},
            {"@type": "ListItem", "position": 3, "name": spec["breadcrumb_name"], "item": url},
        ],
    }
    faq_ld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "dateModified": spec.get("date_modified", "2026-11-07"),
        "mainEntity": [
            {"@type": "Question", "name": qa["q"],
             "acceptedAnswer": {"@type": "Answer", "text": qa["a"]}}
            for qa in faq
        ],
    }
    case_ld = {
        "@context": "https://schema.org",
        "@type": "CaseStudy",
        "name": spec["case_name"],
        "about": {"@type": "Service", "serviceType": "Turnkey EV charging station delivery"},
        "provider": {
            "@type": "Organization",
            "telephone": "+8618866205186",
            "name": "Anari Energy",
            "url": BASE + "/",
            "logo": {"@type": "ImageObject",
                     "url": BASE + "/assets/img/anari-icon.webp", "width": 512, "height": 512},
            "legalName": "Shenzhen Anari Energy Co., Ltd.",
            "image": BASE + "/assets/img/og/cases-jordan-station.jpg",
            "contactPoint": json.loads("[" + ORG_CONTACT + "]"),
            "sameAs": ["https://www.anariev.com/",
                       "https://www.linkedin.com/showcase/shenzhen-anari-energy-co-ltd"],
        },
        "spatialCoverage": {"@type": "Place", "name": spec["place"]},
        "url": url,
        "description": spec["case_description"],
    }

    cards = "\n".join(
        '      <div class="card">\n        <p class="card-kicker">%s</p>\n        <p>%s</p>\n      </div>'
        % (esc(c["kicker"]), c["html"]) for c in spec["cards"])

    sections = []
    for s in spec["sections"]:
        sections.append("    <h2>%s</h2>\n%s" % (esc(s["h2"]), s["html"].strip()))
    sections_html = "\n\n".join(sections)

    deep = ""
    for d in spec.get("deep_dives", []):
        deep += """
    <details class="deep-dive">
      <summary>%s</summary>
%s
    </details>""" % (esc(d["summary"]), d["html"].strip())

    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{meta}">
  <link rel="canonical" href="{url}">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{og_title}">
  <meta property="og:description" content="{og_desc}">
  <meta property="og:url" content="{url}">
  <meta property="og:locale" content="en_US">
  <meta property="og:image" content="{og_img}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Anari Energy — turnkey EV charging and energy storage">
  <meta name="twitter:image" content="{og_img}">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%2326262b'/%3E%3Cpath d='M17.3 8 10 19.2h4.7L13 25l7.9-11.4h-4.8z' fill='%231078f0'/%3E%3C/svg%3E">
  <link rel="apple-touch-icon" sizes="180x180" href="/assets/img/apple-touch-icon.png">
  <link rel="stylesheet" href="/style.css">
  <script type="application/ld+json">
{article_ld}
  </script>
  <script type="application/ld+json">
{breadcrumb_ld}
  </script>
  <script type="application/ld+json">
{faq_ld}
  </script>
  <link rel="alternate" hreflang="en" href="{url}">
  <link rel="alternate" hreflang="x-default" href="{url}">
  <script src="/assets/js/nav.js" defer></script>
  <script src="/assets/js/track.js" defer></script>
  <script src="/assets/js/motion.js" defer></script>
  <script type="application/ld+json">
{case_ld}
  </script>
  <script src="/assets/js/lead-chat.js" defer></script>
  <script src="/assets/js/spotlight.js" defer></script>
</head>
{nav}

<main id="main">
  <nav class="breadcrumb wrap" aria-label="Breadcrumb">
    <ol>
      <li><a href="/">Home</a></li>
      <li><a href="/cases/">Cases</a></li>
      <li><span aria-current="page">{breadcrumb_name}</span></li>
    </ol>
  </nav>

  <section class="hero">
    <div class="wrap">
      <p class="eyebrow">{eyebrow}</p>
      <h1>{h1}</h1>
      <p class="lede">{lede}</p>
      <img class="hero-img" srcset="/assets/img/cases/{hero_base}-640.webp 640w, /assets/img/cases/{hero_base}.webp {img_w}w" sizes="(min-width: 1440px) 1360px, 100vw" src="/assets/img/cases/{hero_base}.webp" alt="{img_alt}" width="{img_w}" height="{img_h}" fetchpriority="high" decoding="async">
      <div class="stat-band">
{stats}
      </div>
      <div class="hero-actions">
        <a class="btn btn-primary" href="/inquiry">Plan a similar project</a>
      </div>
    </div>
  </section>

  <article class="article wrap">
    <div class="meta-row">
      <span class="badge-verified">Last verified: {date_modified}</span>
      <span class="meta-item">Source: Anari Energy delivery records</span>
    </div>

    <div class="tldr">
      <p class="tldr-label">{tldr_label}</p>
      <p>{tldr_html}</p>
    </div>

    <div class="grid grid-3">
{cards}
    </div>

{sections}
{deep}

    <h2>Frequently asked questions</h2>
{faq_visible}

    <div class="cta cta--inquiry">
      <div class="cta-body">
        <h3>{cta_h3}</h3>
        <p>{cta_p}</p>
      </div>
      <a class="btn btn-primary" href="/inquiry">Plan a similar project</a>
    </div>
  </article>
</main>

{footer}
""".format(
        title=esc(spec["title"]),
        meta=esc(spec["meta"]),
        og_title=esc(spec["og_title"]),
        og_desc=esc(spec["og_desc"]),
        url=url,
        og_img=BASE + og_img if og_img.startswith("/") else og_img,
        article_ld=jsonld_str(article_ld),
        breadcrumb_ld=jsonld_str(breadcrumb_ld),
        faq_ld=jsonld_str(faq_ld),
        case_ld=jsonld_str(case_ld),
        nav=nav,
        breadcrumb_name=esc(spec["breadcrumb_name"]),
        eyebrow=esc(spec["eyebrow"]),
        h1=esc(spec["h1"]),
        lede=esc(spec["lede"]),
        slug=slug,
        hero_base=hero_base,
        img_w=img_w, img_h=img_h,
        img_alt=esc(spec["hero_alt"]),
        stats=stat_band(spec["stats"]),
        tldr_label=esc(spec["tldr_label"]),
        tldr_html=spec["tldr_html"],
        cards=cards,
        sections=sections_html,
        deep=deep,
        faq_visible=faq_visible(faq),
        cta_h3=esc(spec["cta_h3"]),
        cta_p=esc(spec["cta_p"]),
        date_modified=spec.get("date_modified", "2026-11-07"),
        footer=footer,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--slug", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    spec = json.load(open(a.spec, encoding="utf-8"))
    cases = spec["cases"] if "cases" in spec else spec
    targets = list(cases.values()) if a.all else [cases[a.slug]]

    for c in targets:
        # 校验 frontmatter 级的硬约束
        if not (140 <= len(c["meta"]) <= 160):
            print("!! %s meta description %d 字符，必须 140-160" % (c["slug"], len(c["meta"])),
                  file=sys.stderr)
            return 2
        out = build(c)
        path = os.path.join(REPO, "site", "cases", c["slug"] + ".html")
        if a.dry:
            print("DRY %s (%d chars)" % (path, len(out)))
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(out)
            print("WROTE %s (%d chars)" % (path, len(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
