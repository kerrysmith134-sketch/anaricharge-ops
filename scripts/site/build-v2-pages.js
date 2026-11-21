#!/usr/bin/env node
/**
 * build-v2-pages.js — 从 JSON 规格生成 v2 页面（全站改版的模板层）
 *
 * 为什么需要：站点有 153 个 HTML，页头页脚是复制粘贴演化的（导航 28 个变体、
 * hero 78 个变体）。逐页手改必然漂移。这里把「页面 = 共享外壳 + 组件块」固化下来。
 *
 * 输入：scripts/site/v2/pages/*.json（一个文件一页）
 * 外壳：scripts/site/fragments/nav.html + footer.html（与生成器共用同一份，避免再漂）
 * 输出：06-site/anari-new-site/site/<slug>/index.html
 *
 * 用法：
 *   node scripts/site/build-v2-pages.js --dry
 *   node scripts/site/build-v2-pages.js
 *   node scripts/site/build-v2-pages.js --only solutions
 */
'use strict';

const fs = require('fs');
const path = require('path');

const WS = path.resolve(__dirname, '..', '..');
const SITE = path.join(WS, '06-site/anari-new-site/site');
const FRAG = path.join(WS, 'scripts/site/fragments');
const SPECS = path.join(WS, 'scripts/site/v2/pages');

const argv = process.argv.slice(2);
const DRY = argv.includes('--dry');
const ONLY = (() => {
  const i = argv.indexOf('--only');
  return i >= 0 ? argv[i + 1] : null;
})();

const esc = (s = '') =>
  String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

const FRAG_CACHE = {};
function frag(kind, locale) {
  const key = kind + '-' + locale;
  if (!FRAG_CACHE[key]) {
    const p = path.join(FRAG, `${kind}${locale === 'en' ? '' : '-' + locale}.html`);
    FRAG_CACHE[key] = fs.readFileSync(fs.existsSync(p) ? p : path.join(FRAG, `${kind}.html`), 'utf8');
  }
  return FRAG_CACHE[key];
}

/* ------------------------------ 组件 ------------------------------ */

function hero(s) {
  const img = s.image;
  return `  <section class="v2-hero"${img ? ` style='background-image:url("${img}")'` : ''}>
    <div class="v2-wrap">
      <p class="v2-eyebrow">${esc(s.eyebrow)}</p>
      <h1>${esc(s.h1)}</h1>
      <p class="v2-lede">${esc(s.lede)}</p>
      <div class="v2-actions">
${(s.actions || [])
  .map((a, i) => `        <a class="v2-btn v2-btn--${i === 0 ? 'primary' : 'onDark'}" href="${a.href}">${esc(a.label)}</a>`)
  .join('\n')}
      </div>
${
  s.facts
    ? `      <div class="v2-facts">
${s.facts
  .map((f) => `        <div><b>${esc(f.value)}</b><span>${esc(f.label)}</span></div>`)
  .join('\n')}
      </div>`
    : ''
}
${s.credit ? `      <p class="v2-hero-credit" style="margin-top:1.1rem">${esc(s.credit)}</p>` : ''}
    </div>
  </section>`;
}

function sceneGrid(s) {
  return `  <section class="v2-section${s.alt ? ' v2-section--alt' : ''}">
    <div class="v2-wrap">
      <div class="v2-section-head">
        <p class="v2-eyebrow">${esc(s.eyebrow)}</p>
        <h2>${esc(s.h2)}</h2>
${s.lede ? `        <p>${esc(s.lede)}</p>` : ''}
      </div>
${s.filters ? filterBar(s.filters) : ''}
      <div class="v2-scenes" data-filter-target>
${s.items
  .map((it) => {
    const tags = it.tags || {};
    const attrs = Object.entries(tags)
      .map(([k, v]) => ` data-${k}="${esc(String(v))}"`)
      .join('');
    return `        <a class="v2-scene" href="${it.href}"${attrs}>
          <img src="${it.image}" alt="" loading="lazy" decoding="async" width="640" height="427">
          <div class="v2-scene-body">
            <h3>${esc(it.title)}</h3>
            <p>${esc(it.text)}</p>
          </div>
        </a>`;
  })
  .join('\n')}
      </div>
${s.filters ? `      <p class="v2-filter-empty" data-filter-empty hidden>No case matches these filters. <a href="${s.filters.reset || '/'}">Clear filters</a></p>` : ''}
    </div>
  </section>`;
}

function filterBar(f) {
  const groups = (f.groups || [])
    .map(
      (g, gi) => `        <div class="v2-filter-group" role="group" aria-label="${esc(g.label)}">
          <span class="v2-filter-label">${esc(g.label)}</span>
          ${(g.options || [])
            .map(
              (o) => `<button type="button" class="v2-chip" data-filter-group="${gi}" data-filter-value="${esc(
                o.value
              )}" aria-pressed="false">${esc(o.label)}</button>`
            )
            .join('\n          ')}
        </div>`
    )
    .join('\n');
  return `      <div class="v2-filters" data-filter-bar data-filter-key="${esc(
    f.key || 'cases'
  )}" aria-label="Filter cases">
${groups}
        <button type="button" class="v2-chip v2-chip--reset" data-filter-reset>Show all</button>
      </div>`;
}

function steps(s) {
  return `  <section class="v2-section${s.alt ? ' v2-section--alt' : ''}">
    <div class="v2-wrap">
      <div class="v2-section-head">
        <p class="v2-eyebrow">${esc(s.eyebrow)}</p>
        <h2>${esc(s.h2)}</h2>
${s.lede ? `        <p>${esc(s.lede)}</p>` : ''}
      </div>
      <div class="v2-steps">
${s.items
  .map(
    (it) => `        <div class="v2-step">
          <b>${esc(it.no)}</b><h3>${esc(it.title)}</h3><p>${esc(it.text)}</p>
        </div>`
  )
  .join('\n')}
      </div>
${
  s.action
    ? `      <div class="v2-actions"><a class="v2-btn v2-btn--ghost" href="${s.action.href}">${esc(s.action.label)}</a></div>`
    : ''
}
    </div>
  </section>`;
}

function productGrid(s) {
  return `  <section class="v2-section${s.alt ? ' v2-section--alt' : ''}">
    <div class="v2-wrap">
      <div class="v2-section-head">
        <p class="v2-eyebrow">${esc(s.eyebrow)}</p>
        <h2>${esc(s.h2)}</h2>
${s.lede ? `        <p>${esc(s.lede)}</p>` : ''}
      </div>
      <div class="v2-products"${s.compare ? ' data-compare-grid' : ''}>
${s.items
  .map((it) => {
    const slug = (it.compareKey || it.href.replace(/\/$/, '').split('/').pop());
    const box = s.compare
      ? `          <label class="v2-compare-check"><input type="checkbox" data-compare-item="${esc(slug)}"><span>Compare</span></label>`
      : '';
    return `        <div class="v2-product-cell">
          <a class="v2-product" href="${it.href}">
            <img src="${it.image}" alt="${esc(it.alt || it.name)}" loading="lazy" decoding="async" width="640" height="427">
            <div class="v2-product-body"><b>${esc(it.name)}</b><span>${esc(it.spec)}</span></div>
          </a>
${box}
        </div>`;
  })
  .join('\n')}
      </div>
${
  s.action
    ? `      <div class="v2-actions"><a class="v2-btn v2-btn--ghost" href="${s.action.href}">${esc(s.action.label)}</a></div>`
    : ''
}
    </div>
  </section>`;
}

function compareTable(s) {
  const data = JSON.stringify({ rows: s.rows || [], products: s.data || {} });
  const head = (s.rows || []).map((r) => `<th scope="row">${esc(r.label)}</th>`).join('');
  return `  <section class="v2-section" data-compare-section>
    <div class="v2-wrap">
      <div class="v2-section-head">
        <p class="v2-eyebrow">${esc(s.eyebrow || 'Compare')}</p>
        <h2>${esc(s.h2)}</h2>
        ${s.lede ? `<p>${esc(s.lede)}</p>` : ''}
      </div>
      <p class="v2-compare-hint" data-compare-hint>Pick up to 3 families above to compare them side by side.</p>
      <div class="v2-compare-wrap" data-compare-wrap hidden>
        <table class="v2-compare" data-compare-table>
          <caption class="sr-only">${esc(s.h2 || 'Product comparison')}</caption>
          <thead><tr><td></td></tr></thead>
          <tbody>
            ${(s.rows || []).map((r) => `<tr data-row="${esc(r.key)}"><th scope="row">${esc(r.label)}</th></tr>`).join('\n            ')}
          </tbody>
        </table>
      </div>
      <script type="application/json" data-compare-data>${data.replace(/</g, '\\u003c')}</script>
    </div>
  </section>`;
}

function cardGrid(s) {
  const cols = s.cols === 2 ? 'v2-capabilities' : 'v2-scenes';
  return `  <section class="v2-section${s.alt ? ' v2-section--alt' : ''}${s.dark ? ' v2-section--dark' : ''}">
    <div class="v2-wrap">
      <div class="v2-section-head">
        <p class="v2-eyebrow">${esc(s.eyebrow)}</p>
        <h2>${esc(s.h2)}</h2>
${s.lede ? `        <p>${esc(s.lede)}</p>` : ''}
      </div>
      <div class="${cols}">
${s.items
  .map((it) =>
    s.cols === 2
      ? `        <div class="v2-cap">
          ${it.status ? `<span class="v2-status v2-status--${it.status.toLowerCase()}">${esc(it.status)}</span>` : ''}
          <b>${esc(it.title)}</b>
          <p>${esc(it.text)}</p>
        </div>`
      : `        <a class="v2-scene" href="${it.href}">
          <img src="${it.image}" alt="" loading="lazy" decoding="async" width="640" height="427">
          <div class="v2-scene-body"><h3>${esc(it.title)}</h3><p>${esc(it.text)}</p></div>
        </a>`
  )
  .join('\n')}
      </div>
    </div>
  </section>`;
}

function evidence(s) {
  return `  <section class="v2-section${s.alt ? ' v2-section--alt' : ''}">
    <div class="v2-wrap">
      <div class="v2-evidence">
        <figure class="v2-evidence-figure">
          <img src="${s.image}" alt="${esc(s.imageAlt || '')}" loading="lazy" decoding="async" width="1280" height="853">
          <figcaption>${esc(s.caption)}</figcaption>
        </figure>
        <div>
          <p class="v2-eyebrow">${esc(s.eyebrow)}</p>
          <h2>${esc(s.h2)}</h2>
${s.lede ? `          <p>${esc(s.lede)}</p>` : ''}
          <dl class="v2-kv">
${s.kv.map((r) => `            <div><dt>${esc(r.k)}</dt><dd>${esc(r.v)}</dd></div>`).join('\n')}
          </dl>
${s.action ? `          <div class="v2-actions"><a class="v2-btn v2-btn--ghost" href="${s.action.href}">${esc(s.action.label)}</a></div>` : ''}
        </div>
      </div>
    </div>
  </section>`;
}

function cta(s) {
  return `  <section class="v2-section v2-section--alt">
    <div class="v2-wrap">
      <div class="v2-cta">
        <p class="v2-eyebrow">${esc(s.eyebrow)}</p>
        <h2>${esc(s.h2)}</h2>
${s.lede ? `        <p>${esc(s.lede)}</p>` : ''}
        <div class="v2-actions">
${(s.actions || [])
  .map((a, i) => `          <a class="v2-btn v2-btn--${i === 0 ? 'primary' : 'ghost'}" href="${a.href}">${esc(a.label)}</a>`)
  .join('\n')}
        </div>
      </div>
    </div>
  </section>`;
}

function productHero(s) {
  return `  <section class="v2-phero">
    <div class="v2-wrap v2-phero-grid">
      <div>
        <p class="v2-eyebrow">${esc(s.eyebrow)}</p>
        <h1>${esc(s.h1)}</h1>
        <p class="v2-lede">${esc(s.lede)}</p>
        <div class="v2-actions">
