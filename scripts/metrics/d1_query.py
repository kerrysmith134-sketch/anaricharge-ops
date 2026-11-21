#!/usr/bin/env python3
"""d1_query.py — 直查 Cloudflare D1（只读），用于验证询盘是否真的落库。

## 为什么需要
`north_star.py` 只能看 GA4 前端事件；**询盘的唯一真实口径是 D1 `submissions` 表**。
而 `check-facts.js` 与 GA4 都看不到 D1。没有这个脚本，"询盘有多少"只能靠猜。

## 凭证
按顺序找：
  1. 环境变量 CF_API_TOKEN
  2. <workspace>/.secrets/cf_token
  3. ~/Documents/kimi/workspace/.cf_token（源工作区，只读引用）
需要权限：**D1 Read**（`Account > D1 > Read`）。仅有 DNS/Pages 权限会返回 7403。

## 用法
  python3 scripts/metrics/d1_query.py counts          # 询盘总量 + consent/status 分布
  python3 scripts/metrics/d1_query.py recent [N]      # 最近 N 条
  python3 scripts/metrics/d1_query.py consent-audit   # P0 假设验证（见下）
  python3 scripts/metrics/d1_query.py sql "SELECT ..."
"""
import json
import os
import sys
import urllib.error
import urllib.request

WS = "/Users/kerrychu/anari-charge-website"
DEFAULT_ACC = "db81cefbae3613ca45f2211620ba6477"
DEFAULT_DB = "8af713d2-a27b-45f7-b5ba-75467600d427"
TOKEN_PATHS = [
    os.path.join(WS, ".secrets", "cf_token"),
    "/Users/kerrychu/Documents/kimi/workspace/.cf_token",
]


def token():
    t = os.environ.get("CF_API_TOKEN")
    if t and len(t.strip()) >= 40:
        return t.strip()
    for p in TOKEN_PATHS:
        if os.path.exists(p):
            c = open(p).read().strip()
            if len(c) >= 40:
                return c
    raise SystemExit("没有可用的 API token；D1 查询请走 wrangler OAuth（默认已自动回退）")


WRANGLER = os.path.join(WS, ".tools", "node_modules", ".bin", "wrangler")
WRANGLER_HOME = os.path.join(WS, ".tools", "home")


def query_via_wrangler(sql, db_name="anari-leads", timeout=45):
    """走 wrangler 的 OAuth 凭证（不需要 API token）。

    2026-11-07 起可用：用户在 gmail 账号（db81cefb…）完成 wrangler login 后，
    OAuth token 含 d1:write，可直接查。这是比 API token 更省事的路径
    —— 之前 `.cf_token` 一直是占位符，D1 因此卡了好几轮。
    """
    import subprocess
    if not os.path.exists(WRANGLER):
        raise SystemExit("未找到 wrangler：%s（先 npm install --prefix .tools wrangler）" % WRANGLER)
    env = dict(os.environ)
    env["HOME"] = WRANGLER_HOME
    env.pop("CLOUDFLARE_API_TOKEN", None)
    # 2026-11-10 修：wrangler OAuth token 每 ~4h 刷新一次，而询盘守夜正每 4h 跑
    # （09:17/13:17/17:17/21:17），于是**每个档位的第一枪都撞上 token 刷新写盘**
    # （实测 default.toml 11:17:05 重写，11:17:06 的调用返回 code 10000）。
    # 这是冷启动竞态，不是权限失效；重试一次即恢复。这里内置重试，避免
    # 所有依赖脚本（inquiry_alert / lead_pipeline / north_star）每档都要人工重跑。
    import time as _time
    delays = (0, 2, 5)
    out = raw = None
    for attempt, delay in enumerate(delays, 1):
        if delay:
            _time.sleep(delay)
        out = subprocess.run(
            [WRANGLER, "d1", "execute", db_name, "--remote", "--command", sql, "--json"],
            capture_output=True, text=True, env=env, timeout=timeout)
        raw = out.stdout.strip()
        err = (out.stderr or "") + raw
        if "code: 10000" in err or "Authentication error" in err:
            continue  # token 刷新竞态 → 退避后重试
        break
    # wrangler 会在 JSON 前后打 banner/进度行，且可能输出多段 JSON：
    # 不能简单从第一个 "[" 解析到结尾（Extra data）。
    # 稳健做法：raw_decode 逐段尝试，取最后一个含 results 的数组。
    import json as _json
    dec = _json.JSONDecoder()
    data, found, idx = None, None, 0
    while idx < len(raw):
        j = raw.find("[", idx)
        if j < 0:
            break
        try:
            obj, end = dec.raw_decode(raw, j)
        except ValueError:
            idx = j + 1
            continue
        if isinstance(obj, list) and obj and isinstance(obj[0], dict) and "results" in obj[0]:
            data, found = obj, j
        idx = end
    if data is None:
        raise SystemExit("wrangler 无 JSON 输出：%s" % (out.stderr or raw)[:300])
    return data[0].get("results") or []


CACHE = os.path.join(WS, "08-execution", "metrics", "d1-cache.json")


def _cache_path():
    return CACHE


