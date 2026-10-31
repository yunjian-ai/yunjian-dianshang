"""算盘 · 算账：店铺「账单」文件夹里的表 → 逐单三层利润 → 汇总
用法：python3 算账.py --起 2026-10-21 --止 2026-10-27 [--店铺 <店铺文件夹>]
读：店铺/账单/ 里核过的结算账单、资金账单、订单表（同类多份自动合并去重）；店铺/底座数据/成本表.csv；
    库/平台规则库 和 店铺/经营决策库 的参数（只认「状态: 生效」，决策库盖规则库，都没有用服装店默认值并记下来）
出：店铺/报告/<起>至<止>/ 逐单账.csv、汇总.json、算账报告.md
口径（三层）：毛利＝收入−成本；到手＝毛利−平台服务费−佣金分成−发货运费；净利＝到手−退货运费−补偿−店铺层面费用−税
"""
import argparse, collections, csv, datetime as dt, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "abacus-fetch")); import 底账, 回执

MOREN = {"快递单价": 3.0, "退回损耗比例": 0.0, "寄样单列": "是", "增值税征收率": 0.01, "免征_月销售额上限": 100000.0,
         "附加税费_合计率_减半后": 0.06, "纳税人类型": "小规模"}
f = lambda x: float(x or 0)
r2 = lambda x: round(x + 0, 2)


