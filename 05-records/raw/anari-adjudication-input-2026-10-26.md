# 插队选题裁决输入（编排复核员 → 周一 22:05 周复盘）

> 复核窗口：2026-10-25 20:47–21:00（策略师周日 20:17 周期产出完成后）。
> 复核范围：`anari-daily-ops-plan.md` 第三节 D1-D10 队列、`anari-keyword-map.md`（含底部 JSON）、`serp-2026-10-25.txt`（13 词 US 实测）、`anari-competitor-intel-2026-10-22.md`。
> 性质：复核建议，非裁决。裁决权在周一复盘与用户（用户对插队有一票否决权）。

## 一、三个候选词的裁决建议

| 候选词 | 策略师处置 | 复核建议 | 核心理由 |
|---|---|---|---|
| china ev charger manufacturer / ev charger factory 簇 | **插队 D1（10-27）**，买家评估指南角度 | ✅ **追认** | 来源为最新情报报告 §一.2（EVB 独占该簇 p1-2、我方零覆盖）；10-25 SERP 实测无 AIO、top10 全小站、Reddit p5 社区缺口，可赢判断与原始明细逐项相符 |
| what is dynamic power management | **折入 D2** 开篇 40 字定义，不单独成篇 | ✅ **追认** | 竞品情报词（KD 0/月量 1300），SERP 可赢（Tesla×2 居前、小站 p5-10）但与 D2 load management 意图重叠，折入处理正确防了自我竞争 |
| ev charger repair | **否决，未入队** | ✅ **同意否决** | SERP=local_pack×3 + 本地电工服务小站（longview/Ada/SanDiego 等），本地服务意图与我方 B2B 制造商身份不符；EVB p10 是其品牌词优势不可复制。本周未消耗队列项，否决零成本 |

## 二、追认 D1 的附带红线条件（写入裁决备注）

1. **不点名任何竞品**、不写 "Top N manufacturers" 清单——写「评估框架」（CE/UL 认证、质保、备件、OCPP 兼容、产能审核、物流）。
2. 公司事实口径只用「**22 国 100+ 客户**」。
3. 与迭代池 China OEM 着陆页（a-comp-china-oem-page，11-05 到期）保持错位：D1=买家指南博客，LP=厂商页；两条线推进时防撞意图。

## 三、复核通过项（供复盘记录）

- 自我竞争：D4 与 dc-fast-charger-maintenance-cost、D8 与 franchise-profit、D9 与 bess-valuation-software 的错位/互链规则均在队列行内写明；D5（保险）、D7（加油站）零覆盖声明经 sitemap 抽查属实；D10 为 CTR 刷新任务非新文。
- 词图底部 JSON 经 python3 校验合法（updatedAt=2026-10-25，23 个词簇）。
- 档期正确：D1-D10 按周二至周六排（10-27→11-07），跳过周日/周一。

## 四、观察项（不阻塞，提醒）

- 本地 sitemap 副本为 101/103 URL，与策略师引用的 origin/main 106 URL（10-25 拉取）不一致；复核按进度记录 105→106 递增链交叉验证无误，但严格撞车核对建议以 origin/main 106 版为准。
- D8 收入模型枢纽篇与 franchise-profit/operating-cost 的边界靠「禁重写 margin 数学」执行约束，依赖主编写稿自律，合并前验收可重点看这一条。
