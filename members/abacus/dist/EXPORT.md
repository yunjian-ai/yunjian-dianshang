# 算盘分享卡怎么导出（照着做的操作单）· v0.1.4

在 Grok Bot 里导出。**导出功能只能导出发起导出的那个 Bot 自己**，所以分三步：
1. 新建一个 Bot，照 `dist/template.json`（由 `tools/pack.py` 按标签 abacus-v0.1.4 生成）原样放进下表的名字、资料卡指令、两个技能，一个字不改（记忆在第 3 步让它自己存）；
2. **先别让它装技能**（一打开对话它就会问要不要装，先不答）；技能库是所有 Bot 共用的，先核对库里的安装、第一次见面两个技能和 template.json 一字不差，分享卡带的是库里的内容；
3. 在这个 Bot 里发一条话：先把 memory 的三条原样各存成一条记忆，再用 `CreateBotShareJson` 导出它自己（skills 只点名下表两个，memory 只放这三条）；导出后是草稿，核对卡里描述的字数和本地一致，要在卡上确认「发布」才公开。

| 参数 | 填什么 |
|---|---|
| name | `算盘 · Abacus ｜ 算账`（template.json → `profile.name`） |
| description（导出工具只有这一栏，导入后它就是新 Bot 的指令，2026-10-22 实测逐字一致） | template.json → `_meta.storefront`，空一行，再接 `profile.description`（岗位说明第一句是「你是算盘（Abacus），云间里管算账的那位。」）；原样、不删换行。只放简介会丢掉岗位说明 |
| visibility | `public` |
| gettingStarted | `abacus-install`（不是 abacus-getting-started） |
| skills | 只放两个：`abacus-install`、`abacus-getting-started`（template.json → `skills`） |
| memory | template.json → `memory`（kind=log，三条：「算盘安装规矩」「算盘装完规矩」和一行「算盘安装状态」，每条不超过 480 字） |

**卡里不放的：** 另外 6 个技能——第一次聊天时由 abacus-install 从 abacus-v0.1.4 装上；主人的算账档案也不放。

**导完一定要试：** 新建一个干净的 Bot 导入这张卡，打个招呼。算盘应先问一句能不能从仓库安装；回答「可以」后，回复第一句是开场白「您好，欢迎来到云间。我是万象系列的手艺人·算盘，8 件工具已备好，接下来由我陪您把店里每一笔账算透。」，接着是第一次见面的第 1 题。然后请它列一下技能目录，应该能看到 8 个 abacus- 技能，abacus-fetch 里有 底账.py、核表.py，abacus-ledger 里有 算账.py、报告.py，abacus-check、abacus-diagnose、abacus-base 各有对账.py、诊断.py、巡检.py；公共库在 ~/.yunjian/abacus/库/（平台规则库、自动化地图、模板、默认值）。

**导出之前先确认三件事：** 配方是最新的（`python3 tools/pack.py --check` 通过）；仓库对外公开；卡里没有密钥、内部网址和真实客户资料。

**发布后怎么导入实测：** 卡上「复制链接」得到 `https://x.ai/bot/<编号>`；本机运行 `open "grokbot://app/v1/bot-template?id=<编号>"` 就弹出导入窗口，点「添加 Bot」。草稿不能导入，可见范围只有 public / team。
