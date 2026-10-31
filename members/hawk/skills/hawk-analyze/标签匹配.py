"""货郎 · 店铺匹配：过了爆品线的候选 × 店铺标签卡 → 留哪些、哪些不匹配和为什么
用法：python3 标签匹配.py --品类 卫衣[,卫裤,打底衫] --价格段 59-89 [--女装|--男装] [--店铺 <店铺文件夹>] [--在售款 <在售款.csv>] [--今天 2026-11-10]
读：观察表.csv（商品名、价格）＋爆品线结论；只看「过线」「差一点」的。
脚本查能查的：品类词、价格段（上下各放 30%）、男女、店铺决策库的售价下限、和在售款撞不撞款（同款式词 ≥2 个且价差 ≤15%）；人群和风格由模型看图看名字判断，写理由。输出是带出处的表格。"""
import argparse, csv, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "hawk-base")); import 底子
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "hawk-scout")); import 爆品线


KUAN = {"半拉链", "立领", "连帽", "圆领", "毛毛领", "花苞袖", "撞色", "加绒", "重磅", "美式", "开衫", "刺绣", "摇粒绒", "无帽"}


def jia(s):
    m = re.findall(r"[\d.]+", s or "")
    return float(m[0]) if m else None


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--品类", required=True); a.add_argument("--价格段", required=True)
    a.add_argument("--男装", action="store_true"); a.add_argument("--女装", action="store_true")   # 女装是默认，写上也认（Bot 自报 3）
    a.add_argument("--店铺"); a.add_argument("--在售款"); a.add_argument("--今天"); a.add_argument("--宽", action="store_true")
    a = a.parse_args(argv)
    dp = 底子.dianpu(a.店铺)
    cs, _ = 底子.canshu(dp)
    jin = 爆品线.rq(a.今天) if a.今天 else 爆品线.dt.date.today()
    rows = list(csv.DictReader(open(dp / "观察表.csv", encoding="utf-8-sig")))
    cc = {}
    jl = 爆品线.pan(rows, cs, jin, cc)
    zs_p = pathlib.Path(a.在售款) if a.在售款 else dp / "在售款.csv"
    zs = list(csv.DictReader(open(zs_p, encoding="utf-8-sig"))) if zs_p.exists() else []
    lo, hi = [float(x) for x in a.价格段.split("-")]
    ming = {}
    for r in rows:
        ming.setdefault(爆品线.jian(r["商品"]), r)
    liu, bu = [], []
    for k, (j, ly_, _) in jl.items():
        if j not in ("过线", "差一点"):
            continue
        r = ming[k]; n = r["商品"]; p = jia(r["价格"]); why = []
        pl = [x for x in a.品类.replace("，", ",").split(",") if x]
        if not any(x in n for x in pl):
            why.append(f"不是{'／'.join(pl)}")
        if p is not None and not (lo * 0.7 <= p <= hi * 1.3):
            why.append(f"价格 {p:g} 不在 {a.价格段}（上下放 30%）")
        if (not a.男装) and re.search(r"男士|男款|男装|男生", n):
            why.append("男装")
        if p is not None and cs.get("售价下限", 0) and p < cs["售价下限"]:
            why.append(f"低于店铺定的售价下限 {cs['售价下限']:g} 元（经营决策库）")
        zhuang = [z["商品"] for z in zs if len(KUAN.intersection(re.findall("|".join(KUAN), z["商品"])) & set(re.findall("|".join(KUAN), n))) >= 2
                  and jia(z.get("价格")) and p and abs(jia(z["价格"]) - p) <= p * 0.15]
        if zhuang and not why:
            j = j + "；⚠️ 和在售「" + "、".join(zhuang) + "」可能撞款，请主人定是新开链接还是给老链接加颜色"
        if why and all(w.startswith("价格") for w in why) and ly_ in ("淘宝", "拼多多"):
            why.append("跨平台价格常比抖音低，款式可以参考")
        (bu if why else liu).append((k, j, n, "；".join(why)))
    print(f"店铺匹配（{a.品类}，{a.价格段}" + (f"，售价下限 {cs['售价下限']:g}" if cs.get("售价下限") else "") + "）\n")
    hang = []
    for k, j, n, w in [(k, j, n, "—") for k, j, n, _ in liu] + bu:
        c = cc.get(k, {})
        hang.append(["留" if w == "—" else "不匹配", k, j, n, c.get("价格", "—"), w, f"{c.get('平台', '—')}·{c.get('页面', '—')}·{c.get('店铺', '—')}·{c.get('记录时间', '—')}"])
    if a.宽:
        print(底子.biao(["结论", "款", "爆品线", "商品", "价格", "理由", "出处（平台·页面·店铺·记录时间）"], hang, kuan=True))
    else:
        print(底子.biao(["结论", "款", "爆品线", "价格", "理由", "出处"], [[h[0], h[1], h[2], h[4], h[5], h[6]] for h in hang], chu=5, zhu=4, jian=1))
    print("\n人群、风格对不对得上，由我看图看名字再写理由；拍板做哪款由主人定。")

if __name__ == "__main__":
    main()
