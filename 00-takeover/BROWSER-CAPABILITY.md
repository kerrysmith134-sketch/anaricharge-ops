# 浏览器自动化能力（BROWSER-CAPABILITY）

> 用户指出的关键缺口：Kimi Work 时代最大的价值是「用真实浏览器带登录态执行操作」——Quora 发帖回答、Reddit、Brevo 工作流。
> 本文件记录：能力已恢复、怎么用、能操作什么、有哪些坑、边界在哪。
> 建立于 2026-11-07 接管首班。

---

## 一、能力状态：已恢复 ✅

| 项 | 状态 |
|---|---|
| Kimi WebBridge 守护进程 | **运行中**，`127.0.0.1:10086`，pid 78103，版本 `v2.0.34` |
| 浏览器扩展连接 | **已连接**（extension_id `bnlffdbcfnanfbknnlaflhlhkocccckg`） |
| 二进制位置 | `~/.kimi-webbridge/bin/kimi-webbridge` |
| 登录态 | Quora / Reddit / Brevo **均已登录**；GSC 与 Cloudflare 后台未登录（改用 API，见第四节） |

**启动方式**（注意：守护进程要在 `~/.kimi-webbridge/` 下写日志与 pid，该目录在工作区之外，需要一次 full-access 才能启动）：
```bash
~/.kimi-webbridge/bin/kimi-webbridge start
~/.kimi-webbridge/bin/kimi-webbridge status    # 期望 running:true + extension_connected:true
```
扩展未连接时的处理：先把浏览器打开（`open -a "Google Chrome"`），扩展会自动连上。

---

## 二、怎么用（工作区内的两个脚本）

### `scripts/browser/wb.py` —— 桥客户端
```bash
python3 scripts/browser/wb.py health                      # 守护进程 + 扩展健康
python3 scripts/browser/wb.py status                      # 各平台登录态一览
python3 scripts/browser/wb.py nav "https://www.quora.com/" --session quora
python3 scripts/browser/wb.py snap --session quora        # 可访问性树（带 @e ref）
python3 scripts/browser/wb.py eval "document.title" --session quora
python3 scripts/browser/wb.py tabs
python3 scripts/browser/wb.py close --session quora
```

Python 内调用：
```python
import sys; sys.path.insert(0, "scripts/browser")
from wb import WB
wb = WB(session="quora")
wb.nav("https://www.quora.com/")
print(wb.text()[:300])
wb.fill("@e123", "text")      # input/textarea/contenteditable 都支持
wb.click("@e124")
wb.wait_text("Answer")        # 等 SPA 渲染完，比裸 sleep 稳
```

### `scripts/browser/ops.py` —— 平台级操作
```bash
python3 scripts/browser/ops.py quora-search "ev charging station franchise"
python3 scripts/browser/ops.py quora-question <url>
python3 scripts/browser/ops.py quora-answer <url> --text "..." # 默认 dry-run
python3 scripts/browser/ops.py reddit-new "electricvehicles" --limit 10
python3 scripts/browser/ops.py reddit-thread <url>
python3 scripts/browser/ops.py reddit-reply <url> --text "..."  # 默认 dry-run
python3 scripts/browser/ops.py brevo-contacts
python3 scripts/browser/ops.py brevo-find someone@example.com
```

**写操作的安全默认**：`quora-answer` / `reddit-reply` 不带 `--confirm` 时**只返回预览，不写入**。这不是能力不足，是刻意设计——发帖不可逆，必须先看到正文再决定。

---

## 三、实测结果（2026-11-07，真实执行）

### Quora ✅ 可用
搜 `ev charging station franchise`，真实返回 8 个问题，并且**直接标出 `unanswered` 条目**（首答红利）：
- `How should I get an EV charging station franchise in India?`（**未回答**）
- `How do I get Tata power EV charging station franchises?`（**未回答**）
- `How profitable is a Tata charging station dealership? ...`（**未回答**）
- `Is the EV charging station the next big franchise opportunity?`（已有答案）

