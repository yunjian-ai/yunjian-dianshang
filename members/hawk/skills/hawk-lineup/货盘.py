"""货郎 · 货盘：在售款（上架日期、近 30 天销量）→ 每款状态建议和提醒
用法：python3 货盘.py <在售款.csv> [--今天 2026-11-10] [--店铺 <店铺文件夹>] [--宽]（默认窄表，要注意的放表下）
在售款列：商品、价格、上架日期，再加「总销量」（抖店商品管理的列，平台自动下架看的就是历史无销量）或「近30天销量」
规则：上架 ≥ 新品没动销提醒天数（默认 25）还没卖出一件 → 提醒「再过约 N 天可能被平台自动下架」（R-SP-005，30 天无编辑无曝光、历史无销量）；
上架 7 天内＝新品，看成交件数、推广达人数、退货率；状态改动（新品→主推→清仓／下架）由主人点，写进经营决策库 D-HP 卡。"""
import argparse, csv, datetime as dt, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "hawk-base")); import 底子, 回执


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("在售款"); a.add_argument("--今天"); a.add_argument("--店铺"); a.add_argument("--宽", action="store_true")
    a = a.parse_args(argv)
    cs, _ = 底子.canshu(a.店铺)
    jin = dt.date.fromisoformat(a.今天) if a.今天 else dt.date.today()
    print(f"货盘（{jin}，出处：抖店·商品管理·在售款 {pathlib.Path(a.在售款).name}）\n")
    hang = []
    for r in csv.DictReader(open(a.在售款, encoding="utf-8-sig")):
        sj = dt.date.fromisoformat(r["上架日期"]); d = (jin - sj).days
        zong = "总销量" in r
        x = int(float((r.get("总销量") if zong else r.get("近30天销量")) or 0))
        kou = "总销量" if zong else "近 30 天"
        zt, ti = ("新品", "看成交件数、推广达人数、退货率") if d <= 7 else ("在售", "—")
        if x == 0:   # 平台规则：上架 30 天无销量无编辑无曝光会自动下架；直接给日期（Bot 实测自报 9）
            xia = sj + dt.timedelta(days=cs["平台自动下架天数"]); sheng = max((xia - jin).days, 0)
            if d >= cs["新品没动销提醒天数"]:
                zt, ti = "⚠️ 0 销量", f"再过约 {sheng} 天（约 {xia:%m-%d}）可能被平台自动下架（R-SP-005）→ 请您定：转主推、改链接还是放弃"
            else:
                ti = f"还没卖出；约 {xia:%m-%d} 前没销量可能被自动下架，第 {cs['新品没动销提醒天数']} 天提醒您"
        hang.append([r["商品"], r["价格"], str(sj), d, f"{x}（{kou}）", zt, ti])
    try:
        回执.ji(底子.dianpu(a.店铺), "hawk", zuole={"看货盘": 1}, shu={"在售款": len(hang), "快下架": [h[0] for h in hang if "下架" in h[6]]}, chuchu="货郎·货盘（在售款表）")
    except SystemExit:
        pass
    if a.宽:
        print(底子.biao(["商品", "价格", "上架日期", "上架天数", "销量（口径）", "状态", "要注意的"], hang, kuan=True))
    else:
        print(底子.biao(["商品", "上架天数", "销量", "状态", "要注意的"], [[h[0], h[3], h[4], h[5], h[6]] for h in hang], zhu=4, jian=0))

if __name__ == "__main__":
    main()
