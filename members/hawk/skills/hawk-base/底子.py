"""货郎各脚本共用的小工具：家目录、店铺文件夹、参数（决策库盖默认值）、卡片开头段、区间档解析、夹带检查。
别的脚本这样引：import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "hawk-base")); import 底子"""
import json, os, pathlib, re

HOME = pathlib.Path(os.environ.get("HAWK_HOME", pathlib.Path.home() / ".yunjian" / "hawk"))
KU = HOME / "库"


def dianpu_gen():
    """店铺根目录：有四位共用的 ~/.yunjian/店铺/ 就用它（一家店一个文件夹、一份经营决策库、掌柜从这里汇总），没有就用自己的 <HOME>/店铺/（只装这一位时）。"""
    g = HOME.parent / "店铺"
    return g if g.is_dir() else HOME / "店铺"


def dianpu(ming=None):
    """店铺文件夹：给了店名就是 店铺/<店名>，给的是路径（带 / 或 ~）照路径；没给就用 店铺/ 下唯一的一家（不止一家要主人说是哪家）。"""
    d = dianpu_gen()
    if ming:
        m = str(ming)
        return pathlib.Path(m).expanduser() if ("/" in m or m.startswith("~")) else d / m
    xs = [p for p in d.iterdir() if p.is_dir()] if d.exists() else []
    if len(xs) != 1:
        raise SystemExit(f"不知道是哪家店：{d} 下有 {len(xs)} 家，用 --店铺 指定")
    return xs[0]


def kaitou(p):
    """读卡片开头 --- 之间的「键: 值」（一层，参数下面缩进的两格也读进「参数」）。"""
    t = pathlib.Path(p).read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---", t, re.S)
    out, cs = {}, None
    for line in (m.group(1).splitlines() if m else []):
        if line.startswith("  ") and cs is not None:
            k, _, v = line.strip().partition(":")
            out.setdefault("参数", {})[k.strip()] = v.split("#")[0].strip()
        elif ":" in line:
            k, _, v = line.partition(":")
            k = k.strip(); cs = k if k == "参数" else None
            if k != "参数":
                out[k] = v.split("#")[0].strip()
    return out


def moren_canshu(ku=None):
    """默认值/选品上架-服装店.md 里的 json 参数块。"""
    t = ((ku or KU) / "默认值" / "选品上架-服装店.md").read_text(encoding="utf-8")
    return json.loads(re.search(r"```json\n(.*?)\n```", t, re.S).group(1))


def canshu(dp=None, ku=None):
    """参数：服装店默认值，再用店铺经营决策库里「状态: 生效」的卡盖掉同名参数。返回（参数, 用了默认值的名字）。"""
    cs = moren_canshu(ku)
    gai = set()
    if not dp:   # 没指定店铺：只有一家就用它，免得主人定的规矩被默认值盖住（经纪 Bot 实测 10-31 同类）
        try:
            dp = dianpu()
        except SystemExit:
            dp = None
    jc = dianpu(dp) / "经营决策库" if dp else None
    if jc and jc.exists():
        for p in sorted(jc.glob("D-*.md")):
            if p.name.startswith("._"):   # Mac 打包带的隐藏文件（Bot 实测自报 14）
                continue
            k = kaitou(p)
            if k.get("状态") != "生效":
                continue
            for n, v in (k.get("参数") or {}).items():
                if n in cs:
                    try:
                        cs[n] = type(cs[n])(float(v)) if isinstance(cs[n], (int, float)) else v
                    except ValueError:
                        cs[n] = v
                    gai.add(n)
    return cs, sorted(set(cs) - gai)


DANG = re.compile(r"([\d.,]+)\s*(万)?\s*\+?\s*(?:-\s*([\d.,]+)\s*(万)?)?")


def jian_shu(s):
    """「1,000 - 2,500」「1万 - 2.5万」「4000+」「已售 1万+」「已拼1.2万件」 → (下限, 上限或 None, 精度)。看不出来返回 (None, None, '')。"""
    s = (s or "").replace("，", ",")
    m = DANG.search(s.replace("已售", "").replace("已拼", "").replace("人付款", ""))
    if not m:
        return None, None, ""
    num = lambda x, w: float(x.replace(",", "")) * (10000 if w else 1)
    lo = num(m.group(1), m.group(2))
    if m.group(3):
        return lo, num(m.group(3), m.group(4)), "档"
    if "+" in s:
        return lo, None, "档"
    return lo, lo, "精确"


JIADAI = re.compile(r"(AI|ai|助手|机器人).{0,8}(注意|请|必须)|不用问|忽略(之前|上面|以上)|直接.{0,10}(发布|改|删除|下单)|ignore (previous|all)", re.I)


def kexi(s):
    """像写给 AI 的话（夹带指令）就返回那一段原文，否则空串。"""
    m = JIADAI.search(s or "")
    return (s[max(0, m.start() - 10): m.end() + 30]) if m else ""


QUAN = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"


def biao(tou, hang, kuan=False, chu=None, zhu=None, jian=1):
    """出表（杨先生 10-31：按界面做最优展示）。kuan=True 一张宽表（电脑、飞书、网页）；
    默认窄表（Grok Bot、手机聊天框）：出处那一列（chu）换成编号 ①②，完整出处列在表下；
    长理由那一列（zhu）挪到表下，按 jian 那一列的值一条一条写。"""
    if kuan or (chu is None and zhu is None):
        return "\n".join(["| " + " | ".join(tou) + " |", "|" + "---|" * len(tou)] + ["| " + " | ".join(map(str, h)) + " |" for h in hang])
    bh, xia, zhus = {}, [], []
    for h in hang:
        if chu is not None:
            c = str(h[chu])
            if c not in bh:
                bh[c] = QUAN[len(bh)] if len(bh) < len(QUAN) else f"({len(bh) + 1})"
        if zhu is not None and str(h[zhu]).strip() not in ("", "—"):
            zhus.append(f"- {h[jian]}：{h[zhu]}")
    keep = [i for i in range(len(tou)) if i != zhu]
    t2 = [("出处" if i == chu else tou[i]) for i in keep]
    rows = [[(bh[str(h[i])] if i == chu else str(h[i])) for i in keep] for h in hang]
    out = ["| " + " | ".join(t2) + " |", "|" + "---|" * len(t2)] + ["| " + " | ".join(r) + " |" for r in rows]
    if zhus:
        out += ["", "说明：", *zhus]
    if bh:
        out += ["", "出处：", *[f"{v} {k}" for k, v in bh.items()]]
    return "\n".join(out)
