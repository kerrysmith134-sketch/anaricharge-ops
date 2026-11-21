# anaricharge.com 行业目录 / B2B 平台候选复核（2026-10-17 实测）

执行单元：AI营销天团 · 外链公关单元（侦察+突击）
复核方式：沙箱内 curl 直连实测（含 HTTP 状态、响应体大小、页面 title、表单字段名提取）；受反爬/JS 拦截的平台改用 websearch 佐证并标注「需人工确认」。
**纪律：不伪造提交结果；本轮沙箱无任何平台账号与公开邮箱凭据，所有条目一律标注真实可执行状态。**

站点自身信息（用于填表，取自线上页脚实测）：
- 公司名：Shenzhen Anari Energy Co., Ltd（Anari Energy）
- 一句话定位：Turnkey EV charging & energy storage — we sell the capability to become a successful CPO
- 官网：https://www.anaricharge.com/ ｜姊妹站：https://www.anariev.com/
- 联系邮箱：sales@anarienergy.com ｜WhatsApp：+86 188 6620 5186
- LinkedIn：https://www.linkedin.com/showcase/shenzhen-anari-energy-co-ltd
- 总部深圳，西安/伊斯坦布尔/迪拜设办公室；服务 100+ 客户 / 22 国

---

## A. 免费可自助提交（入口与字段已实测确认 → 唯一需人工的动作是「登录并提交」）

| # | 平台 | 实测入口 | 状态 | 实测表单字段 | 提交要求 | 预计导流价值 |
|---|---|---|---|---|---|---|
| A1 | **TradeWheel** | `https://www.tradewheel.com/register-free/` | 200 / 45,815 B / title「Register Your Company」 | `_token, source, type, name*, phone_number*, email*, password*, country_id*, company_name*, messenger_type, wa_number, messenger_id` | 免费自助注册，邮箱验证 | B2B 采购方流量，出口品类匹配度中 |
| A2 | **ExportHub** | `https://www.exporthub.com/signup.html` | 200 / 61,402 B / title「Sign Up On The Best B2B Marketplace \| ExportHub」 | `iamseller / iambuyer（角色选择）, name, country, company_name, mobile, email, password, signup_token`（含 captcha） | 免费自助注册，选 Seller 角色 | 中，价格敏感买家多 |
| A3 | **TradeKey** | `https://www1.tradekey.com/products/join-now.html` | 200 / 358,605 B / title「Join Now … Suppliers」 | `is_buyer_or_seller, country, fullname, email, password, company, product, phone1, mobile_number, industry_signup, im_id` | 免费自助注册（原 `/join` 为 404，正式入口为 join-now） | 中高，全球 B2B 老牌站 |
| A4 | **IndiaMART** | `https://seller.indiamart.com/` | 200 / 35,925 B / title「Sell on IndiaMART \| Free Registration」 | 注册向导（JS 应用，字段随步骤加载） | 免费自助注册，需印度/海外卖家资质 | 印度市场专用，与本项目目标市场不重叠，优先级低 |
| A5 | **Open Charge Map** | `https://openchargemap.org/site/poi/add` | 200 → 302 至 `/loginprovider/beginlogin` | 仅 `EmailAddress / Password / RequestVerificationToken` | 需先注册免费账号（站点为 CPO 数据社区，收录充电点位/运营商） | 高相关性（EV/CPO 垂直），但重数据贡献而非企业名录 |
| A6 | **HKTDC 采购平台** | `https://sourcing.hktdc.com/newsbites/become-a-supplier/ecommerce/en/` | 200 / 350,308 B | 该页为供应商引导页 + Contact Form 7 联系表单（`form_fields[...]` 共 11 项），正式上架需 HKTDC 账号 | 免费基础上架 + 付费 2SD 广告位可选；**实际卖家注册入口需登录 HKTDC 账号后进入** | 高，香港贸发局买家质量好 |

> A1–A3 为「入口/字段 100% 实测确认 + 纯自助」，是本周唯一可在有人工账号时 10 分钟内完成注册的三家；A4/A6 需资质或账号体系；A5 是垂直相关性最高的一家。

---

## B. 已确认存在但本轮无法自助（需人工 / 浏览器 / 参展）——不作为「已提交」计数

