#!/usr/bin/env python3
"""build-market-pages.py — F1 国别市场页生成器（市场族专用）。

为什么不直接用 build-pages.py：那个生成器的模板是 cost 族专用的
（面包屑写死 "Cost guides"、schema about 写死 "DC fast charging station cost"、
CTA 写 "Planning a {power} site?"）。套到国别页会产生错误的面包屑与结构化数据。

本生成器只做 F1 族：
  - 输入 scripts/site/pseo/markets-<family>.json（一份数据 → N 页）
  - 输出 06-site/anari-new-site/site/markets/<slug>.html（URL /markets/<slug>）
  - 面包屑 Home / Markets / <Country>；schema Article(about=AdministrativeArea) +
    BreadcrumbList + FAQPage；FAQ 与可见文案同源渲染（validate.js 逐字比对）
  - 硬校验：title 30–60 / meta 140–160 / facts ≥3 / faq ≥3 / sections ≥3 /
    内部链接目标必须真存在（防死链）

用法:
  python3 scripts/site/build-market-pages.py --spec scripts/site/pseo/markets-latam.json --dry
  python3 scripts/site/build-market-pages.py --spec ... --apply
  python3 scripts/site/build-market-pages.py --spec ... --apply --only mexico
  python3 scripts/site/build-market-pages.py --spec ... --audit
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
SITE = os.path.join(REPO, "site")
BASE = "https://www.anaricharge.com"

# 2026-11-09：加 locale 支持（ES 批次）。EN 与 ES 共用同一套结构，
# 只有界面文案、lang、canonical、hreflang、输出目录不同 —— 避免两份模板漂移。
LOCALES = {
    "en": {"lang": "en", "og": "en_US", "dir": "", "home": "Home", "markets": "Markets",
           "glance": "At a glance", "verified": "Last verified", "source": "Source: Anari Energy market notes",
           "faq": "Frequently asked questions", "related": "Related",
           "cta_button": "Talk about a project", "cta_h3": "Planning a station in {country}?",
           "cta_p": "We quote after a free site survey, because the grid connection decides most of the cost."},
    "pt": {"lang": "pt-BR", "og": "pt_BR", "dir": "/pt", "home": "Início", "markets": "Mercados",
           "glance": "Em resumo", "verified": "Última verificação", "source": "Fonte: notas de mercado da Anari Energy",
           "faq": "Perguntas frequentes", "related": "Relacionado",
           "cta_button": "Falar do projeto", "cta_h3": "Planejando uma estação em {country}?",
           "cta_p": "Cotamos depois de um estudo gratuito do local: a conexão elétrica decide a maior parte do custo."},
    "es": {"lang": "es", "og": "es_ES", "dir": "/es", "home": "Inicio", "markets": "Mercados",
           "glance": "De un vistazo", "verified": "Última verificación", "source": "Fuente: notas de mercado de Anari Energy",
           "faq": "Preguntas frecuentes", "related": "Relacionado",
           "cta_button": "Hablar del proyecto", "cta_h3": "¿Planeas una estación en {country}?",
           "cta_p": "Cotizamos después de un estudio gratuito del emplazamiento: la conexión eléctrica decide la mayor parte del costo.",
           "nav": "nav-es.html", "footer": "footer-es.html",
           "home_href": "/es/", "market_label": "Mercado", "region_label": "Región",
           "default_region": "Latinoamérica"},
}

ORG = {
    "@type": "Organization",
    "name": "Anari Energy",
    "legalName": "Shenzhen Anari Energy Co., Ltd.",
    "url": BASE + "/",
    "telephone": "+8618866205186",
    "logo": {"@type": "ImageObject",
             "url": BASE + "/assets/img/anari-icon.webp",
             "width": 512, "height": 512},
    "sameAs": ["https://www.anariev.com/",
               "https://www.linkedin.com/showcase/shenzhen-anari-energy-co-ltd"],
}


def esc(s):
    return html.escape(str(s), quote=False)


def ld(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2)


def stat_band(facts):
    return "\n".join(
        '        <div class="stat"><span class="stat-num">%s</span>'
        '<span class="stat-label">%s</span></div>' % (esc(n), esc(l))
        for n, l in facts)


def spec_panel_rows(spec, locale="en"):
    L = LOCALES[locale]
    rows = [(L.get("market_label", "Market"), esc(spec["country"])),
            (L.get("region_label", "Region"), esc(spec.get("region", L.get("default_region", "Latin America"))))]
    seen = {r[0] for r in rows} | {r[1] for r in rows}
    for n, l in (spec.get("facts") or []):
        if len(rows) >= 4:
            break
        if esc(n) in seen or esc(l) in seen:
            continue
        rows.append((esc(l), esc(n)))
        seen.add(esc(n)); seen.add(esc(l))
    return "\n".join(
        '        <div><b>%s</b><span>%s</span></div>' % (k, v)
        for k, v in rows)


def faq_visible(faq):
    return "\n".join(
        '    <details class="faq-item">\n      <summary>%s</summary>\n      <p>%s</p>\n    </details>'
        % (esc(q), esc(a)) for q, a in faq)


def hreflang_tags(spec, family, locale):
    """2026-11-10：locale 版本是否已存在由 family["hreflang_locales"] 决定，
    避免 EN 页声明不存在的 /es/ 版本（hreflang 指向 404 是质量缺陷）。"""
    slug = spec["slug"]
    urls = {
        "en": BASE + family["base_path"] + "/" + slug,
        "es": BASE + "/es" + family["base_path"] + "/" + slug,
        "pt": BASE + "/pt" + family["base_path"] + "/" + slug,
    }
    have = family.get("hreflang_locales", ["en", "es"])
    labels = {"en": "en", "es": "es", "pt": "pt-BR"}
    out = []
    for loc in have:
        out.append('  <link rel="alternate" hreflang="%s" href="%s">' % (labels[loc], urls[loc]))
    out.append('  <link rel="alternate" hreflang="x-default" href="%s">' % urls["en"])
    return "\n".join(out)


def sources_block(spec):
    """per-page 'Sources and verification' — 只渲染真来源（纯文本，不链外站防死链）。"""
    items = spec.get("sources") or []
    if not items:
        return ""
    lis = "\n".join('      <li>%s</li>' % esc(x) for x in items)
    anchor = spec.get("anchor_fact")
    extra = ""
    if anchor:
        extra = ('      <p class="meta-item">Anchor fact: %s — %s</p>\n'
                 % (esc(anchor.get("fact", "")), esc(anchor.get("source", ""))))
    return ('  <h2>Sources and verification</h2>\n    <ul class="sources-list">\n%s\n    </ul>\n%s'
            % (lis, extra))


def related_links(spec, base_path, label):
    items = "\n".join('      <li><a href="%s">%s</a></li>' % (p, esc(l))
                      for p, l in (spec.get("internal") or []))
    if not items:
        return ""
    return ('  <section class="related wrap">\n    <h2>%s</h2>\n    <ul>\n%s\n    </ul>\n  </section>'
            % (esc(label), items))


def build(spec, family, locale="en"):
    L = LOCALES[locale]
    slug = spec["slug"]
    path = "%s%s/%s" % (L["dir"], family["base_path"], slug)
    url = BASE + path
    dm = family.get("date_modified", "2026-11-07")
    nav = open(os.path.join(FRAG, L.get("nav", "nav.html")), encoding="utf-8").read()
    footer = open(os.path.join(FRAG, L.get("footer", "footer.html")), encoding="utf-8").read()

    article_ld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": spec["h1"],
        "description": spec["meta"],
        "datePublished": dm,
        "dateModified": dm,
        "inLanguage": L["lang"],
        "about": {"@type": "AdministrativeArea", "name": spec["country"]},
        "author": ORG,
        "mainEntityOfPage": url,
    }
    breadcrumb_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": L["home"], "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": L["markets"], "item": BASE + L["dir"] + family["base_path"] + "/"},
            {"@type": "ListItem", "position": 3, "name": spec["country"], "item": url},
        ],
    }
    faq_ld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "dateModified": dm,
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a}}
                       for q, a in spec["faq"]],
    }

    sections = "\n\n".join(
        '    <section class="v2-section">\n      <div class="v2-section-head"><h2>%s</h2></div>\n%s\n    </section>'
        % (esc(h2), body.strip()) for h2, body in spec["sections"])

    return """<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{meta}">
  <link rel="canonical" href="{url}">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{meta}">
  <meta property="og:url" content="{url}">
  <meta property="og:locale" content="{og}">
  <meta property="og:image" content="{base}/assets/img/og/cases-jordan-station.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%2326262b'/%3E%3Cpath d='M17.3 8 10 19.2h4.7L13 25l7.9-11.4h-4.8z' fill='%231078f0'/%3E%3C/svg%3E">
  <link rel="stylesheet" href="/style.css">
  <link rel="stylesheet" href="/assets/css/v2.css?v=20261110b">
  <script type="application/ld+json">
{article_ld}
  </script>
  <script type="application/ld+json">
{breadcrumb_ld}
  </script>
  <script type="application/ld+json">
{faq_ld}
  </script>
{hreflangs}
  <script src="/assets/js/nav.js" defer></script>
  <script src="/assets/js/track.js" defer></script>
  <script src="/assets/js/motion.js" defer></script>
  <script src="/assets/js/lead-chat.js" defer></script>
