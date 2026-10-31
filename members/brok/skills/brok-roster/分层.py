"""经纪 · 分层：每位达人的合作单 → 新／成长／核心／沉睡（阈值从默认值／经营决策库读：核心_近天数、核心_出单合作次数、核心_利润前百分比、沉睡_天、再次邀约_天、没回最多再跟_次）
用法：python3 分层.py --合作单 <合作单.json> [--今天 2026-11-10] [--利润 <算盘回执：{达人编号: 利润}>] [--店铺 …] [--json]
核心：近 60 天至少 2 张合作单出单，或利润排店里达人前 20%（要算盘回执；没装算盘这一条不算、写明）；沉睡：30 天没动静，或跟满次数还没回；成长：出过单；新：其余。
平台「我的达人库」的「流失风险达人（距上次出单超过 30 天）」就是沉睡（R-LM-006），对不上以平台为准。"""
import argparse, datetime as dt, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brok-base")); import 底子

D = lambda s: dt.date.fromisoformat(s[:10])


def riqi(h):
    xs = [h.get(k) for k in ("第一句", "回复", "签收", "上播", "最后动静")] + list(h.get("跟进", [])) + [c["日期"] for c in h.get("出单", [])]
    return [D(x) for x in xs if x]


def fenceng(hds, jin, cs, lirun=None):
    by = {}
    for h in hds:
        by.setdefault(h["达人编号"], []).append(h)
    pai = sorted(lirun.items(), key=lambda x: -x[1]) if lirun else []
    qian = {k for k, _ in pai[:max(1, int(len(pai) * float(cs["核心_利润前百分比"])))]} if pai else set()
    out = {}
    for dr, hs in by.items():
        ds = [d for h in hs for d in riqi(h)]
        zui = max(ds) if ds else None
        chu = [h for h in hs if h.get("出单")]
        jin_chu = [h for h in chu if any((jin - D(c["日期"])).days <= int(cs["核心_近天数"]) for c in h["出单"])]
        gen_man = any(len(h.get("跟进", [])) >= int(cs["没回最多再跟_次"]) and not h.get("回复") and h.get("跟进") and (jin - D(h["跟进"][-1])).days >= int(cs["再次邀约_天"]) for h in hs)
        if zui and (jin - zui).days > int(cs["沉睡_天"]):
            c, li = "沉睡", f"最后动静 {zui}，{(jin - zui).days} 天没动静（>{cs['沉睡_天']} 天）"
        elif gen_man and not chu:
            c, li = "沉睡", "跟满次数还没回"
        elif len(jin_chu) >= int(cs["核心_出单合作次数"]) or dr in qian:
            c, li = "核心", f"近 {cs['核心_近天数']} 天 {len(jin_chu)} 次合作出单" + ("；利润排前" if dr in qian else "")
        elif chu:
            c, li = "成长", f"出过单（{sum(x['单数'] for h in chu for x in h['出单'])} 单）"
        else:
            c, li = "新", "合作过还没出单"
        out[dr] = {"层": c, "理由": li, "最后动静": str(zui) if zui else ""}
    return out


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--合作单", required=True); a.add_argument("--今天"); a.add_argument("--利润")
    a.add_argument("--店铺"); a.add_argument("--json", action="store_true"); a.add_argument("--宽", action="store_true")
    a = a.parse_args(argv)
    cs, mo = 底子.canshu(a.店铺)
    jin = D(a.今天) if a.今天 else 底子.jintian()
    lr = json.loads(pathlib.Path(a.利润).read_text(encoding="utf-8")) if a.利润 else None
    out = fenceng(json.loads(pathlib.Path(a.合作单).read_text(encoding="utf-8")), jin, cs, lr)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1)); return
    n = {c: sum(1 for v in out.values() if v["层"] == c) for c in ("核心", "成长", "新", "沉睡")}
    print(f"{len(out)} 位达人：核心 {n['核心']}、成长 {n['成长']}、新 {n['新']}、沉睡 {n['沉睡']}" + ("" if lr else "（没给算盘利润回执（--利润），「利润前 20%」这条没算）") + ("；阈值按默认值" if "核心_近天数" in mo else ""))
    xu = {"核心": 0, "成长": 1, "新": 2, "沉睡": 3}
    hang = [[k, v["层"], v["最后动静"], v["理由"]] for k, v in sorted(out.items(), key=lambda x: (xu[x[1]["层"]], x[0]))]
    print(底子.biao(["达人", "层", "最后动静", "理由"], hang, kuan=a.宽, zhu=None if a.宽 else 3, jian=0))


if __name__ == "__main__":
    main()
