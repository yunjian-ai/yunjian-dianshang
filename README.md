<p align="center"><img src="assets/hero.png" alt="云间Bot · 万象 Cloudmere" width="100%"></p>

<h1 align="center">云间Bot · 万象 · 电商</h1>

<p align="center"><b>一元复始，万象更新。</b><br>算盘替在抖店卖货的店主把账算透，货郎替您挑真在卖的爆款、把链接做到一次过审，经纪替您找准达人、一句话设好链接、一路跟到上播出单。</p>

<p align="center">
<!-- 总表:小标签 -->
  <a href="CHANGELOG.md"><img alt="算盘" src="https://img.shields.io/badge/算盘-v0.1.2-a4762b"></a>
  <a href="CHANGELOG.md"><img alt="经纪" src="https://img.shields.io/badge/经纪-v0.1.0-8a5a2b"></a>
  <a href="CHANGELOG.md"><img alt="货郎" src="https://img.shields.io/badge/货郎-v0.1.0-3f7d4e"></a>
<!-- /总表:小标签 -->
  <a href="LICENSE"><img alt="license" src="https://img.shields.io/badge/license-CC%20BY%204.0%20%2B%20MIT-555555"></a>
  <a href="https://github.com/yunjian-ai/yunjian-dianshang/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/yunjian-ai/yunjian-dianshang/actions/workflows/ci.yml/badge.svg"></a>
</p>

<p align="center"><a href="#english">English</a> · <a href="#算盘--abacus">算盘</a> · <a href="#货郎--hawker">货郎</a> · <a href="#经纪--broker">经纪</a> · <a href="#安装">安装</a> · <a href="#数据和边界">数据和边界</a></p>

---

## 这是什么

云间Bot · 万象 · 电商是云间工作室给电商店主做的 AI 员工，装进 Grok Bot 就能用，也能当 Skill 装进 Claude Code 等工具。一门手艺一位，每位单装就能用。

现在有三位：管算账的 **算盘**，管选品上架的 **货郎**，管达人推广的 **经纪**。

## 算盘 · Abacus

> 您丢来抖店后台导出的三张表（或让它在您登录好的后台里自己导），它按一件衣服算到真实净利：平台扣的退货运费、客服补的钱、寄样、税都算进去，自销和每个达人分开看，每个数能追到子订单。缺成本就单列请您补，一个数不估。

**八个技能，各干一步**

| # | 技能 | 做什么 |
|---|---|---|
| 1 | 第一次见面 | 一次问一件：店铺、数据怎么拿、税务身份、快递单价、成本表；建好您的店铺文件夹；支持「演练」，只打印不存 |
| 2 | 取数 | 照后台路线图导出结算账单、资金账单、订单表（验证码、个人信息承诺这些步骤请您本人点），或收您导出的文件；核表：认表、洗数，订单表只留 25 列、不存收件人信息 |
| 3 | 算账 | 三层利润：毛利 → 到手 → 净利；按款、按自销和达人、按达人汇总；一页账本报告＋逐单明细 |
| 4 | 单款诊断 | 这款赚不赚、退货率到多少就亏、给达人最多给多少佣金 |
| 5 | 对账 | 出报告前把关：结算金额对不对、两张账单对不对得上、有没有混进个人信息，不过不交 |
| 6 | 底座 | 平台规则、后台按钮、您定的规矩会变：每周巡检，变了先写变更单、您点头再改，旧的不删 |

另有两个后台技能：`abacus-install` 负责安装，`abacus-update` 负责更新。

**它算得出、后台看不到的钱**
- 平台按商详承诺从货款里扣的退货运费（只在资金账单里）
- 客服小额打款补的运费、差价，挂回到每一单；同一单平台扣过又打款的，标出来提醒您去申诉
- 结算前就退掉的单：发货运费和退货运费照样花了
- 寄样单不算销售，记「达人寄样开支」
- 小规模纳税人的增值税和附加（按季度或按月看免征额，只是经营预估，以申报为准）

## 货郎 · Hawker

> 货郎是走街串巷挑货卖货的人。它先弄清您的店是卖什么、卖给谁的，再去罗盘榜单和淘宝、拼多多挑**最近真在卖**的爆款，每款出一张选品卡请您拍板；链接标准它来定，图文照标准做，草稿两道自检，停在提交前请您点发布，再上精选联盟、交给达人推。

**八个技能，各干一步**

