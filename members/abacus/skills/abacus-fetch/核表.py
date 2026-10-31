"""算盘 · 核表：把抖店导出的原表认出来、洗干净、放进店铺的「账单」文件夹。
用法：python3 核表.py <导出的文件...> [--店铺 <店铺文件夹>]
- 认出是结算账单、资金账单、订单表还是待结算订单；跳过公式说明行；去掉长数字前的引号和制表符
- 订单表只留 25 列，带收件人、手机、地址等个人信息的列一律删掉（原文件不动，提醒主人自己删）
- 查：主体名称是否只有一个、时间段从哪天到哪天
输出：店铺/账单/<表名>-<起>至<止>.csv，并打印一行「核表 OK／有问题」"""
import argparse, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import 底账

SHIJIAN = {"结算账单": "结算时间", "资金账单": "动账时间", "订单表": "支付完成时间", "待结算": "下单时间"}

def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("文件", nargs="+"); a.add_argument("--店铺")
    a = a.parse_args(argv)
    dp = 底账.dianpu(a.店铺)
    bad = 0
    jia = []
    for f in a.文件:
        ming, tou, shu = 底账.du_biao(f)
        if not ming:
            print(f"有问题 认不出这张表：{f}（表头前几列：{'、'.join(tou[:5])}）"); bad += 1; continue
        if ming == "订单表":
            shan = [c for c in tou if c not in 底账.DINGDAN_LIE]
            yinsi = [c for c in shan if any(k in c for k in 底账.YINSI)]
            tou = [c for c in 底账.DINGDAN_LIE if c in tou]
            if yinsi:
                print(f"提醒 订单表里带了个人信息列（{'、'.join(yinsi)}），已删掉不存；原文件请主人自己删")
        for hang, lie, hua in 底账.jiadai(shu):
            jia.append({"表": ming, "行": hang, "列": lie, "原话": hua})
            print(f"提醒 {ming} 第 {hang} 行「{lie}」里有像写给 AI 的话，不照做，请主人看：{hua}")
        sj = SHIJIAN[ming]
        ri = sorted(r[sj][:10] for r in shu if r.get(sj))
        zhuti = sorted({r.get("商户主体名称", "") for r in shu} - {""})
        if len(zhuti) > 1:
            print(f"有问题 {ming} 里有 {len(zhuti)} 个主体：{'、'.join(zhuti)}——是不是混了别的店？"); bad += 1
        if not shu:
            print(f"有问题 {ming} 没有数据行：{f}"); bad += 1; continue
        qi, zhi = ri[0] if ri else "无日期", ri[-1] if ri else "无日期"
        if ming == "订单表" and ri:
            import datetime as _d
            kua = (_d.date.fromisoformat(zhi) - _d.date.fromisoformat(qi)).days + 1
            if kua < 60:
                print(f"提醒 订单表只盖 {kua} 天（{qi}～{zhi}）：退货率要近 6 个月才准，这次的退货率只当参考，请主人再导一份近 6 个月的")
        out = dp / "账单" / f"{ming}-{qi}至{zhi}.csv"
        底账.xie_biao(out, tou, shu)
        print(f"核表 {ming} {len(shu)} 行 {qi}～{zhi} → {out}")
    if jia:
        import json
        p = dp / "账单" / "夹带的话.json"; old = json.loads(p.read_text(encoding="utf-8")) if p.exists() else []
        p.write_text(json.dumps(old + jia, ensure_ascii=False, indent=1), encoding="utf-8")
    print("核表 OK" if not bad else f"核表 有问题 {bad} 处")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
