#!/usr/bin/env python3
"""build-pages.py — 程序化页面生成器（页面族通用骨架）。

设计原则（与本仓库既有 build-case-page.py 一致）：
  - **一份数据 → 一个页面族**：内容、meta、FAQ、JSON-LD 全部从同一份 spec 渲染，
    所以 validate.js 的「FAQ schema 必须与可见文案逐字一致」天然成立。
  - 生成器放工作区 `scripts/site/`，**不进入站点仓库**（内容 PR 只碰 site/**）。
  - 生成物落在 `06-site/anari-new-site/site/<base_path>/<slug>.html`。

与 build-case-page.py 的区别：案例页是「一个案例一份 spec」；本生成器是「一个族一份 spec、
N 个页面」，并强制每页的独有事实（否则就是垃圾页）。

用法:
  python3 scripts/site/build-pages.py --spec scripts/site/pseo/cost-bands.json --dry
  python3 scripts/site/build-pages.py --spec scripts/site/pseo/cost-bands.json --apply
  python3 scripts/site/build-pages.py --spec ... --apply --only 120-kw-dc-fast-charging-station
"""
import argparse
import html
import json
import os
import sys

WS = "/Users/kerrychu/anari-charge-website"
FRAG = os.path.join(WS, "scripts", "site", "fragments")
REPO = os.path.join(WS, "06-site", "anari-new-site")

ORG = {
    "@type": "Organization",
    "name": "Anari Energy",
    "legalName": "Shenzhen Anari Energy Co., Ltd.",
    "url": "https://www.anaricharge.com/",
    "telephone": "+8618866205186",
    "logo": {"@type": "ImageObject",
             "url": "https://www.anaricharge.com/assets/img/anari-icon.webp",
             "width": 512, "height": 512},
    "sameAs": ["https://www.anariev.com/",
               "https://www.linkedin.com/showcase/shenzhen-anari-energy-co-ltd"],
}


def esc(s):
    return html.escape(s, quote=False)


def ld(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2)


def stat_band(facts):
    rows = []
    for num, label in facts:
        rows.append('        <div class="stat"><span class="stat-num">%s</span>'
                    '<span class="stat-label">%s</span></div>' % (esc(num), esc(label)))
    return "\n".join(rows)


def spec_panel_rows(spec):
    """hero 右侧规格栏：只放该页已有的真数据（facts / product / power）。

    设计意图：宽屏右侧原本是空白。与其拉长正文（违反量度规则），
    不如把"这页在讲什么规格"用仪表盘式 key/value 呈现 —— 工程感来自信息密度，
    不是来自渐变或阴影。
    """
    rows = []
    rows.append(("Power band", esc(spec["power"])))
    prod = spec.get("product")
    if prod:
        rows.append(("Platform", esc(prod)))
    seen_vals = {rows[0][1], rows[1][1] if len(rows) > 1 else ""}
    seen_keys = {r[0] for r in rows}
    for num, label in (spec.get("facts") or []):
        if len(rows) >= 4:
            break
        if esc(num) in seen_vals or esc(label) in seen_keys:
            continue          # 与 Power band / Platform 重复的跳过
        rows.append((esc(label), esc(num)))
        seen_vals.add(esc(num)); seen_keys.add(esc(label))
    return "\n".join(
        '            <div class="spec-row"><dt>%s</dt><dd>%s</dd></div>' % (k, v)
        for k, v in rows)


def faq_visible(faq):
    out = []
    for q, a in faq:
        out.append('    <details class="faq-item">\n      <summary>%s</summary>\n      <p>%s</p>\n    </details>'
                   % (esc(q), esc(a)))
    return "\n".join(out)


def related_links(spec):
    """页内「相关」列表：只用传入的真实路径，避免死链。"""
    items = []
    for path, label in spec.get("internal", []):
        items.append('      <li><a href="%s">%s</a></li>' % (path, esc(label)))
    if not items:
        return ""
    return ('  <section class="related wrap">\n    <h2>Related</h2>\n    <ul>\n%s\n    </ul>\n  </section>'
            % "\n".join(items))


