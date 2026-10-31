"""掌柜 · 出报：所有店（或指定的店）某时段的报——第一行一句结论、多店总表、每家店一段、员工今天干了什么、要您管的、出处编号。
用法：python3 出报.py --时段 半天|全天|现在 [--今天 2026-11-10] [--店铺 抖店-A …] [--时刻 1150] [--宽] [--卡片 <飞书卡片.json>] [--文字 <报.md>] [--演练]
默认窄表（≤5 列、出处编号列在下面），给聊天框和手机；--宽 一张宽表给电脑。--卡片 另存一份飞书卡片（推送.py 发）。数从 keep-base/汇总.py 拿。"""
import argparse, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "keep-base")); import 底子, 汇总

MING = {"半天": "11:50 半天报", "全天": "23:50 全天报", "现在": "看看店"}


def jian(dian):
    return dian.replace("抖店-", "").replace("微信小店-", "微信·")


def zhi(s, k):
    return (s["实时"].get(k) or {}).get("值")


def chu_bao(snaps, shiduan, kuan=False):
    """返回 (标题, 结论, 段落列表[(小标题, markdown)], 出处列表)。"""
    chu, bh = [], {}

    def ref(t):
        if t not in bh:
            bh[t] = 底子.QUAN[len(bh)] if len(bh) < len(底子.QUAN) else f"({len(bh) + 1})"
            chu.append(f"{bh[t]} {t}")
        return bh[t]

    ok = [s for s in snaps if s["实时"]]
    zong = sum(zhi(s, "成交金额") or 0 for s in ok)
    zr = sum((s["实时"].get("成交金额") or {}).get("昨日") or 0 for s in ok)
    lr = [s["预估利润"] for s in ok if s["预估利润"] is not None]
    yao = sum(1 for s in snaps for y in s["要管"])
    jishi = [f"{jian(s['店铺'])} {y['事']}" for s in snaps for y in s["要管"] if y["级"] == "即时"]
    qian = {"半天": "上午", "全天": "今天", "现在": "到现在"}[shiduan]
    jl = f"{qian} {len(ok)} 家店成交 {底子.yuan(zong)} 元" + (f"，比昨天 {底子.bili(zong / zr - 1)}" if zr else "")
    if shiduan != "半天" and lr:
        jl += f"，预估净赚 {底子.yuan(sum(lr))} 元"
    if jishi:
        jl += "；" + "、".join(jishi)
    jl += f"；{yao} 件事要您看。" if yao else "；没有要您管的事。"
    if len(ok) < len(snaps):
        jl += f"（{len(snaps) - len(ok)} 家没取到）"
    duan = []
    # 多店总表
    if len(snaps) > 1 or shiduan == "全天":
        if shiduan == "半天":
            tou = ["店", "上午成交", "比昨天", "店铺分", "要管"]
            hang = [[jian(s["店铺"]), 底子.yuan(zhi(s, "成交金额")), 底子.bili((s["实时"].get("成交金额") or {}).get("较昨日")),
                     fen(s), str(len(s["要管"]))] for s in snaps]
        else:
            tou = ["店", "成交", "预估利润", "退款", "店铺分"]
            hang = [[jian(s["店铺"]), 底子.yuan(zhi(s, "成交金额")), 底子.yuan(s["预估利润"]),
                     (底子.yuan(zhi(s, "退款金额_支付时间")) + (f"／{zhi(s, '退款订单数_支付时间'):.0f}单" if zhi(s, "退款订单数_支付时间") is not None else "")) if s["实时"] else "—",
                     fen(s)] for s in snaps]
        r = ref(f"业绩：{next((s['出处'].get('实时') for s in ok), '后台')}·{next((s['记录时间'] for s in ok), '')}")
        duan.append((f"多店总表 {r}", 底子.biao(tou, hang, kuan=True)))
    # 每家店一段
    for s in snaps:
        t = []
        if not s["实时"]:
            t.append("没取到：" + "；".join(s["没取到"]))
        else:
            if len(snaps) == 1 and shiduan == "半天":
                t.append(f"成交 {底子.yuan(zhi(s, '成交金额'))} 元（比昨天 {底子.bili((s['实时'].get('成交金额') or {}).get('较昨日'))}）、"
                         f"{zhi(s, '成交订单数') or 0:.0f} 单；店铺分 {fen(s)}")
            if shiduan != "半天" or len(snaps) == 1:
                tk = zhi(s, "退款金额_支付时间")
                tl = zhi(s, "退款率_支付时间")
                if tk is not None:
                    t.append(f"退款 {底子.yuan(tk)} 元" + (f"、退款率 {tl:.0%}" if tl is not None and s.get("报退款率", 1) else "") + "（支付时间口径）")
            if s["达人占比"] is not None:
                lm = s["联盟"]
                t.append(f"达人带货 {底子.yuan(zhi(s, '达人成交金额'))} 元，占 {s['达人占比']:.0%}"
                         + (f"；近 7 天合作达人 {lm['近7日合作达人数']:.0f} 位" if lm.get("近7日合作达人数") else ""))
            b = (s["回执"].get("brok") or {}).get("数") or {}
            if b.get("分层"):
                t.append("达人分层：" + "、".join(f"{k} {v}" for k, v in b["分层"].items()))
            jb = (s["回执"].get("brok") or {}).get("做了") or {}
            if jb:
                t.append("经纪今天：" + "、".join(f"{k} {v:g}" for k, v in jb.items()))
            if shiduan == "全天" and s["预估利润"] is not None:
                t.append(f"预估利润 {底子.yuan(s['预估利润'])} 元 {ref('预估利润：' + s['利润说明'])}")
            elif shiduan != "半天" and s["预估利润"] is None and s["利润说明"]:   # 表里只有「—」，写明为什么空（Bot 实测 S2）
                t.append(f"预估利润没算：{s['利润说明']}")
        if s["商品榜"] and shiduan != "半天":
            r = ref(f"排行：{s['出处'].get('商品榜', '后台')}·{s['店铺']}·{s['记录时间']}")
            t.append(f"销售排行 {r}\n" + 底子.biao(["款", "单", "成交", "退款"],
                     [[x["短名"], f"{x['成交订单数']:.0f}", 底子.yuan(x["成交金额"]), 底子.yuan(x["退款金额"])] for x in s["商品榜"]], kuan=True))
        ty = s["体验分"]
        if ty["总分"] is not None and (shiduan != "半天" or len(snaps) == 1):
            r = ref(f"店铺分：抖店商家体验分页·{s['店铺']}·更新 {ty['更新时间']}")
            fx = "、".join(f"{k} {v:g}" + ((f"↓{abs(ty['分项变化'][k]):g}" if ty["分项变化"][k] < 0 else f"↑{ty['分项变化'][k]:g}") if ty["分项变化"].get(k) else "")
                          for k, v in ty["分项"].items() if k in ("商品", "物流", "服务"))
            t.append(f"店铺分 {fen(s)}（{fx}）{r}" + (f"；{ty['保障']}" if ty.get("保障") else "") + ("" if ty.get("今日已更新") else "；今天的分还没出（约 22 点更新）"))
        if s["要管"]:
            t.append("**要您管的**\n" + "\n".join(f"- {y['事']} {ref(s['店铺'] + '·' + y['出处'])}" for y in s["要管"][:8]))
        if shiduan == "全天":
            t.append("**员工今天**\n" + 底子.biao(["员工", "做了", "出了", "卡在／等您定"], s["员工"], kuan=kuan, zhu=None if kuan else 3, jian=0))
        if s["没取到"] and s["实时"]:
            t.append("没取到：" + "；".join(s["没取到"]))
        duan.append((jian(s["店铺"]) if len(snaps) > 1 else "店况", "\n".join(t)))
    return MING[shiduan], jl, duan, chu


def fen(s):
    ty = s["体验分"]
    if ty["总分"] is None:
        return "—"
    b = ty["变化"]
    return f"{ty['总分']:g}" + ("" if not b else (f" ↓{abs(b):g}" if b < 0 else f" ↑{b:g}"))


def md(biaoti, jl, duan, chu, ri):
    out = [f"**掌柜 · {biaoti} · {ri}**", "", f"**{jl}**"]
    for t, b in duan:
        out += ["", f"**{t}**", b]
    out += ["", "出处：", *chu]
    return 底子.daima("\n".join(out))


def kapian(biaoti, jl, duan, chu, ri):
    el = [{"tag": "markdown", "content": f"**{jl}**"}]
    for t, b in duan:
        el.append({"tag": "markdown", "content": f"**{t}**\n{b}"})
    el.append({"tag": "markdown", "content": "<font color='grey'>出处：" + "　".join(chu) + "</font>"})
    k = {"schema": "2.0", "config": {"wide_screen_mode": True},
         "header": {"title": {"tag": "plain_text", "content": f"掌柜 · {biaoti} · {ri}"}, "template": "orange"},
         "body": {"elements": el}}
    return json.loads(底子.daima(json.dumps(k, ensure_ascii=False)))


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--时段", default="现在", choices=list(MING)); a.add_argument("--今天"); a.add_argument("--店铺", nargs="*")
    a.add_argument("--时刻"); a.add_argument("--宽", action="store_true"); a.add_argument("--卡片"); a.add_argument("--文字"); a.add_argument("--演练", action="store_true")
    a = a.parse_args(argv)
    day = a.今天 or str(底子.jintian())
    dps = [底子.dianpu(x) for x in a.店铺] if a.店铺 else 底子.dianpus()
    if not dps:
        raise SystemExit("还没有店铺文件夹：先照 keep-getting-started 建（或跑 keep-base/统一店铺.py 把另外三位的店并进来）")
    snaps = [汇总.kuaizhao(dp, day, a.时段, a.时刻, xie=not a.演练) for dp in dps]
    bt, jl, duan, chu = chu_bao(snaps, a.时段, a.宽)
    t = md(bt, jl, duan, chu, day[5:])
    print(t)
    if a.文字:
        pathlib.Path(a.文字).write_text(t, encoding="utf-8")
    if a.卡片:
        pathlib.Path(a.卡片).write_text(json.dumps(kapian(bt, jl, duan, chu, day[5:]), ensure_ascii=False, indent=1), encoding="utf-8")
    if not a.演练:
        汇总_huizhi(dps, day, a.时段, len(snaps))


def 汇总_huizhi(dps, day, shiduan, n):
    import importlib.util
    spec = importlib.util.spec_from_file_location("回执", pathlib.Path(__file__).resolve().parent.parent / "keep-base" / "回执.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    for dp in dps:
        m.ji(dp, "keep", zuole={f"出{shiduan}报": 1}, chuchu="掌柜·出报", jintian=day)


if __name__ == "__main__":
    main()
