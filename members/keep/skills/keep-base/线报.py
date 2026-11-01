"""掌柜 · 线报：出完半天报、全天报，顺手把这条线的数写成一份「电商线报」交给统筹面板（格式 线报.schema.json；只在本机，不进仓库）。
放什么（主人 11-01 口述）：销量、店里各款排行、带货达人排行、体验分、达人沟通状态、四位员工进度；运营层面（保分、活动、发票、物流、售后、待发货、违规）不放。
用法：python3 线报.py [--店铺 抖店-A …] [--微信 微信小店-阿青 …] [--今天 2026-11-10] [--出 ~/.yunjian/线报/02-02.json] [--保质期 780] [--格式 线报.schema.json] [--演练]
每个数带出处（平台·页面·店铺·北京时间），读不到写 null；只写条数和达人昵称，不抄消息原话；联系方式打码；写完自己照格式查一遍，不过不写。"""
import argparse, datetime as dt, hashlib, json, os, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import 底子, 汇总

CHENGYUAN = {"abacus": "算盘", "hawk": "货郎", "brok": "经纪", "keep": "掌柜"}
JU_JUE = re.compile(r"不太适合|暂时不用|先做现有货源|以后有机会|不考虑|不需要了")
XITONG = [("已查看你的联系方式", "等达人加微信"), ("已发送联系方式", "达人给了联系方式"), ("买样返款", "买样返款"), ("已申请样品|申请了样品", "达人申样")]


def jie(s, n):
    """达人昵称截短（商品名才用 底子.duanming，它会把「…牛仔裤穿搭」缩成「牛仔裤」）。"""
    s = s or ""
    return s if len(s) <= n else s[:n] + "…"


def jian(ming, i, wx):
    ds = re.findall(r"\d+", ming)
    return ("wx" if wx else "dy") + (ds[-1] if ds else str(i + 1))


def duan(ming):
    return ming.split("-", 1)[-1] if "-" in ming else ming


def jin7(sj, day):
    """合作消息的时间（11:20、昨天、星期三、10/22）在不在 7 天内。"""
    sj = (sj or "").strip()
    if re.fullmatch(r"\d{1,2}:\d{2}|今天|昨天|前天|星期[一二三四五六日天]", sj):
        return True
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})", sj)
    if m:
        try:
            d = dt.date(day.year, int(m.group(1)), int(m.group(2)))
        except ValueError:
            return False
        if d > day:
            d = d.replace(year=day.year - 1)
        return (day - d).days <= 7
    return False


def goutong(xs, day):
    """合作消息（近 7 天）分几类：等我们回、等达人加微信、达人给了联系方式、买样返款、达人申样、婉拒。返回 (各类达人, 一句话)。"""
    fen = {}
    for m in xs or []:
        if not jin7(m.get("时间"), day):
            continue
        ju = m.get("最后一句", "")
        lei = next((l for p, l in XITONG if re.search(p, ju)), None) or ("婉拒" if JU_JUE.search(ju) else "等我们回")
        fen.setdefault(lei, []).append(m.get("达人", ""))
    shunxu = ["等我们回", "等达人加微信", "达人给了联系方式", "达人申样", "买样返款", "婉拒"]
    ju = "；".join(f"{l} {len(fen[l])}（{'、'.join(jie(x, 8) for x in fen[l][:3])}{'等' if len(fen[l]) > 3 else ''}）" for l in shunxu if l in fen)
    return fen, ("近 7 天合作消息：" + ju if ju else "近 7 天没有合作消息")


def bang(rows, ming, je, n=5):
    if not rows:
        return None
    suo = (lambda x: 底子.duanming(x, 14)) if ming == "商品" else (lambda x: jie(x, 12))
    return "；".join(f"{i + 1}. {suo(r[ming])} {底子.yuan(r[je])}" + (f"（{r['占比']:.0%}）" if r.get("占比") is not None else "")
                    for i, r in enumerate(rows[:n]))


def xiang(ming, zhi, chu, dan=None):
    x = {"名字": ming[:20], "值": 底子.daima(zhi) if isinstance(zhi, str) else zhi, "出处": chu}
    if dan:
        x["单位"] = dan
    return x