| # | 平台 | 实测结果 | 阻塞原因 | 建议动作 |
|---|---|---|---|---|
| B1 | IndustryStock | `industrystock.com` 403（首页与 /en/registration 均被 Cloudflare 拦截） | 反爬拦截，字段不可读 | 用真实浏览器打开 → 免费供应商注册 |
| B2 | EC21 | `www.ec21.com` 403「Attention Required! \| Cloudflare」 | 反爬拦截 | 同上（免费会员） |
| B3 | Europages（EU） | `europages.com` / `europages.co.uk` 均返回 202 / 0 B | 机器人防护空响应 | 欧盟买家入口，值得人工注册 |
| B4 | Global Sources | `globalsources.com/register` 58 B（JS 应用） | SPA，需浏览器渲染 | 免费会员需企业资质审核 |
| B5 | eWorldTrade | `eworldtrade.com` 202 / 0 B（`/register/` 同） | 防护拦截 | 人工注册（免费） |
| B6 | Made-in-China | `member.made-in-china.com/register` 连接超时（000） | 沙箱网络不可达 | 人工注册（免费基础会员） |
| B7 | Alibaba.com | 首页 200，未暴露注册字段（JS 应用） | SPA + 企业资质审核 | 人工注册（免费基础会员） |
| B8 | ExportersIndia | 首页 200；`/seller/register/` 404 | 真实卖家入口藏在首页导航内，未定位到 | 人工从首页导航进入注册 |
| B9 | The smarter E Business Directory | `thesmartere.com/business-directory` 200 / 74,580 B，页内无自助申请表单 | 1,132 家企业，收录通常绑定参展/合作 | 邮件联系主办方（the smarter E）询收录条件 |
| B10 | EVTrader EV Database | `evtrader.com/ev-database` 200 / 96,043 B（6,044 家公司 / 86 国） | 收录路径为 WhatsApp 联系：`wa.me/31644796293?text=EV Database listing` | 用 WhatsApp 提交公司资料（荷兰站，垂直相关度高） |
| B11 | PowerStationHQ「Global EV Charging Directory 2026」 | 直连失败（HTTP 000），需联系编辑 | 沙箱不可达 | 邮件联系编辑申请收录 |
| B12 | F6S / Crunchbase / StartupBlink / Product Hunt | F6S 返回「Checking your browser」JS 校验；其余 403 Cloudflare | 需真实浏览器 | 可作为「初创公司画像」外链补充，人工注册 |

---

## C. 复核后排除（判定为非目标，不再投入）

| 站点 | 排除依据 |
|---|---|
| evchargersguide.com | 实测 200 / 242,586 B，但全站为 Amazon 联盟内容站（href 全为 amzn.to），**无企业收录入口**；仅保留「编辑外联/投稿」价值，不作为目录 |
| evchargingdirectory.com | 无 DNS 解析（curl 000，页面残留为上一轮缓存文件，非本站内容），站点不存在 |
| evchargermap.com | DNS 有 A/AAAA 记录但沙箱连接超时（000），**可提交性未确认**；沿用上轮结论，不纳入本周执行 |
| PlugShare | 消费者向充电点位地图，加点位需 App/账号，面向 C 端点位而非 B2B 供应商收录，不符合外链目标 |

---

## D. 结论与本周可执行边界

1. **可自助清单最终为 A1 TradeWheel、A2 ExportHub、A3 TradeKey 三家**（入口 + 必填字段均已实测），加上 A5 Open Charge Map（需免费账号）共 4 家；提交动作本身需人工登录，沙箱无凭据，**本轮不产生实际已提交外链**。
2. **高相关资产**（B9 smarter E、B10 EVTrader、B11 PowerStationHQ）均需人工邮件/WhatsApp 联系，建议本周内由业务侧发出 3 封收录申请，并统一使用 A 组模板话术（见下）。
3. **计数口径**：截至 2026-10-17，实际已落地外链 = **0**（季度目标 ≥20）；本轮产出为「6 家可自助入口 + 9 家需人工联系候选 + 4 家排除」的已验证地图，供人工按序执行。
4. 与 10-15 报告相比的增量：新增实测确认 TradeKey 正式入口（join-now 而非 /join）、ExportHub、IndiaMART、Open Charge Map 四家；新增排除 evchargersguide / evchargingdirectory / PlugShare 三家；新增 EVTrader 的 WhatsApp 收录路径。

### 附：提交/外联统一话术（200 字内，可直接粘贴）
> Anari Energy (Shenzhen, China) builds turnkey EV charging + liquid-cooled BESS for emerging markets — CPO launch, site selection, hardware, OCPP backend and operations in one contract. 100+ customers in 22 countries, support hubs in Xi'an, Istanbul and Dubai. Free ROI/TCO calculators: https://www.anaricharge.com/tools/. Listing contact: sales@anarienergy.com

[DuMate AI生成]