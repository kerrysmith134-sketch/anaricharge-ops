# ChatGPT 获客审计 · 行动项完成度对账清单

- **审计文档**：`ops/chatgpt-acquisition-strategy-20261022.md`（3843 行，2026-10-22 入库，commit 18bbdd6）
- **对账日期**：2026-10-22（首次）/ 2026-10-22 深夜刷新（Worker v2 部署后，commit 73a89a4）
- **判定依据**：plan.md 2026-10-22 记录 + 仓库代码/文件逐项抽查 + 生产端点 curl 验收实证（非仅凭记录）
- **状态口径**：✅ 已完成且有实证 / 🟡 部分完成（注明缺口）/ ⬜ 未做（注明阻塞）
- **行号口径**：`L####` 指审计文档行号；`§P0-x/§P1-x/§P2-x` 指文档末尾「升级实施方案」收敛版章节

## 汇总

| 状态 | 数量 |
|---|---|
| ✅ 已完成 | 12 |
| 🟡 部分完成 | 15 |
| ⬜ 未做 | 9 |
| **合计** | **36** |

## 一、P0：业务可靠性（第一阶段）

| # | 行动项（出处） | 状态 | 证据 / 缺口 |
|---|---|---|---|
| 1 | 统一询盘提交标识 submission_id + 服务端确认 + 幂等（§P0-1 L3272；L2444；L3151） | ✅ | **2026-10-26 全链路打通**（commit 64ffb32）：前端提交瞬间生成 UUID（track.js）→ 隐藏字段进 Web3Forms 邮件 + 成功页 beacon 送 Worker → D1 主键 + Brevo ANARI_SUBMISSION_ID 属性；服务端幂等第 0 层实测 deduped。GA4 侧参数待 GTM 后台配置（见 #15） |
| 2 | CRM 中继持久化、失败重试、幂等、死信、限流（§P0-2 L3319；L1809；L2761） | ✅ | **2026-10-22 已部署上线**（commit 73a89a4，版本 2cbfc3a8）：D1 `anari-leads` 落库优先 + 指数退避 3 次 + 死信 + 邮箱+表单类型+10 分钟窗幂等 + IP 散列 5 次/10 分钟 429 + Origin 白名单。生产 curl 验收 4/4 通过（正常提交 sent / deduped 同 ID / consent=0 只存档 / 第 6 次 429），测试数据已清理。注：外发目标是 Brevo（列表 3 Inquiry Nurture），HubSpot 对接是独立的 #9 |
| 3 | 修正转化事件定义，失败提交不计成功、刷新不重复计数（§P0-3 L3353；L2760；L2406） | 🟡 | 已上线：`?sent=1` 幂等门 + `checklist_request` 改为 fetch `r.ok` 成功回调内上报（track.js L239-240 注释实证）。缺口：审计要求的完整事件分层（form_start/submit_attempt/submit_success/submit_failure/crm_sync_success/lead_qualified…）未建立，`ops/gtm-event-setup.md`（87 行）未同步更新事件口径，GTM 后台未核验 |
| 4 | 统一营销授权、退订与隐私政策（§P0-4 L3389；L3150；方案 B L2843） | 🟡 | 方案 B 已上线：EN/RU/ES 询盘页订阅勾选框（默认不勾，`f-consent`/`marketing_consent` 实证）、consent+时间戳暂存、nurture 仅 consent=1 时发送（inquiry.html L571 实证）、privacy.html 删除虚假声明并如实描述 Brevo opt-in。缺口：统一退订/抑制名单（Consent & Suppression Registry）未建，退订依赖 Brevo 邮件内链接；删除请求仅邮箱人工流程，不可追踪 |
| 5 | 收紧 GitHub 自动合并权限与验证规则（L1810；L1376-1437；L2658） | ✅ | Gatekeeper 新增风险分级：内容白名单外变更（代码/交互/配置/询盘页/tools）不再自动合并、PR 留言转人工（`.github/workflows/pr-gatekeeper.yml` L103-125 实证）；新增事实门步骤；Regenerate 补 llms-full 重建。残留小问题（Actions 未 pin SHA、写权限未拆最小权限 Job）并入 #21 |
| 6 | 首页转化重构（L1714 P0；L1812） | ✅ | 已上线（commit e42824e→994bd9c）：jordan-station 真实摄影 hero、信任条前置、客户六站路径图、客群四卡直链 `/journey/segment?segment=`、任务三卡（三语首页各 5 处 jordan-station 引用实证）；线上 curl 验证通过 |
| 7 | Inquiry 页转化改造：完成率、反馈质量、提交可靠性（L1715 P0） | 🟡 | 提交可靠性部分完成（幂等门、同意勾选、Journey 预填 `?ref=&segment=` 与 `mc_journey_brief` 同意传递，inquiry.html L375-440 实证）。缺口：表单完成率导向的 UX 重构（字段精简、分步、内联校验之外的转化设计）未做 |
| 8 | 复核 BESS 套利公式与示例数字（L2331 P0；§P1-2 L3451） | ✅ | 公式修正已上线：`E_out×(P_high − P_low/η)`，效率损耗计在充电侧（bess-tco.html L253/L398 实证），新增谷价输入，主示例 $17,521/5.6 年 → $18,900/5.1 年，硬件表与敏感性表全部重算，node 复核 JS 与静态数字一致 |
| 9 | 核实并修复询盘到 HubSpot 的实际连接（L1808 P0；L1173-1210） | 🟡 | **2026-10-22 负责人拍板分工：Brevo=营销（培育/订阅序列，已上线），HubSpot=销售（商机跟进）**。网站询盘→Brevo 链路已通（Worker v2）；Brevo→HubSpot 的销售交接桥待建。缺口：HubSpot 账号侧凭证/管线配置 + 交接规则（何时从培育转销售） |
| 10 | 端到端验收：一次完整测试询盘核对浏览器事件/服务端/CRM 三方一致（L3387 验收标准；L2502；L3835 第一批第 4 项） | ✅ | **2026-10-26 通过**：浏览器埋点（inquiry_view/归因固化实测）→ curl POST nurture 200 → D1 行字段完整 status=sent → Brevo List 3 联系人 subscribed，三方一致；CORS 白名单 204/403 边界实测；测试数据已清。GTM/GA4 后台核对转入 #15 的待用户处理 |