def build(spec, family):
    base = family["base_url"]
    path = "%s/%s" % (family["base_path"], spec["slug"])
    url = base + path
    dm = family.get("date_modified", "2026-11-07")

    nav = open(os.path.join(FRAG, "nav.html"), encoding="utf-8").read()
    footer = open(os.path.join(FRAG, "footer.html"), encoding="utf-8").read()

    breadcrumb_name = spec["power"]
    hub_label = family.get("hub_label", "Cost guides")
    source_line = family.get("source_line", "Source: Anari Energy delivery records")
    about_name = family.get("about", "DC fast charging station cost")
    article_ld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": spec["h1"],
        "description": spec["meta"],
        "datePublished": dm,
        "dateModified": dm,
        "inLanguage": "en",
        "about": {"@type": "Thing", "name": about_name},
        "author": ORG,
        "mainEntityOfPage": url,
    }
    breadcrumb_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": base + "/"},
            {"@type": "ListItem", "position": 2, "name": hub_label,
             "item": base + family["base_path"] + "/"},
            {"@type": "ListItem", "position": 3, "name": breadcrumb_name, "item": url},
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

    sections = []
    for h2, body in spec["sections"]:
        sections.append("    <h2>%s</h2>\n%s" % (esc(h2), body.strip()))
    sections_html = "\n\n".join(sections)

    return """<!DOCTYPE html>
<html lang="en">
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
  <meta property="og:locale" content="en_US">
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
  <link rel="alternate" hreflang="en" href="{url}">
  <link rel="alternate" hreflang="x-default" href="{url}">
  <script src="/assets/js/nav.js" defer></script>
  <script src="/assets/js/track.js" defer></script>
  <script src="/assets/js/motion.js" defer></script>
  <script src="/assets/js/lead-chat.js" defer></script>
</head>
{nav}

<main id="main">
  <nav class="breadcrumb wrap" aria-label="Breadcrumb">
    <ol>
      <li><a href="/">Home</a></li>
      <li><a href="{base}{base_path}/">{hub_label}</a></li>
      <li><span aria-current="page">{breadcrumb_name}</span></li>
    </ol>
  </nav>

  <section class="hero">
    <div class="wrap">
      <div class="hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">{eyebrow}</p>
          <h1>{h1}</h1>
          <p class="lede">{lede}</p>
          <div class="hero-actions">
            <a class="btn btn-primary" href="/inquiry">Get a site-specific quote</a>
          </div>
        </div>
        <aside class="hero-spec" aria-label="At a glance">
          <p class="spec-label">At a glance</p>
          <dl>
{spec_rows}
          </dl>
        </aside>
      </div>
    </div>
  </section>

  <article class="article wrap">
    <div class="meta-row">
      <span class="badge-verified">Last verified: {dm}</span>
      <span class="meta-item">{source_line}</span>
    </div>

    <div class="tldr">
      <p class="tldr-label">{tldr_label}</p>
      <p>{tldr}</p>
    </div>

    <div class="stat-band stat-band--inline">
{stats}
    </div>

{sections}

    <h2>Frequently asked questions</h2>
{faq}

{cost_table}

    <div class="cta cta--inquiry">
      <div class="cta-body">
        <h3>Planning a {power} site?</h3>
        <p>We quote after a free site survey, because the grid connection decides most of the cost.</p>
      </div>
      <a class="btn btn-primary" href="/inquiry">Get a site-specific quote</a>
    </div>
  </article>

{related}
</main>

{footer}
""".format(
        title=esc(spec["title"]), meta=esc(spec["meta"]), url=url, base=base,
        base_path=family["base_path"],
        article_ld=ld(article_ld), breadcrumb_ld=ld(breadcrumb_ld), faq_ld=ld(faq_ld),
        nav=nav, footer=footer, breadcrumb_name=esc(breadcrumb_name),
        eyebrow=esc(spec["eyebrow"]), h1=esc(spec["h1"]), lede=esc(spec["lede"]),
        stats=stat_band(spec["facts"]), spec_rows=spec_panel_rows(spec),
        tldr_label=esc(spec["tldr_label"]), tldr=esc(spec["tldr"]),
        sections=sections_html, faq=faq_visible(spec["faq"]),
        dm=dm, related=related_links(spec), power=esc(spec["power"]),
        hub_label=esc(hub_label), source_line=esc(source_line),
        cost_table=cost_table_section(family, spec["power"]),
    )


