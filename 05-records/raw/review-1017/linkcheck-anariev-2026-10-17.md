# anaricharge ↔ anariev 双站互指检查 · 实测证据存档（2026-10-17）

执行单元：AI营销天团 · 外链公关（无付费链接/站群/无差别目录）
方法：线上 curl 实测 + 站点源码全量检索（anaricharge 交付目录 site/）+ anariev sitemap 抽样扫描

## 一、结论
| 方向 | 状态 | 证据 |
|---|---|---|
| anaricharge.com → anariev.com | ✅ 已存在（单向） | 全站页脚 Company 栏固定项：`<a href="https://www.anariev.com/" rel="noopener">Sister site: anariev.com ↗</a>`；源码级 167 处锚点分布在约 110 个交付页面（页脚全局 111 处 + 产品/方案页 CTA 按钮 49 处 + 多语言 /es/ 5 处等）；线上复测首页 /about /inquiry /products 均含该链接，**dofollow、无 nofollow** |
| anariev.com → anaricharge.com | ❌ 全站缺失 | 首页（129,495 B）正文+页脚 0 命中；6 个重点内页（/about-us/ /partner/ /contact-us/ /aicharge/ /category/resources/guide/ /ev-charging-solutions-for-independent-cpos/）0 命中；30 个英文页抽样（service-support / download / solutions 等）0 命中；anariev 共 975 URL（含 ru/es/fr/ar 多语言），WordPress 页脚为全局模板 → 反向链接全站缺失，非单页遗漏 |

## 二、anariev 侧附带技术发现（影响互链可信度，需人工）
1. **apex HTTPS 证书名不匹配**：`https://anariev.com/` 失败（curl 60）。证书 `CN=www.anariev.com`，SAN 仅 `DNS:www.anariev.com`，不含 apex。
2. **明文未强制跳转 HTTPS**：`http://www.anariev.com/` 直接 200；`http://anariev.com/` 301 → `http://www.anariev.com/`（仍为明文）。
3. anariev robots.txt 正常（200），声明 Sitemap: https://www.anariev.com/sitemap_index.xml（200，4 个子 sitemap：post/page/category/post_tag）。

## 三、修复项与执行节点（需 anariev 站主/建站方权限，无 wp-admin 凭据，本轮无法自助执行）
| 优先级 | 动作 | 执行节点 | 验收标准 |
|---|---|---|---|
| P0 | anariev 全站页脚加姊妹站链接（锚文本建议：`anaricharge.com — EV charging ROI & TCO tools`，dofollow，rel="noopener"） | anariev.com 后台（页面源码引用 lingju.global / lingjuimg.com，站点由凌据平台托管）→ 全局页脚组件；或 WordPress 主题 footer.php / 自定义 HTML 区块 | `curl -s https://www.anariev.com/ \| grep -i anaricharge` 返回 ≥1（页脚）；抽检内页同样命中 |
| P0 | /about-us/ 正文补 1 句上下文内链（如组集团品牌矩阵说明，指向 anaricharge.com） | anariev 后台 → 页面 → About us → 正文 | 页面正文出现 1 条 dofollow 出站链接 |
| P1 | /partner/ 页加 "Our sites / Resources" 区块 | anariev 后台 → Partner 页 | 页面出现 1-2 条出站链接 |
| P1 | /download/ 资源页增加工具型资源引用（可指向 anaricharge /tools/ 计算器） | anariev 后台 → Download 页 | 页面出现出站链接 |
| P2 | 4 个语言版本（/es/ /ru/ /fr/ /ar/）页脚同步姊妹站链接 | 同上，随页脚全局组件一次性生效 | 各语言首页命中 anaricharge |
| P2 | 修 apex 证书（SAN 增加 anariev.com）+ http→https 强制跳转 | 建站方/主机 SSL 配置 | `curl -I https://anariev.com/` 返回 301 到 https://www.anariev.com/（无证书错误）；http 明文 301 到 https |

注：两站主题相关（同集团：anariev.com 为品牌/产品站，anaricharge.com 为 EV 充电资源与工具站），属正常合理互链，不构成站群；两侧保持 dofollow，不做 reciprocal nofollow。

## 四、跨站附带发现（供 SEO 巡检 P2 参考）
anaricharge.com `/contact` 返回 **404 且响应体 0 字节**（页脚实际使用 /inquiry）。建议 Cloudflare 侧配置 `not_found_handling="404-page"` 的同时，为 /contact 加 301 → /inquiry。

[DuMate AI生成]