这正是 `quora-log.md` 里验证过的打法（首答抢 SERP），现在可以每天自动跑。

### Reddit ✅ 可用
`r/electricvehicles` 新帖返回带分数的真实帖子（如 "Any hope for a minivan EV in the states?" 110 分）。**用 `old.reddit.com` 抓取**，DOM 稳定。

### Brevo ✅ 可用，且**直接查出了一个 P0 结论**

读 `Contacts` 页实得：
```
1 contact
Anari Energy | Email | kerry@anaricharge.com | 21/10/2026 | 17/10/2026
```

**即：Brevo 全库只有 1 个联系人，是内部地址 `kerry@anaricharge.com`（10 月 17 日创建、10 月 20 日最后变更）。**
→ 这直接闭合了「U-4 真实询盘核对」：**10-26 之后没有任何真实询盘进入 Brevo；历史上也从未有真实客户进过 Brevo。** 此前的 E2E 测试联系人都已被清理干净。
→ 意味着「询盘 2 个」的说法只能来自 Web3Forms 邮件侧，CRM 侧是空的。

证据文件：`08-execution/browser-evidence/`（截图 + 页面文本）。

---

## 四、能操作什么 / 不能操作什么

| 平台 | 登录态 | 可做什么 | 说明 |
|---|---|---|---|
| **Quora** | ✅ | 搜索问题、读问题与答案、写回答（草稿）、回复评论 | 核心获客渠道，已实测 |
| **Reddit** | ✅ | 读子版块/帖子、读评论、写回复（草稿） | 受 karma 门槛限制，纪律见 `anari-reddit-warmup.md` |
| **Brevo** | ✅ | 读联系人/列表/统计、建联系人、编辑属性、看自动化与工作流 | 用户明确要求纳入自动化范围 |
| GSC | ❌ 浏览器未登录 | **改用官方 API**（`scripts/gsc_pull.py` / `index_coverage.py`） | 比浏览器稳、快、可复跑，已是主路径 |
| Cloudflare 后台 | ❌ 浏览器未登录 | **改用 API token**（`.cf_token`，已验证 active） | 本班已用它把 Always Use HTTPS 打开 |
| anariev.com WordPress | 未验证 | 待查 | 姊妹站，历史记录里做过审计 |

### 边界（写在前面，避免踩线）
1. **不代注册、不代登录、不绕过验证码**。
2. **不可逆外部动作必须先预览**：发帖 / 发邮件 / 删数据 → 先 `dry_run`，人工确认后再 `--confirm`。
3. **不批量刷量**：Quora 带链接 ≤3 条/周（沿用 `quora-log.md` 纪律），Reddit 养号期不发链接。
4. **登录态属于用户**：不要在同一浏览器里同时跑互斥操作；结束用 `close_session` 收拾标签页。

---

## 五、五个必须知道的坑（都是本班踩出来的）

### 坑 1【最关键】后台标签页会被 Chrome 节流，页面永远渲染不出来
现象：`wb.text()` 只返回几百字符的导航栏，`screenshot` 里页面停在骨架屏；但第一次导航时是好的。
原因：Chrome 对非前台标签页做定时器节流，SPA 的数据请求/渲染被挂起。
证据：`list_tabs` 里该标签 `active: false`。
**处置**：① 每次操作前把浏览器窗口提到前台（`osascript -e 'tell application "Google Chrome" to activate'`）；② 同一时刻只保留一个会话在操作；③ 操作完 `close_session`，下次重新 `nav` 建新标签；④ 对关键页面用 `wait_text` 等真实内容出现，不要裸 `sleep`。

