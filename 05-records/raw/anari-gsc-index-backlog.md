# GSC / IndexNow 待提交清单（网络恢复后一次性执行）

> 生成：2026-10-17 12:47。背景：本机到 github.com 网页版 / Google 全网 HTTPS 不通（DNS 锁定 20.205.243.166 路由中断），GSC 申请全部顺延。
> **开工前自检**：`curl -s -o /dev/null -w "%{http_code}" --max-time 10 https://search.google.com/search-console` 返回 200 才继续；仍是 000 就再等。

## 一、待提交 GSC 索引请求的 URL（共 12 个）

### A. 本轮合并上线（4 个，IndexNow 已提交 ✅，GSC 待做）
1. https://www.anaricharge.com/inquiry （CRO 改造后重新提交）
2. https://www.anaricharge.com/blog/ev-charging-station-operating-cost （D5）
3. https://www.anaricharge.com/blog/nevi-grants-ev-charging-station （D6）
4. https://www.anaricharge.com/blog/used-ev-charging-equipment （D7）

### B. 10/16–10/17 遗留（6 个，IndexNow/GSC 都欠）
5. https://www.anaricharge.com/products/aquila
6. https://www.anaricharge.com/products/castor
7. https://www.anaricharge.com/solutions/fleet-depot-charging
8. https://www.anaricharge.com/solutions/pv-ess-charging-solution
9. https://www.anaricharge.com/blog/ev-charging-franchise-kenya
10. https://www.anaricharge.com/blog/ev-charging-station-franchise

### C. 排队等合并（2 个，PR 合并 + 线上 200 后才加入）
- https://www.anaricharge.com/blog/ev-charging-revenue-share-hotels-parking （D9，seo/week6-content 待建 PR）
- https://www.anaricharge.com/blog/bess-valuation-software （D10，同上）

## 二、GSC 申请流程（WebBridge 浏览器，会话 seo-ops）

逐 URL 执行（每天额度 ~10-15 个，12 个一次跑完没问题）：

1. 导航 `https://search.google.com/search-console`（若 chrome-error：先开 `https://example.com` 建 session tab，再 evaluate `location.href=` 页内跳 GSC）
2. 等待页面出现站点选择器，确认属性 `www.anaricharge.com`
3. 顶部「检查搜索资源」输入框：URL 全文粘贴（native setter 赋值 + dispatch input 事件）
4. 等 ~1.5s → 按 Enter
5. 等 ~10s 出检查结果页 → 找文字匹配 `/request indexing/i` 的按钮
6. JS click 无效 → snapshot 拿 @ref 用 click action
7. 确认出现 "Indexing requested" 即完成；若显示 "URL is unknown to Google" 也要点 Request indexing
8. 每个 URL 间隔 ~20s，避免触发人机验证

### evaluate 赋值模板（curl 走 /tmp 临时文件，--max-time 55）
```
{"action":"evaluate","args":{"code":"(()=>{const i=document.querySelector('input[aria-label*=\"Inspect\"], input[placeholder*=\"Inspect\"], input[placeholder*=\"检查\"]'); if(!i) return 'NO_INPUT'; const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set; s.call(i,'URL_HERE'); i.dispatchEvent(new Event('input',{bubbles:true})); return 'filled';})()"},"session":"seo-ops"}
```

## 三、IndexNow 批量提交（可重复跑，幂等）

```bash
cat > /tmp/indexnow-req.json <<'EOF'
{"host":"www.anaricharge.com","key":"07a4fc3586fd43710c5ea08299d05c43","keyLocation":"https://www.anaricharge.com/07a4fc3586fd43710c5ea08299d05c43.txt","urlList":[
"https://www.anaricharge.com/inquiry",
"https://www.anaricharge.com/blog/ev-charging-station-operating-cost",
"https://www.anaricharge.com/blog/nevi-grants-ev-charging-station",
"https://www.anaricharge.com/blog/used-ev-charging-equipment",
"https://www.anaricharge.com/products/aquila",
"https://www.anaricharge.com/products/castor",
"https://www.anaricharge.com/solutions/fleet-depot-charging",
"https://www.anaricharge.com/solutions/pv-ess-charging-solution",
"https://www.anaricharge.com/blog/ev-charging-franchise-kenya",
"https://www.anaricharge.com/blog/ev-charging-station-franchise",
"https://www.anaricharge.com/blog/ev-charging-revenue-share-hotels-parking",
"https://www.anaricharge.com/blog/bess-valuation-software"
]}
EOF
curl -s --max-time 30 -X POST "https://api.indexnow.org/indexnow" -H "Content-Type: application/json; charset=utf-8" -d @/tmp/indexnow-req.json -w "\nHTTP %{http_code}\n"
```

注意：D9/D10 两个 URL 在 PR 合并 + Cloudflare 部署（合并后 2-3 分钟）+ curl 确认 200 之后再跑这条；其余 10 个现在就能跑（IndexNow 对 404 URL 会报错但不影响其他）。

## 四、收尾核对

- 12 个 URL 逐个 curl 确认 200
- GSC「网页索引编制」报告里新 URL 状态变「已发现/已抓取」
- 在记忆文件 anari-marketing-ops.md 追加完成记录
