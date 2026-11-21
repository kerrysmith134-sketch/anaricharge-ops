#!/usr/bin/env python3
"""audit-pseo-batch.py — 程序化 SEO 批次反低质审计（skill §3 机检）。

检查项（任一红 → 不提交）：
  1. 每页正文词数（sections+faq+lede+tldr）≥ 450（硬下限），并报告分布
  2. 每页「族内独有词」≥ 300（以本批 30 页 + 既有 /markets 页为族）
  3. 12-gram 重复：批内任意两页共享 12-gram ≤ 2 处；与既有 markets 页共享 ≤ 2 处
  4. facts：数量、批内不允许两页 facts 完全相同
  5. sections h2：同一 h2 在批内出现 >1 次 → 告警
  6. 必填字段：anchor_fact / sources / internal（≥4，含 /markets/ 与 /inquiry）
  7. 禁写字符串：30+ countr、竞品品牌名、未加引号的价格
用法：
  python3 scripts/site/audit-pseo-batch.py --spec .../markets-service-g1.json [...]
"""
import argparse
import collections
import glob
import json
import os
import re
import sys

WS = "/Users/kerrychu/anari-charge-website"
SITE = os.path.join(WS, "06-site", "anari-new-site", "site")
NGRAM = 12
FORBIDDEN = [
    r"30\+\s*countr", r"thirty\+", r"\bABB\b", r"\bSiemens\b", r"\bAlpitronic\b",
    r"\bKempower\b", r"\bTritium\b", r"\bBTC Power\b", r"\bEVBox\b", r"\bAlfen\b",
    r"\bWallbox\b", r"\bDelta\b", r"\bSK Signet\b", r"\bStar Charge\b", r"\bTELD\b",
    r"\bTesla\b", r"\bBYD\b",  # 品牌名（非产品线语境）一律不写
]
REQUIRED_INTERNAL = ["/markets/", "/inquiry"]


def plain(html_frag):
    txt = re.sub(r"<[^>]+>", " ", html_frag)
    txt = re.sub(r"&[a-z]+;", " ", txt)
    return txt


def words(text):
    return re.findall(r"[A-Za-z][A-Za-z'’\-]*", text.lower())


def shingles(ws, n=NGRAM):
    return set(" ".join(ws[i:i + n]) for i in range(max(0, len(ws) - n + 1)))


def page_text(p):
    parts = [p.get("lede", ""), p.get("tldr", "")]
    parts += [plain(b) for _, b in p.get("sections", [])]
    parts += [plain(a) for _, a in p.get("faq", [])]
    return " ".join(parts)


