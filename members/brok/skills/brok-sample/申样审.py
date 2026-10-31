"""经纪 · 申样审：样品管理「待审核」→ 每单 过／提醒主人＋理由，按剩余审核时间排（快到 72 小时的标急）
用法：python3 申样审.py --申样 <样品待审.csv> --合作单 <合作单.json> --标签卡 <店铺标签卡.json> --达人 <达人广场.csv> [--今天 …] [--店铺 …]
规矩（杨先生 10-31）：核心、成长直接过；新达人匹配（精准或外扩）且履约率 ≥ 新达人申样_履约率下限（默认 50%）就过；其余提醒主人。
剩余 ≤12 小时标急。只出建议；点「通过」照经纪设置卡的授权（第一次请主人看着），开发期间不点（AGENTS 第 7 条）。"""
import argparse, csv, datetime as dt, json, pathlib, sys
P = pathlib.Path(__file__).resolve().parent.parent
for x in ("brok-base", "brok-roster", "brok-find"):
    sys.path.insert(0, str(P / x))
import 底子, 分层, 匹配分


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--申样", required=True); a.add_argument("--合作单", required=True)
    a.add_argument("--标签卡", required=True); a.add_argument("--达人", required=True); a.add_argument("--今天"); a.add_argument("--店铺")
    a.add_argument("--json", action="store_true")
    a = a.parse_args(argv)
    cs, _ = 底子.canshu(a.店铺)
    jin = dt.date.fromisoformat(a.今天) if a.今天 else 底子.jintian()
    fc = 分层.fenceng(json.loads(pathlib.Path(a.合作单).read_text(encoding="utf-8")), jin, cs)
    k = json.loads(pathlib.Path(a.标签卡).read_text(encoding="utf-8"))
    with open(a.达人, encoding="utf-8-sig") as f:
        dr = {r["达人编号"]: r for r in csv.DictReader(f)}
    with open(a.申样, encoding="utf-8-sig") as f:
        sy = list(csv.DictReader(f))
    xian = float(cs["新达人申样_履约率下限"])
    out = []
    for s in sorted(sy, key=lambda r: float(r["剩余审核小时"])):
        bh = s["达人编号"]; ceng = fc.get(bh, {}).get("层", "新")
        lv = float(s["履约率"].rstrip("%")) / 100
        pp = 匹配分.ping(dr[bh], k, "直播")["结论"] if bh in dr else "没查到"
        if ceng in ("核心", "成长"):
            jie, li = "过", f"{ceng}达人"
        elif pp in ("精准", "外扩") and lv >= xian:
            jie, li = "过", f"{ceng}达人，{pp}，履约率 {lv:.0%} ≥ {xian:.0%}"
        elif pp not in ("精准", "外扩"):
            jie, li = "提醒", f"{ceng}达人，和店铺标签{pp}（{dr.get(bh, {}).get('粉丝年龄', '')}、{dr.get(bh, {}).get('八大消费人群', '')}）→ 请主人判断"
        else:
            jie, li = "提醒", f"{ceng}达人，{pp}，但履约率 {lv:.0%} < {xian:.0%}（出单率 {s['出单率']}）→ 请主人判断"
        ji = float(s["剩余审核小时"]) <= 12
        out.append({"单号": s["申样单号"], "达人": bh, "剩余小时": s["剩余审核小时"], "急": ji, "结论": jie, "理由": li})
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1)); return
    print(f"待审 {len(out)} 单：建议过 {sum(o['结论'] == '过' for o in out)}、提醒主人 {sum(o['结论'] == '提醒' for o in out)}；"
          f"{'、'.join(o['单号'] for o in out if o['急']) or '没有'}快到 {cs['申样审核时限_小时']} 小时（R-LM-001，超时自动取消），先办。")
    hang = [[("⚠️" if o["急"] else "") + o["单号"], o["达人"], o["剩余小时"] + " 小时", o["结论"], o["理由"]] for o in out]
    print(底子.biao(["单号", "达人", "剩余", "建议", "理由"], hang, zhu=4, jian=0) + "\n出处：精选联盟·样品管理·待审核（剩余小时、履约率照页面）")


if __name__ == "__main__":
    main()
