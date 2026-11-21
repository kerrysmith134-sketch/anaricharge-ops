#!/usr/bin/env python3
"""给 14 个已交付国市场页补上「审批与并网」合规页入口（双向互链用）。"""
import json

DELIVERED = ["lebanon", "israel", "saudi-arabia", "uae", "oman", "bulgaria", "czechia", "finland",
             "armenia", "uzbekistan", "kyrgyzstan", "tajikistan", "ethiopia", "ghana"]
FILES = ["scripts/site/pseo/markets-service-g1.json", "scripts/site/pseo/markets-service-g2.json"]

for f in FILES:
    d = json.load(open(f, encoding="utf-8"))
    n = 0
    for p in d["pages"]:
        if p["slug"] in DELIVERED:
            link = ["/regulations/" + p["slug"], "Approvals and grid connection"]
            if link not in p["internal"]:
                p["internal"].append(link)
                n += 1
    json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f, "patched", n, "pages")