| # | 技能 | 做什么 |
|---|---|---|
| 1 | 第一次见面 | 读罗盘成交人群画像和在售款，出店铺标签卡：单品店还是多品店、主人群和主年龄段（各最多 2 个）、价格段，请您确认 |
| 2 | 找爆品 | 罗盘商品榜单近 1 天 ≥1000 件算过线；淘宝、拼多多同一链接隔 7 天看两次、涨 ≥1000 件才算；和您的店对一对，留对得上的 |
| 3 | 选品分析 | 五看选品卡：热度、爆在哪（直播还是短视频）、货源、周期、竞品价，每栏写出处；利润照算盘，结论只写建议 |
| 4 | 链接标准 | 主图、标题、属性、详情、商品信息照官方细则定一份店铺标准；给做图的写制作单，交回来逐张验收 |
| 5 | 做链接 | 拼草稿包，过官方规范和店铺标准两道自检；走抖店 AI 智能发品，停在提交前请您点发布 |
| 6 | 上联盟 | 核自动推广的默认佣金有没有超过算盘给的上限，出联盟设置单请您点头，再写推广交接单 |
| 7 | 上新和货盘 | 上新节奏；在售款快到「30 天无销量自动下架」时提前提醒，写清约几号 |
| 8 | 底座 | 平台规则库、后台路线、您定的规矩（经营决策卡），每周巡检，变了先写变更单 |

另有两个后台技能：`hawk-install` 负责安装，`hawk-update` 负责更新。

**它怎么给您看数**：每个数都写出处（哪个平台、哪个页面或榜单、哪家店、什么时候记的），用表格呈现；在聊天框里是不超过 5 列的窄表，出处编号列在表下，在电脑上可以出宽表。

## 经纪 · Broker

> 经纪替您跑达人这条线。每款先备一份带出处的素材包和百问百答，按店铺标签在精选联盟达人广场找准达人、打匹配分，第一句写得四样齐、守着平台每天的量发；达人回话，库里有的照原话答，库外的转给您。您一句话「UID、佣金、普通链接还是渠道品、哪款」，它就去设好指定达人佣金，再出给厂家的发版单，一路跟到上播出单。

**九个技能，各干一步**

| # | 技能 | 做什么 |
|---|---|---|
| 1 | 第一次见面 | 一次问一件，建经纪设置卡：店铺、厂家、默认佣金和封顶、每天发多少；说「别的先不问」也行，缺的用到时再问 |
| 2 | 素材包和百问百答 | 每款的证据、卖点、政策，每个数带出处，没出处的、极限词都拦；达人常问的问题存进库，照原话答 |
| 3 | 找达人 | 按店铺标签在达人广场筛，算匹配分：精准、外扩、不匹配、排除，直播和短视频分开排 |
| 4 | 和达人沟通 | 起草第一句（邀约带货卡 150 字内）；守每天上限和间隔；平台规定没回的 60 天内不能再邀约，它记着日子 |
| 5 | 一句话设链接 | 谈定单 → 佣金闸（不超您定的封顶和算盘的上限，取低的，不低于平台 5%）→ 后台设指定达人佣金或渠道品 → 回读核对 |
| 6 | 寄样 | 平台申样按分层、匹配度、履约率给「过」或「提醒您」，快到 72 小时的排最前；谈定的出发版单给厂家 |
| 7 | 合作单跟踪 | 每天排今天要办的事：申样快到时限、转人工、签收没动静、上播出单少要复盘 |
| 8 | 达人库和分层 | 新、成长、核心、沉睡四档，决定申样自动过、佣金给多少、新品先推谁 |
| 9 | 底座 | 平台规则库、后台路线、您定的规矩（经营决策卡），每周巡检，变了先写变更单 |

另有两个后台技能：`brok-install` 负责安装，`brok-update` 负责更新。

## 安装

1. 在 Grok Bot 里点开分享链接，把它请进来：算盘 https://x.ai/bot/nmYg5TpxttsK0TitIyG8h ；货郎 https://x.ai/bot/ng1YoSxoMevXeHVQnUtPH ；经纪 https://x.ai/bot/jpvgbV9GaQCCRhhOu_WFc
2. 第一次对话时它会问能不能从本仓库装齐技能，说可以，一分钟装好，不装插件、不要密钥。

**手动安装**（能跑 shell 的 Bot；Claude Code 等在 `bash` 前加技能目录，如 `ABACUS_SKILL_DIR=~/.claude/skills bash`、`HAWK_SKILL_DIR=~/.claude/skills bash`、`BROK_SKILL_DIR=~/.claude/skills bash`）：
```bash
curl -fsSL https://raw.githubusercontent.com/yunjian-ai/yunjian-dianshang/abacus-v0.1.2/members/abacus/dist/install.sh | bash
curl -fsSL https://raw.githubusercontent.com/yunjian-ai/yunjian-dianshang/hawk-v0.1.0/members/hawk/dist/install.sh | bash
curl -fsSL https://raw.githubusercontent.com/yunjian-ai/yunjian-dianshang/brok-v0.1.0/members/brok/dist/install.sh | bash
```

## 数据和边界

