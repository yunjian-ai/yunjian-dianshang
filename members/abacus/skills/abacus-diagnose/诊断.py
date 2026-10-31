"""算盘 · 单款诊断：一款衣服到底赚不赚、给达人最多给多少、退货率到多少就亏
用法：python3 诊断.py <商品ID或名字里的几个字> [--店铺 <店铺文件夹>] [--佣金 0.20] [--退货率 0.45] [--退货运费 6]
      还没卖过的新款（货郎交接单）：python3 诊断.py AQ-1108 --售价 79 --成本 32 [--品名 …] [--佣金 0.20]
      退货率用全店近 6 个月的、佣金用店里「默认佣金」（没有按 20%）、服务费率读平台规则库；--售价／--成本 也能盖掉卖过的款的数。
诊断完写款回执 店铺/<店>/算盘/款回执/<款号>.json（卖过的款用商品ID当款号）（保本价、每单期望利润、佣金上限……），货郎、经纪按款号去读（联调 10-31：以前只打印，下游只能靠手写）。
数从哪来：售价＝结算账单这款已结算单的收入合计中位数；成本＝成本表（没有这款就按经营决策库「成本_占定价」，都没有不算）；服务费率＝结算账单（没有就用平台规则库）；
          快递单价＝经营决策库；退货率＝订单表这款近 6 个月「发货后退款成功／发货」（可用 --退货率 改）；退货运费＝资金账单这款平均每单（没有就 --退货运费）
公式（一张发出去的单的期望利润，退回来的货原样再卖，平台服务费和佣金退回）：
  A＝售价 ×(1−服务费率−佣金率)−成本；期望利润＝(1−t)×A − 快递 − t×退货运费
  保本退货率 t＝(A−快递)/(A＋退货运费)；佣金上限 y：令期望利润＝0 解出（佣金基数近似取售价，严格是不含运费的实付）
  保本价 p：令期望利润＝0 解出 p＝(成本＋(快递＋t×退货运费)/(1−t))/(1−服务费率−佣金率)
"""
import argparse, collections, csv, datetime as dt, json, os, pathlib, statistics, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "abacus-fetch")); import 底账, 回执

f = lambda x: float(x or 0)

def jisuan(p, c, fw, y, kd, t, ry):
    A = p * (1 - fw - y) - c
    li = (1 - t) * A - kd - t * ry
    t0 = (A - kd) / (A + ry) if A + ry > 0 else 0.0
    ymax = (p * (1 - fw) - c - (kd + t * ry) / (1 - t)) / p if t < 1 else 0.0
    return A, li, t0, ymax

def baoben(c, fw, y, kd, t, ry):
    return (c + (kd + t * ry) / (1 - t)) / (1 - fw - y) if t < 1 and fw + y < 1 else None

def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("款"); a.add_argument("--店铺"); a.add_argument("--佣金", type=float)
    a.add_argument("--退货率", type=float); a.add_argument("--退货运费", type=float)
    a.add_argument("--售价", type=float); a.add_argument("--成本", type=float); a.add_argument("--品名", default="")
    a = a.parse_args(argv)
    dp = 底账.dianpu(a.店铺)
    js, zj, dd = [], [], []
    for p in sorted((dp / "账单").glob("*.csv")):
        ming, _, shu = 底账.du_biao(p)
        {"结算账单": js, "资金账单": zj, "订单表": dd}.get(ming, []).extend(shu)
    hit = lambda sp, mc: a.款 == sp or a.款 in (mc or "")
    yi = [r for r in js if r["结算单类型"] == "已结算" and hit(r["商品ID"], r["商品名称"])]
    if not yi:
        if a.售价 is None or a.成本 is None:
            sys.exit(f"结算账单里找不到「{a.款}」的已结算单（还没卖过的新款给 --售价 --成本 试算）")
        return xinpin(a, dp, dd, zj)
    kuan = collections.Counter(r["商品ID"] for r in yi)
    ming = lambda sid: collections.Counter(r["商品名称"] for r in yi if r["商品ID"] == sid).most_common(1)[0][0]
    if len(kuan) > 1:
        print(f"「{a.款}」对上了 {len(kuan)} 款，请主人说是哪一款（用商品ID再跑一次）：")
        for s_, n in kuan.most_common():
            print(f"  {s_}  {ming(s_)}（{n} 单）")
        sys.exit(2)
    sp = yi[0]["商品ID"]; mc = ming(sp)
    yi = [r for r in js if r["结算单类型"] == "已结算" and r["商品ID"] == sp]  # 同一个 ID 可能有几个标题（改过名、渠道品），都算这一款
    p = a.售价 if a.售价 is not None else statistics.median(f(r["收入合计"]) / max(1, f(r["商品数量"])) for r in yi)
    fw = statistics.median(-f(r["平台服务费"]) / f(r["收入合计"]) for r in yi if f(r["收入合计"]))
    dr = [r for r in yi if r["业务类型"] == "精选联盟" and f(r["收入合计"])]
    y = a.佣金 if a.佣金 is not None else (statistics.median(-f(r["达人佣金"]) / f(r["收入合计"]) for r in dr) if dr else 0.0)
    c, cly = (a.成本, "主人给的数") if a.成本 is not None else (None, "成本表")
    cbp = dp / "底座数据" / "成本表.csv"
    if c is None and cbp.exists():
        for r in csv.DictReader(open(cbp, encoding="utf-8-sig")):
            if 底账.qing(r["商品ID"]) == sp:
                try: c = float(底账.qing(r["单件成本"]))
                except ValueError: pass
    cs, _ = 底账.can_shu(底账.KU / "平台规则库", dp / "经营决策库")
    if c is None and cs.get("成本_占定价") not in (None, ""):   # 成本表没有、主人定过「成本＝定价×几成」：照主人的规矩，和掌柜同一个口径（联调 10-31）
        c, cly = round(p * float(cs["成本_占定价"]), 2), f"店铺规矩估（定价×{float(cs['成本_占定价']):g}，经营决策库）"
    if c is None:
        sys.exit(f"成本表里没有「{mc}」的成本，主人也没定成本规矩，不能诊断（不估）。请主人补成本")
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
    bb = baoben(c, fw, y, kd, t, ry)
    print(f"保本价：{bb:.2f} 元（按这个退货率和佣金，售价低过它就亏）" if bb else "保本价算不出（退货率或费率太高）")
    n_fa = sum(v[0] for v in yue.values())
    if a.退货率 is None and n_fa < 30:
        print(f"⚠️ 这款只有 {n_fa} 张发货单，退货率样本太少，上面的保本退货率和佣金上限只当参考；导近 6 个月订单表再算")
    print("按付款月份的退货率：" + "；".join(f"{k} {v[1] / v[0]:.0%}（{v[0]} 单）" for k, v in sorted(yue.items()) if v[0]))
    xie_huizhi(dp, a.款, sp, mc, p, c, cly, fw, y, kd, t, "这款近 6 个月订单表" if a.退货率 is None else "主人给的数", ry,
               "" if a.退货率 is not None or n_fa >= 30 else f"这款只有 {n_fa} 张发货单，退货率样本少，只当参考", shi=a.佣金 is not None)