def du_weixin(dp, day):
    d = pathlib.Path(dp) / "掌柜" / "后台" / str(day)
    for p in sorted((p for p in d.iterdir() if (p / "微信数.json").exists()), reverse=True) if d.is_dir() else []:
        return json.loads((p / "微信数.json").read_text(encoding="utf-8"))
    return None


def douyin(dp, i, day, cs, jg, wt):
    ming, k = dp.name, jian(dp.name, i, False)
    ht = 汇总.du_houtai(dp, day) or 汇总.du_houtai(dp, day, yao="体验分") or {}
    if not ht:
        wt.append({"编号": f"{k}-meidu", "级别": "P1", "标题": f"{duan(ming)} 今天没读到后台", "对象": ming, "建议": "看掌柜定时任务日志、ego 是否登录", "派给": "掌柜"})
        return
    sj, cc = ht.get("记录时间"), ht.get("出处") or {}
    chu = lambda kuai, mo: f"抖店·{cc.get(kuai, mo)}·{ming}·{sj}"
    ss = ht.get("实时") or {}
    g = lambda x: (ss.get(x) or {}).get("值")
    jc = lambda x: (ss.get(x) or {}).get("较昨日")
    jg[f"{k}_chengjiao"] = xiang(f"{duan(ming)}今日成交", g("成交金额"), chu("实时", "首页·实时") + (f"（较昨日 {底子.bili(jc('成交金额'))}）" if jc("成交金额") is not None else ""), "元")
    jg[f"{k}_dingdan"] = xiang(f"{duan(ming)}今日订单", g("成交订单数"), chu("实时", "首页·实时"), "单")
    tk = g("退款率_支付时间")
    jg[f"{k}_tuikuanlv"] = xiang(f"{duan(ming)}退款率", round(tk * 100, 2) if tk is not None else None, chu("实时", "首页·实时") + "（支付时间口径）", "%")
    ty = ht.get("体验分") or {}
    tchu = f"抖店·商家体验分页·{ming}·更新 {ty.get('更新时间')}"
    jg[f"{k}_tiyanfen"] = xiang(f"{duan(ming)}体验分", ty.get("总分"), tchu, "分")
    fx = ty.get("分项") or {}
    jg[f"{k}_tiyan_fenxiang"] = xiang(f"{duan(ming)}体验分分项", "｜".join(f"{a} {v.get('分'):g}" for a, v in fx.items() if a in ("商品", "物流", "服务") and v.get("分") is not None) or None, tchu)
    bh = None
    if ty.get("总分") is not None:
        bh, fxb, _ = 汇总.tiyan(dp, ty, xie=False)
    jg[f"{k}_tiyan_bianhua"] = xiang(f"{duan(ming)}体验分较上次", bh, tchu + "（和上一次更新比）", "分")
    lm = ht.get("联盟") or {}
    jg[f"{k}_daren7"] = xiang(f"{duan(ming)}近7日达人成交", lm.get("近7日达人成交金额"), f"抖店·首页·精选联盟·{ming}·{sj}", "元")
    jg[f"{k}_darenshu"] = xiang(f"{duan(ming)}近7日合作达人", lm.get("近7日合作达人数"), f"抖店·首页·精选联盟·{ming}·{sj}", "位")
    jg[f"{k}_paihang"] = xiang(f"{duan(ming)}各款排行前5", bang(ht.get("商品榜"), "商品", "成交金额"), chu("商品榜", "电商罗盘·商品列表·实时") + "·成交金额")
    jg[f"{k}_darenbang"] = xiang(f"{duan(ming)}带货达人前5", bang(ht.get("达人榜"), "达人", "成交金额"), chu("达人榜", "电商罗盘·达人概览·TOP达人") + "·直播用户支付金额")
    xs = ht.get("合作消息")
    fen, ju = goutong(xs, day) if xs is not None else ({}, None)
    jg[f"{k}_goutong"] = xiang(f"{duan(ming)}达人沟通", ju, chu("合作消息", "精选联盟·合作消息"))
    if bh is not None and bh <= -float(cs["掉分即时线"]):
        wt.append({"编号": f"{k}-diaofen", "级别": "P1", "标题": f"{duan(ming)}体验分掉 {abs(bh):g} 分", "对象": ming,
                   "说明": (f"后台诊断：{ty['短板']}" if ty.get("短板") else "")[:300], "建议": "看掉在哪一项，商品看品退差评、服务看客服响应", "派给": "掌柜"})
    if fen.get("等我们回"):
        wt.append({"编号": f"{k}-daren-wen", "级别": "P2", "标题": f"{duan(ming)} {len(fen['等我们回'])} 位达人等我们回话", "对象": ming,
                   "说明": "、".join(jie(x, 12) for x in fen["等我们回"][:8]), "建议": "经纪按话术库回，库外的转主人", "派给": "经纪"})
    if ht.get("没取到"):
        wt.append({"编号": f"{k}-meiqudao", "级别": "P2", "标题": f"{duan(ming)}有几块没读到", "对象": ming, "说明": "；".join(ht["没取到"])[:300], "派给": "掌柜"})