def cache_get(key):
    """读上一次成功的查询结果（带时间戳）。用于 wrangler 卡住时降级。"""
    try:
        d = json.load(open(CACHE, encoding="utf-8"))
        return d.get(key)
    except Exception:  # noqa: BLE001
        return None


def cache_put(key, rows):
    try:
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        d = {}
        if os.path.exists(CACHE):
            try:
                d = json.load(open(CACHE, encoding="utf-8"))
            except Exception:  # noqa: BLE001
                d = {}
        d[key] = {"at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
                  "rows": rows}
        json.dump(d, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:  # noqa: BLE001
        pass


def query(sql, acc=DEFAULT_ACC, db=DEFAULT_DB, via=None):
    if via is None:
        # 优先 wrangler OAuth：它一次授权就覆盖 d1:write，且不受 token scope 限制。
        # 2026-11-07 教训：`.cf_token` 有 53 字节"看着像 token"但缺 D1 scope，
        # 结果连查好几轮都是 7403；而 OAuth 登录后一次就通。
        oauth_cfg = os.path.join(
            WS, ".tools", "home", "Library", "Preferences", ".wrangler", "config", "default.toml")
        if os.path.exists(oauth_cfg):
            via = "wrangler"
        else:
            for p in TOKEN_PATHS:
                if os.path.exists(p) and len(open(p).read().strip()) >= 40:
                    via = "api"
                    break
            via = via or "wrangler"
    if via == "wrangler":
        return query_via_wrangler(sql)
    body = json.dumps({"sql": sql}).encode()
    req = urllib.request.Request(
        "https://api.cloudflare.com/client/v4/accounts/%s/d1/database/%s/query" % (acc, db),
        data=body,
        headers={"Authorization": "Bearer " + token(), "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            d = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read()[:400].decode("utf-8", "replace")
        hint = ""
        if "7403" in raw:
            hint = ("\n→ 该 token 无 D1 权限（code 7403）。两个解法："
                    "\n   ① Cloudflare → My Profile → API Tokens → 新建 token，权限含 "
                    "`Account > D1 > Read`，存到 %s"
                    "\n   ② 或在本机 `npx wrangler login` 后改用 "
                    "`npx wrangler d1 execute anari-leads --remote --command \"...\"`"
                    % os.path.join(WS, ".secrets", "cf_token"))
        raise SystemExit("HTTP %s: %s%s" % (e.code, raw[:300], hint))
    if not d.get("success"):
        errs = d.get("errors") or []
        code = (errs[0] or {}).get("code") if errs else None
        hint = ""
        if code == 7403:
            hint = ("\n→ 该 token 无 D1 权限。需要在 Cloudflare 建一个带 "
                    "`Account > D1 > Read` 的 token，放到 .secrets/cf_token；"
                    "或用 `wrangler login` 后改用 wrangler d1 execute。")
        raise SystemExit("查询失败: %s%s" % (json.dumps(errs, ensure_ascii=False)[:300], hint))
    out = []
    for blk in d.get("result") or []:
        out.extend(blk.get("results") or [])
    return out


def show(rows):
    if not rows:
        print("  （无行）")
        return
    for r in rows:
        print("  " + json.dumps(r, ensure_ascii=False))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "counts"
    if cmd == "counts":
        print("=== 总量与 consent 分布 ===")
        show(query("SELECT COUNT(*) AS total, SUM(consent) AS consent_1, "
                   "SUM(CASE WHEN consent=0 THEN 1 ELSE 0 END) AS consent_0 FROM submissions"))
        print("=== status 分布 ===")
        show(query("SELECT status, COUNT(*) AS n FROM submissions GROUP BY status ORDER BY n DESC"))
    elif cmd == "recent":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        show(query("SELECT created_at, email, consent, status FROM submissions "
                   "ORDER BY created_at DESC LIMIT %d" % n))
    elif cmd == "consent-audit":
        # P0 假设：若 consent=0 的行数为 0 且总量很小 → 前端 consent 门确实在丢线索
        rows = query("SELECT COUNT(*) AS total, "
                     "SUM(CASE WHEN consent=0 THEN 1 ELSE 0 END) AS no_consent, "
                     "SUM(CASE WHEN status='stored' THEN 1 ELSE 0 END) AS stored, "
                     "SUM(CASE WHEN status='sent' THEN 1 ELSE 0 END) AS sent FROM submissions")
        show(rows)
        if rows:
            r = rows[0]
            total = r.get("total") or 0
            nc = r.get("no_consent") or 0
            print()
            if total == 0:
                print("  判定：D1 里一条询盘记录都没有 → 落库链路从未成功过（不只是 consent 门）")
            elif nc == 0:
                print("  判定：⚠️ P0 假设成立 —— 从未有一行 consent=0，说明未勾选的询盘全被前端拦掉")
            else:
                print(f"  判定：consent=0 已有 {nc} 行 → 门已不再完全拦截（可能修复已生效）")
    elif cmd == "sql":
        show(query(sys.argv[2]))
    else:
        raise SystemExit("用法: counts | recent [N] | consent-audit | sql \"SELECT ...\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
