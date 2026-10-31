"""掌柜 · 读页面：把存下来的后台页面文字（首页、商家体验分、合作消息）变成一份 后台数.json（格式见 库/模板/后台数格式.json）。
用法：python3 读页面.py <文件夹> --店铺 <店铺文件夹名，如 抖店-A> [--后台店名 <后台右上显示的店名>] [--记录时间 "2026-11-10 11:48"] [--出 <后台数.json>]
后台店名不给：读店铺文件夹里 掌柜/店铺档案.json 的「后台店名」；档案里还没有就把这次看到的记下来（第一次），以后对不上整份作废。
文件夹里放：首页.txt＋首页-涨跌.json、体验分.txt＋体验分-涨跌.json、合作消息.json（可选，[{"达人","最后一句","时间"}]）。
涨跌.json 是页面上「较昨日／较前1日」箭头的方向，按页面顺序：[{"值": "43.94%", "方向": "down"}]（路线卡 M-KP-001、M-KP-002）。
页面文字里只有百分比、没有正负号，方向只认涨跌.json；对不上就写 null，不猜。缺哪个文件，那块进「没取到」。"""
import argparse, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import 底子

NUM = re.compile(r"^[¥￥]?\s*(-?[\d,]+(?:\.\d+)?)\s*(万)?$")
PCT = re.compile(r"^(-?[\d.]+)\s*%$")


def shu(s):
    m = NUM.match((s or "").strip())
    if not m:
        return None
    v = float(m.group(1).replace(",", ""))
    return v * 10000 if m.group(2) else v


class Qushi:
    """按页面顺序消费涨跌箭头：值对得上才用，方向 up→正、down→负，没有箭头（持平）→0。"""
    def __init__(self, xs):
        self.xs, self.yong = list(xs or []), set()

    def na(self, zhi):
        for j, x in enumerate(self.xs):
            v = str(x.get("值", "")).strip()
            if j not in self.yong and (v == zhi or v.endswith(zhi)):
                self.yong.add(j)
                return {"up": 1, "down": -1}.get(x.get("方向", ""), 0)
        return None


def jiao(lines, i, qs, biaoqian="较昨日", chang=12):
    """从第 i 行往后找「较昨日」后面的百分比或持平，返回带符号小数；找不到 None。"""
    for k in range(i, min(i + chang, len(lines))):
        if lines[k].startswith(biaoqian):
            nxt = lines[k + 1].strip() if k + 1 < len(lines) else ""
            if nxt == "持平":
                return 0.0
            m = PCT.match(nxt) or re.match(r"^(-?[\d.]+)$", nxt)
            if not m:
                return None
            fx = qs.na(nxt)
            if fx is None:
                return None
            v = float(m.group(1))
            return fx * (v / 100 if nxt.endswith("%") else v)
    return None


def zhi_hou(lines, i, chang=6, tiao=("¥", "￥", "构成", "支付时间", "退款时间", "退款时…", "支付时…", "分")):
    for k in range(i + 1, min(i + 1 + chang, len(lines))):
        t = lines[k].strip()
        if t in tiao or not t:
            continue
        v = shu(t)
        if v is not None:
            return v, k
        return None, k
    return None, i


SHISHI = [("成交金额", "成交金额", None), ("成交订单数", "成交订单数", None), ("支出金额", "支出金额", None),
          ("退款金额", "退款金额_支付时间", "支付时间"), ("退款金额", "退款金额_退款时间", "退款时间"),
          ("商品曝光人数", "商品曝光人数", None), ("商品点击人数", "商品点击人数", None), ("成交人数", "成交人数", None),
          ("用户支付金额", "用户支付金额", None), ("客单价", "客单价", None), ("结算金额", "结算金额", None),
          ("退款订单数", "退款订单数_退款时间", "退款时"), ("退款订单数", "退款订单数_支付时间", "支付时")]
DAIBAN = ["待支付", "待发货", "异常包裹", "待处理售后", "服务工单", "待整改风险点", "待处理违规"]