**2026-11-13 复测补充（这条最容易被误诊）**：
- 本机 `osascript` 已被 macOS TCC 拒绝（`System Events 权限违例` / `AppleEvent 已超时 -1712`），`open -a "Google Chrome"` 也返回 `-1712` → **"提到前台"这条路在本机不通**。
- 此时复用旧标签访问 GSC 控制台 → 页面不渲染 → `snapshot/evaluate` 超时 → **daemon 回 502**。
  旧脚本把 502 吞掉后记成 `no_input`，看起来像"选择器坏了"，实际是标签/渲染问题。
- **可靠解法（实测）**：每个 URL `navigate(newTab:true)` 开新标签 → 等 `input[aria-label*="Inspect any URL"]` 出现 → 操作 → `close_tab`。
  2026-11-13 用这个方式：sitemap 重提 1 次成功、requestIndexing **9/10 成功**（第 10 个本就已收录）。
- 已固化：`scripts/tools/gsc_request_indexing.py` 新增 `fresh_tab()`，并在每个 URL 后 `close_tab`；`call()` 对 502 指数退避重试。

### 坑 2 Reddit 必须用 `old.reddit.com`
新版 Reddit 的 DOM 是重 JS 渲染，且加载慢；`old.reddit.com` 结构稳定、锚点多（实测 370 个 a 标签 vs 新版 36 个）。
`ops.py reddit_new()` 已内置 old → www 回退。

### 坑 3 【已更正】GSC 其实是登录的——失败原因是 URL 参数没编码

**我上一版写错了。2026-11-07 复测：GSC 登录态正常，且 URL Inspection 请求编入索引可以完全自动化跑通。**

失败的真正原因有两个：

1. **`resource_id` 必须 URL 编码**。传 `resource_id=sc-domain:anaricharge.com`（冒号未编码）会让控制台退回到营销页 `/about`，看起来像"未登录"；
   正确写法：`resource_id=sc-domain%3Aanaricharge.com`。
2. **`/inspect?resource_id=...&id=<url>` 这条「直链」不存在**，会 404。正确流程是进入控制台后用顶部 `input[aria-label^="Inspect any URL"]` 填 URL 再回车。

**还有一个可复用的技巧（Material 按钮）**：`REQUEST INDEXING` 在可访问性树里只暴露成 `StaticText`、拿不到 `@e` ref，直接用 class 选择器又会点到隔壁按钮。
可靠做法是「按文本定位 → 找最近的 `[role=button]` → 原生 `.click()`」：

```js
const t = Array.from(document.querySelectorAll('div,span'))
  .filter(e => (e.innerText || '').trim() === 'REQUEST INDEXING');
const btn = t[t.length-1].closest('[role=button],button,[jsaction]');
btn.click();          // 实测有效，会先跑 live test 再返回 Indexing requested
```

**2026-11-10 复测（E1 内容验收）**：GSC 请求编入索引已全自动跑通 **5/5** 个 URL（`/blog/transformer-upgrade-ev-charging` + `/markets/{israel,ethiopia,india,uae}`），全部返回 "Indexing requested — URL was added to a priority crawl queue"。补充两条实测细节：① CDP `Input.dispatchKeyEvent` 在后台标签页**不触发**，回车改派发**合成 KeyboardEvent** 即可；② `REQUEST INDEXING` 按文本定位后取最近 `[role=button]/button/[jsaction]` 原生 `.click()` 可直接生效，无需坐标换算。已脚本化：`scripts/tools/gsc_request_indexing.py`。

**实测结果（2026-11-07）**：对 `/blog/bess-600kwh-for-ev-charging`（41 天未被发现）执行后返回
`check_circle Indexing requested — URL was added to a priority crawl queue`。
证据：`08-execution/gsc/indexing-requested-bess-600kwh-20261107.png` 与同名 `.txt`。

→ 结论：**GSC 的 URL inspection / 请求编入索引 = 可自动化**；日常数据仍优先走官方 API（更快、可批量）。
→ Cloudflare 后台确实未登录，但 API token 已够用（本班用它开了 Always Use HTTPS）。

### 坑 4 Quora 回答框是 contenteditable，不是 textarea
必须用 `fill`（底层走 `execCommand('insertText')`），直接改 `.value` 无效。

