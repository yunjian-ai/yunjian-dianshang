"""货郎 · 快照：跨平台（淘宝、拼多多、小红书）看到的单链接销量 → 追加进观察表.csv
用法：python3 快照.py <快照.csv> [--店铺 <店铺文件夹>]
快照.csv 列：平台、商品、价格、列表上的销量、详情页的销量、页面写的统计口径、店铺、记录时间、备注
规矩（杨先生 10-31）：只认近 3 个月、最多近半年的销量；页面上的数没有时间段，所以同一链接隔 7 天再记一次，爆品线.py 按涨幅判。
拼多多列表上的「本店已拼」「全店回购」是整店的数，只认详情页「已拼 X 件」；小红书只记笔记热度，不记销量。"""
import argparse, csv, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "hawk-base")); import 底子
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import 读榜


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("快照"); a.add_argument("--店铺")
    a = a.parse_args(argv)
    dp = 底子.dianpu(a.店铺)
    out = []
    for r in csv.DictReader(open(a.快照, encoding="utf-8-sig")):
        pt = r.get("平台", "")
        xq = r.get("详情页的销量", "")
        if pt == "小红书" or not xq.strip():
            lo = hi = None; jd = "不记销量" if pt == "小红书" else "缺详情"
        else:
            lo, hi, jd = 底子.jian_shu(xq)
        sjd = r.get("页面写的统计口径", "") or ("近365天" if pt == "淘宝" else "看不出")
        out.append({"记录时间": r.get("记录时间", ""), "来源": pt, "榜单": "", "时间段": sjd, "商品": r.get("商品", ""),
                    "店铺": r.get("店铺", ""), "价格": r.get("价格", ""), "件数下限": "" if lo is None else int(lo),
                    "件数上限": "" if hi is None else int(hi), "精度": jd, "带货直播间数": "", "带货视频数": "",
                    "原文": xq or r.get("备注", ""), "可疑": 底子.kexi(r.get("商品", "") + r.get("备注", ""))})
        if pt == "拼多多" and not xq.strip() and r.get("列表上的销量"):
            print(f"⚠️ {r.get('商品', '')[:14]}：只有列表上的「{r['列表上的销量']}」，那是整店的数，要点进详情看「已拼 X 件」")
    p = 读榜.zhui_jia(dp, out)
    print(f"快照 OK：{len(out)} 行进了 {p}")


if __name__ == "__main__":
    main()