def du_shouye(t, qs):
    L = [x.strip() for x in t.splitlines()]
    s0 = next((i for i, x in enumerate(L) if x == "实时"), 0)
    shishi, yong = {}, set()
    for lab, key, sub in SHISHI:
        for i in range(s0, len(L)):
            if L[i] != lab or i in yong:
                continue
            if sub and not (i + 1 < len(L) and L[i + 1].startswith(sub)):
                continue
            if not sub and i + 1 < len(L) and L[i + 1] in ("支付时间", "退款时间", "退款时…", "支付时…"):
                continue
            v, k = zhi_hou(L, i)
            if v is None:
                continue
            yong.add(i)
            shishi[key] = {"值": v, "较昨日": jiao(L, k + 1, qs, chang=5)}
            break
    m = re.search(r"退款率\(支付时间\)\s*([\d.]+)%", t)
    if m:
        shishi["退款率_支付时间"] = {"值": float(m.group(1)) / 100, "较昨日": None}
    daiban = {}
    for lab in DAIBAN:
        if lab in L:
            i = L.index(lab)
            if i + 1 < len(L) and re.fullmatch(r"\d+", L[i + 1]):
                daiban[lab] = int(L[i + 1])
    lianmeng = {}
    for lab in ("近7日达人成交金额", "近7日合作达人数"):
        if lab in L:
            v, _ = zhi_hou(L, L.index(lab))
            lianmeng[lab] = v
    dian = next((L[i] for i in range(len(L) - 1) if L[i + 1] in ("企业店", "个体店", "旗舰店", "专营店", "专卖店") and L[i]), None)
    return shishi, daiban, lianmeng, dian


def du_tiyan(t, qs):
    L = [x.strip() for x in t.splitlines()]
    out = {"总分": None, "更新时间": None, "今日已更新": None, "分项": {}, "短板": None, "保障": None}
    m = re.search(r"更新时间[：:]\s*([\d-]+ [\d:]+)(（今日待更新）)?", t)
    if m:
        out["更新时间"], out["今日已更新"] = m.group(1), not bool(m.group(2))
    if "我的总分" in L:
        i = L.index("我的总分")
        v, k = zhi_hou(L, i)
        out["总分"] = v
        out["较前1日"] = jiao(L, k + 1, qs, "较前1日", 5)
        s0 = k
    else:
        s0 = 0
    for lab, key in (("商品体验", "商品"), ("物流体验", "物流"), ("服务体验", "服务"), ("加分项", "加分"), ("扣分项", "扣分")):
        for i in range(s0, len(L)):
            if L[i] == lab:
                v, k = zhi_hou(L, i, chang=4, tiao=("¥", "分", "单独计算加分", "单独计算扣分") + tuple(x for x in L[i + 1:i + 2] if x.endswith("权重")))
                if v is None:
                    continue
                out["分项"][key] = {"分": v, "较前1日": jiao(L, k + 1, qs, "较前1日", 6)}
                break
    m = re.search(r"主要短板\s*(.+)", t)
    if m:
        out["短板"] = 底子.zhaiju(m.group(1).replace("当前主要短板", "").strip(), 60)
    if "只涨不跌" in t:
        m = re.search(r"保障最长至\s*([^\s，,。]+)", t)
        out["保障"] = "物流分只涨不跌" + (f"（保障至 {m.group(1)}）" if m else "（大促保障期）")
    return out


LUOPAN = [("成交金额", "成交金额"), ("用户支付金额", "用户支付金额"), ("结算金额", "结算金额"), ("成交订单数", "成交订单数"),
          ("商品曝光人数", "商品曝光人数"), ("商品点击人数", "商品点击人数"), ("客单价", "客单价"), ("成交人数", "成交人数"),
          ("退款金额（退款时间）", "退款金额_退款时间"), ("退款金额（支付时间）", "退款金额_支付时间"), ("退款订单数（退款时间）", "退款订单数_退款时间"),
          ("退款订单数（支付时间）", "退款订单数_支付时间"), ("达人佣金（预估口径）", "达人佣金_预估"), ("平台佣金（预估口径）", "平台佣金_预估")]


def zhi_lianxu(L, i, chang=4):
    """罗盘的数会被拆成几行（¥｜8,480｜.｜63），拼回去。返回 (值, 下一个下标)。"""
    buf, k = "", i
    while k < min(i + chang, len(L)):
        t = L[k].strip()
        if t in ("¥", "￥") and not buf:
            k += 1; continue
        if re.fullmatch(r"[\d,]+|\.|\d+|[\d,]+\.\d+|[¥￥][\d,]+(\.\d+)?|万|%", t):
            buf += t; k += 1
            if re.fullmatch(r"[¥￥]?[\d,]+\.\d+(万)?|[¥￥]?[\d,]+万", buf):
                break
            continue
        break
    buf = buf.replace("¥", "").replace("￥", "").replace("%", "")
    return shu(buf), k