### 坑 5 合成事件的 `isTrusted=false`
部分站点（银行、验证码）会因此拒绝点击/填写。这是产品边界，不是 bug。Quora / Reddit / Brevo 实测不受影响。

---

## 六、这让哪些工作流从「半自动」变成「可自动」

| 工作流 | 之前 | 现在 |
|---|---|---|
| **W11 社区引流** | 「Quora 可浏览器发布，Reddit 只备稿」 | 搜索→选题→写稿→填草稿全链可跑；发布保留人工确认 |
| **W12 询盘监控** | 靠人工去 Brevo 后台看 | 可直接读联系人/列表验证真实询盘 |
| **W10 外链与数字公关** | 稿件产出后卡在人工发信 | Qwoted / Source of Sources 的记者 query 可自动读取与匹配 |
| **W13 索引提交** | 浏览器逐个 URL 请求索引 | GSC 未登录 → 改走 IndexNow API + GSC API 查状态（更稳） |
| **W1 日终简报** | 团队运行状态靠推断 | 可直接查各平台真实状态取证 |

---

## 六点五、标签页卫生（硬要求）

**用户明确要求**：用完浏览器必须关掉不用的标签，否则标签堆积会拖慢用户电脑。

规则：
1. **同一时刻最多保留 1–2 个标签**；能复用就复用（`nav(..., new_tab=False)`）。
2. **每次任务结束必须执行** `python3 scripts/browser/wb.py cleanup` —— 它会遍历所有会话并关闭全部标签。
3. 自查：`python3 scripts/browser/wb.py tabs-all` 会列出各会话剩余标签数。
4. 不要按站点各开一个会话放着不动；一个任务一个会话，任务完就 `close_session`。

历史教训：2026-11-07 一轮浏览器操作累计开了 **24 个标签**（gtm 10 个、reddit 5 个、其余各 1）。已全部清理并写成规则。

## 七、规则变更：R6 被用户显式覆盖

**旧规则 R6（Kimi 时代）**：禁止用浏览器自动化操作第三方后台（Brevo/GTM/GA4 UI）。
**新规则（2026-11-07 用户指令）**：浏览器自动化**恢复为允许能力**，范围包括 Quora / Reddit / Brevo 工作流。

保留的约束：
- **不可逆动作（发帖、发信、删数据、改线上配置）仍需逐次人工确认或显式授权**。
- 账号操作不可跨用户：不代注册、不猜密码、不绕验证码。
- 所有浏览器操作要留下留痕（截图或文本证据在 `08-execution/browser-evidence/`）。

已同步更新：`AGENTS.md` R6、`05-records/decisions.md`。

## Gmail 自动化（2026-11-11 实测可用）

### 关键结论：Gmail 现代 UI 的 `.click()` 无效，必须派发完整指针事件序列
```js
var el = /* 目标按钮 */;
var r = el.getBoundingClientRect();
var opts = {bubbles:true, cancelable:true, clientX:r.left+r.width/2, clientY:r.top+r.height/2, view:window};
['pointerdown','mousedown','pointerup','mouseup'].forEach(function(t){
  el.dispatchEvent(new (t.indexOf('pointer')===0?PointerEvent:MouseEvent)(t, opts));
});
el.click();
```
只调 `el.click()` 时 Gmail **不执行**（选中态不生效、Move to Inbox 不动作），加指针序列后才生效。
实测：把回收站里 6 封 "New inquiry" 通知移回收件箱，搜索 `in:trash` 由 6 → 0，`in:inbox` 由 0 → 6。

### 可用的选择器与流程
- 搜索：直接导航 `https://mail.google.com/mail/u/0/#search/<urlencoded query>`，比点搜索框稳
- 全选：`document.querySelectorAll('[role=checkbox]')[0].click()`（这个直接 click 有效）
- 工具栏按钮用 aria-label / data-tooltip / innerText 精确匹配：
  `Archive`、`Delete`、`Move to Inbox`、`Report spam`、`Mark as unread`、`Labels`、`More email options`
