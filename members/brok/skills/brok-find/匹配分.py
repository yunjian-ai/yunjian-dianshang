"""经纪 · 匹配分：达人（达人广场导出或抄下的表）× 店铺标签卡 → 精准／外扩／不匹配／排除、匹配分、命中哪几条、出处
用法：python3 匹配分.py --标签卡 <店铺标签卡.json> --达人 <达人广场.csv> [--渠道 直播|视频] [--宽] [--json]
两边写法不一样要换算（实地摸清 10-31）：达人广场年龄档 18-23/24-30/31-40/41-50/50+ 对罗盘 18-24/25-30/31-35…，
按「重叠年数 ÷ 达人那一档年数 ≥ 0.5」算命中；人群名「00后」＝罗盘「Z世代」。
分：类目 30、年龄 主 25／扩 12、人群 主 25／扩 12、达人类型对上推荐渠道 20（另一种 10）。精准＝类目对＋年龄主＋人群主；外扩＝类目对、年龄和人群都在主或扩里、至少一样是扩；
图文、橱窗达人不算我们的渠道。达人名、数照抄，出处写「精选联盟·达人广场·店铺·记录时间」。"""
import argparse, csv, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brok-base")); import 底子

TONG = {"00后": "Z世代", "Z 世代": "Z世代", "z世代": "Z世代"}


def duan(s):
    """「18-23岁居多」「50岁+居多」「31-35」→ (起, 止)。"""
    s = (s or "").replace("岁", "").replace("居多", "").strip()
    m = re.match(r"(\d+)\s*\+", s)
    if m:
        return int(m.group(1)), int(m.group(1)) + 10
    m = re.match(r"(\d+)\s*-\s*(\d+)", s)
    return (int(m.group(1)), int(m.group(2))) if m else None


def zhong(a, bs):
    """达人那一档 a 和店铺的档 bs 有没有命中（重叠年数 ÷ a 的年数 ≥ 0.5）。"""
    if not a:
        return False
    n = a[1] - a[0] + 1
    for b in filter(None, bs):
        lap = min(a[1], b[1]) - max(a[0], b[0]) + 1
        if lap > 0 and lap / n >= 0.5:
            return True
    return False


def ping(r, k, qudao):
    leimu = k.get("主营类目", "服饰内衣")
    rq = TONG.get(r["八大消费人群"].strip(), r["八大消费人群"].strip())
    zhu_rq = [TONG.get(x, x) for x in k["主人群"]]; kuo_rq = [TONG.get(x, x) for x in k.get("扩标签人群", [])]
    nl = duan(r["粉丝年龄"])
    nl_zhu = zhong(nl, [duan(x) for x in k["主年龄段"]]); nl_kuo = zhong(nl, [duan(x) for x in k.get("扩标签年龄", [])])
    lei = leimu in re.split(r"[/／、,，\s]+", r["主推类目"].strip())   # 达人主推类目常是多个（「服饰内衣/美妆」），包含就算（实测 10-31）
    lx = r["达人类型"].replace("达人", "").strip()
    fen, ming = 0, []
    if lei:
        fen += 30; ming.append("类目")
    if nl_zhu:
        fen += 25; ming.append("年龄主")
    elif nl_kuo:
        fen += 12; ming.append("年龄扩")
    if rq in zhu_rq:
        fen += 25; ming.append("人群主")
    elif rq in kuo_rq:
        fen += 12; ming.append("人群扩")
    if lx == qudao:
        fen += 20; ming.append(f"{lx}对上推荐渠道")
    elif lx in ("直播", "视频"):
        fen += 10
    if not lei:
        jie, li = "排除", f"类目「{r['主推类目']}」不是{leimu}"
    elif lx not in ("直播", "视频"):
        jie, li = "不匹配", f"{r['达人类型']}，不是直播、短视频渠道"
    elif nl_zhu and rq in zhu_rq:
        jie, li = "精准", ""
    elif (nl_zhu or nl_kuo) and (rq in zhu_rq or rq in kuo_rq):
        jie, li = "外扩", "落在扩标签（" + "、".join(x for x in ming if "扩" in x) + "）"
    else:
        jie, li = "不匹配", f"粉丝 {r['粉丝年龄']}、{r['八大消费人群']} 和店铺主／扩标签对不上"
    return {"结论": jie, "分": fen, "命中": ming, "理由": li}


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--标签卡", required=True); a.add_argument("--达人", required=True)
    a.add_argument("--渠道", default="直播", choices=["直播", "视频"]); a.add_argument("--店铺", default="")
    a.add_argument("--宽", action="store_true"); a.add_argument("--json", action="store_true")
    a = a.parse_args(argv)
    k = json.loads(pathlib.Path(a.标签卡).read_text(encoding="utf-8"))
    dian = a.店铺 or k.get("店名", "")
    with open(a.达人, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    out = {}
    for r in rows:
        jia = 底子.kexi(" ".join(r.values()))
        p = ping(r, k, a.渠道)
        if jia:
            p["结论"], p["理由"] = "不判", f"资料里夹带给 AI 的话，不照做：「{jia}」"
        p.update(达人=r["达人"], 类型=r["达人类型"], 出处=f"精选联盟·达人广场·{dian}·{r.get('记录时间', '')}")
        out[r["达人编号"]] = p
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1)); return
    xu = {"精准": 0, "外扩": 1, "不匹配": 2, "排除": 3, "不判": 4}
    pai = sorted(out.items(), key=lambda x: (xu[x[1]["结论"]], -x[1]["分"]))
    n = {j: sum(1 for v in out.values() if v["结论"] == j) for j in xu}
    print(f"共 {len(out)} 位：精准 {n['精准']}、外扩 {n['外扩']}、不匹配 {n['不匹配']}、排除 {n['排除']}" + (f"、不判 {n['不判']}" if n["不判"] else "") + f"；推荐渠道 {a.渠道}，{a.渠道}达人排前。")
    hang = [[b, v["达人"], v["结论"], v["分"], "、".join(v["命中"]), v["理由"] or "—", v["出处"]] for b, v in pai]
    tou = ["编号", "达人", "结论", "分", "命中", "理由", "出处"]
    print(底子.biao(tou, hang, kuan=a.宽, chu=None if a.宽 else 6, zhu=None if a.宽 else 5, jian=0) if not a.宽 else 底子.biao(tou, hang, kuan=True))


if __name__ == "__main__":
    main()