def du_luopan(t):
    """罗盘首页「经营概况 · 实时」：每项「值｜昨日｜昨日值」；另有达人佣金、平台佣金（预估口径）和载体分布。"""
    L = [x.strip() for x in t.splitlines() if x.strip()]
    out = {}
    for lab, key in LUOPAN:
        if key in out or lab not in L:
            continue
        i = L.index(lab)
        v, k = zhi_lianxu(L, i + 1)
        if v is None:
            continue
        zr = None
        if k < len(L) and L[k] == "昨日":
            zr, _ = zhi_lianxu(L, k + 1)
        out[key] = {"值": v, "昨日": zr, "较昨日": (v / zr - 1) if zr else None}
    m = re.search(r"退款率（支付时间）\s*([\d.]+)%\s*昨日\s*([\d.]+)\s*%", " ".join(L))
    if m:
        out["退款率_支付时间"] = {"值": float(m.group(1)) / 100, "昨日": float(m.group(2)) / 100, "较昨日": None}
    zaiti = {}
    for lab in ("商品卡", "直播", "短视频", "图文"):
        for i, x in enumerate(L[:-2]):
            if x == lab and re.fullmatch(r"\(([\d.]+)%\)", L[i + 1]):
                zaiti[lab] = float(L[i + 1][1:-2]) / 100
                break
    return out, zaiti


def du_shangpin(t, n=20):
    """罗盘商品列表（实时、全店成交 TOP）：每个商品一行——序号｜商品名｜载体贡献｜各列「值｜昨日｜昨日值」。"""
    L = [x.strip() for x in t.splitlines() if x.strip()]
    s0 = max((i for i, x in enumerate(L) if x == "操作"), default=0)
    rows, i = [], s0 + 1
    while i < len(L) and len(rows) < n:
        nxt = L[i + 1] if i + 1 < len(L) else ""
        if L[i] == str(len(rows) + 1) and len(nxt) >= 6 and re.search(r"[\u4e00-\u9fff]", nxt) and nxt not in ("昨日", "看详情", "SKU明细"):
            ming, tie = L[i + 1], ""
            j = i + 2
            if j < len(L) and "贡献" in L[j]:
                tie = L[j]; j += 1
            vals = []
            while j < len(L) and L[j] not in ("看详情", "SKU明细") and len(vals) < 9:
                if L[j] == "昨日":
                    j += 2; continue
                v = shu(L[j].replace("¥", "").replace("￥", "")) if re.fullmatch(r"[¥￥]?[\d,]+(\.\d+)?(万)?", L[j]) else None
                if v is not None:
                    vals.append(v)
                j += 1
            if len(vals) >= 7:
                rows.append({"商品": ming, "主要载体": tie, "成交金额": vals[2], "成交订单数": vals[3], "退款金额": vals[5], "退款订单数": vals[6]})
            i = j
        else:
            i += 1
    return rows


SHIJIAN = re.compile(r"^(\d{1,2}:\d{2}|昨天|前天|星期[一二三四五六日天]|\d{1,2}/\d{1,2}|\d{4}-\d{2}-\d{2})$")


