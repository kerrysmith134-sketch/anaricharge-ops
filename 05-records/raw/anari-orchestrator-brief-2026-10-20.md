# 营销编排简报（2026-10-20）

> 只读汇总：分派单 anari-handoff-2026-10-20.md × anari-weekly-actions.json × 三组日志尾部交叉核对。

## 【各组上周产出】

- **外链组**：10-20 单日高产——13 封邮件经用户确认发出（12 封第 4 天跟进 + Canary 首发，状态全部转「已跟进/已联系」）；目录注册 4 家全部终态（TradeWheel / TradeKey / ExportHub 注册成功，OCM 持既有账号不提交 POI）；EVTrader（WhatsApp）/ smarter E / PowerStationHQ 三封收录申请已由用户从 sales@ 发出。OpenSEO 复测恢复：backlinks 40 / 引用域 38（自然收录口径，主动成果仍为 0）。
- **社区组**：Quora 10-19/10-20 各发 1 条纯干货回答（功率档位成本、建站成本五层框架，均三证验证通过）；W43 带链接配额已用 1/3（ROI 六行稿 10-19 由平行会话发布）。Reddit 储备池达 10 条（R9 供应商尽调 / R10 二手设备尽调），遵守养号纪律未发帖。
- **数据组**：GSC 周报（10-11~10-17）——展示 116（+55）、点击 1（-1）；唯一点击来自 business-plan 博文；「ev charging business case template」词排第 10 零点击，已由 10-20 上线的姊妹篇承接（actions.json a-business-case-post=done，PR #25 合并、IndexNow 已提交）。
- **优化/内容组**：business-case-template 博文 10-20 上线并与 business-plan 双向内链；franchise CTR 二轮改写素材包备妥，待 10-24 快照条件触发。

## 【遗留项与阻塞】

| 事项 | 负责组 | 状态 | 阻塞原因 |
|---|---|---|---|
| Franchise 两篇 CTR 二轮改写 | 优化组 | todo（条件触发） | 等 10-24 周五 GSC 快照判定（CTR=0% 且展示≥15 才执行） |
| fact-30-countries 口径 PR 补建 | 优化组（验收员） | 待明日 10:43 档 | 远端分支已消失且 main 无合并，全站仍 22 countries |
| GA4 generate_lead 点星 | 数据组 | **阻塞 >3 周** | 只有用户能操作（Admin → Events → 点星） |
| Reddit karma 报数 | 社区组 | 阻塞 | 用户未报数，储备池已 10 条只等放行 |
| Qwoted 档案补完（剩 25%） | 外链组 | 阻塞 | 用户手动项（Title/公司关联已补，余标签类） |
| EVTrader / smarter E / PowerStationHQ 回复 | 外链组 | 待回复 | 10-24 周五复查；引导付费即按红线暂缓 |
| 12 家零回复者模板 H 收尾 | 外链组 | 排期 10-27 | 第 10 天节点未到 |

## 【组间冲突/依赖】

1. **22 国 vs 30 国口径链**：外链 13 封跟进稿与 Quora bio 均按 22 国口径发出（正确——官网线上版仍是 22）；口径切换硬依赖 fact-30-countries PR 明日补建合并，合并后下一批外联稿才切 30+，不可提前。
2. **W43 Quora 带链接配额剩 2 条但暂无排队草稿**：ROI 稿（原 W43 首选）已于 10-19 提前发布，solar 稿 10-18 延迟落袋——分派单"ROI 草稿为首选"已过时，社区组需为剩余 2 个配额补选题（建议承接本周 business-case-template / used-equipment 新文）。
3. **actions.json 覆盖面不足**：GA4 点星、Reddit karma、Qwoted 三项用户阻塞在分派单 §用户待办中挂着，但未登记进 anari-weekly-actions.json（清单仅 3 条）——看板读数会低估阻塞面，建议数据组下次运行时补登。

## 【给各组的本周提醒】

- **外链组**：10-24 周五出 Canary 第 4 天跟进稿 + 复查 EV4Life/ESI/Smart Energy 刊出痕迹 + 三封目录申请回复检查（付费引导即暂缓）。
- **社区组**：W43 带链接配额剩 2 条，先补选题再发；发帖纪律不变（每会话首发后 ~30 分钟窗口、验证失败隔 ≥2h 再查防重复提交）。
- **数据组**：10-24 09:17 GSC 周五快照首次自动运行，产出即判 CTR 改写触发条件；顺手把 3 条用户阻塞补登 actions.json。
- **优化组**：明日 10:43 档补建 fact-30-countries PR；合并后立即通知外链组切换 30+ 口径。
- **内容主编**：队列以策略师周日重置为准，今日无插单。

## 【需要用户处理】

1. **GA4 generate_lead 点星**（最高杠杆，5 分钟，已拖 3 周+——卡住全渠道询盘归因和漏斗 Widget）
2. **Reddit karma 报数**（u/Sad-Researcher3564 当前 karma，决定 10 条储备帖能否放行）
3. **Qwoted 档案补完**（剩 25%，记者请求平台的被动曝光入口）

---

**本周最需要关注的一件事：GA4 generate_lead 点星已阻塞 3 周以上，询盘归因为零意味着所有组的产出都无法被衡量——这是 5 分钟就能解开的全局瓶颈。**