</head>
<body>
{nav}

<main id="main" class="v2">
  <nav class="breadcrumb wrap" aria-label="Breadcrumb">
    <ol>
      <li><a href="{home_href}">{home_label}</a></li>
      <li><a href="{markets_href}">{markets_label}</a></li>
      <li><span aria-current="page">{country}</span></li>
    </ol>
  </nav>

  <section class="v2-hero">
    <div class="v2-wrap">
      <p class="v2-eyebrow">{eyebrow}</p>
      <h1>{h1}</h1>
      <p class="v2-lede">{lede}</p>
      <div class="v2-actions">
        <a class="v2-btn v2-btn--primary" href="{inquiry}">{cta_button}</a>
      </div>
      <div class="v2-facts">
{spec_rows}
      </div>
    </div>
  </section>

  <article class="article wrap v2-wrap">
    <div class="meta-row">
      <span class="badge-verified">{verified}: {dm}</span>
      <span class="meta-item">{source}</span>{coverage_note}
    </div>

    <div class="tldr">
      <p class="tldr-label">{tldr_label}</p>
      <p>{tldr}</p>
    </div>

    <div class="stat-band stat-band--inline">
{stats}
    </div>

{sections}

    <h2>{faq_label}</h2>
{faq}

{sources}

    <div class="v2-cta">
      <h3>{cta_h3}</h3>
      <p>{cta_p}</p>
      <div class="v2-actions"><a class="v2-btn v2-btn--primary" href="{inquiry}">{cta_button}</a></div>
    </div>
  </article>

