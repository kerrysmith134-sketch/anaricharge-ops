#!/usr/bin/env python3
"""zenodo_upload.py — 把数据集发到 Zenodo 并拿 DOI（REST API，不是浏览器）。

## 为什么用 API 而不是 UI
2026-11-07 实测：浏览器桥接的 `upload` 与 CDP `DOM.setFileInputFiles` 都被
Chrome 的「允许访问文件 URL」策略挡住（需要用户手动开），UI 上传不可自动化。
Zenodo REST API 一次配置长期可用，且发新版本时只需改 version 字段。

## 用法
  python3 scripts/outbound/zenodo_upload.py draft      # 建草稿 + 传文件（不发布）
  python3 scripts/outbound/zenodo_upload.py publish <record_id>
  python3 scripts/outbound/zenodo_upload.py show <record_id>

凭证：.secrets/zenodo.json（600，不进 git）
"""
import json
import os
import sys
import urllib.request

WS = "/Users/kerrychu/anari-charge-website"
SEC = os.path.join(WS, ".secrets", "zenodo.json")
BASE = "https://zenodo.org/api"
FILES = [
    ("hot-climate-observations-2026.json", "application/json"),
    ("README.md", "text/markdown"),
    ("CITATION.cff", "text/plain"),
]
SRC = "/tmp/anari-dataset"
STATE = os.path.join(WS, "08-execution", "backlink", "zenodo-record.json")


def token():
    d = json.load(open(SEC, encoding="utf-8"))
    tok = d.get("token") or ""
    if len(tok) < 20:
        raise SystemExit("Zenodo token 缺失或无效")
    return tok


def call(method, path, data=None, ctype="application/json", raw=None):
    tok = token()
    url = BASE + path
    body = None
    if raw is not None:
        body = raw
    elif data is not None:
        body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, method=method,
                                 headers={"Authorization": "Bearer " + tok,
                                          "Content-Type": ctype})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            txt = r.read().decode()
            return json.loads(txt) if txt.strip() else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:400]
        raise SystemExit(f"HTTP {e.code} {method} {path}\n{detail}")


METADATA = {
    "title": "Verified Hot-Climate EV Charging Observations, 2026",
    "resource_type": {"id": "dataset"},
    "publication_date": "2026-11-07",
    "creators": [{"person_or_org": {
        "type": "organizational",
        "name": "Shenzhen Anari Energy Co., Ltd.",
    }}],
    "description": (
        "<p>Field observations from operating EV charging sites in hot-climate and monsoon "
        "markets (Israel, Saudi Arabia, Cambodia, Jordan).</p>"
        "<p>Contents: 3 field observations, 3 equipment ratings, and <strong>4 explicitly "
        "stated gaps</strong> — things we could not measure. Each record separates the "
        "measurement, the conditions it was measured under, and the stated limit.</p>"
        "<p>Published so the numbers can be checked rather than taken on trust. Most "
        "manufacturer material in this category presents derating curves without stating "
        "test conditions, which makes it unusable for an engineer sizing a site. If a figure "
        "is not in this dataset, treat it as unverified rather than assuming a value.</p>"
        "<p>Analysis and method: "
        "<a href=\"https://www.anaricharge.com/data/hot-climate-charging\">"
        "anaricharge.com/data/hot-climate-charging</a></p>"
    ),
    "rights": [{"id": "cc-by-4.0"}],
    "subjects": [{"subject": k} for k in [
        "EV charging", "hot climate", "derating", "DC fast charging",
        "charging infrastructure", "energy storage", "emerging markets"]],
    "related_identifiers": [
        {"identifier": "https://www.anaricharge.com/data/hot-climate-charging",
         "relation_type": {"id": "isdocumentedby"}, "scheme": "url"},
        {"identifier": "https://github.com/kerrysmith134-sketch/anari-hot-climate-observations",
         "relation_type": {"id": "issupplementedby"}, "scheme": "url"},
    ],
    "version": "1.0.0",
}


def cmd_draft():
    d = call("POST", "/records", {"metadata": METADATA,
                                  "files": {"enabled": True},
                                  "access": {"record": "public", "files": "public"}})
    rid = d["id"]
    print("草稿 id:", rid, "| 状态:", d.get("status"))
    for name, ctype in FILES:
        path = os.path.join(SRC, name)
        size = os.path.getsize(path)
        call("POST", f"/records/{rid}/draft/files", [{"key": name}])
        raw = open(path, "rb").read()
        call("PUT", f"/records/{rid}/draft/files/{name}/content",
             ctype="application/octet-stream", raw=raw)
        call("POST", f"/records/{rid}/draft/files/{name}/commit")
        print(f"  已上传 {name} ({size} bytes)")
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump({"record_id": rid, "draft_url": f"https://zenodo.org/uploads/{rid}",
               "metadata": METADATA}, open(STATE, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n草稿链接: https://zenodo.org/uploads/%s" % rid)
    print("→ 核对无误后执行: python3 scripts/outbound/zenodo_upload.py publish %s" % rid)
    return 0


def cmd_publish(rid):
    d = call("POST", f"/records/{rid}/draft/actions/publish")
    doi = (d.get("pids") or {}).get("doi", {}).get("identifier") or d.get("doi")
    print("✅ 已发布")
    print("  DOI:", doi)
    print("  记录页:", d.get("links", {}).get("self_html") or f"https://zenodo.org/records/{rid}")
    if os.path.exists(STATE):
        s = json.load(open(STATE, encoding="utf-8"))
        s.update(published=True, doi=doi,
                 record_url=d.get("links", {}).get("self_html"))
        json.dump(s, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0


def cmd_show(rid):
    d = call("GET", f"/records/{rid}")
    m = d.get("metadata") or {}
    print("标题:", m.get("title"))
    print("状态:", d.get("status"), "| DOI:", (d.get("pids") or {}).get("doi", {}).get("identifier"))
    print("文件:", [f.get("key") for f in (d.get("files", {}).get("entries") or {})])
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("用法: draft | publish <id> | show <id>")
    a = sys.argv[1]
    if a == "draft":
        sys.exit(cmd_draft())
    if a == "publish":
        sys.exit(cmd_publish(sys.argv[2]))
    if a == "show":
        sys.exit(cmd_show(sys.argv[2]))
    raise SystemExit("未知命令")