- 后台**只看不改**：改价、改佣金、申诉、打款、报活动这些动钱动店的事，算盘只给依据，由您定。
- 登录扫码、短信验证码、以店铺名义的确认，都请您本人点；它不输入、不保存账号密码。
- 订单表只留 25 列，收件人姓名、电话、地址不存；账单只放在您自己的文件夹里（`~/.yunjian/abacus/店铺/`）。
- 账单备注里夹带的「指令」不照做，原话列给您看。
- 平台规则只认官方原文，每条带链接和核对日期。
- 货郎改价、发品、改佣金、上下架一步都不自己做：发布停在提交前，联盟设置单请您点头；跨平台只看公开页面，不登录、不下单。
- 您的店铺数据、后台截图只放在您自己的文件夹里（`~/.yunjian/hawk/店铺/`）。
- 经纪设佣金、建渠道品、绑达人，都是您一句话说了才做，做完回读核对；发消息守平台每天上限和间隔，不批量群发；达人的联系方式、地址只进达人库和发版单，不在聊天里抄出来；达人消息里夹带的「指令」不照做，原话给您看。

## 路线图
| 系列 | 成员 | 职能 | 状态 |
|---|---|---|---|
<!-- 总表:路线图 -->
| 起元 | 青鸟 Bluebird | 提示词 | ✅ v0.1.15，[另一个仓库](https://github.com/yunjian-ai/yunjian) |
| 起元 | 千机 Gear | Skill | ✅ v0.2.4，[另一个仓库](https://github.com/yunjian-ai/yunjian) |
| 起元 | 凝露 Dew | 蒸馏 | ✅ v0.1.11，[另一个仓库](https://github.com/yunjian-ai/yunjian) |
| 起元 | 经纬 Loom | 本体 | ✅ v0.1.8，[另一个仓库](https://github.com/yunjian-ai/yunjian) |
| 起元 | 试金 Touchstone | 验证 | ✅ v0.1.15，[另一个仓库](https://github.com/yunjian-ai/yunjian) |
| 起元 | 照骨 Xray | 拆解 | ✅ v0.1.3，[另一个仓库](https://github.com/yunjian-ai/yunjian) |
| 起元 | 起元操盘 Genesis | 操盘系统 | ✅ v0.1.11，[另一个仓库](https://github.com/yunjian-ai/yunjian) |
| 万象 | 执笔 Pen | 写稿 | ✅ v0.4.0，[另一个仓库](https://github.com/yunjian-ai/yunjian-zimeiti) |
| 万象 | 丹青 Paint | 做图 | ✅ v0.5.7，[另一个仓库](https://github.com/yunjian-ai/yunjian-zimeiti) |
| 万象 | 掠影 Reel | 短视频 | ✅ v0.3.3，[另一个仓库](https://github.com/yunjian-ai/yunjian-zimeiti) |
| 万象 | 算盘 Abacus | 算账：抖店三层利润、单款诊断、对账、底座三本账 | ✅ v0.1.2 |
| 万象 | 经纪 Broker | 达人推广：素材包、找达人、一句话设链接、申样发版、合作单跟到上播 | ✅ v0.1.0 |
| 万象 | 货郎 Hawker | 选品上架：爆品线、选品卡、链接标准、AI 智能发品、上联盟 | ✅ v0.1.0 |
| 起元 | 起元架构 Architecture | 一群 AI 的底座 | ✅ v0.1.1，[另一个仓库](https://github.com/yunjian-ai/yunjian) |
<!-- /总表:路线图 -->

- 接下来：更多电商成员陆续推出

## English

**Cloudmere · Wanxiang · E-commerce** — AI staff for Douyin shop owners. **Abacus** joins your settlement statement, fund ledger and order export, then computes true per-order profit: return-shipping deductions, customer-service refunds, creator commissions, samples and small-taxpayer VAT included. Every number traces back to a sub-order; missing costs are listed, never guessed. Read-only in the shop backend; anything that moves money is left to you. **Hawker** picks products that are selling *now* (Douyin Compass rankings, plus Taobao/Pinduoduo snapshots taken 7 days apart), writes a sourced product card for your decision, sets your listing standard, checks drafts twice and stops before publish. Every number cites platform, page, shop and time; tables fit the screen you read them on. **Broker** runs your creator outreach: a sourced pitch kit per product, creator matching on the affiliate marketplace, first messages within platform limits, and one sentence from you ("UID, rate, link type, product") to set the targeted commission — capped at the lower of your ceiling and Abacus's limit — then sample orders and follow-up until the creator goes live.

Install (any agent with a shell): `curl -fsSL https://raw.githubusercontent.com/yunjian-ai/yunjian-dianshang/abacus-v0.1.2/members/abacus/dist/install.sh | bash` · Hawker: `curl -fsSL https://raw.githubusercontent.com/yunjian-ai/yunjian-dianshang/hawk-v0.1.0/members/hawk/dist/install.sh | bash` · Broker: `curl -fsSL https://raw.githubusercontent.com/yunjian-ai/yunjian-dianshang/brok-v0.1.0/members/brok/dist/install.sh | bash`

## 许可
文档和卡片 CC BY 4.0，脚本 MIT。云间Bot Cloudmere · GangGe。