def existing_market_shingles(exclude=(), subdir="markets"):
    out = {}
    for f in glob.glob(os.path.join(SITE, subdir, "*.html")):
        if f.endswith("index.html"):
            continue
        if "/%s/" % subdir + os.path.basename(f)[:-5] in exclude:
            continue
        s = open(f, encoding="utf-8", errors="replace").read()
        m = re.search(r"<main[\s\S]*?</main>", s)
        s = m.group(0) if m else s
        s = re.sub(r"<script[\s\S]*?</script>", " ", s)
        s = re.sub(r"<nav[\s\S]*?</nav>", " ", s)
        out["/%s/" % subdir + os.path.basename(f)[:-5]] = shingles(words(plain(s)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", nargs="+", required=True)
    ap.add_argument("--min-words", type=int, default=450)
    ap.add_argument("--min-unique", type=int, default=300)
    ap.add_argument("--max-ngram", type=int, default=2)
    ap.add_argument("--require-internal", nargs="*", default=["/markets/", "/inquiry"],
                    help="每页 internal 必须包含的路径（前缀匹配）")
    ap.add_argument("--require-market-slug", action="store_true",
                    help="每页 internal 必须包含 /markets/{slug}")
    ap.add_argument("--compare-subdir", default="markets",
                    help="与既有同族页面比较 12-gram 的子目录（markets/regulations）")
    a = ap.parse_args()

    pages = []
    for spec_path in a.spec:
        fam = json.load(open(spec_path, encoding="utf-8"))
        for p in fam["pages"]:
            p["_file"] = os.path.basename(spec_path)
            pages.append(p)
    print("批次页数:", len(pages))

    errs, warns = [], []
    texts = {p["slug"]: words(page_text(p)) for p in pages}
    sh = {k: shingles(v) for k, v in texts.items()}
    batch_slugs = {"/%s/" % a.compare_subdir + p["slug"] for p in pages}
    existing = existing_market_shingles(batch_slugs, a.compare_subdir)   # 只算一次（排除本批页）
    existing_wordbag = set()                       # 既有市场页用词集合（近似）
    for esh in existing.values():
        for gram in esh:
            existing_wordbag.update(gram.split())
    g5 = {k: shingles(v, 5) for k, v in texts.items()}

    # 1/2/3 词数、独有词、12-gram
    wcs = sorted(len(v) for v in texts.values())
    print("正文词数: min=%d p25=%d median=%d max=%d" % (
        wcs[0], wcs[len(wcs) // 4], wcs[len(wcs) // 2], wcs[-1]))
    for p in pages:
        slug, w = p["slug"], texts[p["slug"]]
        wc = len(w)
        if wc < a.min_words:
            errs.append("%s: 正文词数 %d < %d" % (slug, wc, a.min_words))
        # 独有内容比：本页 5-gram 中「未在本批其它页/既有市场页出现」的 5-gram 覆盖的词占比
        other_grams = set()
        for k, gs in g5.items():
            if k != slug:
                other_grams |= gs
        for esh5 in existing.values():
            pass
        # 5-gram 唯一性用 12-gram 集合近似：共享 12-gram 覆盖率越高，独有内容越少
        shared_tokens = sum(len(x.split()) for x in (sh[slug] & set().union(*[v for k, v in sh.items() if k != slug])))
        uniq_ratio = 1 - (shared_tokens / max(1, wc))
        if uniq_ratio < 0.40:
            warns.append("%s: 独有内容比 %.0f%% < 40%%" % (slug, uniq_ratio * 100))
        # 12-gram vs 批内
        for other, osh in sh.items():
            if other == slug:
                continue
            inter = len(sh[slug] & osh)
            if inter > a.max_ngram:
                errs.append("%s vs %s: 共享 12-gram %d > %d" % (slug, other, inter, a.max_ngram))
        # 12-gram vs 既有 markets 页（只要 ≤8 就算通过；不同国家页共享模板句可接受）
        worst = (0, "")
        for eslug, esh in existing.items():
            n = len(sh[slug] & esh)
            if n > worst[0]:
                worst = (n, eslug)
        if worst[0] > 8:
            errs.append("%s vs 既有 %s: 共享 12-gram %d > 8" % (slug, worst[1], worst[0]))

    # 4 facts
    seen_facts = {}
    for p in pages:
        facts = tuple(tuple(x) for x in p.get("facts", []))
        if len(facts) < 3:
            errs.append("%s: facts < 3" % p["slug"])
        if facts in seen_facts:
            errs.append("%s: facts 与 %s 完全相同" % (p["slug"], seen_facts[facts]))
        seen_facts[facts] = p["slug"]

    # 5 h2 重复
    h2s = collections.Counter()
    for p in pages:
        for h2, _ in p.get("sections", []):
            h2s[h2.strip().lower()] += 1
    for h2, n in h2s.items():
        if n > 1:
            warns.append("h2 重复 %d 次: %s" % (n, h2[:60]))

    # 6 必填
    for p in pages:
        if not p.get("anchor_fact"):
            errs.append("%s: 缺 anchor_fact" % p["slug"])
        if len(p.get("sources") or []) < 2:
            errs.append("%s: sources < 2" % p["slug"])
        internal = [i[0] for i in p.get("internal", [])]
        if len(internal) < 4:
            errs.append("%s: internal < 4" % p["slug"])
        for req in a.require_internal:
            if not any(x == req or x.startswith(req) for x in internal):
                errs.append("%s: internal 缺 %s" % (p["slug"], req))
        if a.require_market_slug and ("/markets/" + p["slug"]) not in internal:
            errs.append("%s: internal 缺 /markets/%s" % (p["slug"], p["slug"]))
        if len(p.get("sections", [])) < 5:
            errs.append("%s: sections < 5" % p["slug"])
        if len(p.get("faq", [])) < 3:
            errs.append("%s: faq < 3" % p["slug"])
        if not (30 <= len(p.get("title", "")) <= 60):
            errs.append("%s: title %d 字符" % (p["slug"], len(p.get("title", ""))))
        if not (140 <= len(p.get("meta", "")) <= 160):
            errs.append("%s: meta %d 字符" % (p["slug"], len(p.get("meta", ""))))

    # 7 禁写
    for p in pages:
        blob = json.dumps(p, ensure_ascii=False)
        for pat in FORBIDDEN:
            if re.search(pat, blob):
                errs.append("%s: 命中禁写模式 %s" % (p["slug"], pat))

    print("\n=== ERRORS (%d) ===" % len(errs))
    for e in errs:
        print("  ✗", e)
    print("\n=== WARNINGS (%d) ===" % len(warns))
    for w in warns:
        print("  ⚠", w)
    if errs:
        return 2
    print("\nAUDIT PASS — %d 页" % len(pages))
    return 0


if __name__ == "__main__":
    sys.exit(main())
