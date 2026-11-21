# GSC 收录验证改造方案：浏览器 → URL Inspection API

> 2026-10-26 值班长产出。背景：10-24 / 10-25 连续两晚浏览器复查失败（任务配置越界一次 + 本机到 Google 链路 ERR_CONNECTION_TIMED_OUT 两晚），10-26 恢复后人工补跑才清账。浏览器链路有三个脆弱点：本机代理/VPN、GSC 登录态、SPA 交互（Shadow DOM / 合成事件边界）。API 改造后三点全部绕开。

## 一、目标

用 Google Search Console **URL Inspection API**（`POST https://searchconsole.googleapis.com/v1/urlInspection/index:inspect`）替代 WebBridge 浏览器复查，脚本化、可进定时任务、不受本机到 Google 网页链路影响（走 googleapis.com，且可重试）。

## 二、前提（一次性设置，约 20 分钟，需用户操作 Google Cloud 控制台）

1. Google Cloud 项目启用 **Search Console API**；
2. 创建 **OAuth 2.0 桌面客户端**（或 service account + 域级委托，但 GSC 对 SA 支持麻烦，推荐 OAuth 桌面流）；
3. 本机跑一次授权（浏览器弹一次 Google 登录，scope: `https://www.googleapis.com/auth/webmasters.readonly`），拿到 refresh_token 落本机 keychain/本地文件（0600 权限）；
4. GSC 资源 `sc-domain:anaricharge.com` 对该 Google 账号已有权限（现状已满足，浏览器登录的即该账号）。

> 只读 scope 足够复查；若未来要 API 化「请求索引」，注意 **Indexing API 仅官方支持 JobPosting/BroadcastEvent 类型站点**，请求索引仍需浏览器通道或手动——本方案只替代「查状态」，不替代「请求索引」。

## 三、请求与返回（每次每 URL 一次调用）

```
POST /v1/urlInspection/index:inspect
{
  "inspectionUrl": "https://www.anaricharge.com/blog/<slug>",
  "siteUrl": "sc-domain:anaricharge.com",
  "languageCode": "en-US"
}
```

返回 `indexStatusResult.verdict`（PASS=已收录 / NEUTRAL / FAIL）、`coverageState`（如 "URL is unknown to Google"、"Crawled - currently not indexed"）、`lastCrawlTime`、`pageFetchState` 等——比浏览器读页面文本更结构化。

配额：每站点每天 200 次查询（同资源维度），8 URL 复查每天一次远低于上限。

## 四、落地形态

1. 新 Python 脚本 `gsc_url_status.py`（约 80 行）：读 URL 清单 → 逐条 inspect → 写 `anari-index-verify-<日期>.md` 对照表 + artifact JSON；refresh_token 自动续期（google-auth 库或纯 urllib 手写 token 刷新，避免装重型依赖）；
2. 把现有「GSC 收录复查」类一次性/周复查任务（如 automation_cd1ad04a、连接器文章收录周复查 automation_1ac1a550）从 agent+浏览器改为 code+python 执行，工作目录不再越界、无浏览器依赖；
3. 浏览器方案保留为降级通道（API 配额耗尽或返回异常时手动用）。

## 五、迁移步骤建议

1. 用户完成第二节 OAuth 设置（唯一手动步）；
2. 我写脚本并用 8 个存量 URL 实跑一次，与 10-26 浏览器结果（8/8 已收录）交叉验证一致性；
3. 一致后切换定时任务执行方式；不一致则保留浏览器通道并排查口径差异。

## 六、风险与边界

- refresh_token 泄漏=GSC 只读权限泄漏：落盘 0600 权限，不进 git；
- API 数据有小时级延迟，与页面实测差异属正常；
- 「请求索引」动作不在本方案范围（见第二节备注）。
