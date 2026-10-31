"""算盘 · 报告：把算账.py 出的「逐单账.csv」「汇总.json」排成给主人看的一页报告（网页；Bot 里当附件发，电脑上直接打开）
用法：python3 报告.py --起 2026-10-21 --止 2026-10-27 [--店铺 <店铺文件夹>] [--模拟 成本,快递单价]
顺序（设计稿 v0.1，主人认过）：三句话 → 四个大数 → 三层账 → 自销和达人 → 按款 → 按达人（含近 6 个月退货率）→ 要注意的 → 逐单明细
三句话由数据按模板生成，不让模型编；数都能在逐单账里追到子订单。
"""
import argparse, collections, csv, html, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "abacus-fetch")); import 底账

f = lambda x: float(x or 0)
yuan = lambda x: f"{x:,.0f}"
bai = lambda a, b: f"{a / b:.0%}" if b else "—"
E = html.escape
m = lambda x: ("−" + yuan(-x)) if x <= -0.5 else yuan(abs(x) if abs(x) < 0.5 else x)


def tb(head, body, num_from=1, num_to=99):
    c = lambda i: "n" if num_from <= i < num_to else ""
    h = "".join(f'<th class="{c(i)}">{E(x)}</th>' for i, x in enumerate(head))
    b = "".join("<tr>" + "".join(f'<td class="{c(i)}{" neg" if str(v).startswith("−") else ""}">{v}</td>' for i, v in enumerate(r)) + "</tr>" for r in body)
    return f'<div class="tw"><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>'


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--起", required=True); a.add_argument("--止", required=True)
    a.add_argument("--店铺"); a.add_argument("--模拟", default="")
    a = a.parse_args(argv)
    dp = 底账.dianpu(a.店铺)
    out = dp / "报告" / f"{a.起}至{a.止}"
    hz = json.loads((out / "汇总.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader(open(out / "逐单账.csv", encoding="utf-8-sig")))
    for r in rows:
        for k in ["件数", "收入", "成本", "平台服务费", "佣金分成", "发货运费", "毛利", "到手", "退货运费", "运费补偿", "客服补偿", "单前净利"]:
            r[k] = f(r[k])
    ok = [r for r in rows if not r["缺成本"]]
    t = hz["三层"]

    # 近 6 个月退货率（按达人 ID），订单表有才算
    th6 = collections.defaultdict(lambda: [0, 0]); ming = {}
    for p in sorted((dp / "账单").glob("订单表-*.csv")):
        for o in 底账.du_biao(p)[2]:
            did = o["达人ID"] if o["流量来源"] == "精选联盟" and o["达人ID"] not in ("", "-") else "自销"
            if o["发货时间"] and o["是否属于寄样订单"] != "是":
                th6[did][0] += 1; th6[did][1] += o["售后状态"].endswith("退款成功")
            if did != "自销" and o["达人昵称"] not in ("", "-"):
                ming[did] = o["达人昵称"]

    def zu(key):
        g = collections.defaultdict(lambda: collections.defaultdict(float))
        for r in ok:
            x = g[key(r)]
            x["单"] += 1; x["收入"] += r["收入"]; x["到手"] += r["到手"]; x["退货运费"] += r["退货运费"]; x["净"] += r["单前净利"]
        return g
    mingzi = collections.defaultdict(collections.Counter)
    for r in ok:
        mingzi[r["商品ID"]][r["商品"]] += 1
    kuan = zu(lambda r: r["商品ID"] or "（款不明）")  # 按商品 ID 分组：同一款可能有几个标题（改过名、渠道品）
    kname = lambda sid: (mingzi[sid].most_common(1)[0][0] if mingzi.get(sid) else sid) or "（款不明）"
    dr = zu(lambda r: (r["达人ID"] or "") if r["卖法"] == "达人" else "自销")
    zx = dr.pop("自销", collections.defaultdict(float))
    def name(did):
        n = ming.get(did) or next((r["达人"] for r in ok if r["达人ID"] == did and r["达人"] not in ("", "-")), "")
        return n or (f"达人 ID 尾号 {did[-4:]}" if did.strip("0") else "（达人不明：账单里没写是谁）")
    dr_sr = sum(v["收入"] for v in dr.values())
    jz = sorted((v[1] / v[0], k) for k, v in th6.items() if k != "自销" and v[0] >= 300)
    top = min(kuan.items(), key=lambda i: i[1]["退货运费"]) if kuan else ("", {"退货运费": 0})

    san = [f"这期到手 {yuan(t['到手'])} 元，扣掉退货运费、补偿、寄样和税，净利约 {yuan(t['净利'])} 元。"]
    if t["退货运费"] < 0 and t["到手"] > 0:
        san.append(f"退货运费被平台扣了 {yuan(-t['退货运费'])} 元，占到手的 {bai(-t['退货运费'], t['到手'])}" +
                   (f"，其中「{kname(top[0])[:14]}」一款 {yuan(-top[1]['退货运费'])} 元。" if top[1]["退货运费"] < 0 else "。"))
    if t["收入"]:
        san.append(f"达人单占收入的 {bai(dr_sr, t['收入'])}" + (f"；近 6 个月发货 300 单以上的达人，退货率在 {jz[0][0]:.0%}～{jz[-1][0]:.0%} 之间。" if len(jz) > 1 else "。"))

    zhang = [["收入", m(t["收入"]), "结算账单「收入合计」"], ["− 货品成本", m(t["成本"]), "成本表" + ("（模拟）" if "成本" in a.模拟 else "")],
             ["<b>= 毛利</b>", f"<b>{m(t['毛利'])}</b>", ""], ["− 平台服务费", m(t["平台服务费"]), "结算账单"],
             ["− 达人佣金和分成", m(t["佣金分成"]), "结算账单"],
             ["− 发货运费", m(t["发货运费"]), f"快递单价 {hz['快递单价']} 元 × 包裹数" + ("（模拟）" if "快递" in a.模拟 else "")],
             ["<b>= 到手利润</b>", f"<b>{m(t['到手'])}</b>", ""], ["− 退货运费（平台扣）", m(t["退货运费"]), "资金账单：上门取件、消费者赔付"],
             ["− 客服补的运费", m(t["运费补偿"]), "资金账单：小额打款（运费补偿）"], ["− 客服补偿", m(t["客服补偿"]), "资金账单：小额打款（补差价等）"],
             ["− 偏远地区费等", m(t["店铺层面"]), "资金账单"], ["− 达人寄样开支", m(t["达人寄样开支"]), "订单表寄样单：成本＋运费"],
             ["− 增值税＋附加", m(t["增值税"] + t["附加"]), hz["税"]["说明"]], ["<b>= 净利</b>", f"<b>{m(t['净利'])}</b>", "企业所得税按年另算"]]
    def tuilv(k):
        n, t_ = th6.get(k, [0, 0])
        return "—" if not n else f"{t_ / n:.0%}（{n} 单{'，样本少' if n < 30 else ''}）"
    k_body = [[E(kname(k)[:20]), int(v["单"]), m(v["收入"]), m(v["到手"]), m(v["退货运费"]), m(v["净"])] for k, v in sorted(kuan.items(), key=lambda i: -i[1]["收入"])[:8]]
    d_body = [[E(name(k)[:16]), int(v["单"]), m(v["收入"]), m(v["到手"]), m(v["退货运费"]), m(v["净"]), tuilv(k)]
              for k, v in sorted(dr.items(), key=lambda i: -i[1]["收入"])[:8]]
    if zx:
        d_body.append(["（店铺自销）", int(zx["单"]), m(zx["收入"]), m(zx["到手"]), m(zx["退货运费"]), m(zx["净"]), tuilv("自销")])
    zhu = [f"缺成本、没进合计：<b>{len(hz['缺成本'])}</b> 款" + ("（" + "；".join(E(x["商品"][:14]) for x in hz["缺成本"]) + f"，收入 {yuan(hz['缺成本收入'])} 元）请补成本" if hz["缺成本"] else ""),
           f"可能重复赔付（平台已扣运费、客服又补运费）：<b>{len(hz['重复赔付'])}</b> 单" + ("：" + "、".join(x[-8:] for x in hz["重复赔付"][:5]) + "，可以去「赔付管理」申诉" if hz["重复赔付"] else ""),
           f"本期寄样单：<b>{len(hz['寄样'])}</b> 单（不算销售，记达人寄样开支）",
           f"还没结算的单（只进预估）：<b>{hz['预估']['单数']}</b> 单，商家收入约 {yuan(hz['预估']['商家收入金额'])} 元",
           "用了默认值：" + ("、".join(hz["用了默认值"]) + "（主人没定，先按服装店默认值）" if hz["用了默认值"] else "无"),
           "退货率按付款月份看才准：这期退回来的多是前几周发出去的单。"]
    zhu += [f"<b>数据缺口</b>：{E(x)}" for x in hz.get("数据缺口", [])]
    dz_ = hz.get("对账", {})
    zhu += [f"<b>对账提醒</b>：{E(x)}" for x in dz_.get("提醒", []) if not any(k in x for k in ("缺成本", "重复赔付", "用了默认值", "夹带", "资金账单只盖"))]
    if dz_.get("抽单"):
        zhu.append(f"<b>后台抽单</b>：请在后台「资金 → 账单管理 → 结算账单 → 结算明细」按子订单号查这 {len(dz_['抽单'])} 单，看结算金额对不对：" + "、".join(dz_["抽单"]) + f"（结果：{E(dz_.get('抽单结果', '待回'))}）")
    elif not dz_:
        zhu.append("<b>还没对账</b>：这份报告没过 abacus-check，不能当定稿")
    zhu += [f"<b>同一编号两张生效的决策卡</b>（数可能用错了）：{E(x)}" for x in hz.get("参数冲突", [])]
    zhu += [f"<b>账单里夹带了像写给 AI 的话，没照做</b>：{E(x['表'])}第 {x['行']} 行「{E(x['原话'])}」" for x in hz.get("夹带的话", [])]
    pick = [r for r in rows if r["类型"] == "已结算"][:12] + [r for r in rows if "退款" in r["类型"]][:6] + [r for r in rows if r["类型"] == "结算前退货"][:12]
    mx = [[E(r["子订单号"][-8:]), r["卖法"], E((r["达人"] or "-")[:10]), E(r["商品"][:12]), E(r["类型"]), m(r["收入"]), m(r["成本"]),
           m(r["平台服务费"] + r["佣金分成"]), m(r["发货运费"]), m(r["退货运费"] + r["运费补偿"] + r["客服补偿"]), m(r["单前净利"])] for r in pick]
    mo = "、".join(x for x in a.模拟.split(",") if x)
    page = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>算盘账本</title><style>
:root{{--bg:#fbfaf7;--card:#fff;--fg:#1f1e1c;--mut:#6b6a66;--line:#e6e3dc;--accbg:#fbf3e4;--neg:#a32d2d}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#1b1a18;--card:#242320;--fg:#ecebe6;--mut:#a9a79f;--line:#3a3833;--accbg:#2e2618;--neg:#f09595}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.7 -apple-system,"PingFang SC","Helvetica Neue",sans-serif}}
main{{max-width:900px;margin:0 auto;padding:24px 16px 56px}}h1{{font-size:22px;font-weight:600;margin:0}}h2{{font-size:17px;font-weight:600;margin:30px 0 10px}}
.sub{{color:var(--mut);font-size:13px;margin:4px 0 18px}}.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px}}
.san{{background:var(--accbg);border-color:transparent}}.san ol{{margin:0;padding-left:20px}}.san li{{margin:4px 0}}
.kpi{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:14px 0 0}}.kpi div{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px}}
.kpi b{{display:block;font-size:22px;font-variant-numeric:tabular-nums}}.kpi span{{color:var(--mut);font-size:12px}}
.tw{{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--card)}}table{{border-collapse:collapse;width:100%;font-size:14px}}
th,td{{padding:7px 10px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}}th{{color:var(--mut);font-weight:500;font-size:12px}}
tr:last-child td{{border-bottom:none}}.n{{text-align:right;font-variant-numeric:tabular-nums}}.neg{{color:var(--neg)}}ul.zhu{{margin:0;padding-left:20px}}.foot{{color:var(--mut);font-size:12px;margin-top:28px}}
</style></head><body><main>
<h1>{E(hz["店铺"])} · 账本</h1><div class="sub">{a.起} ～ {a.止} · 算盘{(" · " + E(mo) + "为模拟值") if mo else ""} · 每个数都能在逐单明细里追到子订单</div>
<div class="card san"><ol>{"".join(f"<li>{E(x)}</li>" for x in san)}</ol></div>
<div class="kpi"><div><span>收入</span><b>{yuan(t["收入"])}</b></div><div><span>到手利润</span><b>{yuan(t["到手"])}</b></div><div><span>退货运费</span><b class="neg">{m(t["退货运费"])}</b></div><div><span>净利</span><b>{yuan(t["净利"])}</b></div></div>
<h2>一、三层账</h2>{tb(["项", "金额（元）", "从哪来"], zhang, 1, 2)}
<h2>二、自销和达人</h2>{tb(["卖法", "单数", "收入", "到手", "退货运费", "单前净利"], [["达人", int(sum(v["单"] for v in dr.values())), m(dr_sr), m(sum(v["到手"] for v in dr.values())), m(sum(v["退货运费"] for v in dr.values())), m(sum(v["净"] for v in dr.values()))], ["店铺自销", int(zx.get("单", 0)), m(zx.get("收入", 0)), m(zx.get("到手", 0)), m(zx.get("退货运费", 0)), m(zx.get("净", 0))]])}
<h2>三、按款（收入前八）</h2>{tb(["款", "单数", "收入", "到手", "退货运费", "单前净利"], k_body)}
<h2>四、按达人（收入前八）</h2>{tb(["达人", "单数", "收入", "到手", "退货运费", "单前净利", "近 6 个月退货率"], d_body)}
<h2>五、要注意的</h2><div class="card"><ul class="zhu">{"".join(f"<li>{x}</li>" for x in zhu)}</ul></div>
<h2>六、逐单明细（每种情况挑几行；全部 {len(rows)} 行见「逐单账.csv」，Excel 能直接打开）</h2>{tb(["子订单", "卖法", "达人", "款", "类型", "收入", "成本", "服务费＋佣金", "发货运费", "退货运费＋补偿", "单前净利"], mx, 5)}
<div class="foot">单前净利＝到手利润＋这一单的退货运费和客服补的钱，不含店铺层面的费用、寄样和税。参数出处：{E("；".join(f"{k}←{v}" for k, v in hz["参数来源"].items()))}</div>
</main></body></html>'''
    (out / "报告.html").write_text(page, encoding="utf-8")
    print("报告已出：", out / "报告.html")

if __name__ == "__main__":
    main()
