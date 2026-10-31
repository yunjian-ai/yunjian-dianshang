"""经纪 · 发送节流（**只读检查，不发任何消息**；`--记一条` 只往本地发送记录.csv 记一行，真发消息在后台 M-BY-003 由人或浏览器做）：能不能现在发这一条（第一句或跟进）——每天上限、两条间隔、同一达人没回最多再跟几次、本周建联额度
达人没回：平台 60 天内不许再发邀约（邀约带货表单提示，实测 10-31），60 天后可再邀约一次。
用法：python3 发送节流.py --记录 <发送记录.csv> --达人 D21 --类型 第一句|跟进 [--现在 "2026-11-10 15:00"]
        [--合作单 <合作单.json>] [--额度 <建联额度.json>] [--店铺 <店铺文件夹>] [--记一条 --模板 T1]
能发退出码 0（--记一条 会把这条写进发送记录）；不能发退出码 1。线从默认值／经营决策库读（每天发第一句上限、两条最少间隔_分钟、没回最多再跟_次、建联额度提醒比例）。
来由：规则 101665 第 5.23 条不许 IM 大量频繁发；6.2.5 第 4 项程序干预可终止合作（杨先生 10-31：照人的节奏、限量）。"""
import argparse, csv, datetime as dt, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brok-base")); import 底子

FMT = "%Y-%m-%d %H:%M"


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--记录", required=True); a.add_argument("--达人", required=True)
    a.add_argument("--类型", default="第一句", choices=["第一句", "跟进"]); a.add_argument("--现在")
    a.add_argument("--合作单"); a.add_argument("--额度"); a.add_argument("--店铺"); a.add_argument("--记一条", action="store_true"); a.add_argument("--模板", default="")
    a = a.parse_args(argv)
    cs, mo = 底子.canshu(a.店铺)
    now = dt.datetime.strptime(a.现在, FMT) if a.现在 else (dt.datetime.combine(底子.jintian(), dt.datetime.now().time()).replace(second=0, microsecond=0))
    p = pathlib.Path(a.记录)
    jl = []
    if p.exists():
        with open(p, encoding="utf-8-sig") as f:
            jl = list(csv.DictReader(f))
    jin = [r for r in jl if r["时间"][:10] == now.strftime("%Y-%m-%d")]
    shang = int(cs["每天发第一句上限"]); jian = int(cs["两条最少间隔_分钟"]); gen = int(cs["没回最多再跟_次"])
    bu, ti = [], []
    if len(jin) >= shang:
        bu.append(f"今天已发 {len(jin)} 条，到每天上限 {shang}（{'按默认值' if '每天发第一句上限' in mo else '主人定的'}；规则 101665 第 5.23 条不许大量频繁发）→ 明天接着发")
    if jin:
        zui = max(dt.datetime.strptime(r["时间"], FMT) for r in jin)
        cha = (now - zui).total_seconds() / 60
        if cha < jian:
            bu.append(f"上一条 {zui:%H:%M} 发的，离现在 {cha:.0f} 分钟，不到 {jian} 分钟 → 等 {jian - cha:.0f} 分钟")
    if a.合作单:
        for h in json.loads(pathlib.Path(a.合作单).read_text(encoding="utf-8")):
            if h["达人编号"] != a.达人:
                continue
            if h.get("拒绝") or "拒绝" in h.get("步", ""):
                bu.append(f"{a.达人} 已拒绝／设了拒绝邀约 → 不再发")
            if a.类型 == "跟进" and not h.get("回复") and h.get("第一句"):
                last = max([h["第一句"]] + list(h.get("跟进", [])))
                tian = (now.date() - dt.date.fromisoformat(last[:10])).days
                if tian < int(cs["再次邀约_天"]):
                    bu.append(f"{a.达人} 没回：{last} 发的邀约，{tian} 天，平台 {cs['再次邀约_天']} 天内不能再邀约（R-LM-006）→ {dt.date.fromisoformat(last[:10]) + dt.timedelta(days=int(cs['再次邀约_天']))} 以后才能再邀约一次")
                elif len(h.get("跟进", [])) >= gen:
                    bu.append(f"{a.达人} 已再邀约过 {len(h['跟进'])} 次还没回（最多 {gen} 次）→ 进沉睡，不再发")
            if a.类型 == "第一句" and h.get("第一句"):
                bu.append(f"{a.达人} 已经发过第一句（{h['第一句']}）→ 要发就按「跟进」")
    if a.额度:
        e = json.loads(pathlib.Path(a.额度).read_text(encoding="utf-8"))
        bl = e["本周已用"] / e["本周总额"] if e.get("本周总额") else 0
        if bl >= float(cs["建联额度提醒比例"]):
            ti.append(f"本周建联额度已用 {e['本周已用']}/{e['本周总额']}（{bl:.0%}），过了 {float(cs['建联额度提醒比例']):.0%} 提醒线 → 告诉主人；出处：{e.get('出处', '合作消息页')}")
        if e.get("本周总额") and e["本周已用"] >= e["本周总额"]:
            bu.append("本周建联额度用完了，下周一 0 点更新（R-LM-006）")
    for x in ti:
        print("⚠️ " + x)
    if bu:
        print(f"{a.达人} 这条{a.类型}现在不能发：\n" + "\n".join(f"- {x}" for x in bu)); raise SystemExit(1)
    print(f"{a.达人} 这条{a.类型}可以发（今天第 {len(jin) + 1} 条／上限 {shang}）")
    if a.记一条:
        xin = not p.exists()
        with open(p, "a", encoding="utf-8-sig" if xin else "utf-8", newline="") as f:
            w = csv.writer(f)
            if xin:
                w.writerow(["时间", "达人编号", "类型", "模板"])
            w.writerow([now.strftime(FMT), a.达人, a.类型, a.模板])
        print("已记进发送记录")


if __name__ == "__main__":
    main()