def xinpin(a, dp, dd, zj):
    """还没卖过的新款（货郎交接单给售价、成本）：退货率用全店近 6 个月的，佣金用店里「默认佣金」，服务费率读平台规则库。"""
    cs, _ = 底账.can_shu(底账.KU / "平台规则库", dp / "经营决策库")
    fw = float(cs.get("费率_服饰内衣", 0.05))
    y = a.佣金 if a.佣金 is not None else float(cs.get("默认佣金") or 0.20)
    cang = cs.get("默认仓"); kd = float(cs.get(f"{cang}_每单", cs.get("快递单价", 3.0)))
    zi = [o for o in dd if o["发货时间"] and o["是否属于寄样订单"] != "是"]
    if a.退货率 is not None:
        t, tly = a.退货率, "主人给的数"
    elif zi:
        ri = sorted(o["支付完成时间"][:10] for o in zi if o.get("支付完成时间"))
        tian = (dt.date.fromisoformat(ri[-1]) - dt.date.fromisoformat(ri[0])).days + 1 if ri else 0
        t, tly = sum(o["售后状态"].endswith("退款成功") for o in zi) / len(zi), f"全店订单表（{ri[0] if ri else '?'}～{ri[-1] if ri else '?'}，{tian} 天、{len(zi)} 张发货单；新款还没卖过）"
        if tian < 60 or len(zi) < 30:   # 写实际盖了几天，不写死「近 6 个月」（联调 Bot 自报 10-31）
            print(f"⚠️ 借来的全店退货率只盖 {tian} 天、{len(zi)} 张发货单，样本少，保本价和佣金上限只当参考；导近 6 个月订单表再算")
            tly += "；样本少，只当参考"
    else:
        sys.exit("新款没有自己的退货率，店里也没有订单表：先导订单表，或用 --退货率 给一个")
    ty = [-f(r["动账金额"]) if r["动账方向"] == "出账" else f(r["动账金额"]) for r in zj if r["动账场景"] in ("上门取件-支付快递费", "消费者赔付")]
    ry = a.退货运费 if a.退货运费 is not None else (-statistics.mean(ty) if ty else 6.0)
    p, c = a.售价, a.成本
    A, li, t0, ymax = jisuan(p, c, fw, y, kd, t, ry)
    mc = a.品名 or a.款
    print(f"# 新款试算：{mc}（{a.款}，还没卖过）")
    print(f"售价 {p:.2f}｜成本 {c:.2f}｜平台服务费率 {fw:.1%}｜达人佣金率 {y:.1%}｜快递 {kd:.2f}｜退货率 {t:.0%}（{tly}）｜每单退货运费 {ry:.2f}")
    print(f"卖掉一件（不退）挣：{A - kd:.2f} 元；一张发出去的单期望挣：{li:.2f} 元（{'赚' if li > 0 else '亏'}）")
    bb = baoben(c, fw, y, kd, t, ry)
    print(f"保本价：{bb:.2f} 元（按这个退货率和佣金，售价低过它就亏）" if bb else "保本价算不出（退货率或费率太高）")
    print(f"按这个退货率，达人佣金最多给到：{ymax:.0%}（再高就亏；只给依据，佣金由主人定）")
    xie_huizhi(dp, a.款, "", mc, p, c, "货郎交接单" if a.成本 is not None else "成本表", fw, y, kd, t, tly, ry, "新款还没卖过，退货率借全店的，上架后用这款自己的数重算", shi=a.佣金 is not None)


