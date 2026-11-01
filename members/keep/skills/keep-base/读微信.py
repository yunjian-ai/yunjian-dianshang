"""掌柜 · 读微信：把存下来的微信小店后台页面文字（首页、商品数据、合作管理）变成一份 微信数.json（全部只读，路线卡 M-KP-004）。
用法：python3 读微信.py <文件夹> --店铺 <店铺文件夹名，如 微信小店-阿青> [--后台店名 <首页店名>] [--记录时间 "2026-11-10 11:48"] [--出 <微信数.json>]
文件夹里放：微信首页.txt、微信商品.txt、微信带货者.txt（整页快照里的字一行一个，第一行「@@URL 网址」；微信小店内容在内嵌框里，只能这样读）。
首页被跳到登录页、店名对不上、哪页没有，就写进「没取到」，不猜；读不到的数写 null。联系方式（微信号、手机号）一律不读不存。"""
import argparse, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import 底子

QIAN = re.compile(r"^[¥￥]\s*(-?[\d,]+(?:\.\d+)?)$")
SHU = re.compile(r"^-?[\d,]+(?:\.\d+)?$")


def qian(s):
    m = QIAN.match((s or "").strip())
    return float(m.group(1).replace(",", "")) if m else None


def hang(t):
    L = [x.strip() for x in (t or "").splitlines() if x.strip()]
    url = L[0][7:].strip() if L and L[0].startswith("@@URL ") else ""
    return url, (L[1:] if url else L)


def hou(L, biaoqian, pan, chang=4):
    """标签后面 chang 个字里第一个合 pan 的。"""
    if biaoqian not in L:
        return None
    i = L.index(biaoqian)
    for x in L[i + 1:i + 1 + chang]:
        v = pan(x)
        if v is not None:
            return v
    return None


def du_shouye(t):
    url, L = hang(t)
    if url and "/shop/home" not in url:
        return None, None, None, "微信小店首页被跳走（多半没登录，请主人在 ego 里扫码）"
    shuzi = lambda x: float(x.replace(",", "")) if SHU.match(x) else None
    zhi = {"成交金额": hou(L, "成交金额", qian), "成交订单数": hou(L, "成交订单数", shuzi), "成交人数": hou(L, "成交人数", shuzi),
           "体验分": hou(L, "店铺体验分", shuzi)}
    gx = next((x.replace("更新于", "").strip() for x in L if x.startswith("更新于")), None)
    i = L.index("店铺体验分") if "店铺体验分" in L else -1
    dian = L[i - 2] if i >= 2 and L[i - 1] == "分享" else None   # 首页右边「<店名>｜分享｜店铺体验分」
    return zhi, gx, dian, None


def du_shangpin(t, n=5):
    """商品数据「重点关注优秀商品 · 成交金额高」：每款「名字｜￥价格｜￥成交金额｜较上周期｜涨跌」，第 4 款起前面有序号。"""
    _, L = hang(t)
    fw = next((x.replace("统计时间", "").strip() for x in L if x.startswith("统计时间")), None)
    if "成交金额高" not in L:
        return [], fw
    s, e = L.index("成交金额高") + 1, (L.index("成交件数高") if "成交件数高" in L else len(L))
    rows, i = [], s
    while i < e and len(rows) < n:
        if qian(L[i]) is None and not SHU.match(L[i]) and L[i] != "较上周期" and not re.match(r"^[+-]?[\d.]+%$", L[i]):
            ms = [qian(x) for x in L[i + 1:i + 3]]
            if None not in ms:
                rows.append({"商品": L[i], "成交金额": ms[1]})
                i += 3; continue
        i += 1
    return rows, fw


def du_daihuo(t, n=5):
    """合作管理 · 带货者管理：一位一段，到「详情」为止——昵称｜标签｜ID｜…｜¥累计销售额｜¥近30日销售额｜累计订单｜近30日订单…。按近 30 日销售额排、只留卖过的。"""
    _, L = hang(t)
    s = max((i for i, x in enumerate(L) if x == "操作"), default=-1) + 1
    rows, buf = [], []
    for x in L[s:]:
        if x == "详情":
            qs = [qian(y) for y in buf if qian(y) is not None]
            if buf and len(qs) >= 2:
                rows.append({"达人": buf[0], "近30日销售额": qs[1], "累计销售额": qs[0]})
            buf = []
        else:
            buf.append(x)
    rows = sorted((r for r in rows if r["近30日销售额"] > 0), key=lambda r: -r["近30日销售额"])
    return rows[:n]


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("文件夹"); a.add_argument("--店铺", required=True)
    a.add_argument("--后台店名"); a.add_argument("--记录时间"); a.add_argument("--出")
    a = a.parse_args(argv)
    d = pathlib.Path(a.文件夹)
    rd = lambda n: (d / n).read_text(encoding="utf-8") if (d / n).exists() else None
    m = re.search(r"(\d{4}-\d{2}-\d{2})/(\d{2})(\d{2})/?$", str(d.resolve()))
    jl = a.记录时间 or (f"{m.group(1)} {m.group(2)}:{m.group(3)}" if m else 底子.xianzai().strftime("%Y-%m-%d %H:%M"))
    out = {"店铺": a.店铺, "平台": "微信小店", "记录时间": jl, "实时": {}, "体验分": None, "商品榜": [], "达人榜": [], "合作消息": None,
           "出处": {"实时": "微信小店·首页·经营数据·今天", "体验分": "微信小店·首页·店铺体验分（满分 5）", "合作消息": "微信小店后台没有带货者消息列表（11-01 实地摸清）"},
           "没取到": []}
    sy = rd("微信首页.txt")
    if sy:
        zhi, gx, dian, cuo = du_shouye(sy)
        if cuo:
            out["没取到"].append(cuo)
        else:
            yao = a.后台店名
            if not yao:
                try:
                    yao = json.loads((底子.dianpu(a.店铺) / "掌柜" / "店铺档案.json").read_text(encoding="utf-8")).get("后台店名")
                except (OSError, ValueError, SystemExit):
                    yao = None
            if dian and yao and yao not in dian and dian not in yao:
                out["没取到"].append(f"首页店名是「{dian}」，不是这家店（{yao}），这份不算")
            else:
                out["实时"] = {k: v for k, v in zhi.items() if k != "体验分"}
                out["体验分"] = zhi["体验分"]
                out["后台店名"] = dian
                if gx:
                    out["出处"]["实时"] += f"·更新于 {gx}"
    else:
        out["没取到"].append("微信首页没取到")
    sp = rd("微信商品.txt")
    if sp:
        out["商品榜"], fw = du_shangpin(sp)
        out["出处"]["商品榜"] = "微信小店·店铺数据·商品数据·成交金额高" + (f"（{fw}）" if fw else "")
    else:
        out["没取到"].append("商品数据没取到")
    dh = rd("微信带货者.txt")
    if dh:
        out["达人榜"] = du_daihuo(dh)
        out["出处"]["达人榜"] = "微信小店·优选联盟·合作管理·带货者管理（第 1 页，近 30 日销售额）"
    else:
        out["没取到"].append("带货者没取到")
    p = pathlib.Path(a.出) if a.出 else d / "微信数.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    ss = out["实时"]
    print(f"{a.店铺} {jl}：成交 {底子.yuan(ss.get('成交金额'))}，订单 {ss.get('成交订单数')}，体验分 {out['体验分']}；商品榜 {len(out['商品榜'])} 款、带货达人 {len(out['达人榜'])} 位"
          + (f"；没取到：{'、'.join(out['没取到'])}" if out["没取到"] else ""))
    print("已存", p)


if __name__ == "__main__":
    main()