${(s.actions || [])
  .map((a, i) => `          <a class="v2-btn v2-btn--${i === 0 ? 'primary' : 'ghost'}" href="${a.href}">${esc(a.label)}</a>`)
  .join('\n')}
        </div>
        <p class="v2-small" style="margin-top:1rem">${esc(s.note || '')}</p>
      </div>
      <div class="v2-phero-media">
        <img src="${s.image}" alt="${esc(s.imageAlt || s.h1)}" width="1800" height="1200"
             srcset="${s.image1024 ? s.image1024 + ' 1024w, ' : ''}${s.image} 1800w" sizes="(max-width: 900px) 90vw, 560px">
      </div>
    </div>
  </section>`;
}

function specTable(s) {
  return `  <section class="v2-section${s.alt ? ' v2-section--alt' : ''}">
    <div class="v2-wrap">
      <div class="v2-section-head">
        <p class="v2-eyebrow">${esc(s.eyebrow)}</p>
        <h2>${esc(s.h2)}</h2>
${s.lede ? `        <p>${esc(s.lede)}</p>` : ''}
      </div>
      <div class="v2-table-wrap">
        <table class="v2-table">
          <caption class="v2-table-cap">${esc(s.caption || s.h2)}</caption>
          <tbody>
${s.rows.map((r, i) => `            <tr><th scope="row">${esc(r.k)}</th><td>${esc(r.v)}</td></tr>`).join('\n')}
          </tbody>
        </table>
      </div>
${s.action ? `      <div class="v2-actions"><a class="v2-btn v2-btn--ghost" href="${s.action.href}">${esc(s.action.label)}</a></div>` : ''}
    </div>
  </section>`;
}

function mapPanel(s) {
  const dots = (s.dots || [])
    .map(
      (d) =>
        `        <span class="v2-map-dot" style="left:${d.x}%;top:${d.y}%" title="${esc(d.name)}" aria-hidden="true"></span>`
    )
    .join('\n');
  return `  <section class="v2-section${s.alt ? ' v2-section--alt' : ''}">
    <div class="v2-wrap">
      <div class="v2-section-head">
        <p class="v2-eyebrow">${esc(s.eyebrow)}</p>
        <h2>${esc(s.h2)}</h2>
${s.lede ? `        <p>${esc(s.lede)}</p>` : ''}
      </div>
      <div class="v2-map-grid">
        <figure class="v2-map">
          <div class="v2-map-canvas" role="img" aria-label="${esc(s.alt || 'World map of countries served')}">
${dots}
          </div>
          <figcaption>${esc(s.caption || '')}${s.caption_note ? `<span class="v2-map-key"><span class="v2-map-dot v2-map-dot--key" aria-hidden="true"></span> ${esc(s.caption_note)}</span>` : ''}</figcaption>
        </figure>
        <div class="v2-map-legend">
${(s.regions || [])
  .map(
    (r) => `          <div class="v2-region">
            <div class="v2-region-head"><b>${esc(r.name)}</b><span>${esc(r.count)}</span></div>
            <p>${esc(r.countries)}</p>
          </div>`
  )
  .join('\n')}
        </div>
      </div>
    </div>
  </section>`;
}


function linkList(s) {
  return `  <section class="v2-section${s.alt ? ' v2-section--alt' : ''}${s.dark ? ' v2-section--dark' : ''}">
    <div class="v2-wrap">
      <div class="v2-section-head">
        <p class="v2-eyebrow">${esc(s.eyebrow)}</p>
        <h2>${esc(s.h2)}</h2>
${s.lede ? `        <p>${esc(s.lede)}</p>` : ''}
      </div>
      <div class="v2-capabilities">
