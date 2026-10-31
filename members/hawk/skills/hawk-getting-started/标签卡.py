"""货郎 · 标签卡草稿：罗盘成交人群画像「下载结果」＋在售款 → 店铺标签卡草稿（状态「待确认」，主人确认了才算数）
用法：python3 标签卡.py --人群 <罗盘下载的成交人群画像.xlsx 或 .csv> [--在售款 <在售款.csv>] [--店铺 <店铺文件夹>] [--演练]
人群表：罗盘「下载结果」原样的 xlsx（分段：8大人群分布／性别分布／年龄分布……，每段第一行是表头，Z 世代写作 genz；2026-10-31 实测）；
  也认 csv（列：维度、分组、占比）。在售款列：商品、价格
主人群＝占比最高的 2 个、主年龄＝占比最高的 2 档（和达人标签一样最多两个，多了不准；杨先生 10-31）；排第 3 的人群和年龄＝扩标签（往外扩时用），其余是次人群；价格段＝在售款最低到最高。"""
import argparse, csv, pathlib, re, sys, zipfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "hawk-base")); import 底子

PINLEI = ["卫衣", "卫裤", "打底衫", "T恤", "针织衫", "毛衣", "开衫", "衬衫", "羽绒服", "棉服", "外套", "大衣", "风衣", "连衣裙", "半身裙", "裤", "马甲", "套装"]
BIEMING = {"genz": "Z世代", "Z世代": "Z世代", "z世代": "Z世代"}


def du_xlsx(p):
    """罗盘下载的 xlsx → [{维度, 分组, 占比}]。只用标准库：读 sharedStrings 和第一张表。"""
    z = zipfile.ZipFile(p)
    ss = [re.sub(r"<[^>]+>", "", x) for x in re.findall(r"<si>(.*?)</si>", z.read("xl/sharedStrings.xml").decode(), re.S)]
    rows = []
    for r in re.findall(r"<row[^>]*>(.*?)</row>", z.read("xl/worksheets/sheet1.xml").decode(), re.S):
        cells = []
        for at, body in re.findall(r"<c ([^>]*?)(?:/>|>(.*?)</c>)", r, re.S):
            v = re.search(r"<v>([^<]*)</v>", body or "")
            if not v:
                continue
            t = re.search(r't="(\w+)"', at)
            cells.append(ss[int(v.group(1))] if t and t.group(1) == "s" else v.group(1))
        rows.append(cells)
    out, wd = [], ""
    for c in rows:
        if len(c) >= 2 and not re.fullmatch(r"[\d.]+", c[1] or ""):
            wd = "八大策略人群" if "8大人群" in c[0] or "八大" in c[0] else ("年龄" if "年龄" in c[0] else c[0]); continue
        if len(c) >= 2 and wd:
            out.append({"维度": wd, "分组": BIEMING.get(c[0], c[0]).replace("岁", "").replace("以上", "+"), "占比": c[1]})
    return out


BA = ["新锐白领", "资深中产", "精致妈妈", "小镇青年", "Z世代", "都市银发", "小镇中老年", "都市蓝领"]


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--人群", required=True); a.add_argument("--在售款"); a.add_argument("--店铺"); a.add_argument("--演练", action="store_true")
    a = a.parse_args(argv)
    rows = du_xlsx(a.人群) if a.人群.endswith(".xlsx") else list(csv.DictReader(open(a.人群, encoding="utf-8-sig")))
    for r in rows:
        r["分组"] = BIEMING.get(r["分组"], r["分组"])
    ren = sorted([(r["分组"], float(r["占比"])) for r in rows if r["维度"].startswith("八大")], key=lambda x: -x[1])
    bad = [n for n, _ in ren if n not in BA]
    zhu, kuo = ren[:2], ren[2:3]   # 主人群最多 2 个，第 3 个是扩标签（杨先生 10-31：和达人标签一样，多了不准）
    nian = [(r["分组"], float(r["占比"])) for r in rows if r["维度"] == "年龄"]
    pai = sorted(nian, key=lambda x: -x[1])
    zhu_nl = sorted(pai[:2], key=nian.index); kuo_nl = pai[2:3]
    fmt = lambda xs, h="": "、".join(f"{n}{h} {v:.0%}" for n, v in xs) or "无"
    jg, dw, pl = "", "待主人说", ""
    if a.在售款:
        zs = list(csv.DictReader(open(a.在售款, encoding="utf-8-sig")))
        ps = sorted(float(r["价格"]) for r in zs if r.get("价格"))
        jg = f"{ps[0]:g}-{ps[-1]:g}" if ps else ""
        shu = {}
        for r in zs:
            k = next((p for p in PINLEI if p in r["商品"]), "其他")
            shu[k] = shu.get(k, 0) + 1
        zhu_pl, n = max(shu.items(), key=lambda x: x[1]) if shu else ("", 0)
        if zhu_pl != "其他" and n == len(zs):
            pl = zhu_pl; dw = f"单品店（在售 {len(zs)} 款都是{pl}，请主人确认）"
        elif zhu_pl != "其他" and n * 2 > len(zs):   # 过半是一类：单品店带几款搭配（2026-10-31 真店实测：卫衣 9／13，另有卫裤、打底衫）
            pl = zhu_pl
            pei = "、".join(f"{k} {v}" for k, v in shu.items() if k != zhu_pl)
            dw = f"像单品店，以{pl}为主（{n}/{len(zs)} 款），带搭配款（{pei}）；请主人确认"
        else:
            dw = "像多品店（在售款品类不一：" + "、".join(f"{k} {v}" for k, v in shu.items()) + "；请主人确认围绕哪个人群）"
    t = f"""# 店铺标签卡（草稿 · 待确认）
- 定位：{dw}
- 主攻品类：{pl or '待主人说'}
- 人群（罗盘成交人群画像）：{fmt(ren)}
- 主人群（最多 2 个）：{fmt(zhu)}
- 扩标签人群（排第 3，往外扩时用）：{fmt(kuo)}
- 主年龄段（最多 2 档）：{fmt(zhu_nl, '岁')}
- 扩标签年龄：{fmt(kuo_nl, '岁')}
- 价格段（在售款）：{jg or '待在售款'}
- 风格、货源、卖法、链接模板：待问
- 主人确认：未确认
"""
    if bad:
        t += f"- ⚠️ 这些分组名不是官方八大人群的叫法，核一下表：{'、'.join(bad)}\n"
    print(t)
    if not a.演练:
        dp = pathlib.Path(a.店铺) if a.店铺 else 底子.dianpu()
        dp.mkdir(parents=True, exist_ok=True)
        (dp / "店铺标签卡.md").write_text(t, encoding="utf-8")
        print(f"已写 {dp / '店铺标签卡.md'}（待确认）")


if __name__ == "__main__":
    main()
