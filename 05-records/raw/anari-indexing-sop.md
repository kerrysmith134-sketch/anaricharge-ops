# Anari 新文章收录加速 SOP（v1.0）

> 依据 2026-10-23《CCS1 vs CCS2 vs NACS 连接器选型指南》收录加速实操整理。
> 当日成绩：IndexNow 返回 202 受理 → GSC 请求编入索引 → **约 25 分钟后 GSC 确认已收录**。

## 适用场景

新博客文章（/blog/ 下任一 slug）上线后 24 小时内执行一次。已存在 `anari-<主题>-indexed.done` 标记文件的文章不要重复执行。

## 前置确认

1. 读取当前本地时间（`date '+%Y-%m-%dT%H:%M:%S%z'`），用于报告与标记文件。
2. 从 `https://www.anaricharge.com/sitemap.xml` 定位新 URL（比对 `<lastmod>` 日期）；sitemap 未收录时尝试常见候选 slug。
3. `curl -o /dev/null -w "%{http_code}" <URL>` 验证返回 **200**。
   - 若为 404：写报告「文章未实际上线」并结束，不做任何提交。

## 执行步骤

### 1. IndexNow 提交

```bash
curl -s -o /dev/null -w "%{http_code}" \
  "https://api.indexnow.org/indexnow?url=<新URL>&key=anari-indexnow-key"
```

- 预期 `202`（Accepted，受理成功）；`200` 亦可。记录实际状态码。
- 空响应体属正常。

### 2. GSC URL Inspection 请求编入索引

入口：`https://search.google.com/search-console/inspect?resource_id=sc-domain:anaricharge.com`

通过 WebBridge（`http://127.0.0.1:10086/command`）操作，要点：

- **请求方式**：JSON 体写入唯一临时文件，`curl --data-binary @<file>` 发送，禁 `-d` 内联。
- **填写 URL**：snapshot 定位顶部 combobox（"Inspect any URL..."），`fill` 后点击 Search。
- **点击 REQUEST INDEXING 的坑**：GSC 是 Shadow DOM，WebBridge 合成 `click` 可能无效（页面无反应）。
  解法：CDP 真实鼠标事件——
  1. `evaluate` 读取 `innerWidth/innerHeight/devicePixelRatio`（常见 dpr=2）；
  2. 截图推算按钮像素坐标 ÷ dpr 得 CSS 坐标；
  3. `cdp Input.dispatchMouseEvent` 依次发 `mousePressed` + `mouseReleased`（`button:"left", clickCount:1`）；
  4. 等待 8 秒后重新 snapshot 确认出现 **"Indexing requested"**。
- 若检查结果是 "URL is on Google"：已收录，无需点击，直接进入第 3 步。

### 3. 连接器/目标主题词展示数基线

打开性能报告（可按主题替换 query 参数）：

```
https://search.google.com/search-console/performance/search-analytics?resource_id=sc-domain:anaricharge.com&breakdown=query&query=*ccs*&query=*connector*&query=*nacs*
```

从 snapshot 的按钮文本读取 `Total impressions N` / `Total clicks N`。新文章预期为 0，记录即可。

## 收尾

1. 在 workspace 写报告 `anari-index-submission-<YYYY-MM-DD>.md`：新 URL、URL 状态码、IndexNow 状态码、GSC 请求结果 + 截图路径、主题词展示数。
2. 创建标记文件 `anari-<主题>-indexed.done`，写入完成时间与 URL，防止任务重复触发。
3. 截图统一存 `gsc-screenshots/`。

## 红线

- 不动仓库代码，不做任何部署改动。
- 不改 GSC 任何设置：只允许 URL 检查、读取性能数据、对目标文章点 REQUEST INDEXING。
- WebBridge 不可用/未登录时如实记录失败，不伪造数据。
- 公司事实口径固定为「22 国 100+ 客户」。

## 已有配套自动化

| 资产 | 作用 |
| --- | --- |
| 定时任务「连接器文章收录周复查」 | 每周五 12:47 复查收录状态 + 主题词展示数，未收录自动再请求 |
| 小组件「连接器文章收录追踪」 | Anari Charge 营销看板上的状态徽章 + 展示量趋势图 |
| `index-monitor/connector-index-log.jsonl` | 逐次检查历史，widget 趋势图数据源 |

> 注意：复查类任务依赖本机浏览器在线（WebBridge）。浏览器关闭时任务会记录 error，不会产出假数据。

## 参考时间线（2026-10-23 实测）

| 时间 | 事件 |
| --- | --- |
| 12:25 | 发现 sitemap 更新，URL 验证 200 |
| 12:26 | IndexNow 提交 → 202 |
| 12:35 | GSC 确认 "Indexing requested" |
| 12:48 | 自动复查确认 "URL is on Google"（已收录），主题词展示 0 |
