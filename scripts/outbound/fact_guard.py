#!/usr/bin/env python3
"""fact_guard.py — 外联文案事实校验（补 check-facts.js 的盲区）。

`check-facts.js` 只检查站点页面；**邮件/外联文案没人查**——历史 SDR 文案就曾用过
事实库之外的数字（"21 days"）。本脚本在发送前把序列文案里的数字与事实库比对。

用法：
  python3 scripts/outbound/fact_guard.py text "<文案>"
  python3 scripts/outbound/fact_guard.py campaigns <campaign_id> [campaign_id...]

已知局限（务必知道）：
  - 这是**数字级**比对，不是语义比对。若某个编造数字恰好也是事实库里某个数字
    （例："21" 因认证名 "CEI 0-21" 而在白名单里），就会漏报。
  - 「47 countries」这类**新增国家数**能被抓到（47 不在白名单），但「21 days」这种
    恰好撞号的情报需要人工再看一遍。
  - 所以它是**第一道筛**，不是最终裁决。发送前仍要看一眼上下文。
"""
import json
import re
import sys
import os

WS = "/Users/kerrychu/anari-charge-website"
FACT = os.path.join(WS, "06-site/anari-new-site/ops/fact-library.json")


def allowed_numbers():
    """从事实库里抽出所有允许出现的数字 token。"""
    d = json.load(open(FACT, encoding="utf-8"))
    fs = d.get("facts") or d
    toks, raw = set(), []
    for f in fs:
        v = str(f.get("value") or "")
        raw.append(v)
        for n in re.findall(r"\d+(?:[.,]\d+)?", v):
            toks.add(n.replace(",", ""))
    return toks, raw


# 这些是"提议的规格"而不是事实主张，不参与事实校验
BENIGN = re.compile(
    r"\d[\d.,]*\s*(?:[-–—~]\s*\d[\d.,]*)?\s*[-–—]?\s*"
    r"(?:word|words|minute|minutes|page|pages|step|steps|词)\b",
    re.I)


def numbers_in(text):
    # 先剔除良性上下文（如 "300-word guest piece"），再抽数字
    cleaned = BENIGN.sub(" ", text)
    # 剔除 URL 里的数字（UTM/路径）
    cleaned = re.sub(r"https?://\S+", " ", cleaned)
    # 2026-11-07：剔除标识符（DOI / 许可版本 / ISBN）——这些是**可核对的引用标识**，
    # 不是事实性宣称。原实现把 DOI 的 10.5281 与 "CC BY 4.0" 的 4.0 都当"可疑数字"，
    # 属于误报；误报会让真实可疑数字被噪声淹没。
    cleaned = re.sub(r"\b10\.\d{4,9}/\S+", " ", cleaned)              # DOI
    cleaned = re.sub(r"\bdoi:\s*\S+", " ", cleaned, flags=re.I)       # doi: 前缀
    cleaned = re.sub(r"\b(?:CC|cc)[- ](?:BY|by)[- ](?:SA|sa|NC|nc)?[- ]?\d\.\d\b", " ", cleaned)  # CC BY 4.0
    cleaned = re.sub(r"\b(?:MIT|Apache|GPL|BSD)[- ]?\d?(?:\.\d)?\b", " ", cleaned)
    # 2026-11-07：再排除两类标识符（同样不是事实宣称，而是元数据）
    #   ① ISO 时间戳（自动草稿页脚 "2026-11-07T10:00:00Z" 会被拆成 2026/11/07/10/00/00）
    cleaned = re.sub(r"\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?Z?)?", " ", cleaned)
    #   ② 电话号码（+86 188 6620 5186 等，是联系方式不是事实数字）
    cleaned = re.sub(r"\+?\d[\d\s\-()]{6,}\d", " ", cleaned)
    return re.findall(r"\d+(?:[.,]\d+)?", cleaned)


def check(text, toks, raw):
    """返回 (可疑数字列表, 命中的事实库值列表)。"""
    nums = numbers_in(text)
    suspicious = []
    for n in nums:
        norm = n.replace(",", "")
        if norm in toks:
            continue
        # 排除日期/年份/百分比外的显然项：1-9 的序数、货币、时间单位
        if norm.isdigit() and int(norm) <= 9:
            continue
        suspicious.append(n)
    hits = [r for r in raw if r and len(str(r)) > 6 and str(r)[:40] in text]
    return sorted(set(suspicious)), hits


def payload_texts(payload):
    """把 activity 序列里的 subject/body 全抽成文本。"""
    out = []
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ("subject", "body") and isinstance(v, str):
                    out.append(v)
                else:
                    walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(payload)
    return out


def main():
    toks, raw = allowed_numbers()
    print(f"事实库允许的数字 token: {len(toks)} 个\n")
    if sys.argv[1] == "text":
        texts = sys.argv[2:]
        label = "输入文案"
    else:
        sys.path.insert(0, os.path.join(WS, "scripts/outbound"))
        import instantly_client as ic
        texts = []
        for cid in sys.argv[2:]:
            c = ic.campaign_by_id(cid)
            label = c.get("name")
            print(f"=== {label} (status={c.get('status')}) ===")
            for t in payload_texts({"sequences": c.get("sequences")}):
                texts.append(t)
        label = "campaigns"

    bad_total = 0
    for t in texts:
        sus, hits = check(t, toks, raw)
        if sus:
            bad_total += len(sus)
            print("  ⚠️ 可疑数字:", sus)
            for s in sus:
                for line in t.split("\n"):
                    if s in line:
                        print("      上下文:", line.strip()[:120])
                        break
    print()
    if bad_total == 0:
        print("✅ 未发现事实库之外的数字")
    else:
        print(f"⚠️ 共 {bad_total} 处可疑数字——发送前必须核实或改写")
    return 1 if bad_total else 0


if __name__ == "__main__":
    sys.exit(main())
