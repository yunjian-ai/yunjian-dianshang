"""货郎 · 爆品线：观察表.csv → 每条链接过没过线
用法：python3 爆品线.py [--店铺 <店铺文件夹>] [--今天 2026-11-10] [--json] [--宽]
默认出窄表（Grok Bot、手机聊天框：出处编号列在表下、理由放表下）；--宽 出一张宽表（电脑、飞书、网页）。
线从参数读（店铺经营决策库盖服装店默认值）：
  抖音（罗盘）：近 1 天成交件数档的下限 ≥ 抖音爆品线（默认 1000）过线；≥ 差一点线（默认 750）标「差一点」
  跨平台（淘宝、拼多多）：同一链接两次记录相隔 ≥7 天、件数涨 ≥ 跨平台爆品线（默认 1000）过线；
    总数都不到线 → 不过；只有一次、间隔不够、或两次都是同一个粗档（淘宝 4000+ 这种）→「待核」；记录超过 180 天的不用
  小红书：不判销量；商品名里像写给 AI 的话：不判、请主人看"""
import argparse, collections, csv, datetime as dt, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "hawk-base")); import 底子


def rq(s):
    return dt.datetime.strptime(s.strip()[:10], "%Y-%m-%d").date()


def jian(name):
    """同一链接的键：商品名前面的编号或整条名字。"""
    m = re.match(r"([A-Za-z]\d+)\b", name.strip())
    return m.group(1) if m else name.strip()