## 二、P1：工具与内容成为销售资产（第二阶段）

| # | 行动项（出处） | 状态 | 证据 / 缺口 |
|---|---|---|---|
| 11 | ROI 计算器专业模式（§P1-1 L3421；L2338） | ✅ | 已上线（c51debc）：Professional 模式——利用率爬坡、购售电价及年递增、需量电费、四项 opex、初始+更新投资、三情景、5–15 年、逐年现金流、NPV/IRR/回收期、敏感性矩阵；两组独立 node 验算分毫不差，边界无 NaN（charging-station-roi.html 1232 行、L283-406 实证） |
| 12 | Journey 三态区分 + 可追溯 + 简报传递（§P1-3 L3491；L2117 静默降级问题） | ✅ | journey.js v2（838 行）：demo/rules/ai 三态徽章、Agent 失败只标 rules 绝不伪装 AI（L14 注释实证）、每步引擎/版本/状态/耗时/输入追溯、输入完整性硬校验、S4 财务与 bess-tco 公式对齐、S7 项目简报+一键复制+同意传递（`mc_journey_brief`）。AI 端点未接属审计允许范围（保留回退但诚实标注） |
| 13 | 内容事实库 + 事实质量门禁（§P1-4 L3511；L2219；L2341） | ✅ | `ops/fact-library.json` + `scripts/check-facts.js` + Gatekeeper 接入（check-facts 非零不合并，yml L100-101 实证）。当前 62 条全部 verified——400 页脚电话条目已按负责人 2026-10-22 决定**从模板契约与事实库一并删除**（commit 8b33014），功率口径条目已转 verified |
| 14 | 统一功能状态目录（§五 L3548；L2534；L2763） | ✅ | `ops/system-capabilities.json` 实测 29 项能力（plan 记 26 项），含 capability_id/状态/验收方法字段；**2026-10-22 刷新：`nurture_worker` 已随 Worker v2 上线转 live**，剩余非 live 项（hubspot_relay、indexnow_keys planned）如实标注 |
| 15 | 网站行为→CRM 商机归因模型（L1811；L370 Growth Data Layer） | 🟡 | **Phase 1 代码侧 2026-10-26 上线**（commit 64ffb32）：三级 ID + submission_id 四方对账键 + 双快照（first-touch 主口径/last-non-direct 副口径）+ 内容路径 + D1 五新列 + Brevo 7 个 ANARI_* 属性 + 隐私披露同步。剩余：GTM/GA4 后台配置（ops/gtm-event-setup.md 末节，待用户）+ Brevo 属性一眼核对（待用户） |
| 16 | 客户细分落地页改造（L1716 P1） | 🟡 | who-we-serve 4 个细分页（cpo-entrepreneurs/fleet-operators/engineering-contractors/energy-real-estate）存在，首页客群卡已直链 Journey 预填。缺口：细分页本身未按审计目标（让该客群快速找到相关方案）做内容与转化重构 |
| 17 | 完善案例证据链（L2764 P1；L2678-2718） | 🟡 | fact-library case 8 条 verified；jordan-160kw 页有 Source/Last verified 徽章与「客户要求匿名」说明（L269-376 实证）。缺口：审计要求的完整证据链（测试报告、可用率统计口径、客户授权披露范围、ROI 计算口径）未系统补齐 |
| 18 | 聊天进度/表单数据的浏览器存储管理（L3153 P1；L3012-3043） | 🟡 | lead-chat.js 完成时 `clearStore()` 已有（L117/401 实证）。缺口：无 TTL 有效期机制、无明确「主动重新开始」入口的实证、多人共用设备提示未做 |
| 19 | 询盘反垃圾加强（L3154 P1；L3047-3074） | ✅ | honeypot(botcheck)+Origin 白名单 CORS + **IP 散列限流 5 次/10 分钟 + 幂等去重已随 Worker v2 上线**（生产 429 实证）。Turnstile 未引入——审计亦建议不强制验证码，属合理取舍 |
| 20 | GA4 与追踪同意状态线上核验（L3155 P1；L2977-3008） | ⬜ | 未做。阻塞：需干净浏览器实测 + GTM 后台核对（Consent Mode、事件标签、Cookie 写入时机），纯代码侧无法完成 |
| 21 | CI/CD 升级：统一构建 + 风险分级测试 + 预览/审批/冒烟/回滚（§六 L3588；L2762 P0；L2590-2630） | 🟡 | 统一构建已补齐（Gatekeeper Regenerate 含 sitemap+md 镜像+llms-full，L74-78 实证）；风险分级转人工已实现；部署手册有一键回滚说明。缺口：JS 单测、浏览器/e2e 测试、视觉回归、预览部署、发布后冒烟测试均无；Actions 用 `@v4` 浮动标签未 pin SHA；写权限未拆独立最小权限 Job |
| 22 | validate.js 升级为分级质量引擎（Blocker/Major/Minor/Warning）（L1441-1500） | ⬜ | 未做：validate.js 无 severity 分级证据；事实语义校验改由独立 check-facts.js 承担（部分等效），但「分级结果 + 自动修复与验证分离（site-fixes.js）」未实现 |
| 23 | 营销数据治理层四组件：Submission Registry / Consent & Suppression / Delivery Queue / Audit Log（L3078-3142） | 🟡 | A（提交登记）与 C（投递队列）**已随 Worker v2 D1+重试+死信上线**；B（授权与抑制名单）仅有前端 consent 记录，统一抑制名单未建；D（审计日志）未做 |
| 24 | 建设五个 Skill：website-release-qa / content-evidence-qa / search-opportunity-analysis / lead-conversion-analysis / calculator-validation（L2311；L3716） | ⬜ | 未建。仓库内无对应 skill 文件（仅审计文档自身提及）。事实门+validate 已覆盖其中两个 Skill 的部分职能，但非 Skill 形态 |
| 25 | MCP 只读连接 GitHub/Cloudflare/GSC/GA4/HubSpot，最小权限+审批（L2321；L3733） | ⬜ | 未按 MCP 形态建设。注：GSC 数据已通过官方 API 在迭代中使用（plan.md 10-21 记录），但其余四源未接，权限审批机制未建 |