def he_bing(dp, ming, key):
    """同一类表的所有份合并，按 key 去重（后读的盖前读的）。"""
    out = {}
    for p in sorted((dp / "账单").glob(f"{ming}-*.csv")):
        for r in 底账.du_biao(p)[2]:
            out[key(r)] = r
    return list(out.values())


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--起", required=True); a.add_argument("--止", required=True); a.add_argument("--店铺")
    a = a.parse_args(argv)
    dp = 底账.dianpu(a.店铺)
    js_all = he_bing(dp, "结算账单", lambda r: (r["子订单号"], r["结算单类型"], r["结算时间"]))
    zj_all = he_bing(dp, "资金账单", lambda r: r.get("动帐流水号") or (r["动账时间"], r["子订单号"], r["动账金额"]))
    dd = {r["子订单编号"]: r for r in he_bing(dp, "订单表", lambda r: r["子订单编号"])}
    if not js_all:
        sys.exit("账单文件夹里没有结算账单，先照 abacus-fetch 取数、核表")
    cb = {}
    cbp = dp / "底座数据" / "成本表.csv"
    if cbp.exists():
        for r in csv.DictReader(open(cbp, encoding="utf-8-sig")):
            if 底账.qing(r.get("单件成本")) not in ("", "（元，进价或生产成本，含包装）"):
                try:
                    cb[底账.qing(r["商品ID"])] = float(底账.qing(r["单件成本"]))
                except ValueError:
                    pass
    cs, ly = 底账.can_shu(底账.KU / "平台规则库", dp / "经营决策库")
    yong_moren = []
    def P(k):
        if k in cs:
            return cs[k]
        yong_moren.append(k); return MOREN[k]
    cang = cs.get("默认仓")
    kd = float(cs[f"{cang}_每单"]) if cang and f"{cang}_每单" in cs else float(P("快递单价"))
    sunhao, zz_lv, mian, fj_lv = float(P("退回损耗比例")), float(P("增值税征收率")), float(P("免征_月销售额上限")), float(P("附加税费_合计率_减半后"))

    zai = lambda t: a.起 <= (t or "")[:10] <= a.止
    js = [r for r in js_all if zai(r["结算时间"])]
    zj = [r for r in zj_all if zai(r["动账时间"])]
    js_zi_all = {r["子订单号"] for r in js_all}

    # 资金账单：平台扣的退货运费、小额打款（分运费补偿／客服补偿）、店铺层面费用
    tuiyun, buchang, yunbu = collections.defaultdict(float), collections.defaultdict(float), collections.defaultdict(float)
    dian = collections.defaultdict(float)
    for r in zj:
        cj, je, zi = r["动账场景"], f(r["动账金额"]), r["子订单号"]
        fx = -1 if r["动账方向"] == "出账" else 1
        if cj in ("上门取件-支付快递费", "消费者赔付"):
            tuiyun[zi] += fx * je
        elif "小额打款" in cj:
            (yunbu if "运费" in r.get("备注", "") else buchang)[zi or "店铺"] += fx * je
        elif cj in ("偏远地区物流服务",):
            dian["偏远地区配送费"] += fx * je
        elif cj not in ("货款结算入账", "提现") and not cj.startswith("退款-"):
            dian[cj] += fx * je  # 没见过的动账场景：先记店铺层面，报告里列出来

    def gui(zi, sp="", mc="", drid="", drm=""):
        """用订单表补上款和达人（资金账单退货行只有子订单号）"""
        o = dd.get(zi)
        if o:
            sp, mc = o["商品ID"] or sp, o["选购商品"] or mc
            if o["流量来源"] == "精选联盟" and o["达人ID"] not in ("", "-"):
                drid, drm = o["达人ID"], o["达人昵称"]
            elif o["流量来源"] == "小店自卖":
                drid = drm = ""
        maifa = ("达人" if drid else "自销") if (o or sp) else "未知"
        return sp, mc, drid, drm, maifa

    zhu_bao = collections.Counter(r["订单号"] for r in js if r["结算单类型"] == "已结算")
    hang, que = [], set()
    for r in js:
        sp, n = r["商品ID"], int(f(r["商品数量"]) or 1)
        lx = r["结算单类型"]
        yi = lx == "已结算"
        tui = "退款" in lx
        if sp not in cb:
            que.add((sp, r["商品名称"]))
        dj = cb.get(sp, 0.0)
        chengben = dj * n if yi else (-dj * n * (1 - sunhao) if tui else 0.0)  # 结算后退款：货退回来，成本冲回（扣掉损耗）
        fy = kd / zhu_bao[r["订单号"]] if yi else 0.0
        sr = f(r["收入合计"]); zc = f(r["支出合计"]); fw = f(r["平台服务费"])
        ml = sr - chengben; dz = ml + zc - fy
        zi = r["子订单号"]
        th, yb, kb = tuiyun.pop(zi, 0.0), yunbu.pop(zi, 0.0), buchang.pop(zi, 0.0)  # 客服补的钱（运费、差价）都挂回这一单
        maifa = "达人" if r["业务类型"] == "精选联盟" else "自销"
        hang.append(dict(子订单号=zi, 日期=r["结算时间"][:10], 类型=lx, 卖法=maifa, 达人ID=r["达人ID"], 达人=r["达人名称"],
                         商品ID=sp, 商品=r["商品名称"], 件数=n, 收入=r2(sr), 成本=r2(-chengben), 平台服务费=r2(fw), 佣金分成=r2(zc - fw),
                         发货运费=r2(-fy), 毛利=r2(ml), 到手=r2(dz), 退货运费=r2(th), 运费补偿=r2(yb), 客服补偿=r2(kb), 单前净利=r2(dz + th + yb + kb),
                         免佣=r.get("是否免佣", "")[:1], 缺成本="是" if sp not in cb else ""))
    # 结算前就退了、被扣了退货运费的单：损失＝发货运费＋退货运费（＋客服补的运费）
    for zi in list(tuiyun):
        th, yb, kb = tuiyun.pop(zi), yunbu.pop(zi, 0.0), buchang.pop(zi, 0.0)
        sp, mc, drid, drm, maifa = gui(zi)
        hang.append(dict(子订单号=zi, 日期="", 类型="结算前退货", 卖法=maifa, 达人ID=drid, 达人=drm, 商品ID=sp, 商品=mc, 件数=0,
                         收入=0, 成本=0, 平台服务费=0, 佣金分成=0, 发货运费=r2(-kd), 毛利=0, 到手=r2(-kd), 退货运费=r2(th),
                         运费补偿=r2(yb), 客服补偿=r2(kb), 单前净利=r2(-kd + th + yb + kb), 免佣="", 缺成本=""))
    # 只有客服补钱、没有别的记录的单
    for zi in sorted((set(yunbu) | set(buchang)) - {"店铺"}):
        yb, kb = yunbu.get(zi, 0.0), buchang.get(zi, 0.0)
        sp, mc, drid, drm, maifa = gui(zi)
        hang.append(dict(子订单号=zi, 日期="", 类型="只有客服补钱", 卖法=maifa, 达人ID=drid, 达人=drm, 商品ID=sp, 商品=mc, 件数=0, 收入=0, 成本=0,
                         平台服务费=0, 佣金分成=0, 发货运费=0, 毛利=0, 到手=0, 退货运费=0, 运费补偿=r2(yb), 客服补偿=r2(kb), 单前净利=r2(yb + kb), 免佣="", 缺成本=""))

    # 寄样：不算销售，记达人寄样开支（成本＋运费）
    jiyang = []
    for o in dd.values():
        if o["是否属于寄样订单"] == "是" and zai(o["支付完成时间"]) and o["发货时间"]:
            c = cb.get(o["商品ID"])
            jiyang.append(dict(子订单号=o["子订单编号"], 达人=o["达人昵称"], 商品=o["选购商品"], 开支=r2(-((c or 0) + kd)), 缺成本="" if c is not None else "是"))
    # 预估：近 45 天付款、已发货、没退款、哪份结算账单里都还没有的单
    zhi = dt.date.fromisoformat(a.止)
    yugu = [o for o in dd.values() if o["发货时间"] and not o["售后状态"].endswith("退款成功") and o["是否属于寄样订单"] != "是"
            and o["子订单编号"] not in js_zi_all and o["支付完成时间"][:10] >= (zhi - dt.timedelta(days=45)).isoformat()
            and o["支付完成时间"][:10] <= a.止]

    ok = [x for x in hang if not x["缺成本"]]
    S = lambda k, rs=ok: r2(sum(x[k] for x in rs))
    tian = (dt.date.fromisoformat(a.止) - dt.date.fromisoformat(a.起)).days + 1
    sr_all = S("收入")
    # 免征额：按月申报看月 10 万，按季度申报看季度 30 万；超过就按全部销售额计税（不是只算超出部分，R-GZ-001）
    jidu = str(cs.get("申报周期", "季度")).startswith("季")
    yue = sr_all * (90 if jidu else 30) / tian
    mian_x = float(cs.get("免征_季度销售额上限", 300000)) if jidu else mian
    zzs = 0.0 if yue <= mian_x else r2(sr_all / (1 + zz_lv) * zz_lv)
    fj = r2(zzs * fj_lv)
    bc = r2(S("客服补偿") + buchang.get("店铺", 0.0))  # 挂在单上的＋没写子订单号的
    dian_he = r2(sum(dian.values()))
    jy = r2(sum(x["开支"] for x in jiyang))
    jl = r2(S("单前净利") + buchang.get("店铺", 0.0) + dian_he + jy - zzs - fj)
    chong = sorted({x["子订单号"] for x in hang if x["退货运费"] < 0 and x["运费补偿"] < 0})

    out = dp / "报告" / f"{a.起}至{a.止}"; out.mkdir(parents=True, exist_ok=True)
    with open(out / "逐单账.csv", "w", newline="", encoding="utf-8-sig") as fo:
        w = csv.DictWriter(fo, fieldnames=list(hang[0])); w.writeheader(); w.writerows(hang)
    hz = {"店铺": dp.name, "起": a.起, "止": a.止, "天数": tian, "快递单价": kd,
          "三层": {"收入": sr_all, "成本": S("成本"), "毛利": S("毛利"), "平台服务费": S("平台服务费"), "佣金分成": S("佣金分成"),
                   "发货运费": S("发货运费"), "到手": S("到手"), "退货运费": S("退货运费"), "运费补偿": S("运费补偿"), "客服补偿": bc,
                   "店铺层面": dian_he, "达人寄样开支": jy, "增值税": -zzs or 0.0, "附加": -fj or 0.0, "净利": jl},
          "店铺层面明细": {k: r2(v) for k, v in dian.items()},
          "税": {"纳税人类型": P("纳税人类型"), "申报周期": "季度" if jidu else "月", "本期折算收入": r2(yue), "免征额": mian_x,
                "说明": (f"折{'季' if jidu else '月'}不超免征额，增值税 0" if not zzs else f"折{'季' if jidu else '月'}超过免征额，全部销售额按 {zz_lv:.0%} 估")},
          "参数冲突": list(底账.CHONG), "夹带的话": json.loads((dp / "账单" / "夹带的话.json").read_text(encoding="utf-8")) if (dp / "账单" / "夹带的话.json").exists() else [],
          "数据缺口": [],
          "缺成本": [{"商品ID": s, "商品": m, "单数": sum(1 for x in hang if x["商品ID"] == s)} for s, m in sorted(que)],
          "缺成本收入": r2(sum(x["收入"] for x in hang if x["缺成本"])),
          "重复赔付": chong, "寄样": jiyang,
          "预估": {"单数": len(yugu), "商家收入金额": r2(sum(f(o["商家收入金额"]) for o in yugu)), "说明": "近 45 天付款、已发货、没退款、结算账单里还没有"},
          "参数来源": {k: ly.get(k, "库/默认值（服装店默认值）") for k in ["快递单价", "退回损耗比例", "增值税征收率", "免征_月销售额上限", "附加税费_合计率_减半后"]},
          "用了默认值": sorted(set(yong_moren)), "有订单表": bool(dd)}
    (out / "汇总.json").write_text(json.dumps(hz, ensure_ascii=False, indent=1), encoding="utf-8")
    zj_ri = sorted(r["动账时间"][:10] for r in zj_all if r.get("动账时间"))
    if not zj_ri or zj_ri[0] > a.起 or zj_ri[-1] < a.止:
        hz["数据缺口"].append(f"资金账单只盖 {zj_ri[0] if zj_ri else '无'}～{zj_ri[-1] if zj_ri else '无'}，退货运费、补偿可能算少了")
    dd_ri = sorted(o["支付完成时间"][:10] for o in dd.values() if o.get("支付完成时间"))
    if not dd_ri or (dt.date.fromisoformat(dd_ri[-1]) - dt.date.fromisoformat(dd_ri[0])).days < 59:
        hz["数据缺口"].append("订单表不到 2 个月，退货率只当参考" if dd_ri else "没有订单表：结算前退掉的单挂不到款和达人，退货率算不了")
    (out / "汇总.json").write_text(json.dumps(hz, ensure_ascii=False, indent=1), encoding="utf-8")
    t = hz["三层"]
    md = [f"# {dp.name} 算账 · {a.起}～{a.止}", "", "| 项 | 元 |", "|---|---|"] + [f"| {k} | {v} |" for k, v in t.items()] + [
          "", f"缺成本 {len(que)} 款（收入 {hz['缺成本收入']} 元没进合计）；重复赔付 {len(chong)} 单；寄样 {len(jiyang)} 单；预估（未结算）{len(yugu)} 单",
          f"用了默认值：{'、'.join(hz['用了默认值']) or '无'}"]
    (out / "算账报告.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md)); print("出到", out)
    回执.ji(dp, "abacus", zuole={"算账": 1}, kazai=[f"缺成本 {len(que)} 款"] if que else [],
           shu={"账": {"起": a.起, "止": a.止, **t}}, chuchu=f"算盘·算账·{a.起}～{a.止}")

if __name__ == "__main__":
    main()
