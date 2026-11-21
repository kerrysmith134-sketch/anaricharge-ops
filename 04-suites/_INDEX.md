# 套件索引（04-suites）

> 套件 = 「按序编排」的工作流/技能组合，一条命令启动，有明确输入、产出、时长、验收。
> 来源：`AI营销团队增强报告-v3-136技能.md:276-316` 的四个黄金组合 + 本工作区补充的两个产线级套件。
> 每个套件文件内的步骤引用 `03-workflows/W*.md`，技能名以 `02-skills/_MERGE-MAP.md` 为准。

## 套件总表

| 编号 | 名称 | 启动前置 | 串联工作流 | 总时长 | 状态 |
|---|---|---|---|---|---|
| [S1](S1-inquiry-growth-launch.md) | 询盘增长启动包 | P0 手动配置完成（GSC/GA4/GTM/OpenSEO + product-marketing.md） | W8 → W14 → W6/W20 → W11 → W10 → W12 | 3–5 天（一次启动，两周见效） | 可启动（付费/外联受人工限制） |
| [S2](S2-seo-geo-growth.md) | SEO + GEO 增长包 | 站点镜像就绪 + GSC API 可用 | W3 → W8 → W6 → W4 → W13 → W5 | 2 周 | 可启动 |
| [S3](S3-paid-media-diagnostic.md) | 付费媒体诊断包 | **预算决策变更（当前 $500 全有机）** + 广告账户凭证 | 打分审计 6 技能（不接站点工作流） | 半天 | **暂停**（模板保留） |
| [S4](S4-growth-experiment-engine.md) | 增长实验引擎 | GA4 归因后台配置完成（用户）+ 基线流量 ≥1000 展示/月 | W19 → W20 → W12 → W4 → W16 | 4–6 周/实验 | 条件启动 |
| [S5](S5-content-weekly-pipeline.md) | 内容周产线包 | W8 队列已批准 + 站点镜像同步 origin/main | W8 → W9 → W6×5 → W7 → W17 → W18 → W13 → W21 | 1 周（每日约 2.5h） | 可启动 |
| [S6](S6-monthly-review-pack.md) | 月度复盘验收包 | 本月周报 ≥3 份 + 验收基线 | W19 → W2 → W16 → 用户决策会 | 1 天 | 可启动（月度） |

## 一条命令启动（约定）

```bash
# 在 /Users/kerrychu/anari-charge-website 下执行；S 换成 S1..S6
S=S1; D="08-execution/suites/$(date +%Y%m%d)-$S"; mkdir -p "$D"
cp 04-suites/$S-*.md "$D/plan.md"
printf '{"suite":"%s","started":"%s","status":"running"}\n' "$S" "$(date -Iseconds)" > "$D/run.json"
echo "启动：读 $D/plan.md，按序执行步骤；每步产出落 $D/"; echo "$D"
```

- 启动后 agent 逐步执行套件文件中的「步骤」；每步把产出写到 `$D/step-N-*.md`，并更新 `run.json` 的 `status/step`。
- 任一步命中人工卡点（G1–G17）→ 停下并在 `run.json` 记 `blocked_on`，写进用户待办；**不跳过、不代做**。
- 套件结束生成 `$D/summary.md`：完成步骤 / 卡点 / 产出清单 / 验收对照 / 下一步。

## 与单工作流的关系

- 套件是**编排**，不新增业务流程；任何一步都复用对应 `W*.md` 的步骤、命令、验收、失败处理。
- 套件级验收 = 各步验收 + 1 个业务结果指标（如「询盘增长启动包」验收是「首批 ≥3 条可跟进线索」）。
- 同一工作流可被多个套件复用（如 W6 同时属 S1/S2/S5）；并发启动时按 `_SCHEDULE.json` 档位错峰，避免同站点分支冲突。