## 三、P2：持续增长闭环（第三阶段）

| # | 行动项（出处） | 状态 | 证据 / 缺口 |
|---|---|---|---|
| 26 | P2-1 连接搜索、网站与 CRM 数据，统一分析维度与核心指标（§P2-1 L3656；L2345） | 🟡 | 前置设计完成（attribution-model.md 双快照归因+四方对账键）；**Worker v2 已部署，启动钥匙已就位**，实施待排期 |
| 27 | P2-2 内容增长闭环：内容效果→询盘→商机反馈驱动更新（§P2-2 L3682；L2237 闭环 1） | ⬜ | 未做。营销团队内容管线在跑且有 Gatekeeper 质量门，但「内容→有效询盘→商机」的效果反馈闭环无数据通路（依赖 #26） |
| 28 | P2-3 视觉与转化实验机制（§P2-3 L3696；L2281 闭环 4） | ⬜ | 未做。无 A/B 或分阶段实验框架；首页改版 8 条验收标准中 #1/#2（点击深度/路径长度）待 1–2 周 GTM/GA4 数据回收 |

## 四、未标优先级但明确建议的项

| # | 行动项（出处） | 状态 | 证据 / 缺口 |
|---|---|---|---|
| 29 | 转化入口多样化，按决策阶段提供不同下一步（L678 七.1） | ✅ | 首页重构后达成：六站路径图（规划/选型/验证/测算/交付/运营各链对应工具）、任务三卡 Plan/Calculate/Learn、客群卡直链 Journey 预填、邮箱捕获上移——不再是单一通用表单 |
| 30 | 询盘质量评分（可解释规则模型，区分 Lead Score 与 Deal Probability）（L693 七.2） | ⬜ | 未做。CRM 分工已定（Brevo 营销 / HubSpot 销售，2026-10-22）；剩余阻塞：评分规则需结合销售反馈数据拍板，建议积累 4–6 周真实询盘后再定规则 |
| 31 | 自动化销售交接：询盘摘要→CRM 建档→分配→跟进建议→结果回传（L720 七.3） | ⬜ | 未做。分工已定：询盘→Brevo 建档已通（Worker v2）；待建的是 **Brevo（营销）→HubSpot（销售）交接桥**——触发条件（如评分达标/回复培育邮件）、HubSpot 管线配置需业务拍板 |
| 32 | 自动化检查扩展：视觉回归、JS 错误监控、接口可用性、部署告警、CWV 监控（L761 八） | 🟡 | CWV/性能做过一轮实修（10-21 字体 preload/GTM preconnect/logo decoding，validate+线上 curl 验证）；Cloudflare Web Analytics 可用。缺口：视觉回归、错误监控、部署告警未建制化 |
| 33 | 品牌设计系统升级（设计 Token、组件库、页面模板、移动端规范）（L75-221 二；L854） | 🟡 | 首页三语已按提案重构并有截图评审；全站设计 Token/组件库/视觉回归测试未建（审计收敛版亦将其排在可靠性之后） |
| 34 | 五类核心内容资产：解决方案页/国家市场页/技术知识库/真实案例/互动工具（L405 五.1） | 🟡 | 五类资产均已存在并持续扩充（who-we-serve、markets、academy/blog、cases、tools 目录实证）。缺口：案例证据链（#17）与技术内容专家审核机制未完全落地 |
| 35 | 内容质量八项门槛：意图/原创/事实/深度/差异化/结构/转化/品牌（L501 五.2） | 🟡 | 「事实准确性」已由事实门覆盖；「页面结构」由 validate.js 覆盖。缺口：原创价值、搜索意图、商业转化的评分/审核未自动化 |
| 36 | Growth Brain 增长决策引擎 + 项目 A/B/C 总框架（L540 六；L936 十一） | ⬜ | 未做。审计自身定位为长期方向（P2 之后/第四阶段），属合理排后期 |

