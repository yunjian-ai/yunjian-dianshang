"""算盘 · 对账：出报告前把关，不过就不交。
用法：python3 对账.py --起 2026-10-21 --止 2026-10-27 [--店铺 <店铺文件夹>]
查（拦＝不能交；提醒＝交，但写进报告「要注意的」）：
  拦  结算账单每行：结算金额 ≠ 收入合计＋支出合计（差 >0.01）
  拦  逐单账加总 ≠ 汇总.json（脚本自己算错）
  拦  账单文件夹里的订单表带个人信息列
  拦  本期结算账单一行都没有（取数没取全）
  提醒 资金账单「货款结算入账」合计 和 结算账单已结算的结算金额 差 >1%（看资金账单的时间段够不够）
  拦  决策库同一编号有两张「生效」卡（参数可能用错）
  提醒 缺成本、重复赔付、用了默认值、资金账单时间段没盖住本期、账单里夹带像写给 AI 的话
  提醒 同一子订单：结算账单的结算金额 ≠ 资金账单「货款结算入账」；结算后退款在资金账单里找不到退款流水
"""
import argparse, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "abacus-fetch")); import 底账

f = lambda x: float(x or 0)

def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--起", required=True); a.add_argument("--止", required=True); a.add_argument("--店铺")
    a = a.parse_args(argv)
    dp = pathlib.Path(a.店铺) if a.店铺 else 底账.dianpu()
    zai = lambda t: a.起 <= (t or "")[:10] <= a.止
    lan, ti = [], []
    js, zj = [], []
    for p in sorted((dp / "账单").glob("*.csv")):
        ming, tou, shu = 底账.du_biao(p)
        if ming == "结算账单":
            js += [r for r in shu if zai(r["结算时间"])]
        elif ming == "资金账单":
            zj += shu
        elif ming == "订单表":
            yinsi = [c for c in tou if any(k in c for k in 底账.YINSI)]
            if yinsi:
                lan.append(f"{p.name} 带个人信息列（{'、'.join(yinsi)}），重新跑核表.py")
    if not js:
        lan.append("本期结算账单一行都没有：先照 abacus-fetch 取数")
    for r in js:
        if abs(f(r["结算金额"]) - (f(r["收入合计"]) + f(r["支出合计"]))) > 0.01:
            lan.append(f"子订单 {r['子订单号']} 结算金额对不上收入＋支出")
    ruzhang = {r["子订单号"]: f(r["动账金额"]) for r in zj if r["动账场景"] == "货款结算入账"}
    bu = [r["子订单号"] for r in js if r["结算单类型"] == "已结算" and r["子订单号"] in ruzhang and abs(ruzhang[r["子订单号"]] - f(r["结算金额"])) > 0.01]
    if bu: ti.append(f"{len(bu)} 单结算金额和资金账单入账对不上：{'、'.join(bu[:5])}")
    tuikuan = {r["子订单号"] for r in zj if r["动账场景"].startswith("退款-结算后退款")}
    meiyou = [r["子订单号"] for r in js if "结算后退款" in r["结算单类型"] and r["子订单号"] not in tuikuan]
    if meiyou and zj: ti.append(f"{len(meiyou)} 笔结算后退款在资金账单里找不到退款流水（多半是资金账单时间段不够）：{'、'.join(meiyou[:5])}")
    ru = sum(f(r["动账金额"]) for r in zj if r["动账场景"] == "货款结算入账" and zai(r["动账时间"]))
    jie = sum(f(r["结算金额"]) for r in js if r["结算单类型"] == "已结算")
    if zj and jie and abs(ru - jie) / jie > 0.01:
        ti.append(f"资金账单货款入账 {ru:.2f} 和结算账单已结算 {jie:.2f} 差 {abs(ru - jie) / jie:.1%}：两张表的时间段可能不一样，或有结算延迟")
    zj_ri = sorted(r["动账时间"][:10] for r in zj if r.get("动账时间"))
    if not zj_ri or zj_ri[0] > a.起 or zj_ri[-1] < a.止:
        ti.append(f"资金账单只盖到 {zj_ri[0] if zj_ri else '无'}～{zj_ri[-1] if zj_ri else '无'}，本期是 {a.起}～{a.止}：退货运费、补偿可能算少了")
    out = dp / "报告" / f"{a.起}至{a.止}"
    if (out / "汇总.json").exists():
        import csv
        hz = json.loads((out / "汇总.json").read_text(encoding="utf-8"))
        rows = [r for r in csv.DictReader(open(out / "逐单账.csv", encoding="utf-8-sig")) if not r["缺成本"]]
        for k in ["收入", "成本", "到手", "退货运费"]:
            if abs(sum(f(r[k]) for r in rows) - hz["三层"][k]) > 0.05:
                lan.append(f"逐单账「{k}」加总和汇总对不上")
        if hz["缺成本"]: ti.append(f"缺成本 {len(hz['缺成本'])} 款，收入 {hz['缺成本收入']} 元没进合计")
        if hz["重复赔付"]: ti.append(f"可能重复赔付 {len(hz['重复赔付'])} 单")
        if hz["用了默认值"]: ti.append("用了默认值：" + "、".join(hz["用了默认值"]))
        for x in hz.get("参数冲突", []): lan.append("决策库" + x)
        for x in hz.get("夹带的话", []): ti.append(f"{x['表']}第 {x['行']} 行夹带像写给 AI 的话（没照做）：{x['原话']}")
    else:
        ti.append("还没算账（没有汇总.json），只查了账单")
    # 要请主人（或在后台）抽查的单：本期结算金额最大的几单，第一次算账抽 10 单、以后 5 单
    if (out / "汇总.json").exists():
        hz = json.loads((out / "汇总.json").read_text(encoding="utf-8"))
        n = 10 if len(list((dp / "报告").glob("*"))) <= 1 else 5
        chou = [r["子订单号"] for r in sorted((r for r in js if r["结算单类型"] == "已结算"), key=lambda r: -f(r["结算金额"]))[:n]]
        hz["对账"] = {"结论": "OK" if not lan else "不过", "拦": lan, "提醒": ti, "抽单": chou, "抽单结果": hz.get("对账", {}).get("抽单结果", "待回")}
        (out / "汇总.json").write_text(json.dumps(hz, ensure_ascii=False, indent=1), encoding="utf-8")
    for x in lan: print("拦", x)
    for x in ti: print("提醒", x)
    print("对账 OK" if not lan else f"对账 不过 {len(lan)} 处，不能交")
    return 1 if lan else 0

if __name__ == "__main__":
    sys.exit(main())