def xie_huizhi(dp, kuan, sp, mc, p, c, cly, fw, y, kd, t, tly, ry, beizhu, shi=False):
    """款回执：货郎选品卡、佣金闸，经纪佣金闸按款号读 店铺/<店>/算盘/款回执/<款号>.json。"""
    A, li, t0, ymax = jisuan(p, c, fw, y, kd, t, ry)
    bb = baoben(c, fw, y, kd, t, ry)
    day = str(os.environ.get("YUNJIAN_TODAY") or dt.date.today())[:10]
    cs, _ = 底账.can_shu(底账.KU / "平台规则库", dp / "经营决策库")
    fd = float(cs["佣金封顶_主人定"]) if cs.get("佣金封顶_主人定") not in (None, "") else None   # 主人定的封顶；回执里直接给取低的，免得下游只看上限（联调 10-31）
    hz = {"款号": kuan, "商品ID": sp, "品名": mc, "来自": "算盘", "算的日期": day,
          "售价": round(p, 2), "成本": round(c, 2), "成本来源": cly,
          "保本价": round(bb, 2) if bb else None, "每单期望利润_算退货": round(li, 2), "卖一件不退挣": round(A - kd, 2),
          "每单期望利润_自销": round(jisuan(p, c, fw, 0.0, kd, t, ry)[1], 2),
          "佣金率_按此算": round(y, 4), "佣金上限": round(max(ymax, 0.0), 3), "佣金封顶_主人定": fd, "可给佣金_取低": round(min(max(ymax, 0.0), fd if fd is not None else 1.0), 3),
          "保本退货率": round(t0, 3),
          "退货率": round(t, 3), "退货率来源": tly, "平台服务费率": round(fw, 4), "快递": round(kd, 2), "每单退货运费": round(ry, 2),
          "说明": f"每单期望利润按达人单算（佣金 {y:.0%}），自销单不付佣金另列；都按退货率 {t:.0%} 摊（退回的货原样再卖、服务费和佣金退回）；卖一件不退挣是不算退货的；保本价、佣金上限只给依据，定价和佣金主人定" + (f"；{beizhu}" if beizhu else "")}
    jian = sp or kuan   # 卖过的款按商品ID存（主人随口说的「开衫」会和新款撞名，联调 Bot 自报 10-31），新款按款号存
    hz["款号"] = jian
    d = dp / "算盘" / "款回执"; d.mkdir(parents=True, exist_ok=True)
    out = d / (str(jian).replace("/", "_") + ".json")
    jiu = json.loads(out.read_text(encoding="utf-8")) if out.exists() else None
    shisuan = {f"{y:.0%}": {"每单期望利润_算退货": round(li, 2), "保本价": round(bb, 2) if bb else None, "算的日期": day}}
    if shi and jiu and abs(float(jiu.get("佣金率_按此算", y)) - y) > 1e-9:
        # 已有基准回执、这次是「给 X% 还赚多少」的试算：只记进「按佣金试算」，基准数不动，免得和货郎选品卡上的对不上（联调 Bot 自报 10-31）
        jiu.setdefault("按佣金试算", {}).update(shisuan); hz = jiu
        print(f"款回执基准没动（按 {jiu['佣金率_按此算']:.0%}），这次按 {y:.0%} 的试算记进「按佣金试算」：{out}")
    else:
        if jiu and jiu.get("按佣金试算"):
            hz["按佣金试算"] = jiu["按佣金试算"]
        print(f"款回执已写：{out}（货郎、经纪用 --款号 {jian} 读）")
    out.write_text(json.dumps(hz, ensure_ascii=False, indent=1), encoding="utf-8")
    deng = [f"{mc}（{jian}）按佣金 {y:.0%} 每单期望亏 {abs(li):.2f} 元：压佣金到 {max(ymax, 0):.0%} 以内，或提价到保本价 {bb:.2f} 元以上，请主人定" if bb else f"{mc}（{jian}）按佣金 {y:.0%} 每单期望亏 {abs(li):.2f} 元，请主人定"] if li < 0 else []
    回执.ji(dp, "abacus", zuole={"单款诊断": 1}, chule=[f"款回执 {jian}"], deng=deng, chuchu="算盘·单款诊断")   # 算出亏钱的进「等主人定」，掌柜报里看得到

if __name__ == "__main__":
    main()
