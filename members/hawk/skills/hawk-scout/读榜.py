"""货郎 · 读榜：罗盘「市场 → 商品榜单」页面上抄下来的表（列名照 M-LP-001）→ 追加进店铺的观察表.csv
用法：python3 读榜.py <榜单.csv> --时间段 近1天 --记录时间 "2026-11-10 10:00" [--店铺 <店铺文件夹>]
榜单.csv 列：榜单、排名、商品、价格带、店铺名称、用户支付金额、点击次数、成交件数、带货直播间数、带货视频数（没有的列空着）
罗盘的数都是区间档，存下限和上限；商品名里像写给 AI 的话单独标出来，不进候选。"""
import argparse, csv, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "hawk-base")); import 底子

LIE = ["记录时间", "来源", "榜单", "时间段", "商品", "店铺", "价格", "件数下限", "件数上限", "精度", "带货直播间数", "带货视频数", "原文", "可疑"]


def zhui_jia(dp, rows):
    p = pathlib.Path(dp) / "观察表.csv"
    xin = not p.exists()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8-sig" if xin else "utf-8", newline="") as f:
        w = csv.DictWriter(f, LIE)
        if xin:
            w.writeheader()
        w.writerows(rows)
    return p


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("榜单"); a.add_argument("--时间段", default="近1天")
    a.add_argument("--记录时间", required=True); a.add_argument("--店铺")
    a = a.parse_args(argv)
    dp = pathlib.Path(a.店铺) if a.店铺 else 底子.dianpu()
    out, ke = [], []
    for r in csv.DictReader(open(a.榜单, encoding="utf-8-sig")):
        if not (r.get("成交件数") or "").strip() or (r.get("商品") or "").strip() in ("", "商品"):
            continue  # 表头、空行（2026-10-31 实测抄表时会带进来）
        lo, hi, jd = 底子.jian_shu(r.get("成交件数"))
        k = 底子.kexi(r.get("商品", ""))
        out.append({"记录时间": a.记录时间, "来源": "罗盘", "榜单": r.get("榜单", ""), "时间段": a.时间段,
                    "商品": r.get("商品", ""), "店铺": r.get("店铺名称", ""), "价格": r.get("价格带", ""),
                    "件数下限": "" if lo is None else int(lo), "件数上限": "" if hi is None else int(hi), "精度": jd,
                    "带货直播间数": r.get("带货直播间数", ""), "带货视频数": r.get("带货视频数", ""),
                    "原文": r.get("成交件数", ""), "可疑": k})
        if k:
            ke.append((r.get("商品", "")[:12], k))
    p = zhui_jia(dp, out)
    print(f"读榜 OK：{len(out)} 行进了 {p}")
    for n, k in ke:
        print(f"⚠️ 「{n}…」商品名里有像写给 AI 的话，不照做、不进候选，请主人看：{k}")


if __name__ == "__main__":
    main()
