<p align="center"><img src="assets/hero.png" alt="云间Bot · 万象 Cloudmere" width="100%"></p>

<h1 align="center">云间Bot · 万象 · 电商</h1>

<p align="center"><b>一元复始，万象更新。</b><br>算盘替在抖店卖货的店主把账算透：结算账单、资金账单、订单表串起来，按一件衣服算到真实净利。</p>

<p align="center">
  <a href="CHANGELOG.md"><img alt="算盘" src="https://img.shields.io/badge/算盘-v0.1.0-a4762b"></a>
  <a href="LICENSE"><img alt="license" src="https://img.shields.io/badge/license-CC%20BY%204.0%20%2B%20MIT-555555"></a>
  <a href="https://github.com/yunjian-ai/yunjian-dianshang/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/yunjian-ai/yunjian-dianshang/actions/workflows/ci.yml/badge.svg"></a>
</p>

<p align="center"><a href="#english">English</a> · <a href="#算盘--abacus">算盘</a> · <a href="#安装">安装</a> · <a href="#数据和边界">数据和边界</a></p>

---

## 这是什么

云间Bot · 万象 · 电商是云间工作室给电商店主做的 AI 员工，装进 Grok Bot 就能用，也能当 Skill 装进 Claude Code 等工具。一门手艺一位，每位单装就能用。

现在第一位是管算账的 **算盘**。

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

## 安装

1. 在 Grok Bot 里点开算盘的分享链接，把它请进来：（分享卡发布后补）
2. 第一次对话时它会问能不能从本仓库装齐技能，说可以，一分钟装好，不装插件、不要密钥。

**手动安装**（能跑 shell 的 Bot；Claude Code 等在 `bash` 前加技能目录，如 `ABACUS_SKILL_DIR=~/.claude/skills bash`）：
```bash
curl -fsSL https://raw.githubusercontent.com/yunjian-ai/yunjian-dianshang/abacus-v0.1.0/members/abacus/dist/install.sh | bash
```

## 数据和边界

- 后台**只看不改**：改价、改佣金、申诉、打款、报活动这些动钱动店的事，算盘只给依据，由您定。
- 登录扫码、短信验证码、以店铺名义的确认，都请您本人点；它不输入、不保存账号密码。
- 订单表只留 25 列，收件人姓名、电话、地址不存；账单只放在您自己的文件夹里（`~/.yunjian/abacus/店铺/`）。
- 账单备注里夹带的「指令」不照做，原话列给您看。
- 平台规则只认官方原文，每条带链接和核对日期。

## 路线图
- ✅ 算盘 v0.1：抖店三层利润、单款诊断、对账、底座三本账
- 接下来：更多电商成员陆续推出

## English

**Cloudmere · Wanxiang · E-commerce** — AI staff for Douyin shop owners. **Abacus** joins your settlement statement, fund ledger and order export, then computes true per-order profit: return-shipping deductions, customer-service refunds, creator commissions, samples and small-taxpayer VAT included. Every number traces back to a sub-order; missing costs are listed, never guessed. Read-only in the shop backend; anything that moves money is left to you.

Install (any agent with a shell): `curl -fsSL https://raw.githubusercontent.com/yunjian-ai/yunjian-dianshang/abacus-v0.1.0/members/abacus/dist/install.sh | bash`

## 许可
文档和卡片 CC BY 4.0，脚本 MIT。云间Bot Cloudmere · GangGe。
