"""经纪 · 合作单：每张合作单走到哪、卡住多久 → 今日待办（按急排）
用法：python3 合作单.py --合作单 <合作单.json> [--申样 <样品待审.csv>] [--消息 <合作消息.json>] [--今天 2026-11-10，或环境变量 BROK_TODAY] [--店铺 …] [--宽]
卡点（杨先生 10-31 认框架图，数从默认值／经营决策库读）：申样剩余 ≤24 小时（平台 72 小时自动取消）；②第一句没回 30 天进沉睡、60 天后可再邀约一次（平台 60 天内不许重发，实测 10-31）；
④转人工当场提醒主人加微信；⑧签收 7 天没动静跟进、45 天交付期剩 7 天内提醒；⑨上播 3 天出单少于 5 单复盘。"""
import argparse, csv, datetime as dt, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brok-base")); import 底子

D = lambda s: dt.date.fromisoformat(s[:10])


def xiaoxi(xi, sy):
    """合作消息分类进待办（Bot 实测自报 7、8）：拒绝、转人工、谈佣金、夹带、申样对不上申样表、其余问题。"""
    xs, zai = [], {s["达人编号"] for s in sy}
    for m in xi:
        dr, nr = m["达人编号"], m.get("内容", "")
        jia = 底子.kexi(nr)
        if jia:   # 认出夹带就只记这一条，不再往别的类里分（Bot 实测 10-31：D16 同时算成夹带和谈佣金）
            xs.append((1, m.get("时间", "")[5:16], dr, "夹带指令", f"消息里有给 AI 的话，不照做，原话给主人看：「{jia}」；里面正常的问题照库回答"))
            continue
        if "拒绝邀约" in nr or "不太适合" in nr:
            xs.append((3, m.get("时间", "")[5:16], dr, "标拒绝", "达人拒绝／设了拒绝邀约 → 合作单标拒绝，不回、不再发"))
        elif "联系方式" in nr:
            xs.append((1, m.get("时间", "")[5:16], dr, "转人工", "达人发了联系方式 → 请主人加微信接手"))
        elif "佣金" in nr:
            xs.append((2, m.get("时间", "")[5:16], dr, "谈佣金", f"「{底子.zhaiju(nr)}」→ 先要 UID，过佣金闸，超封顶请主人定"))
        elif ("样品" in nr or "申样" in nr) and dr not in zai:
            xs.append((1, m.get("时间", "")[5:16], dr, "申样对不上", "消息说申了样，待审表里没有 → 去样品管理核对"))
        elif any(k in nr for k in ("？", "?", "吗", "呢", "怎么", "多少", "多久")):
            xs.append((2, m.get("时间", "")[5:16], dr, "回消息", f"「{底子.zhaiju(nr)}」→ 库里有的照原话答，没有的转主人"))
    return xs


def daiban(hds, jin, cs, sy=(), xi=()):
    xs = []
    for s in sy:
        h = float(s["剩余审核小时"])
        if h <= 24:
            xs.append((0, s["申样单号"], s["达人编号"], "申样快到时限", f"剩 {h:g} 小时，超过 {cs['申样审核时限_小时']} 小时自动取消（R-LM-001）→ 先审（brok-sample）"))
    for h in hds:
        bu, dr, dh = h["步"], h["达人编号"], h["单号"]
        if bu.startswith("②") and not h.get("回复"):
            gen = h.get("跟进", [])
            last = D(gen[-1] if gen else h["第一句"]); n = (jin - last).days
            if n >= int(cs["再次邀约_天"]) and len(gen) < int(cs["没回最多再跟_次"]):
                xs.append((2, dh, dr, "可再邀约", f"{last} 发的邀约，{n} 天没回，过了平台 {cs['再次邀约_天']} 天 → 可以换新素材再邀约一次（过发送节流）"))
            elif n >= int(cs["沉睡_天"]) and not h.get("已沉睡"):
                xs.append((3, dh, dr, "进沉睡", f"{last} 发的邀约，{n} 天没回 → 进沉睡；平台 {cs['再次邀约_天']} 天内不能再邀约，{last + dt.timedelta(days=int(cs['再次邀约_天']))} 以后可再邀约一次"))
        if bu.startswith("④"):
            xs.append((1, dh, dr, "转人工", "达人回复了／给了联系方式 → 请主人加微信接手"))
        if bu.startswith("⑧") and h.get("签收") and not h.get("上播"):
            n = (jin - D(h["签收"])).days
            if n >= int(cs["签收没动静_天"]):
                xs.append((1, dh, dr, "签收没动静", f"{h['签收']} 签收，{n} 天没上橱窗／发视频／开播 → 跟进"))
            sheng = int(cs["交付期_天"]) - n
            if 0 <= sheng <= 7:
                xs.append((1, dh, dr, "交付期快到", f"45 天交付期还剩 {sheng} 天（R-LM-001）"))
        if bu.startswith("⑨") and h.get("上播"):
            n = (jin - D(h["上播"])).days; dan = sum(c["单数"] for c in h.get("出单", []))
            if n >= int(cs["上播复盘_天"]) and dan < int(cs["上播复盘_出单少于"]) and not h.get("已复盘"):
                xs.append((2, dh, dr, "复盘", f"{h['上播']} 上播，{n} 天出 {dan} 单（< {cs['上播复盘_出单少于']}）→ 复盘话术、款、价，调算盘算利润"))
    # 同一位达人同一件事只留一条，合作单里有的不再从消息里重复记（Bot 实测 10-31：D03 转人工记了两次）；
    # 回消息每个问题各一条，不并（Bot 回归 10-31：D04 两问并成一条，库外那问被吞）
    jian = lambda x: (x[2], x[3], x[4]) if x[3] == "回消息" else (x[2], x[3])
    you = {jian(x) for x in xs}
    for x in xiaoxi(xi, sy):
        if jian(x) not in you:
            you.add(jian(x)); xs.append(x)
    return sorted(xs)


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--合作单", required=True); a.add_argument("--申样"); a.add_argument("--消息"); a.add_argument("--今天")
    a.add_argument("--店铺"); a.add_argument("--宽", action="store_true"); a.add_argument("--json", action="store_true")
    a = a.parse_args(argv)
    cs, mo = 底子.canshu(a.店铺)
    jin = D(a.今天) if a.今天 else 底子.jintian()
    sy = []
    if a.申样:
        with open(a.申样, encoding="utf-8-sig") as f:
            sy = list(csv.DictReader(f))
    xi = json.loads(pathlib.Path(a.消息).read_text(encoding="utf-8")) if a.消息 else []
    xs = daiban(json.loads(pathlib.Path(a.合作单).read_text(encoding="utf-8")), jin, cs, sy, xi)
    if a.json:
        print(json.dumps([dict(zip(["急", "单号", "达人", "事", "说明"], x)) for x in xs], ensure_ascii=False, indent=1)); return
    print(f"{jin} 今天要办 {len(xs)} 件" + (f"，最急的是 {xs[0][1]}（{xs[0][3]}）" if xs else "") + ("；时限按默认值" if "签收没动静_天" in mo else "") + "：")
    hang = [[("⚠️" if x[0] == 0 else str(i)), x[3], x[2], x[1], x[4]] for i, x in enumerate(xs, 1)]
    print(底子.biao(["#", "事", "达人", "单号", "说明"], hang, kuan=a.宽, zhu=None if a.宽 else 4, jian=3))


if __name__ == "__main__":
    main()