- 列表计数从 `document.querySelector('[role=main]').innerText` 读："Showing most relevant 1–6 of 6 Conversations"
- 旧选择器 `tr.zA` 在本账号（"Anari EV Mail" 新版 Gmail）**已不适用**（返回 0）

### 已知坑
- Chrome 窗口不在前台时列表可能不渲染 → 先 `osascript -e 'tell application "Google Chrome" to activate'`
- 自发自收（from=to=同一地址）的邮件易被 Gmail 归到「已发送」或被误删，**通知类邮件应换发件人或用 plus 地址**

## Gmail 发信（2026-11-12 实测可用）

### 为什么必须用这条通道
Instantly `/emails/test` 代发通知/回信时，**信能到但正文是空的**（用户截图确认：
主题正常、发件人正常、正文一片空白）。所以对外发信统一走真实 Gmail compose。

### 关键实现（`scripts/tools/gmail_send.py`）
1. 打开全屏撰写：`https://mail.google.com/mail/u/0/?view=cm&fs=1&tf=1`
2. 收件人：`input[aria-label="To recipients"]`（旧版是 `textarea[name=to]`）→ 设 value + input/change + Enter
3. 主题：`input[name=subjectbox]` → 设 value + input/change
4. **正文是 contenteditable**：`div[aria-label="Message Body"]`
   - 不能用 `.value`；要 `focus()` → 把选区折叠到开头 → `document.execCommand('insertText', false, text)`
   - 这样换行、中文、破折号都能正确保留
5. 发送：`[role=button]` 里 aria-label 以 `Send` 开头的（中英两版都匹配）
6. **按钮必须派发 pointer 事件序列**（pointerdown/mousedown/pointerup/mouseup + click），
   直接 `.click()` Gmail 不响应
7. 验证：`document.body.innerText` 出现 `Message sent`/`已发送`，再到 `in:sent to:<addr>` 搜一遍

### 已验证
- 正文 1378 字符的回信发到真实客户 → Sent 里读到完整正文
- 通道测试信发到 kerry@ → 收件箱里读到完整中文正文（不再是空信）

### 已知限制
- 需要 Chrome 前台激活（后台标签会被节流）→ 先 `osascript -e 'tell application "Google Chrome" to activate'`
- compose 是异步渲染，打开后要等 ~9 秒再填

## 多浏览器（2026-11-21 实测，重要）

**WebBridge 跟随「最近连接的浏览器扩展」**，同一时刻只有一个连接。本机 Chrome 与 Edge 都装了 Kimi WebBridge 扩展：

| 场景 | 结果 |
|---|---|
| Chrome 与 Edge 同时开 | 桥连的是 **Chrome**（先连/抢占），`navigator.userAgent` 无 `Edg/` |
| 业务账号只在 Edge | 所以会出现「GSC 显示无权限 / Gmail 是个人邮箱」的假故障 |
| **关掉 Chrome（pkill 主进程即可，osascript quit 常被 TCC 拒）** | 桥自动切到 **Edge**（`extension_id` 变化、UA 带 `Edg/157.0.0.0`） |

**切换步骤（实测可用）**：
```bash
pkill -f "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"   # 关 Chrome
open -a "Microsoft Edge" "https://mail.google.com/mail/u/0/#inbox"        # 确保 Edge 扩展在线
python3 scripts/browser/wb.py status   # 期望 quora/gsc/brevo 全 ✅
```

**教训**：遇到"登录态消失"，先看 `wb.py status` + `navigator.userAgent` 判断桥连的是哪个浏览器，**不要急着断定账号失效**。
Edge 上的账号（2026-11-21 实测）：Quora ✅ / GSC ✅ / Brevo ✅ / Gmail=Anari EV Mail ✅ / Cloudflare ❌（仍需单独登录）。