def pan(rows, cs, jin, cc=None):
    """判每条链接；cc 传一个 dict 进来会顺便填上出处（平台、页面、店铺、价格、件数原文、记录时间）。"""
    res = {}
    cc = {} if cc is None else cc
    zu = collections.defaultdict(list)
    for r in rows:
        zu[(r["来源"], jian(r["商品"]))].append(r)
    for (ly, k), rs in zu.items():
        rs = [r for r in rs if (jin - rq(r["记录时间"])).days <= cs["销量最长可用天数"]]
        if not rs:
            continue
        sj = sorted({r["记录时间"] for r in rs})
        cc[k] = {"平台": ly, "页面": "、".join(sorted({r["榜单"] for r in rs if r["榜单"]})) or "—", "店铺": rs[-1]["店铺"] or "—",
                 "价格": rs[-1]["价格"] or "—", "件数原文": " → ".join(r["原文"] for r in sorted(rs, key=lambda r: r["记录时间"]) if r["原文"]) or "—",
                 "记录时间": sj[0] if len(sj) == 1 else f"{sj[0]} → {sj[-1]}"}
        if sj[-1][:10] > str(jin):   # 记录时间晚于今天（Bot 实测 10-31：材料写的 11-03、11-10），先请主人核
            res[k] = ("待核", f"记录时间 {sj[-1]} 晚于今天 {jin}，请先核一下日期是不是抄错了", ly); continue
        if any(r["可疑"] for r in rs):
            res[k] = ("不判", "商品名里有像写给 AI 的话，请主人看：" + next(r["可疑"] for r in rs if r["可疑"]), ly); continue
        if ly == "罗盘":
            d = [r for r in rs if r["时间段"] == "近1天" and r["件数下限"] != ""]
            if not d:
                res[k] = ("待核", "没有近 1 天的件数", ly); continue
            best = max(d, key=lambda r: int(r["件数下限"]))
            lo = int(best["件数下限"])
            qudao = "；".join(f"{r['榜单']} {r['原文']}" + (f"，带货直播间 {r['带货直播间数']}" if r["带货直播间数"] else "")
                            + (f"，带货视频 {r['带货视频数']}" if r["带货视频数"] else "") for r in d)
            if lo >= cs["抖音爆品线_近1天件数下限"]:
                res[k] = ("过线", f"近 1 天 {best['原文']} 件（{qudao}）", ly)
            elif lo >= cs["抖音差一点_近1天件数下限"]:
                res[k] = ("差一点", f"近 1 天 {best['原文']} 件，没到 {cs['抖音爆品线_近1天件数下限']}", ly)
            else:
                res[k] = ("不过", f"近 1 天 {best['原文']} 件", ly)
            continue
        if ly == "小红书":
            res[k] = ("不判", "小红书只当种草热度参考，不判销量", ly); continue
        rs = sorted([r for r in rs if r["件数下限"] != ""], key=lambda r: r["记录时间"])
        if not rs:
            res[k] = ("待核", "没有详情页的单链接件数（列表上的是整店数）", ly); continue
        a, b = rs[0], rs[-1]
        gap = (rq(b["记录时间"]) - rq(a["记录时间"])).days
        if int(b["件数下限"]) < cs["跨平台爆品线_涨幅件数"]:
            res[k] = ("不过", f"总共才 {b['原文']}，近期不可能涨到 {cs['跨平台爆品线_涨幅件数']} 件", ly); continue
        if len(rs) < 2 or gap < cs["跨平台快照最少间隔天数"]:
            res[k] = ("待核", f"只有 {len(rs)} 次记录、间隔 {gap} 天，隔 {cs['跨平台快照最少间隔天数']} 天再看一次（页面上的数没有时间段，大数可能是几年累计的）", ly); continue
        if a["精度"] == "档" and b["精度"] == "档" and a["件数下限"] == b["件数下限"]:
            res[k] = ("待核", f"两次都是「{b['原文']}」同一个粗档（{b['时间段']}），看不出这 {gap} 天卖了多少；看评价日期或再隔一周", ly); continue
        zhang = int(b["件数下限"]) - int(a["件数下限"])
        tou = f"{gap} 天从 {a['原文']} 到 {b['原文']}，涨 {zhang} 件"
        if zhang >= cs["跨平台爆品线_涨幅件数"]:
            res[k] = ("过线", tou, ly)
        elif zhang <= 0:
            res[k] = ("不过", tou + "：没涨，大数是早年累计的，没有参考价值", ly)
        else:
            res[k] = ("不过", tou + f"：在卖，但不到 {cs['跨平台爆品线_涨幅件数']}", ly)
    return res


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--店铺"); a.add_argument("--今天"); a.add_argument("--json", action="store_true"); a.add_argument("--宽", action="store_true")
    a = a.parse_args(argv)
    dp = 底子.dianpu(a.店铺)
    cs, mr = 底子.canshu(dp)
    jin = rq(a.今天) if a.今天 else dt.date.today()
    rows = list(csv.DictReader(open(dp / "观察表.csv", encoding="utf-8-sig")))
    cc = {}
    res = pan(rows, cs, jin, cc)
    if a.json:
        print(json.dumps({k: {"结论": v[0], "理由": v[1], "来源": v[2], "出处": cc.get(k, {})} for k, v in res.items()}, ensure_ascii=False, indent=1)); return
    print(f"爆品线（{jin}）：抖音近 1 天 ≥{cs['抖音爆品线_近1天件数下限']} 件；跨平台隔 {cs['跨平台快照最少间隔天数']} 天涨 ≥{cs['跨平台爆品线_涨幅件数']} 件"
          + ("（按默认值）" if "抖音爆品线_近1天件数下限" in mr else "") + "\n")
    hang = []
    for jl in ["过线", "差一点", "待核", "不过", "不判"]:
        for k, v in res.items():
            if v[0] == jl:
                c = cc.get(k, {})
                hang.append([jl, k, v[2], c.get("页面", "—"), c.get("店铺", "—"), c.get("价格", "—"), c.get("件数原文", "—"), v[1], c.get("记录时间", "—")])
    if a.宽:
        print(底子.biao(["结论", "商品", "平台", "页面／榜单", "店铺", "价格", "件数（页面原文）", "依据", "记录时间"], hang, kuan=True))
    else:
        print(底子.biao(["结论", "款", "价格", "件数", "依据", "出处"],
                       [[h[0], h[1], h[5], h[6], h[7], f"{h[2]}·{h[3]}·{h[4]}·{h[8]}"] for h in hang], chu=5, zhu=4, jian=1))

if __name__ == "__main__":
    main()