def weixin(dp, i, day, jg, wt):
    ming, k = dp.name, jian(dp.name, i, True)
    w = du_weixin(dp, day)
    if not w:
        wt.append({"编号": f"{k}-meidu", "级别": "P1", "标题": f"{duan(ming)} 今天没读到后台", "对象": ming, "建议": "看掌柜定时任务日志、ego 是否登录微信小店", "派给": "掌柜"})
        return
    sj, cc, ss = w.get("记录时间"), w.get("出处") or {}, w.get("实时") or {}
    chu = lambda kuai: f"{cc.get(kuai, '微信小店')}·{ming}·{sj}"
    jg[f"{k}_chengjiao"] = xiang(f"{duan(ming)}今日成交", ss.get("成交金额"), chu("实时"), "元")
    jg[f"{k}_dingdan"] = xiang(f"{duan(ming)}今日订单", ss.get("成交订单数"), chu("实时"), "单")
    jg[f"{k}_tiyanfen"] = xiang(f"{duan(ming)}体验分", w.get("体验分"), chu("体验分"), "分")
    jg[f"{k}_paihang"] = xiang(f"{duan(ming)}各款排行前5", bang(w.get("商品榜"), "商品", "成交金额"), chu("商品榜") + "·成交金额")
    jg[f"{k}_darenbang"] = xiang(f"{duan(ming)}带货达人前5", bang(w.get("达人榜"), "达人", "近30日销售额"), chu("达人榜"))
    jg[f"{k}_goutong"] = xiang(f"{duan(ming)}达人沟通", None, chu("合作消息"))
    if any("没登录" in x or "扫码" in x for x in w.get("没取到", [])):
        wt.append({"编号": f"{k}-denglu", "级别": "P1", "标题": f"{duan(ming)}后台没登录", "对象": ming, "建议": "在 ego 浏览器里重新扫码登录微信小店", "要人处理": "主人扫码登录"})
    elif w.get("没取到"):
        wt.append({"编号": f"{k}-meiqudao", "级别": "P2", "标题": f"{duan(ming)}有几块没读到", "对象": ming, "说明": "；".join(w["没取到"])[:300], "派给": "掌柜"})


def jindu(dps, day, dd):
    """四位员工：读各店回执合起来，一位一行；没回执写「今天没跑」，不替员工补。"""
    out = []
    for k, zh in CHENGYUAN.items():
        zuo, chu, ka, you = {}, [], [], False
        for dp in dps:
            p = dp / "回执" / str(day) / f"{k}.json"
            try:
                h = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            you = True
            for a, b in (h.get("做了") or {}).items():
                zuo[a] = zuo.get(a, 0) + b
            chu += h.get("出了") or []
            ka += h.get("卡在") or []
            for x in h.get("等主人定") or []:
                bh = f"{k}-{hashlib.md5(x.encode('utf-8')).hexdigest()[:8]}"
                if not any(y["编号"] == bh for y in dd):
                    dd.append({"编号": bh, "标题": 底子.daima(x)[:40].ljust(2, "。"), "推荐": f"照{zh}回执里的推荐定（详情问{zh}）", "出处": f"{zh}回执·{dp.name}·{day}"})
        if not you:
            out.append({"谁": zh, "做了": "今天没跑"})
            continue
        h = {"谁": zh, "做了": ("、".join(f"{a} {b:g}" for a, b in zuo.items()) or "有回执、没记做了什么")[:100]}
        if chu:
            h["出了"] = [底子.daima(x)[:80] for x in chu[:10]]
        if ka:
            h["卡在"] = [底子.daima(x)[:80] for x in ka[:10]]
        out.append(h)
    return out