{related}
</main>

{footer}
</body>
</html>
""".format(
        title=esc(spec["title"]), meta=esc(spec["meta"]), url=url, base=BASE,
        base_path=family["base_path"], article_ld=ld(article_ld),
        breadcrumb_ld=ld(breadcrumb_ld), faq_ld=ld(faq_ld), nav=nav, footer=footer,
        country=esc(spec["country"]), eyebrow=esc(spec["eyebrow"]),
        h1=esc(spec["h1"]), lede=esc(spec["lede"]), stats=stat_band(spec["facts"]),
        spec_rows=spec_panel_rows(spec, locale), home_href=L.get("home_href", "/"),
        home_label=L["home"], tldr_label=esc(spec["tldr_label"]),
        tldr=esc(spec["tldr"]), sections=sections, faq=faq_visible(spec["faq"]),
        dm=dm, related=related_links(spec, family["base_path"], L["related"]),
        sources=sources_block(spec),
        coverage_note=(' <span class="meta-item">Market intelligence — not a claim of delivered'
                       ' operations in %s.</span>' % esc(spec["country"])
                       if spec.get("coverage") == "target" else ""),
        lang=L["lang"], og=L["og"], locale_dir=L["dir"], markets_label=L["markets"],
        glance=L["glance"], verified=L["verified"], source=L["source"],
        faq_label=L["faq"], related_label=L["related"],
        cta_button=L["cta_button"], cta_h3=L["cta_h3"].format(country=esc(spec["country"])),
        cta_p=L["cta_p"], inquiry=spec.get("inquiry_href") or (L["dir"] + "/inquiry"),
        markets_href=spec.get("markets_href") or (L["dir"] + family["base_path"] + "/"),
        hreflangs=hreflang_tags(spec, family, locale))


def body_wordcount(html_frag):
    txt = re.sub(r"<[^>]+>", " ", html_frag)
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’\-]*", txt))


def validate_spec(spec, family, batch_paths=None):
    errs = []
    t, m = spec.get("title", ""), spec.get("meta", "")
    if not (30 <= len(t) <= 60):
        errs.append("title %d 字符（需 30–60）: %s" % (len(t), t))
    if not (140 <= len(m) <= 160):
        errs.append("meta %d 字符（需 140–160）: %s" % (len(m), m))
    if len(spec.get("facts") or []) < 3:
        errs.append("facts 少于 3 条（垃圾页风险）")
    if len(spec.get("faq") or []) < 3:
        errs.append("faq 少于 3 条")
    if len(spec.get("sections") or []) < 3:
        errs.append("sections 少于 3 节")
    # 死链防护：内部链接目标必须真存在
    batch_paths = batch_paths or set()
    for p, _ in (spec.get("internal") or []):
        if p in batch_paths:
            continue
        target = os.path.join(SITE, p.strip("/"))
        ok = (os.path.isfile(target + ".html") or os.path.isfile(os.path.join(target, "index.html"))
              or os.path.isdir(target))
        if not ok:
            errs.append("内部链接目标不存在: %s" % p)
    if len(spec.get("internal") or []) < 3:
        errs.append("内部链接少于 3 条")
    # 词数（正文，不含 nav/footer/schema）
    wc = body_wordcount(" ".join(b for _, b in spec.get("sections") or []))
    wc += body_wordcount(" ".join(a for _, a in spec.get("faq") or []))
    if wc < 450:
        errs.append("正文词数 %d < 450（薄页风险）" % wc)
    return errs, wc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--only", default=None)
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--locale", default="en", choices=list(LOCALES))
    a = ap.parse_args()

    with open(a.spec, encoding="utf-8") as f:
        fam = json.load(f)
    base_path = fam.get("base_path", "/markets")
    L = LOCALES[a.locale]
    outdir = os.path.join(SITE, *([L["dir"].strip("/")] if L["dir"] else []), base_path.strip("/"))
    pages = fam["pages"]
    if a.only:
        pages = [p for p in pages if p["slug"] == a.only]
        if not pages:
            raise SystemExit("--only %s 未匹配" % a.only)

    bad = 0
    words = []
    batch_paths = {"%s/%s" % (base_path, p["slug"]) for p in fam["pages"]}
    for spec in pages:
        errs, wc = validate_spec(spec, fam, batch_paths)
        words.append((spec["slug"], wc))
        if errs:
            bad += 1
            print("✗ %-22s %s" % (spec["slug"], "; ".join(errs)))
        elif a.audit:
            print("✓ %-22s words=%d facts=%d sections=%d links=%d"
                  % (spec["slug"], wc, len(spec["facts"]), len(spec["sections"]),
                     len(spec["internal"])))
    if a.audit:
        print("\n词数分布: min=%d max=%d avg=%d" % (
            min(w for _, w in words), max(w for _, w in words),
            sum(w for _, w in words) // max(len(words), 1)))
    if bad:
        print("\n%d 页未通过自检，未写盘。" % bad)
        return 2
    if a.dry or a.audit:
        print("\n[dry] %d 页通过自检，未写盘。" % len(pages))
        return 0

    os.makedirs(outdir, exist_ok=True)
    for spec in pages:
        out = os.path.join(outdir, spec["slug"] + ".html")
        with open(out, "w", encoding="utf-8") as f:
            f.write(build(spec, fam, a.locale))
        print("  written site%s%s/%s.html" % (L["dir"], base_path, spec["slug"]))
    print("\n生成 %d 页 → %s" % (len(pages), os.path.relpath(outdir, REPO)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
