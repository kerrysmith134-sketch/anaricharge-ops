# 迭代计划 · 2026-09-25（全面检查 + 一次转化迭代）

> ⚠️ **已过期（superseded），仅作历史留档，勿执行 §5 runbook。**
> 本文件写于本地 `main` 落后 `origin/main` 46 提交、shell 不可用的窗口。§1/§2/§3 的"转化层未上线 /
> main 仍有 400 电话 / track.js 不在磁盘"等结论，均以**旧本地 main**（90c83d6）为基线。
> 现已同步至 `origin/main` = `7e37baa` 并核验：`track.js`（含 UTM 归因）/`motion.js`/`lead-chat.js`/
> `sitemap.md` 均在树内，`400-827-9882` 全站 0 处（已改 LinkedIn），`seo/week1-content` 的合并
> （`7ba7348`）早已完成——即 §5 的 merge 已发生，**不要再跑一遍**。
> 当前真实状态与本轮"全面复检 + 迭代"的落地记录见 `plan.md` 末尾 "2026-09-25 全面复检 + 迭代" 一节。

> 本文件基于 **实际磁盘与 `.git` 核验**，不是继承会话的描述。写于执行 shell 不可用的窗口，
> 恢复工具后可按 §5 直接执行。

## 1. 已核验的事实（可信）

| 项 | 值 | 来源 |
|---|---|---|
| 当前分支 | `main` | `.git/HEAD` |
| `main` HEAD | `7e37baa` | `.git/refs/heads/main` |
| 未合并分支 | `seo/week1-content` @ `c229816`（约 31 提交） | `.git/refs/heads/seo/week1-content` |
| 分支间关系 | `main` 与 `week1` 已分叉；`main` 曾从 `90c83d6` 被**主动 reset** 到 `7e37baa` | `.git/logs/HEAD` L34–40 |
| 部署 | Cloudflare Pages 跟踪 `main` → 线上 = `7e37baa`（本轮未能 curl 复核，shell 不可用） | — |

## 2. 核心结论：转化层"有，但没上线"

`seo/week1-content` 里有一整层**未合并**的转化/体验工作，线上 `main` 完全没有：

- `site/assets/js/track.js`（9 事件 + UTM 归因）— **磁盘上不存在**
- `site/assets/js/motion.js`（动效层）— 不存在
- 400 电话 → LinkedIn 替换 — **未做：首页页脚与 JSON-LD 仍是 `+86-400-827-9882`**
- HubSpot CRM 对接 + GTM 事件配置手册 — 不在 main
- 对话式询盘浮窗、明暗双主题视觉包、AGENTS.md / Markdown 镜像 — 不在 main
- `generate_lead` 目前只在 3 个询盘页 `?sent=1` 触发，无 UTM/来源字段进表单

**即："本周更新没完成"= 这层工作被留在分支上、main 被 reset 回简化态，所以线上仍显示 400 电话、无归因埋点。**

## 3. 回归风险（务必先复测再合并）

`week1` 分支提交史里有：
`fix(motion): reveal 兜底——IO 不触发时内容永久隐藏导致"大白板/显示不全"`（`bf8b1c4`）。
说明该分支的 reveal/入场动效**曾造成整片内容不可见**的严重缺陷（已在分支内修，但要**重新验证**再上线）。
盲目 `git merge` 可能把"内容被隐藏"的边界情况带上线。

## 4. 两条执行路径

### A. 合并 week1 → main（杠杆最大，推荐）
复用已写好的转化代码，补一次关键回归验证后上线。

### B. main 为基线，重建聚焦转化层（更干净）
忽略分支，把最小闭环（`track.js` 事件+UTM归因 + 400→LinkedIn + 全站 sticky CTA）
作为独立增量重做。风险低、不引入分支上的暗区，但放弃已完成的 20+ 提交。

> 建议 **A**，前提是 §3 的 reveal 回归 + 首屏可见词数复测通过。若 week1 上 CSS/视觉改动
> 太"暗"或难以抽验，则退 **B**。

## 5. 恢复工具后按此执行（runbook）

前置：`git status` 确认干净；`git log --oneline main..seo/week1-content | head` 看差异量。

```bash
cd /Users/kerrychu/Documents/kimi/workspace/anaricharge-website
# A: 合并
git checkout main
git merge --no-ff seo/week1-content          # 预期有冲突（main 被 reset 过）
#   冲突解决原则：转化/埋点/归因文件以 week1 为准；纯文案/SEO 以 main 现状为准

# 回归闸门（合并后必过）
node validate.js                              # 单 h1 / 死链 / FAQ 对齐
node build-sitemap.js && git add sitemap.xml

# reveal 可见性回归：无头浏览器在 320/768/1440 各渲染 index + 一页正文，
# 断言 body 可见文本字数 > 阈值（防"内容被永久隐藏"）。IO 失败时走 reveal 兜底分支。

# 400 电话清零确认（LinkedIn 落地后）
! grep -rn "400-827-9882\|4008279882" site/index.html site/inquiry.html

# 部署
git commit -am "merge: week1 转化层并入 main（含回归复测）"
git push origin main                          # Cloudflare 自动部署
```

## 6. 我现在被卡住的地方（需要你）

1. **执行环境**：本轮 `Bash` 持续返回 "Execution adapter is shutting down"，无法
   `validate` / `build-sitemap` / `git push`。请确认 shell/沙箱是否可恢复。
2. **路径 A vs B**：是否复用 week1 分支（A）还是重建（B）。若 A，接受先过 §3 回归闸门。
3. **LinkedIn URL** 与 **HubSpot 凭据**：400 替换与 CRM 对接都依赖这两个真实值。

## 7. 最小转化闭环（无论 A/B 都应确保最终具备）

1. `track.js`：`segment_select / journey_step / journey_complete / inquiry_view /
   whatsapp_click / generate_lead` + **UTM 会话首次落地归因**（写 sessionStorage，不被站内跳转覆盖）
2. 询盘表单提交前注入 `attr_line / attr_source / attr_medium / attr_campaign / attr_landing`
   隐藏字段（Web3Forms 或 HubSpot 都能带）
3. 全站 sticky CTA + 联系条（WhatsApp/Email/LinkedIn），400 电话下线
4. 三条流量线打标（outbound / anariev 反向 / organic·AI），供每周复盘分流