## 五、关键结论（2026-10-26 二次刷新）

1. ~~P0 服务端半边卡在 Worker v2 未部署~~ → **已解除**：Worker v2 2026-10-22 部署上线，验收 4/4（commit 73a89a4）。P0 服务端能力（submission_id、D1 持久化、重试、幂等、限流、死信）全部在生产运行。
2. ~~需要业务决策的口子~~ → **已全部拍板**：CRM 分工定为 **Brevo=营销培育（已上线）/ HubSpot=销售跟进（交接桥待建）**（#9/#30/#31，2026-10-22 负责人决定）；400 电话条目已删。
3. ~~两个无法纯代码侧完成的核验~~ → **#10 端到端三方对账 2026-10-26 已通过 ✅**；剩 GA4/同意线上核验（#20）与 Phase 1 新参数的 GTM/GA4 后台配置属人工项，已列入 plan.md 待用户处理。
4. **P2 三项中 #26 归因 Phase 1 代码侧已上线**（2026-10-26，commit 64ffb32：submission_id 四方对账键 + 双快照 + 内容路径 + D1/Brevo 缝合）；#27 内容闭环待 GA4 侧参数配置完成后有数据可回；#28 实验机制待首页改版 1–2 周数据回收。
5. 审计文档自己的最终建议（L3830-3841）「第一批四项」对照现实：**询盘状态/转化事件 ✅、CRM 持久化重试 ✅、端到端测试 ✅（2026-10-26）、营销授权退订 🟡（方案 B 上线，抑制名单未建 → #23 在队）**。