def du_xiaoxi(t):
    """合作消息页左栏：「达人昵称｜最后一句｜时间」三个一组（M-BY-003 第 3 步）；顶上读 7 日回复率、建联额度。"""
    L = [x.strip() for x in t.splitlines() if x.strip()]
    tou = {}
    for lab in ("7日回复率", "建联额度"):
        if lab in L and L.index(lab) + 1 < len(L):
            tou[lab] = L[L.index(lab) + 1]
    s0 = L.index("我接收的") + 1 if "我接收的" in L else 0
    xs, buf = [], []
    for x in L[s0:]:
        if x in ("7天前的消息", "没有更多了", "加载更多"):
            continue
        if SHIJIAN.match(x) and len(buf) >= 2:
            xs.append({"达人": buf[-2], "最后一句": buf[-1], "时间": x})
            buf = []
        else:
            buf.append(x)
    return xs, tou


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("文件夹"); a.add_argument("--店铺", required=True)
    a.add_argument("--后台店名"); a.add_argument("--记录时间"); a.add_argument("--出")
    a = a.parse_args(argv)
    d = pathlib.Path(a.文件夹)
    rd = lambda n: (d / n).read_text(encoding="utf-8") if (d / n).exists() else None
    rj = lambda n: json.loads((d / n).read_text(encoding="utf-8")) if (d / n).exists() else []
    import datetime as dt
    m = re.search(r"(\d{4}-\d{2}-\d{2})/(\d{2})(\d{2})/?$", str(d.resolve()))
    jl = a.记录时间 or (f"{m.group(1)} {m.group(2)}:{m.group(3)}" if m else dt.datetime.now().strftime("%Y-%m-%d %H:%M"))   # 不给就用文件夹名（<日期>/<时刻>）
    out = {"店铺": a.店铺, "记录时间": jl,
           "出处": {"实时": "抖店首页·经营数据·实时（R-KP-002）", "体验分": "抖店·商家体验分页（R-KP-001）", "合作消息": "精选联盟·合作消息（M-BY-003）"},
           "实时": {}, "待办": {}, "联盟": {}, "体验分": {"总分": None}, "合作消息": [], "没取到": []}
    sy = rd("首页.txt")
    if sy:
        out["实时"], out["待办"], out["联盟"], dian = du_shouye(sy, Qushi(rj("首页-涨跌.json")))
        dang = None   # 店铺档案：第一次记下后台店名，以后对不上整份作废（读错店）
        try:
            dp = 底子.dianpu(a.店铺)
            dang = dp / "掌柜" / "店铺档案.json"
            dangan = json.loads(dang.read_text(encoding="utf-8")) if dang.exists() else {}
        except SystemExit:
            dangan = {}
        yao = a.后台店名 or dangan.get("后台店名")
        if dian and yao and yao not in dian and dian not in yao:
            out["没取到"].append(f"首页右上是「{dian}」，不是这家店（{yao}），这份不算")
            out["实时"], out["待办"], out["联盟"] = {}, {}, {}
        elif dian and dang is not None and not dangan.get("后台店名"):   # 第一次（给了 --后台店名 且对得上也记）
            dang.parent.mkdir(parents=True, exist_ok=True)
            dang.write_text(json.dumps({**dangan, "后台店名": dian}, ensure_ascii=False, indent=1), encoding="utf-8")
        out["后台店名"] = dian
        if not out["实时"] and not out["没取到"] and not rd("罗盘首页.txt"):
            out["没取到"].append("首页实时数据认不出（页面改了？照 M-KP-002 自愈）")
    else:
        out["没取到"].append("首页没取到")
    lp = rd("罗盘首页.txt")
    if lp:
        ss, zaiti = du_luopan(lp)
        if ss:
            out["实时"].update(ss)   # 罗盘有「昨日」的绝对值，口径和首页一样，优先用
            out["出处"]["实时"] = "电商罗盘·首页·经营概况·实时（昨日为后台口径）"
            out["载体"] = zaiti
    hz = rd("罗盘首页-合作.txt")
    if hz:
        hss, _ = du_luopan(hz)
        if hss.get("成交金额"):
            out["实时"]["达人成交金额"] = hss["成交金额"]
    sp = rd("商品榜.txt")
    if sp:
        out["商品榜"] = du_shangpin(sp)
        out["出处"]["商品榜"] = "电商罗盘·商品列表·实时·全店成交TOP"
    ty = rd("体验分.txt")
    if ty:
        out["体验分"] = du_tiyan(ty, Qushi(rj("体验分-涨跌.json")))
        if out["体验分"]["总分"] is None:
            out["没取到"].append("体验分认不出（照 M-KP-001 自愈）")
    else:
        out["没取到"].append("体验分没取到")
    if (d / "合作消息.json").exists():
        out["合作消息"] = [{k: str(m.get(k, "")) for k in ("达人", "最后一句", "时间")} for m in rj("合作消息.json")]
    elif rd("合作消息.txt"):
        out["合作消息"], tou = du_xiaoxi(rd("合作消息.txt"))
        out["联盟"].update(tou)
    else:
        out["没取到"].append("合作消息没取到")
    p = pathlib.Path(a.出) if a.出 else d / "后台数.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    ss, ty = out["实时"], out["体验分"]
    print(f"{a.店铺} {out['记录时间']}：成交 {底子.yuan((ss.get('成交金额') or {}).get('值'))}，订单 {(ss.get('成交订单数') or {}).get('值')}，"
          f"店铺分 {ty.get('总分')}（更新 {ty.get('更新时间')}）；合作消息 {len(out['合作消息'])} 条" + (f"；没取到：{'、'.join(out['没取到'])}" if out["没取到"] else ""))
    print("已存", p)


if __name__ == "__main__":
    main()