def geshi(xb, gs):
    """照格式查：有 jsonschema 和格式文件就全查；没有就查必填和长度（够拦住常见的错）。返回错的列表。"""
    try:
        import jsonschema
        sc = json.loads(pathlib.Path(gs).read_text(encoding="utf-8"))
        return [f"{'/'.join(map(str, e.path))}：{e.message}" for e in jsonschema.Draft202012Validator(sc, format_checker=jsonschema.FormatChecker()).iter_errors(xb)]
    except (ImportError, OSError, TypeError):
        cuo = [f"缺 {x}" for x in ("格式", "线", "名字", "统筹", "更新时间", "保质期分钟", "结果", "进度", "等你定", "问题") if x not in xb]
        cuo += [] if re.fullmatch(r"\d{2}(-\d{2})?|ai", str(xb.get("线", ""))) else ["线 编号不合（如 02-02）"]
        cuo += [f"结果/{k} 键名不合" for k in xb.get("结果", {}) if not re.fullmatch(r"[a-z][a-z0-9_]{0,30}", k)]
        cuo += [f"问题/{w['编号']} 说明超 300 字" for w in xb.get("问题", []) if len(w.get("说明", "")) > 300]
        return cuo


def zhaogeshi(gs):
    if gs:
        return gs
    for p in (底子.KU / "线报.schema.json", pathlib.Path(__file__).resolve().parents[4] / "shared" / "线报.schema.json"):
        if p.exists():
            return p
    return None


def main(argv=None):
    a = argparse.ArgumentParser()
    a.add_argument("--店铺", nargs="*", default=[]); a.add_argument("--微信", nargs="*", default=[])
    a.add_argument("--今天"); a.add_argument("--出"); a.add_argument("--线", default="02-02"); a.add_argument("--名字", default="万象·电商")
    a.add_argument("--保质期", type=int, default=780); a.add_argument("--格式"); a.add_argument("--现在"); a.add_argument("--演练", action="store_true")
    a = a.parse_args(argv)
    day = dt.date.fromisoformat(a.今天) if a.今天 else 底子.jintian()
    dys = [底子.dianpu(x) for x in a.店铺]
    wxs = [底子.dianpu(x) for x in a.微信]
    if not dys and not wxs:
        dys = [底子.dianpu()]
    cs, _ = 底子.canshu(dys[0] if dys else None)
    jg, wt, dd = {}, [], []
    for i, dp in enumerate(dys):
        douyin(dp, i, day, cs, jg, wt)
    for i, dp in enumerate(wxs):
        weixin(dp, i, day, jg, wt)
    now = dt.datetime.fromisoformat(a.现在) if a.现在 else 底子.xianzai()
    xb = {"格式": "1", "线": a.线, "名字": a.名字, "统筹": "掌柜", "更新时间": now.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
          "保质期分钟": a.保质期, "结果": jg, "进度": jindu(dys + wxs, day, dd), "等你定": dd, "问题": wt}
    gs = zhaogeshi(a.格式)
    cuo = geshi(xb, gs)
    if cuo:
        print("线报格式不过，没写：\n" + "\n".join(cuo[:20]))
        return 1
    kong = [v["名字"] for v in jg.values() if v["值"] is None]
    print(f"线报 {a.线}：结果 {len(jg)} 项（读不到 {len(kong)}：{'、'.join(kong) or '无'}）、进度 {len(xb['进度'])} 位、等你定 {len(dd)}、问题 {len(wt)}；格式 {'照 ' + pathlib.Path(gs).name + ' 查过' if gs else '只查了必填'}")
    if a.演练:
        print(json.dumps(xb, ensure_ascii=False, indent=1))
        return 0
    p = pathlib.Path(a.出).expanduser() if a.出 else 底子.HOME.parent / "线报" / f"{a.线}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(xb, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)
    print("已写", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