def cost_table_section(family, power):
    """族级可选的「报价拆分」表格（cost 族用；markets 等族可关闭）。"""
    if not family.get("cost_table", True):
        return ""
    return '''    <section class="v2-section">
      <div class="v2-section-head">
        <h2>What we can quote, and what depends on the site</h2>
        <p>We do not publish one number for every market. The columns below are the real split:
           anything marked <em>site-specific</em> cannot be priced honestly without a survey.</p>
      </div>
      <div class="v2-table-wrap">
        <table class="v2-table">
          <caption class="v2-table-cap">Cost components for a %s site</caption>
          <thead><tr><th>Component</th><th>Who prices it</th><th>What it depends on</th></tr></thead>
          <tbody>
            <tr><td>DC charging equipment</td><td>Anari — quotable</td><td>power class, number of connectors, connector standard, enclosure</td></tr>
            <tr><td>Transformer &amp; switchgear</td><td>Local electrical contractor — site-specific</td><td>available grid capacity, existing transformer headroom, utility requirements</td></tr>
            <tr><td>Civil works &amp; foundations</td><td>Local contractor — site-specific</td><td>ground conditions, drainage, access, fencing, permits</td></tr>
            <tr><td>Installation &amp; commissioning</td><td>Anari or local partner, depending on scope</td><td>site conditions, grid connection procedure, local labour</td></tr>
            <tr><td>Energy management platform</td><td>Anari — quotable (ANARI OS)</td><td>number of sites, subscription level, integration needs</td></tr>
            <tr><td>Operations &amp; maintenance</td><td>Anari — quotable (service plan)</td><td>climate, duty cycle, SLA target, spares held locally</td></tr>
            <tr><td>Import duty, certification, freight</td><td>Determined by destination</td><td>tariff code, market certification, shipping route and volume</td></tr>
          </tbody>
        </table>
      </div>
      <p class="small muted">Two rows move the total more than the chargers do: the transformer/grid
        connection and the civil works. Both are decided by the site, which is why a survey comes first.</p>
    </section>''' % esc(power)


def validate_spec(spec):
    """生成前自检：长度、必填、独有事实。"""
    errs = []
    t, m = spec.get("title", ""), spec.get("meta", "")
    if not (30 <= len(t) <= 60):
        errs.append("title %d 字符（需 30–60）: %s" % (len(t), t))
    if not (140 <= len(m) <= 160):
        errs.append("meta %d 字符（需 140–160）: %s" % (len(m), m))
    for k in ("slug", "h1", "eyebrow", "lede", "tldr_label", "tldr", "facts", "sections", "faq"):
        if not spec.get(k):
            errs.append("缺字段: " + k)
    if len(spec.get("faq") or []) < 3:
        errs.append("FAQ 少于 3 条")
    if len(spec.get("facts") or []) < 3:
        errs.append("独有事实少于 3 条（垃圾页风险）")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()

    fam = json.load(open(a.spec, encoding="utf-8"))
    outdir = os.path.join(REPO, "site", fam["base_path"].strip("/"))
    pages = fam["pages"]
    if a.only:
        pages = [p for p in pages if p["slug"] == a.only]

    bad = 0
    for spec in pages:
        errs = validate_spec(spec)
        if errs:
            bad += 1
            print("✗ %s" % spec.get("slug"))
            for e in errs:
                print("    " + e)
            continue
        htmlout = build(spec, fam)
        target = os.path.join(outdir, spec["slug"] + ".html")
        if a.apply:
            os.makedirs(outdir, exist_ok=True)
            open(target, "w", encoding="utf-8").write(htmlout)
            print("  WROTE %s (%d KB)" % (os.path.relpath(target, REPO),
                                          len(htmlout.encode()) // 1024))
        else:
            print("  [dry] %s/%s.html %d KB" % (fam["base_path"].strip("/"),
                                                spec["slug"], len(htmlout.encode()) // 1024))
    if bad:
        return 1
    if a.apply:
        print("\n生成 %d 页 → %s" % (len(pages), os.path.relpath(outdir, REPO)))
        print("下一步：cd %s && node validate.js && node scripts/check-facts.js" % REPO)
    return 0


if __name__ == "__main__":
    sys.exit(main())
