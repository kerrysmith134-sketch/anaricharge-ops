#!/usr/bin/env node
/**
 * reshell-v2.js — 给现有内容页套 v2 外壳（保留正文、结构化数据与页面脚本）
 *
 * 策略：**不加 hero、不改正文**。只做三件事：
 *   1. head 里补 v2.css（保留原 meta 与所有 JSON-LD）
 *   2. 导航/页脚换成共享片段（fragments/nav.html、footer.html）
 *   3. <main> 外包一层 v2 容器；保留 </main> 之后的全部脚本（GTM、nav.js、motion.js）
 *
 * 为什么这么保守：内容页的价值在正文与结构化数据；重写正文风险远大于收益。
 * 视觉统一靠 v2.css 的容器、排版与背景，而不是重写每一段文字。
 *
 * 用法：
 *   node scripts/site/reshell-v2.js --list
 *   node scripts/site/reshell-v2.js --dry --only blog/xxx
 *   node scripts/site/reshell-v2.js --apply
 */
'use strict';

const fs = require('fs');
const path = require('path');

const WS = path.resolve(__dirname, '..', '..');
const SITE = path.join(WS, '06-site/anari-new-site/site');
const FRAG = path.join(WS, 'scripts/site/fragments');

const argv = process.argv.slice(2);
const LIST = argv.includes('--list');
const APPLY = argv.includes('--apply');
const ONLY = (() => { const i = argv.indexOf('--only'); return i >= 0 ? argv[i + 1] : null; })();

// 产品详情页有自己的两栏 hero 与深色产品图渲染，套通用外壳会破坏产品主图绘制
// → 由专属模板单独处理，这里明确跳过（2026-11-07 实测：套壳后主图不绘制）。
const SKIP_PATTERNS = [
  /^products\/(?!index\.html$)[^/]+\.html$/,
  /^(ru|es)\/products\/(?!index\.html$)[^/]+\.html$/,
];

const V2_SPECS = new Set(
  fs.readdirSync(path.join(WS, 'scripts/site/v2/pages')).map((f) => f.replace(/\.json$/, ''))
);

const FAMILIES = ['blog', 'academy', 'regulations', 'playbooks', 'products', 'tools', 'journey',
  'data', 'markets', 'cost', 'depot', 'solutions', 'who-we-serve', 'turnkey', 'cases', 'agents',
  'ru', 'es'];
const ROOT_PAGES = ['about.html', 'inquiry.html', 'privacy.html', '404.html'];

const FRAGS = {};
function frag(kind, lang) {
  const key = kind + '-' + lang;
  if (!FRAGS[key]) {
    const p = path.join(FRAG, `${kind}${lang === 'en' ? '' : '-' + lang}.html`);
    FRAGS[key] = fs.readFileSync(fs.existsSync(p) ? p : path.join(FRAG, `${kind}.html`), 'utf8');
  }
  return FRAGS[key];
}
function localeOf(rel) {
  const seg = rel.split('/')[0];
  if (seg === 'ru') return 'ru';
  if (seg === 'es') return 'es';
  return 'en';
}

function candidates() {
  const out = [];
  for (const fam of FAMILIES) {
    const dir = path.join(SITE, fam);
    if (!fs.existsSync(dir)) continue;
    // ru/ es/ 有子目录（agents/index.html 等）→ 递归；其他族只扫一层即可（子目录是另生成的族）
    const recursive = fam === 'ru' || fam === 'es';
    const walk = (base, rel) => {
      for (const ent of fs.readdirSync(path.join(base, rel), { withFileTypes: true })) {
        const relPath = rel ? path.join(rel, ent.name) : ent.name;
        if (ent.isDirectory()) { if (recursive) walk(base, relPath); continue; }
        if (!ent.name.endsWith('.html')) continue;
        if (ent.name === 'index.html' && V2_SPECS.has(fam) && !rel) continue;
        out.push(path.join(fam, relPath));
      }
    };
    walk(dir, '');
  }
  for (const f of ROOT_PAGES) if (fs.existsSync(path.join(SITE, f))) out.push(f);
  return out.sort();
}

function processOne(rel) {
  const file = path.join(SITE, rel);
  const src = fs.readFileSync(file, 'utf8');

  if (/<main id="main" class="v2"|<main[^>]*class="[^"]*\bv2\b/.test(src)) {
    return { rel, skip: '已是 v2' };
  }
  const headMatch = src.match(/<head>([\s\S]*?)<\/head>/);
  const mainMatch = src.match(/<main\b[^>]*>([\s\S]*?)<\/main>/);
  if (!headMatch || !mainMatch) return { rel, skip: '无 head/main' };

  const head = headMatch[1];
  const mainInner = mainMatch[1];
  const afterMain = src.slice(src.indexOf('</main>') + '</main>'.length);

  // 已有 v2.css 就不要重复加
  const hasV2Css = /assets\/css\/v2\.css/.test(head);
  let newHead = head;
  if (!hasV2Css) {
    if (/<link rel="stylesheet" href="\/style\.css">/.test(head)) {
      newHead = head.replace(/<link rel="stylesheet" href="\/style\.css">/,
        '<link rel="stylesheet" href="/style.css">\n  <link rel="stylesheet" href="/assets/css/v2.css">');
    } else {
      newHead = head.replace('</title>', '</title>\n  <link rel="stylesheet" href="/assets/css/v2.css">');
    }
  }

  const lang = localeOf(rel);
  const srcLang = (src.match(/<html[^>]*lang="([^"]+)"/) || [,'en'])[1];
  const out = `<!DOCTYPE html>
<html lang="${srcLang}">
<head>${newHead}</head>
<body>
${frag('nav', lang)}
<main id="main" class="v2">
  <div class="v2-wrap v2-doc">
${mainInner}
  </div>
</main>
${frag('footer', lang)}${afterMain}`;

  return { rel, html: out };
}

const all = candidates();
const targets = ONLY ? all.filter((r) => r.includes(ONLY)) : all;

if (LIST) {
  console.log(`候选 ${all.length} 页：`);
  for (const r of all) console.log('  ' + r);
  process.exit(0);
}

let ok = 0;
const skipped = [];
for (const rel of targets) {
  if (SKIP_PATTERNS.some((re) => re.test(rel))) { skipped.push(`${rel}: 产品详情页由专属模板处理`); continue; }
  const res = processOne(rel);
  if (res.skip) { skipped.push(`${rel}: ${res.skip}`); continue; }
  if (APPLY) {
    fs.writeFileSync(path.join(SITE, rel), res.html);
    console.log(`  ✅ ${rel}`);
  } else {
    console.log(`  [dry] ${rel} → ${(res.html.length / 1024).toFixed(1)} KB`);
  }
  ok++;
}
console.log(`\n${APPLY ? '重壳' : 'dry-run'} ${ok} 页，跳过 ${skipped.length} 页`);
for (const s of skipped.slice(0, 12)) console.log('  跳过: ' + s);