${(s.items || [])
  .map((it) => `        <a class="v2-cap" href="${it.href}"><b>${esc(it.title)}</b><p>${esc(it.text || '')}</p></a>`)
  .join('\n')}
      </div>
    </div>
  </section>`;
}

const COMPONENTS = {
  hero,
  sceneGrid,
  filterBar,
  steps,
  productGrid,
  productHero,
  specTable,
  mapPanel,
  cardGrid,
  linkList,
  compareTable,
  evidence,
  cta,
};

/* ------------------------------ 外壳 ------------------------------ */

function build(spec) {
  // 站点约定：canonical 无扩展名（/products/vulco），alternate 指向 /products/vulco.md
  const isHtml = spec.url.endsWith('.html');
  const cleanPath = isHtml ? spec.url.replace(/\.html$/, '') : spec.url;
  const url = 'https://www.anaricharge.com' + cleanPath;
  const blocks = spec.sections.map((s) => {
    const fn = COMPONENTS[s.type];
    if (!fn) throw new Error(`unknown section type: ${s.type}`);
    return fn(s);
  });

  const breadcrumbLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://www.anaricharge.com/' },
      { '@type': 'ListItem', position: 2, name: spec.breadcrumb, item: url },
    ],
  };
  const pageLd = {
    '@context': 'https://schema.org',
    '@type': 'WebPage',
    name: spec.title,
    url,
    description: spec.meta,
    inLanguage: spec.locale || 'en',
    isPartOf: { '@type': 'WebSite', name: 'Anari Energy', url: 'https://www.anaricharge.com/' },
  };

  return `<!DOCTYPE html>
<html lang="${spec.locale || 'en'}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${esc(spec.title)}</title>
  <meta name="description" content="${esc(spec.meta)}">
  <link rel="canonical" href="${url}">
${(spec.hreflangs || []).map((h) => `  <link rel="alternate" hreflang="${h.lang}" href="${h.href}">`).join('\n')}
${(spec.hreflangs || []).length ? `  <link rel="alternate" hreflang="x-default" href="${(spec.hreflangs.find((h) => h.lang === 'en') || {}).href || url}">` : ''}
  <link rel="alternate" type="text/markdown" href="${isHtml ? cleanPath + '.md' : spec.url + 'index.md'}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="${esc(spec.title)}">
  <meta property="og:description" content="${esc(spec.meta)}">
  <meta property="og:url" content="${url}">
  <meta property="og:locale" content="en_US">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%2326262b'/%3E%3Cpath d='M17.3 8 10 19.2h4.7L13 25l7.9-11.4h-4.8z' fill='%231078f0'/%3E%3C/svg%3E">
  <link rel="stylesheet" href="/style.css">
  <link rel="stylesheet" href="/assets/css/v2.css">
  <script type="application/ld+json">
${JSON.stringify(pageLd, null, 2)}
  </script>
  <script type="application/ld+json">
${JSON.stringify(breadcrumbLd, null, 2)}
  </script>
</head>
<body>
<!-- GTM noscript（无 JS 用户的兜底统计；原本误放在 nav 片段里，已移到页面模板） -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-MRHHMP62" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
${frag('nav', spec.locale || 'en')}
<main id="main" class="v2">
${blocks.join('\n\n')}
</main>
${frag('footer', spec.locale || 'en')}
${spec.sections.some((s) => s.filters) ? '<script src="/assets/js/cases-filter.js" defer></script>' : ''}
${spec.sections.some((s) => s.type === 'compareTable') ? '<script src="/assets/js/product-compare.js" defer></script>' : ''}
</body>
</html>
`;
}

/* ------------------------------ 执行 ------------------------------ */

function collectSpecs(dir) {
  const out = [];
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) out.push(...collectSpecs(p));
    else if (ent.name.endsWith('.json')) out.push(JSON.parse(fs.readFileSync(p, 'utf8')));
  }
  return out;
}
const specs = collectSpecs(SPECS)
  .filter((s) => !ONLY || s.slug === ONLY || s.url.replace(/\//g, '') === ONLY);

let wrote = 0;
for (const spec of specs) {
  const html = build(spec);
  const clean = spec.url.replace(/^\//, '');
  const out = spec.url.endsWith('.html')
    ? path.join(SITE, clean)
    : path.join(SITE, spec.url.replace(/^\/|\/$/g, ''), 'index.html');
  const outDir = path.dirname(out);
  if (DRY) {
    console.log(`  [dry] ${path.relative(SITE, out)} ${(html.length / 1024).toFixed(1)} KB`);
  } else {
    fs.mkdirSync(outDir, { recursive: true });
    fs.writeFileSync(out, html);
    console.log(`  ✅ ${path.relative(SITE, out)} ${(html.length / 1024).toFixed(1)} KB`);
    wrote++;
  }
}
console.log(`\n${DRY ? 'dry-run' : '生成'} ${DRY ? specs.length : wrote} 页`);
