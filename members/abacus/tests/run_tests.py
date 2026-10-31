"""算盘自测：用考题材料（虚构店小林针织）把 核表 → 算账 → 对账 → 报告 → 诊断 → 巡检 跑一遍，对标准答案；再埋错看对账拦不拦。
用法：python3 members/abacus/tests/run_tests.py    只用标准库；在临时文件夹里跑，不碰主人的 ~/.yunjian/abacus"""
import csv, json, os, pathlib, shutil, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
M = HERE.parent; SK = M / "skills"
bad = 0
def ok(cond, msg):
    global bad
    print(("✅ " if cond else "❌ ") + msg); bad += 0 if cond else 1
def run(script, *args, env=None):
    return subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True, env=env)

with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    cl = t / "材料"; shutil.copytree(HERE / "材料", cl)
    subprocess.run([sys.executable, "出题.py"], cwd=cl, check=True, capture_output=True)
    ans = json.loads((cl / "标准答案.json").read_text(encoding="utf-8"))
    home = t / "home"; shutil.copytree(M / "库", home / "库")
    dp = home / "店铺" / "小林针织"
    for d in ["经营决策库", "底座数据"]: (dp / d).mkdir(parents=True)
    shutil.copy(cl / "成本表.csv", dp / "底座数据" / "成本表.csv")
    (dp / "经营决策库" / "D-ZC-007-快递单价.md").write_text("---\n编号: D-ZC-007\n标题: 快递单价\n状态: 生效\n参数:\n  快递单价: 3.0\n---\n", encoding="utf-8")
    env = {**os.environ, "ABACUS_HOME": str(home)}
    QZ = ["--起", "2026-11-01", "--止", "2026-11-07", "--店铺", str(dp)]

    r = run(SK / "abacus-fetch/核表.py", str(cl / "结算账单-1101至1107.csv"), str(cl / "资金账单-1101至1107.csv"), str(cl / "订单-近期.csv"), "--店铺", str(dp), env=env)
    ok("核表 OK" in r.stdout and r.stdout.count("核表 ") >= 4, "核表：三张表都认出来、洗干净")
    ok("像写给 AI 的话" in r.stdout and "S02" in r.stdout, "核表：资金账单备注里夹带的话认出来、不照做")
    ok((dp / "底座数据/商户主体.txt").exists(), "核表：第一次记下这家店的商户主体")
    bie = dp.parent / "别的店"; (bie / "底座数据").mkdir(parents=True); (bie / "底座数据/商户主体.txt").write_text("别家服饰有限公司\n", encoding="utf-8")
    r = run(SK / "abacus-fetch/核表.py", str(cl / "结算账单-1101至1107.csv"), "--店铺", str(bie), env=env)
    ok(r.returncode != 0 and "传错店" in r.stdout and not (bie / "账单").exists(), "核表：账单主体和店记的对不上不收进来（联调 Bot 自报 10-31）")
    jsb = next((dp / "账单").glob("结算账单-*.csv")).read_text(encoding="utf-8-sig")
    ok("收入+支出" not in jsb, "核表：结算账单第 2 行公式说明没进数据")

    r = run(SK / "abacus-ledger/算账.py", *QZ, env=env)
    ok(r.returncode == 0, "算账能跑" + ("" if r.returncode == 0 else "：" + r.stderr[-300:]))
    out = dp / "报告" / "2026-11-01至2026-11-07"
    rows = list(csv.DictReader(open(out / "逐单账.csv", encoding="utf-8-sig")))
    by = {}
    for x in rows: by.setdefault("S" + x["子订单号"][-2:], []).append(x)
    for zi, v in ans["逐单"].items():
        g = by.get(zi, [])
        if v["毛利"] == "缺成本":
            ok(bool(g) and all(x["缺成本"] == "是" for x in g), f"{zi} 缺成本单列、不当 0 算"); continue
        ml, dz = round(sum(float(x["毛利"]) for x in g), 2), round(sum(float(x["到手"]) for x in g), 2)
        ok((ml, dz) == (v["毛利"], v["到手"]), f"{zi} 毛利 {ml}／到手 {dz}（答案 {v['毛利']}／{v['到手']}）")
        if "退货运费" in v:
            th = round(sum(float(x["退货运费"]) for x in g), 2)
            ok(th == v["退货运费"], f"{zi} 退货运费 {th}（答案 {v['退货运费']}）")
    hz = json.loads((out / "汇总.json").read_text(encoding="utf-8"))
    ok(any(z.endswith("09") for z in hz["重复赔付"]), "查出 S09 重复赔付")
    ok(len(hz["寄样"]) == 1 and hz["寄样"][0]["开支"] == -48.0, "寄样单不算销售，寄样开支 48")
    ok(hz["预估"]["单数"] == 1, "S12 没结算，只进预估")
    ok(hz["三层"]["客服补偿"] == -10.0 and hz["三层"]["运费补偿"] == -6.0, "小额打款分客服补偿 10、运费补偿 6")
    ok(hz["三层"]["增值税"] == 0 and "免征" in hz["税"]["说明"] and hz["税"]["申报周期"] == "季度", "小规模、默认按季度看 30 万，免征")
    s02 = by["S02"][0]
    ok(float(s02["客服补偿"]) == -10.0 and float(s02["单前净利"]) == 38.75, "S02 客服补的 10 元挂回这一单（单前净利 38.75）")
    ok(any("资金账单只盖" in x for x in hz["数据缺口"]) and any("订单表" in x for x in hz["数据缺口"]), "数据缺口：资金账单一天、订单表太短都列出来")
    ok(len(hz["夹带的话"]) == 1, "汇总里记下夹带的话，报告会列给主人")
    s06 = by["S06"][0]
    ok(float(s06["平台服务费"]) == -0.35, "S06 商品卡免佣，服务费按账单 0.35")

    r = run(SK / "abacus-check/对账.py", *QZ, env=env)
    ok("对账 OK" in r.stdout and "重复赔付" in r.stdout and "缺成本" in r.stdout, "对账：过，并提醒缺成本、重复赔付")
    r = run(SK / "abacus-ledger/报告.py", *QZ, env=env)
    html = (out / "报告.html").read_text(encoding="utf-8")
    ok(r.returncode == 0 and "三层账" in html and "要注意的" in html, "报告出得来，结构对")
    ok("后台抽单" in html and "待回" in html and "找不到退款流水" in html, "报告列出对账提醒和后台抽单（待回）")
    r = run(SK / "abacus-diagnose/诊断.py", "开衫", "--店铺", str(dp), "--佣金", "0.3", env=env)
    ok("保本退货率" in r.stdout and "佣金最多给到" in r.stdout, "单款诊断出保本退货率和佣金上限")
    r = run(SK / "abacus-diagnose/诊断.py", "马甲", "--店铺", str(dp), env=env)
    ok(r.returncode != 0 and "不能诊断" in (r.stdout + r.stderr), "缺成本的款不诊断、不估")
    gz = dp / "经营决策库" / "D-ZC-099-成本规矩-测.md"; gz.parent.mkdir(parents=True, exist_ok=True)
    gz.write_text("---\n编号: D-ZC-099\n标题: 成本规矩\n状态: 生效\n参数:\n  成本_占定价: 0.5\n---\n", encoding="utf-8")
    r = run(SK / "abacus-diagnose/诊断.py", "马甲", "--店铺", str(dp), env=env)
    mj = json.loads(next((dp / "算盘/款回执").glob("8000000000000000003.json")).read_text(encoding="utf-8")) if r.returncode == 0 else {}
    ok("店铺规矩估" in mj.get("成本来源", "") and abs(mj.get("成本", 0) - mj.get("售价", 0) * 0.5) < 0.01, "成本表没有、主人定过成本规矩：照规矩估、写明来源（联调 10-31）")
    gz.unlink()
    hz = json.loads((dp / "算盘/款回执/8000000000000000001.json").read_text(encoding="utf-8"))
    ok(hz["来自"] == "算盘" and hz["佣金上限"] is not None and hz["保本价"] and hz["成本来源"] == "成本表" and "卖一件不退挣" in hz and "每单期望利润_算退货" in hz,
       "单款诊断写款回执（保本价、佣金上限、成本来源；不算退货和算退货的利润分两栏，联调 10-31）")
    ok(not (dp / "算盘/款回执/开衫.json").exists() and hz["款号"] == "8000000000000000001" and hz["每单期望利润_自销"] > hz["每单期望利润_算退货"]
       and hz["可给佣金_取低"] == min(hz["佣金上限"], hz["佣金封顶_主人定"] or 1.0),
       "卖过的款按商品ID存款回执（不按主人说的几个字）；自销单利润另列；可给佣金取上限和主人封顶低的（联调 Bot 自报 10-31）")
    r = run(SK / "abacus-diagnose/诊断.py", "AQ-1108", "--店铺", str(dp), "--售价", "79", "--成本", "32", "--品名", "新开衫", env=env)
    xh = json.loads((dp / "算盘/款回执/AQ-1108.json").read_text(encoding="utf-8")) if (dp / "算盘/款回执/AQ-1108.json").exists() else {}
    t_, y_, kd_, ry_ = xh.get("退货率", 0), xh.get("佣金率_按此算", 0), xh.get("快递", 0), xh.get("每单退货运费", 0)
    bb_ = (32 + (kd_ + t_ * ry_) / (1 - t_)) / (1 - xh.get("平台服务费率", 0) - y_) if xh else 0
    ok(r.returncode == 0 and "新款试算" in r.stdout and xh.get("成本来源") == "货郎交接单" and "全店" in xh.get("退货率来源", "") and y_ == 0.2 and abs(xh["保本价"] - round(bb_, 2)) < 0.01,
       "新款（没卖过）给售价成本就试算：退货率借全店、佣金按 20%、保本价算对、写款回执")
    r = run(SK / "abacus-diagnose/诊断.py", "AQ-1108", "--店铺", str(dp), "--售价", "79", "--成本", "32", "--品名", "新开衫", "--佣金", "0.22", env=env)
    x2 = json.loads((dp / "算盘/款回执/AQ-1108.json").read_text(encoding="utf-8"))
    ok(x2["佣金率_按此算"] == 0.2 and x2["每单期望利润_算退货"] == xh.get("每单期望利润_算退货") and "22%" in x2.get("按佣金试算", {}),
       "款回执：已有基准时按别的佣金试算只记进「按佣金试算」，基准不动（联调 Bot 自报 10-31）")
    r = run(SK / "abacus-diagnose/诊断.py", "AQ-2001", "--店铺", str(dp), "--售价", "79", "--成本", "70", "--品名", "贵衬衫", "--佣金", "0.22", env=env)
    hzj = json.loads(sorted((dp / "回执").glob("*/abacus.json"))[-1].read_text(encoding="utf-8"))
    ok(any("AQ-2001" in x and "亏" in x for x in hzj.get("等主人定", [])), "算出亏钱的款进算盘回执「等主人定」，掌柜报里看得到（联调 Bot 自报 10-31）")
    r = run(SK / "abacus-diagnose/诊断.py", "AQ-9999", "--店铺", str(dp), env=env)
    ok(r.returncode != 0 and "--售价 --成本" in (r.stdout + r.stderr), "没卖过又没给售价成本：不估，说清要什么")

    # 反向用例：埋错，对账必须拦
    jp = next((dp / "账单").glob("结算账单-*.csv"))
    yuan = jp.read_text(encoding="utf-8-sig")
    rows2 = list(csv.reader(yuan.splitlines())); h = rows2[0]; i = h.index("结算金额")
    rows2[1][i] = str(float(rows2[1][i]) + 5)
    with open(jp, "w", newline="", encoding="utf-8-sig") as f: csv.writer(f).writerows(rows2)
    r = run(SK / "abacus-check/对账.py", *QZ, env=env)
    ok(r.returncode != 0 and "结算金额对不上" in r.stdout, "埋错：结算金额改了 5 元，对账拦住")
    jp.write_text(yuan, encoding="utf-8-sig")
    dp2 = next((dp / "账单").glob("订单表-*.csv"))
    rows3 = list(csv.reader(dp2.read_text(encoding="utf-8-sig").splitlines())); rows3[0].append("收件人手机号"); [r_.append("138********") for r_ in rows3[1:]]
    bak = dp2.read_text(encoding="utf-8-sig")
    with open(dp2, "w", newline="", encoding="utf-8-sig") as f: csv.writer(f).writerows(rows3)
    r = run(SK / "abacus-check/对账.py", *QZ, env=env)
    ok(r.returncode != 0 and "个人信息" in r.stdout, "埋错：订单表混进手机号列，对账拦住")
    dp2.write_text(bak, encoding="utf-8-sig")
    # 决策库同一编号两张「生效」卡：对账要拦
    (dp / "经营决策库" / "D-ZC-007-快递单价-v2.md").write_text("---\n编号: D-ZC-007\n标题: 快递单价\n状态: 生效\n参数:\n  快递单价: 3.5\n---\n", encoding="utf-8")
    run(SK / "abacus-ledger/算账.py", *QZ, env=env)
    r = run(SK / "abacus-check/对账.py", *QZ, env=env)
    ok(r.returncode != 0 and "D-ZC-007" in r.stdout, "埋错：同一编号两张生效决策卡，对账拦住")
    (dp / "经营决策库" / "D-ZC-007-快递单价-v2.md").unlink()
    run(SK / "abacus-ledger/算账.py", *QZ, env=env)
    # 巡检：改一个字的正文要被查出来，没改的不误报
    zw = t / "正文"; zw.mkdir()
    card = (home / "库" / "平台规则库" / "R-JS-004-达人佣金和团长服务费.md").read_text(encoding="utf-8")
    (zw / "112620-正文.txt").write_text("页面更新日期：2026-10-11\n----正文----\n新正文，和原来不一样\n", encoding="utf-8")
    r = run(SK / "abacus-base/巡检.py", "--店铺", str(dp), "--正文", str(zw), env=env)
    ok("变了 R-JS-004" in r.stdout and "一致 R-JS-004" not in r.stdout, "巡检：正文变了查得出来")
    ok(any((dp / "变更单").glob("B-草稿-*R-JS-004.md")), "巡检：写了变更单草稿，没自己改卡")
    ok(card == (home / "库" / "平台规则库" / "R-JS-004-达人佣金和团长服务费.md").read_text(encoding="utf-8"), "巡检：规则卡本身没被改")

print("算盘自测全过" if not bad else f"算盘自测 {bad} 处不过")
sys.exit(1 if bad else 0)
