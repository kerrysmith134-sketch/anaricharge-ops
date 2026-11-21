# 接管完整性校验报告

生成: `python3 scripts/verify-takeover.py --write 00-takeover/VERIFICATION.md`

**PASS 38 / FAIL 0 / WARN 0**

## 技能

- ✅ **源技能集合已解析** — agents=137 + claude独立=10 → 去重后 146
- ✅ **.agents/skills 已迁移** — 137 个目录
- ✅ **无遗漏技能目录** — 146 个目录全在
- ✅ **每个技能有 SKILL.md** — 146/146
- ✅ **全部有 frontmatter** — 146/146
- ✅ **frontmatter 字段完整** — name + description 齐全
- ✅ **_manifest 条目数与目录数一致** — 146 == 146
- ✅ **_MERGE-MAP 存在** — 24341 字符
## 工作流

- ✅ **工作流数量 ≥15** — 21 个 SOP
- ✅ **每个 SOP 含触发与验收** — 21/21
- ✅ **_INDEX 覆盖全部 SOP** — 21 个全链接
- ✅ **_SCHEDULE 可解析且引用有效** — 25 个档位
## 套件

- ✅ **套件数量 ≥4** — 6 个
- ✅ **套件内容非空壳（>800B）** — 6/6
## 执行记录

- ✅ **timeline.md 内容充足** — 46202B
- ✅ **current-state.md 内容充足** — 22743B
- ✅ **open-items.md 内容充足** — 23221B
- ✅ **decisions.md 内容充足** — 16436B
- ✅ **时间线条目 ≥100** — 123 条
- ✅ **时间线覆盖起点** — 含 7/9 月记录
- ✅ **原始记录快照** — 61 份
## 站点工程

- ✅ **找到站点镜像** — anari-new-site
- ✅ **site/ 文件数不少于源** — 镜像 402 >= 源 335
- ✅ **镜像 sitemap 已同步到线上（≥119）** — 119 URL
- ✅ **RUNBOOK.md 存在** — 6730B
- ✅ **ARCHITECTURE.md 存在** — 8247B
- ✅ **GATE-RESULTS.md 存在** — 5135B
- ✅ **质量门结果含真实退出码** — ok
## 文档链接

- ✅ **内部 markdown 链接可解析** — 59 条全通
## 浏览器自动化

- ✅ **wb.py 存在** — 10500B
- ✅ **ops.py 存在** — 11327B
- ✅ **能力文档存在** — 11345B
- ✅ **浏览器操作留痕** — 10 份证据
- ✅ **WebBridge 运行中且扩展已连接** — v2.0.34
## 执行产出

- ✅ **执行数据 JSON 合法** — 6 个
- ✅ **GSC 真实数据已拉取** — 点击 28 / 展示 2634
- ✅ **2026-11-07-daily-run.md 存在** — 11020B
- ✅ **TECH-FINDINGS-20261107.md 存在** — 5604B
