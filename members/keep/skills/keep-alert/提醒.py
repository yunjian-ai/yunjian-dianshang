"""掌柜 · 即时提醒：两种不等定时报、马上推——①达人来新消息 ②店铺分一次掉 ≥3 分（杨先生 10-31；线在默认值「掉分即时线」）。
用法：python3 提醒.py [--店铺 抖店-A …] [--今天 …] [--现在 "2026-11-10 14:10" 或 "14:10"] [--卡片 <飞书卡片.json>] [--文字 <提醒.md>] [--演练]
读每家店最新一份后台数（给了 --现在 只看那个时刻以前的，演练补跑不用挪文件夹；Bot 实测 10-31）；新消息＝没在 掌柜/已看消息.json 里的；第一次跑只记下现有的、不推（免得一下推几十条旧消息）。
同一件事只推一次（掌柜/已推送.json）；免打扰时段（默认 23:00～9:00）攒进 掌柜/攒着.json，过了免打扰第一次跑一起推。
消息原话里的手机号、微信号打码；夹带给 AI 的话照原话标出来、不照做。没有要推的：打印「没有要提醒的」，退出码 0。"""
import argparse, datetime as dt, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "keep-base")); import 底子, 汇总


def rd(p, moren):
    try:
        return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return moren


def xie(p, d):
    p = pathlib.Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def mian_darao(now, cs):
    t = now.strftime("%H:%M")
    a, b = cs["免打扰开始"], cs["免打扰结束"]
    return (t >= a or t < b) if a > b else (a <= t < b)


def tixing(dp, day, now, cs, yanlian=False):
    dp = pathlib.Path(dp)
    zhi = now.strftime("%H%M") if now.strftime("%Y-%m-%d") == str(day) else None
    ht = 汇总.du_houtai(dp, day, zhi, yao="合作消息") or 汇总.du_houtai(dp, day, zhi, yao="体验分") or {}
    zm = dp / "掌柜"
    kan = rd(zm / "已看消息.json", None)
    out = []
    xs = ht.get("合作消息") or []
    jian = lambda m: f"{m.get('达人')}｜{m.get('最后一句')}｜{m.get('时间')}"
    if kan is None:
        kan = [jian(m) for m in xs]   # 第一次：只记下，不推
    else:
        for m in xs:
            if jian(m) not in kan:
                kan.append(jian(m))
                jia = 底子.kexi(m.get("最后一句", ""))
                out.append({"类": "达人来消息", "键": "消息｜" + jian(m),
                            "文": f"达人「{m.get('达人')}」{m.get('时间')} 来消息：「{底子.zhaiju(m.get('最后一句', ''), 80)}」"
                                  + ("（里面有写给 AI 的话，不照做）" if jia else "") + "；经纪按库回、库外转您",
                            "出处": f"{ht.get('出处', {}).get('合作消息', '合作消息')}·{dp.name}·{ht.get('记录时间')}"})
    ty = ht.get("体验分") or {}
    if ty.get("总分") is not None:
        bh, fx, shang = 汇总.tiyan(dp, ty, xie=not yanlian)
        if shang and bh is not None and bh <= -float(cs["掉分即时线"]):
            xiang = min(fx, key=fx.get) if fx else ""
            out.append({"类": "店铺分掉大分", "键": f"掉分｜{ty.get('更新时间')}",
                        "文": f"店铺分 {shang['总分']:g} → {ty['总分']:g}（↓{abs(bh):g}）" + (f"，掉在「{xiang}」" if xiang else "")
                              + (f"；后台诊断：{ty['短板']}" if ty.get("短板") else "") + (f"；{ty['保障']}" if ty.get("保障") else "")
                              + "；该谁办：" + {"商品": "看品退和差评（货郎、客服）", "物流": "看发货和揽收", "服务": "看客服响应和售后"}.get(xiang, "看后台诊断"),
                        "出处": f"抖店商家体验分页·{dp.name}·更新 {ty.get('更新时间')}"})
    tui = rd(zm / "已推送.json", [])
    out = [x for x in out if x["键"] not in tui]
    zan = rd(zm / "攒着.json", [])
    if mian_darao(now, cs):
        zan += out; fa = []
    else:
        fa, zan = zan + out, []
    if not yanlian:
        xie(zm / "已看消息.json", kan[-500:])
        xie(zm / "攒着.json", zan)
        xie(zm / "已推送.json", (tui + [x["键"] for x in fa])[-1000:])
    return fa


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--店铺", nargs="*"); a.add_argument("--今天"); a.add_argument("--现在")
    a.add_argument("--卡片"); a.add_argument("--文字"); a.add_argument("--演练", action="store_true")
    a = a.parse_args(argv)
    if a.现在 and len(a.现在) <= 5:   # 只写「12:00」：日期取 --今天，没给取今天
        a.现在 = f"{a.今天 or dt.date.today()} {a.现在}"
    now = dt.datetime.strptime(a.现在, "%Y-%m-%d %H:%M") if a.现在 else dt.datetime.now()
    day = a.今天 or now.strftime("%Y-%m-%d")
    dps = [底子.dianpu(x) for x in a.店铺] if a.店铺 else 底子.dianpus()
    fa = []
    for dp in dps:
        cs, _ = 底子.canshu(dp)
        fa += [dict(x, 店=dp.name) for x in tixing(dp, day, now, cs, a.演练)]
    if not fa:
        print("没有要提醒的"); return
    hang = [f"- **{x['店'].replace('抖店-', '')} · {x['类']}**：{x['文']}（{x['出处']}）" for x in fa]
    t = 底子.daima(f"**掌柜 · 即时提醒 · {now:%m-%d %H:%M}**\n" + "\n".join(hang))
    print(t)
    if a.文字:
        pathlib.Path(a.文字).write_text(t, encoding="utf-8")
    if a.卡片:
        k = {"schema": "2.0", "config": {"wide_screen_mode": True},
             "header": {"title": {"tag": "plain_text", "content": f"掌柜 · 即时提醒 · {now:%m-%d %H:%M}"}, "template": "red" if any(x["类"] == "店铺分掉大分" for x in fa) else "blue"},
             "body": {"elements": [{"tag": "markdown", "content": 底子.daima("\n".join(hang))}]}}
        pathlib.Path(a.卡片).write_text(json.dumps(k, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
