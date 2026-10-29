"""算盘 · 单款诊断：一款衣服到底赚不赚、给达人最多给多少、退货率到多少就亏
用法：python3 诊断.py <商品ID或名字里的几个字> [--店铺 <店铺文件夹>] [--佣金 0.20] [--退货率 0.45] [--退货运费 6]
数从哪来：售价＝结算账单这款已结算单的收入合计中位数；成本＝成本表；服务费率＝结算账单（没有就用平台规则库）；
          快递单价＝经营决策库；退货率＝订单表这款近 6 个月「发货后退款成功／发货」（可用 --退货率 改）；退货运费＝资金账单这款平均每单（没有就 --退货运费）
公式（一张发出去的单的期望利润，退回来的货原样再卖，平台服务费和佣金退回）：
  A＝售价 ×(1−服务费率−佣金率)−成本；期望利润＝(1−t)×A − 快递 − t×退货运费
  保本退货率 t＝(A−快递)/(A＋退货运费)；佣金上限 y：令期望利润＝0 解出（佣金基数近似取售价，严格是不含运费的实付）
"""
import argparse, collections, csv, pathlib, statistics, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "abacus-fetch")); import 底账

f = lambda x: float(x or 0)

def jisuan(p, c, fw, y, kd, t, ry):
    A = p * (1 - fw - y) - c
    li = (1 - t) * A - kd - t * ry
    t0 = (A - kd) / (A + ry) if A + ry > 0 else 0.0
    ymax = (p * (1 - fw) - c - (kd + t * ry) / (1 - t)) / p if t < 1 else 0.0
    return A, li, t0, ymax

def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("款"); a.add_argument("--店铺"); a.add_argument("--佣金", type=float)
    a.add_argument("--退货率", type=float); a.add_argument("--退货运费", type=float)
    a = a.parse_args(argv)
    dp = pathlib.Path(a.店铺) if a.店铺 else 底账.dianpu()
    js, zj, dd = [], [], []
    for p in sorted((dp / "账单").glob("*.csv")):
        ming, _, shu = 底账.du_biao(p)
        {"结算账单": js, "资金账单": zj, "订单表": dd}.get(ming, []).extend(shu)
    hit = lambda sp, mc: a.款 == sp or a.款 in (mc or "")
    yi = [r for r in js if r["结算单类型"] == "已结算" and hit(r["商品ID"], r["商品名称"])]
    if not yi:
        sys.exit(f"结算账单里找不到「{a.款}」的已结算单")
    kuan = collections.Counter(r["商品ID"] for r in yi)
    ming = lambda sid: collections.Counter(r["商品名称"] for r in yi if r["商品ID"] == sid).most_common(1)[0][0]
    if len(kuan) > 1:
        print(f"「{a.款}」对上了 {len(kuan)} 款，请主人说是哪一款（用商品ID再跑一次）：")
        for s_, n in kuan.most_common():
            print(f"  {s_}  {ming(s_)}（{n} 单）")
        sys.exit(2)
    sp = yi[0]["商品ID"]; mc = ming(sp)
    yi = [r for r in js if r["结算单类型"] == "已结算" and r["商品ID"] == sp]  # 同一个 ID 可能有几个标题（改过名、渠道品），都算这一款
    p = statistics.median(f(r["收入合计"]) / max(1, f(r["商品数量"])) for r in yi)
    fw = statistics.median(-f(r["平台服务费"]) / f(r["收入合计"]) for r in yi if f(r["收入合计"]))
    dr = [r for r in yi if r["业务类型"] == "精选联盟" and f(r["收入合计"])]
    y = a.佣金 if a.佣金 is not None else (statistics.median(-f(r["达人佣金"]) / f(r["收入合计"]) for r in dr) if dr else 0.0)
    c = None
    cbp = dp / "底座数据" / "成本表.csv"
    if cbp.exists():
        for r in csv.DictReader(open(cbp, encoding="utf-8-sig")):
            if 底账.qing(r["商品ID"]) == sp:
                try: c = float(底账.qing(r["单件成本"]))
                except ValueError: pass
    if c is None:
        sys.exit(f"成本表里没有「{mc}」的成本，不能诊断（不估）。请主人补成本")
    cs, _ = 底账.can_shu(底账.KU / "平台规则库", dp / "经营决策库")
    cang = cs.get("默认仓"); kd = float(cs.get(f"{cang}_每单", cs.get("快递单价", 3.0)))
    zi = [o for o in dd if o["商品ID"] == sp and o["发货时间"] and o["是否属于寄样订单"] != "是"]
    yue = collections.defaultdict(lambda: [0, 0])
    for o in zi:
        yue[o["支付完成时间"][:7]][0] += 1; yue[o["支付完成时间"][:7]][1] += o["售后状态"].endswith("退款成功")
    t = a.退货率 if a.退货率 is not None else (sum(v[1] for v in yue.values()) / sum(v[0] for v in yue.values()) if zi else None)
    if t is None:
        sys.exit("没有订单表算不出退货率：先导订单表，或用 --退货率 给一个")
    zis = {o["子订单编号"] for o in zi}
    ty = [-f(r["动账金额"]) if r["动账方向"] == "出账" else f(r["动账金额"]) for r in zj if r["动账场景"] in ("上门取件-支付快递费", "消费者赔付") and r["子订单号"] in zis]
    ry = a.退货运费 if a.退货运费 is not None else (-statistics.mean(ty) if ty else 6.0)
    A, li, t0, ymax = jisuan(p, c, fw, y, kd, t, ry)
    print(f"# 单款诊断：{mc}（{sp}）")
    print(f"售价 {p:.2f}｜成本 {c:.2f}｜平台服务费率 {fw:.1%}｜达人佣金率 {y:.1%}｜快递 {kd:.2f}｜退货率 {t:.0%}｜每单退货运费 {ry:.2f}")
    print(f"卖掉一件（不退）挣：{A - kd:.2f} 元；一张发出去的单期望挣：{li:.2f} 元（{'赚' if li > 0 else '亏'}）")
    print(f"保本退货率：{t0:.0%}（退货率高过它就亏）")
    print(f"按现在退货率，达人佣金最多给到：{ymax:.0%}（再高就亏；只给依据，佣金由主人定）")
    n_fa = sum(v[0] for v in yue.values())
    if a.退货率 is None and n_fa < 30:
        print(f"⚠️ 这款只有 {n_fa} 张发货单，退货率样本太少，上面的保本退货率和佣金上限只当参考；导近 6 个月订单表再算")
    print("按付款月份的退货率：" + "；".join(f"{k} {v[1] / v[0]:.0%}（{v[0]} 单）" for k, v in sorted(yue.items()) if v[0]))

if __name__ == "__main__":
    main()
