"""掌柜 · 汇总：一家店某个时段的「快照」——后台数（掌柜自己读的）＋三位员工的回执＋店里规矩 → 业绩、预估利润、店铺分变化、排行、达人、员工、要您管的。
出报.py、提醒.py、员工看板.py 都从这里拿数；数全有出处，缺什么写「没取到」，不估不编。只用标准库。"""
import datetime as dt, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import 底子

YUANGONG = {"abacus": "算盘", "hawk": "货郎", "brok": "经纪"}
HUIZHI_BIXU = ["成员", "店铺", "日期", "做了", "出了", "卡在", "等主人定", "数"]


def du_houtai(dp, day, zhi=None, yao="实时"):
    """这家店这天最新一份「有 yao 这块」的后台数（掌柜/后台/<日期>/<时刻>/后台数.json）；给了 zhi（如 "1150"）只看这个时刻以前的。
    出报要「实时」（每小时看消息那次只读体验分和消息，不能拿来出报），提醒要「合作消息」。"""
    d = pathlib.Path(dp) / "掌柜" / "后台" / str(day)
    if not d.is_dir():
        return None
    for p in sorted((p for p in d.iterdir() if p.is_dir() and (p / "后台数.json").exists() and (zhi is None or p.name <= zhi)), reverse=True):
        ht = json.loads((p / "后台数.json").read_text(encoding="utf-8"))
        if not yao or ht.get(yao):
            return ht
    return None


def du_huizhi(dp, day):
    """三位员工这天的回执；格式不对的标「回执格式不对」，不猜（格式见 库/回执格式.json）。"""
    out = {}
    d = pathlib.Path(dp) / "回执" / str(day)
    for k in YUANGONG:
        p = d / f"{k}.json"
        if not p.exists():
            out[k] = None
            continue
        try:
            h = json.loads(p.read_text(encoding="utf-8"))
            que = [x for x in HUIZHI_BIXU if x not in h]
            out[k] = h if not que else {"_坏": f"回执格式不对（缺 {'、'.join(que)}）"}
        except ValueError:
            out[k] = {"_坏": "回执格式不对（不是 JSON）"}
    return out


def yunfei(dp, cs):
    """每单运费：店里经营决策卡写了「默认仓」和「<仓>_每单」就用它，否则用参数「运费_每单」。"""
    jc = pathlib.Path(dp) / "经营决策库"
    for p in sorted(jc.glob("D-*.md")) if jc.is_dir() else []:
        k = 底子.kaitou(p)
        if k.get("状态", "").startswith("生效"):
            can = k.get("参数") or {}
            cang = can.get("默认仓")
            if cang and f"{cang}_每单" in can:
                try:
                    return float(can[f"{cang}_每单"]), f"店里快递单价（{k.get('编号')}）"
                except ValueError:
                    pass
    v = float(cs.get("运费_每单") or 0)
    return (v, "参数 运费_每单") if v else (None, "")


def yugu(ss, cs, yf):
    """当天预估利润（粗算）：成交 − 退款（支付时间）− 成本 − 达人佣金 − 平台佣金 − 运费。缺成本规矩或运费就不算，写明缺什么。"""
    g = lambda k: (ss.get(k) or {}).get("值")
    cj, tk, dd = g("成交金额"), g("退款金额_支付时间") or 0, g("成交订单数")
    zb = float(cs.get("成本_占定价") or 0)
    que = [x for x, ok in (("成交金额", cj is not None), ("成本规矩（成本占定价）", zb > 0), ("每单运费", yf[0] is not None), ("订单数", dd is not None)) if not ok]
    if que:
        return None, "预估利润没算：缺" + "、".join(que)
    jing = cj - tk
    dr = g("达人佣金_预估")
    drs = "后台预估口径"
    if dr is None:
        dr = (g("达人成交金额") or jing * float(cs.get("达人带货占比") or 0)) * float(cs.get("默认佣金") or 0)
        drs = "按默认佣金估"
    pt = g("平台佣金_预估")
    pts = "后台预估口径"
    if pt is None:
        pt = cj * float(cs.get("平台服务费率") or 0)
        pts = f"按 {float(cs.get('平台服务费率') or 0):.0%} 估"
    lr = jing * (1 - zb) - dr - pt - dd * yf[0]
    return lr, (f"成交 {cj:,.0f} − 退款 {tk:,.0f}（支付时间）− 成本（定价×{zb:g}）− 达人佣金 {dr:,.0f}（{drs}）"
                f"− 平台佣金 {pt:,.0f}（{pts}）− 运费 {dd:.0f} 单×{yf[0]:g}（{yf[1]}）；退货运费没算，以算盘结算为准")


def tiyan(dp, ty, xie=True):
    """店铺分变化：和自己存的上一次「更新时间不同」的记录比（体验分每天约 22 点更新一次）。返回 (总分变化, 各分项变化, 上次)。"""
    p = pathlib.Path(dp) / "掌柜" / "体验分记录.json"
    try:
        jl = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        jl = {}
    gx, zf = ty.get("更新时间"), ty.get("总分")
    if not gx or zf is None:
        return None, {}, None
    qian = [k for k in sorted(jl) if k < gx]
    bh, fx, shang = None, {}, None
    if qian:
        shang = jl[qian[-1]]
        bh = zf - shang["总分"]
        for k, v in (ty.get("分项") or {}).items():
            if k in (shang.get("分项") or {}):
                fx[k] = v["分"] - shang["分项"][k]
    elif ty.get("较前1日") is not None:   # 第一次跑，没有自己的记录：用页面给的较前1日
        bh = ty["较前1日"]
        fx = {k: v.get("较前1日") for k, v in (ty.get("分项") or {}).items() if v.get("较前1日") is not None}
    if xie and gx not in jl:
        jl[gx] = {"总分": zf, "分项": {k: v["分"] for k, v in (ty.get("分项") or {}).items()}}
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(jl, ensure_ascii=False, indent=1), encoding="utf-8")
    return bh, fx, shang


