# ANARI Charge — AI 搜索可见度台账（双周测量）

## 表头

- **本期日期**：2026-10-29（CST；测量窗口 15:28–16:15 + 19:10–19:45 续跑，中段任务中断后恢复）
- **上期日期**：2026-10-22（首期基线）
- **趋势线**：anaricharge.com 被引次数：上期 **0/11 实测格** → 本期 **1/18 实测格**（宽松口径）。保守口径 **0/18**——唯一命中（ChatGPT Q1）出现在仍可使用账号记忆的临时聊天内，个性化嫌疑无法排除，详见诚实记录 ①
- **竞品被引/提及 Top3（本期）**：ChargePoint 2 格（Gemini Q2/Q10）、FLO 1 格（Gemini Q10）、Wallbox 1 格（Gemini Q10）；另有 SWTCH 1 格（Gemini Q10）、Blink Charging 1 格（Gemini Q1）——全部来自 Gemini，ChatGPT 十格零品牌
- **测量覆盖**：计划 30 格（10 题 × 3 引擎）；实测 **18 格**（ChatGPT 10/10、Gemini 8/10）；跳过 10 格（Perplexity 遇 Cloudflare 人机验证，连续第二期，按规则不绕）；未测 2 格（Gemini Q7：提交 2 次无响应 + 回答超时 2 次；Q9：提交 3+ 次无响应，疑账号级频率限制）
- **固定问题电池（10 题，与上期一致）**：
  1. turnkey EV charging solution for emerging markets
  2. how to become a CPO (charge point operator)
  3. EV charging station franchise cost and ROI
  4. DC fast charging station cost breakdown
  5. best EV charging business models 2026
  6. EV charging station demand charges reduction
  7. solar plus storage plus EV charging station design
  8. EV charging station grants and subsidies (NEVI / PM E-DRIVE)
  9. used / refurbished EV charging equipment buying guide
  10. EV charging for apartment buildings and condos

## 测量诚实记录（重要，影响读数解释）

1. **ChatGPT 中性化只做到一半**：本期改用「临时聊天」（?temporary-chat=true），但页面明示「此聊天可使用记忆、插件和自定义指令」——记忆仍可用。Q1 答案带 anaricharge.com 首页链接（utm_source=chatgpt.com，真实可点引用），但同答文字显示模型熟悉本站（"align with the customer profiles presented on Anari Energy's current turnkey website"），无法区分是联网检索命中还是记忆引导。**记 1 次被引 + 个性化嫌疑标注**。Q3/Q7/Q8 出现无链接的 "Anari Energy / For Anari EV" 文字提及 = 记忆个性化，**不计入**。
2. **ChatGPT 本期开始自主联网**：与上期「10/10 零外链」不同，本期答案带 utm_source=chatgpt.com 引用链接与 "Source:" 归属（如 Q4 引 USDOT），说明免费版模型本期自主触发检索。外链抽取基于 main 容器，侧栏会话链接已剔除；引用域名以答案内链接+Source 文本为准。
3. **Gemini 提交链路已修复**：CDP Input.insertText（同步 Angular 模型，Send 按钮转可用）+ 指针事件序列点击「Send message」，成功率从上期 1/10 → 本期 8/10。失败模式集中在 19:20 后（Q7/Q9 多次提交零响应，编辑器有文字、按钮可点但页面不提交）——疑账号级频率限制，非选择器问题。Gemini 引用以 "Source: X" 文字 chip 呈现（无 URL），账号为 Anari EV 企业 Workspace 号，Q6 出现 "Anari Energy" 无来源文字提及 = 个性化嫌疑，不计入。
4. **Perplexity 连续第二期跳过**：打开即 Cloudflare「正在进行安全验证」（Ray ID a5209505b955f7bb），等待 20 秒未放行，不硬试不绕。

## 明细表（问题 × 引擎）

| # | 问题 | ChatGPT（临时聊天/已登录） | Perplexity | Gemini（Anari EV 企业号） |
|---|------|---------|-----------|--------|
| 1 | turnkey EV charging solution for emerging markets | **引用：anaricharge.com 首页（utm_source=chatgpt.com，个性化嫌疑）**；竞品：无；推荐清单：无 | 跳过（人机验证） | 引用：无；竞品：**Blink Charging**（具名为新兴市场 turnkey 方案示例）；推荐清单：Blink 等 |
| 2 | how to become a CPO | 引用：无；竞品：无；推荐清单：无 | 跳过 | 引用：Source 文字源 ChargeTronix、Powerbank；竞品：ChargePoint（漫游互联例）；推荐清单：无 |
| 3 | franchise cost and ROI | 引用：无；竞品：无；推荐清单：无（"Anari Energy +1" 记忆提及，不计） | 跳过 | 引用：无；竞品：无；推荐清单：无 |
| 4 | DC fast charging cost breakdown | 引用：Source 文本 USDOT "Climate Strategies that Work"；竞品：无；推荐清单：无 | 跳过 | 引用：无；竞品：无；推荐清单：无 |
| 5 | best business models 2026 | 引用：无；竞品：无；推荐清单：无（含 Anari 记忆提及，不计） | 跳过 | 引用：无；竞品：无；推荐清单：无 |
| 6 | demand charges reduction | 引用：无；竞品：无；推荐清单：无 | 跳过 | 引用：无；竞品：无（"Anari Energy" 无源文字提及，个性化嫌疑，不计）；推荐清单：无 |
| 7 | solar+storage+EV design | 引用：无；竞品：无；推荐清单：无（"For Anari EV" 记忆提及，不计） | 跳过 | **未测**（提交 2 次无响应 + 超时 2 次） |
| 8 | grants & subsidies (NEVI/PM E-DRIVE) | 引用：无；竞品：无；推荐清单：无（含 Anari 记忆提及，不计） | 跳过 | 引用：无；竞品：无；推荐清单：无 |
| 9 | used/refurbished equipment buying guide | 引用：无；竞品：无；推荐清单：无 | 跳过 | **未测**（提交 3+ 次无响应） |
| 10 | apartment/condo charging | 引用：无；竞品：无；推荐清单：无 | 跳过 | 引用：无；竞品：**ChargePoint / FLO / Wallbox / SWTCH**（"Software providers (e.g., …)" 计费软件清单）；推荐清单：该 4 家 |

原始回答全文存于 `workspace/ai-vis-raw-2026-10-29/r_<engine>_q<N>.json`（18 份；Q7/Q9 Gemini 无回答可存）。

## 三行结论

1. **我们被引的变化**：0/11 → 宽松 1/18、保守 0/18。唯一命中是 ChatGPT Q1 对首页的链接引用，但测量环境仍带账号记忆，不能确认为纯有机 GEO 成果；趋势线要等中性账号就位后才真正可比（已连续两期登记，仍未落实）。
2. **竞品的打法动向**：竞品开始在 **Gemini** 的答案框具名出现——Q10 公寓/多户型题直接给出「ChargePoint / FLO / Wallbox / SWTCH」计费软件供应商清单，Q1 具名 Blink Charging 为新兴市场 turnkey 方案示例，Q2 CPO 题引用 ChargeTronix/Powerbank 图文源；ChatGPT 侧仍是零品牌的纯知识作答。竞品占位形态 = 场景化软件清单 + 图文步骤指南源。
3. **给 GEO 优化师/内容主编的建议**（已登记 anari-weekly-actions.json）：
   - ① 测量环境（提请用户）：为 ChatGPT/Gemini 建专用无 Anari 记忆的中性测量账号（临时聊天仍会读记忆，不达标）；Perplexity 测前请手动过一次 Cloudflare 验证保持会话——连续两期 10 格空白。
   - ② 公寓/多户型场景：AI 答案正在固化「计费软件供应商清单」位（ChargePoint/FLO/Wallbox/SWTCH 已占），我们 10-21 上线的 apartment-condo-ev-charging-roi 文建议补「计费软件与供应商选择」对比段（不点名贬损、只做选择框架 + 我方方案位），争取下期进入该清单。
   - ③ CPO 入门题：「how to become a CPO」在 Gemini 已引用 ChargeTronix/Powerbank 等步骤指南型图文源，而本站词图无对应支柱页——建议新增 become-a-cpo 步骤指南页（licensing/选址/软件栈/上线 checklist 结构 + 配图），对标该答案框的内容形态。

---
*测量方法：WebBridge daemon（session ai-vis），每题新会话提问，ChatGPT 用临时聊天 URL，Gemini 用 CDP Input.insertText + 指针事件点击提交；回答等待 ≤60s（Gemini 放宽至 110s）；抽取回答全文 + 外链 + Source 归属文本。只测量不互动。*
