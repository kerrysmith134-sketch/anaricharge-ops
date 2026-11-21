#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cf-builds-audit.py — 查 CF Workers Builds 的构建记录/失败原因（需要 API token）

为什么需要：2026-11-16 起 `anaricharge-website` 的 CF 自动构建连续多次不触发/失败，
我们一直靠 `publish.sh` 的「发布即部署」兜底，但根因没查到。CF 后台的构建日志是唯一能定位的入口，
而 2026-11-19 后台会话已登出、现有 token 全部 401。

用法:
  CF_API_TOKEN=*** python3 scripts/tools/cf-builds-audit.py
  CF_API_TOKEN=*** python3 scripts/tools/cf-builds-audit.py --account <acc> --limit 20

需要的 token 权限（最小集）:
  - Account → Workers Builds: Read（读构建记录/日志）
  - 可选 Account → Workers Scripts: Read

退出码: 0 成功 / 1 请求失败 / 2 缺 token（打印获取步骤）
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

ACC = os.environ.get("CF_ACCOUNT_ID", "db81cefbae3613ca45f2211620ba6477")
WORKER = os.environ.get("CF_WORKER_NAME", "anaricharge-website")
BASE = "https://api.cloudflare.com/client/v4"


def call(path, token):
    req = urllib.request.Request(BASE + path, headers={
        "Authorization": "Bearer " + token, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8", "replace") or "{}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", default=ACC)
    ap.add_argument("--limit", type=int, default=10)
    a = ap.parse_args()
    token = os.environ.get("CF_API_TOKEN", "").strip()
    if not token:
        print("缺 CF_API_TOKEN。获取方式（二选一）：")
        print("  A) 登录 Cloudflare 后台 → My Profile → API Tokens → Create Token")
        print("     权限：Account → Workers Builds: Read（够查日志）")
        print("  B) 在浏览器登录 dash.cloudflare.com 后，把 token 存到 .secrets/cf_api_token（600）")
        print("然后：CF_API_TOKEN=*** python3 scripts/tools/cf-builds-audit.py")
        return 2
    try:
        print("== Workers Builds 记录（最近 %d 条）==" % a.limit)
        data = call("/accounts/%s/builds?per_page=%d" % (a.account, a.limit), token)
        rows = data.get("result") or []
        if not rows:
            print("没有构建记录（说明平台上确实没有触发构建 —— 与 11-16 现象一致）")
        for b in rows:
            print(json.dumps({
                "uuid": b.get("build_uuid") or b.get("id"),
                "created": b.get("created_on"),
                "status": b.get("status"),
                "trigger": (b.get("build_trigger") or {}).get("trigger_type"),
                "commit": (b.get("build_trigger") or {}).get("commit_hash"),
                "branch": (b.get("build_trigger") or {}).get("branch"),
            }, ensure_ascii=False))
        print("\n下一步：拿失败 build_uuid 查日志：")
        print("  GET /accounts/%s/builds/<build_uuid>/logs" % a.account)
        return 0
    except urllib.error.HTTPError as e:
        body = e.read()[:300].decode("utf-8", "replace")
        print("HTTP %s：%s" % (e.code, body))
        if e.code in (401, 403):
            print("→ token 无效或权限不足（需要 Account: Workers Builds Read）")
        return 1
    except Exception as e:  # noqa: BLE001
        print("请求失败：%s" % e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