def yuangong(hz):
    """员工看板：一位一行——今天做了／出了什么／卡在哪、等您定。"""
    rows = []
    for k, zh in YUANGONG.items():
        h = hz.get(k)
        if h is None:
            rows.append([zh, "今天没跑（没有回执）", "—", "—"])
        elif "_坏" in h:
            rows.append([zh, h["_坏"], "—", "—"])
        else:
            zuo = "、".join(f"{a} {b:g}" for a, b in h["做了"].items()) or "—"
            chu = "、".join(h["出了"][:3]) + ("等" if len(h["出了"]) > 3 else "") or "—"
            ka = "；".join((h["卡在"] + [f"等您定：{x}" for x in h["等主人定"]])[:3]) or "—"
            rows.append([zh, zuo, chu, ka])
    return rows


def kuaizhao(dp, day, shiduan="现在", zhi=None, xie=True):
    """一家店的快照，写进 掌柜/快照/<日期>-<时段>.json（xie=False 只算不写，演练用）。"""
    dp = pathlib.Path(dp)
    cs, mo = 底子.canshu(dp)
    ht = du_houtai(dp, day, zhi) or {}
    hz = du_huizhi(dp, day)
    ss = ht.get("实时") or {}
    yf = yunfei(dp, cs)
    lr, lrs = yugu(ss, cs, yf) if ss else (None, "后台没取到")
    ty = ht.get("体验分") or {}
    bh, fx, _ = tiyan(dp, ty, xie) if ty.get("总分") is not None else (None, {}, None)
    g = lambda k: (ss.get(k) or {}).get("值")
    dr_zb = (g("达人成交金额") / g("成交金额")) if g("达人成交金额") and g("成交金额") else None
    yao = []
    if bh is not None and bh <= -float(cs["掉分即时线"]):
        yao.append(("即时", f"店铺分掉 {abs(bh):g} 分" + (f"（{min(fx, key=fx.get)}）" if fx else ""), "体验分"))
    elif bh is not None and bh <= -float(cs["掉分进报线"]):
        yao.append(("今天", f"店铺分掉 {abs(bh):g} 分" + (f"（{min(fx, key=fx.get)}）" if fx else ""), "体验分"))
    jz = (ss.get("成交金额") or {}).get("较昨日")
    if jz is not None and jz <= float(cs["业绩掉线"]):
        yao.append(("今天", f"成交比昨天 {底子.bili(jz)}", "实时"))
    for x in ((hz.get("brok") or {}).get("数") or {}).get("今日待办", []):
        if x.get("事") in ("申样快到时限", "转人工", "谈佣金", "申样对不上", "夹带指令", "签收没动静"):
            yao.append(("今天", f"达人 {x.get('达人')} {x.get('事')}", "经纪回执"))
    for k in ("brok", "hawk", "abacus"):
        for x in (hz.get(k) or {}).get("等主人定", []):
            if not any(x in y[1] for y in yao):
                yao.append(("今天", f"{YUANGONG[k]}：{x}", f"{YUANGONG[k]}回执"))
    for x in (((hz.get("hawk") or {}).get("数") or {}).get("快下架") or []):
        yao.append(("本周", f"{底子.duanming(x)} 快被自动下架", "货郎回执"))
    dai = ht.get("待办") or {}
    if dai.get("待处理违规"):
        yao.append(("今天", f"后台有 {dai['待处理违规']} 条待处理违规（抖店首页顶部待办点「待处理违规」进去看；申诉、整改由您办，掌柜后台只看不改）", "首页待办"))
    snap = {"店铺": dp.name, "日期": str(day), "时段": shiduan, "记录时间": ht.get("记录时间"),
            "实时": ss, "达人占比": dr_zb, "预估利润": lr, "利润说明": lrs,
            "体验分": {"总分": ty.get("总分"), "变化": bh, "分项变化": fx, "分项": {k: v.get("分") for k, v in (ty.get("分项") or {}).items()},
                    "短板": ty.get("短板"), "保障": ty.get("保障"), "更新时间": ty.get("更新时间"), "今日已更新": ty.get("今日已更新")},
            "报退款率": int(cs["报退款率"]),
            "商品榜": [dict(r, 短名=底子.duanming(r["商品"])) for r in (ht.get("商品榜") or [])[: int(cs["报里每张表最多行"])]],
            "待办": dai, "联盟": ht.get("联盟") or {}, "载体": ht.get("载体") or {},
            "员工": yuangong(hz), "回执": {k: (v if v and "_坏" not in v else None) for k, v in hz.items()},
            "要管": [{"级": a, "事": b, "出处": c} for a, b, c in yao],
            "没取到": (ht.get("没取到") or []) if ht else ["后台数没取到（这个时段没读到后台）"],
            "出处": ht.get("出处") or {}, "用了默认值": [x for x in mo if x in ("成本_占定价", "运费_每单")]}
    if xie:
        p = dp / "掌柜" / "快照" / f"{day}-{shiduan}.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap
