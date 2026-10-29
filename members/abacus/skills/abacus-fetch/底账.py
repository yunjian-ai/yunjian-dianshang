"""算盘公共小工具：读抖店导出的表、读三本账的参数、找主人的店铺文件夹。只用标准库。别的技能用：
  import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "abacus-fetch")); import 底账"""
import csv, io, os, pathlib, re

HOME = pathlib.Path(os.environ.get("ABACUS_HOME", pathlib.Path.home() / ".yunjian" / "abacus"))
KU = HOME / "库"

# 四种表：认表靠表头里一定有的列
BIAO = {"结算账单": ("结算金额", "收入合计", "结算单类型"), "资金账单": ("动账场景", "动账金额", "动账方向"),
        "订单表": ("子订单编号", "订单状态", "售后状态"), "待结算": ("预计结算金额", "预计结算时间")}
# 订单表只留这 25 列（抖店订单「自定义报表」照这个勾）；收件人信息一律不留
DINGDAN_LIE = ["主订单编号", "子订单编号", "选购商品", "商品ID", "商品数量", "商品金额", "订单提交时间", "支付完成时间", "订单完成时间",
               "订单状态", "售后状态", "订单类型", "是否属于寄样订单", "发货时间", "订单应付金额", "运费", "商家收入金额", "达人ID", "达人昵称",
               "流量来源", "仓库名称", "流量渠道", "是否是渠道商品", "渠道商品ID", "渠道商品类型"]
YINSI = ("收件人", "手机", "电话", "详细地址", "街道", "身份证", "买家昵称", "买家留言")

# 账单的备注、说明里夹带的「指令」：碰到这些字就报给主人，不照做（考题 K13、Bot 实测 10-29）
JIADAI = ("算盘", "请把", "不用告诉", "不要告诉", "忽略", "直接改", "记成", "http://", "https://", "AI ")

def jiadai(shu):
    """返回 [(第几行, 列名, 原话)]：备注类列里像是写给 AI 的话。"""
    out = []
    for i, r in enumerate(shu, 2):
        for k, v in r.items():
            if ("备注" in k or "说明" in k or "留言" in k) and v and any(w in v for w in JIADAI):
                out.append((i, k, v[:120]))
    return out

def du_wenben(p):
    b = pathlib.Path(p).read_bytes()
    for enc in ("utf-8-sig", "gb18030"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            pass
    raise ValueError(f"认不出编码：{p}")

def qing(v):
    """去掉抖店给长数字加的英文单引号、制表符和首尾空白。"""
    return (v or "").strip().lstrip("'").lstrip("\t").strip()

def ren_biao(tou):
    tou = set(tou)
    for ming, bi in BIAO.items():
        if all(x in tou for x in bi):
            return ming
    return None

def du_biao(p):
    """读一张抖店导出的表 → (哪种表, 表头, [每行字典])。跳过第 2 行那种公式说明（第一格不是日期也不是编号的行）。"""
    rows = list(csv.reader(io.StringIO(du_wenben(p))))
    tou = [qing(x) for x in rows[0]]
    ming = ren_biao(tou)
    shu = []
    for r in rows[1:]:
        if len(r) != len(tou):
            continue
        d = {k: qing(v) for k, v in zip(tou, r)}
        di = d[tou[0]]
        if not di or not (re.match(r"^\d{4}-\d{2}-\d{2}", di) or re.match(r"^\d{6,}$", di)):
            continue  # 公式说明行、空行
        shu.append(d)
    return ming, tou, shu

def xie_biao(p, tou, shu):
    p = pathlib.Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=tou, extrasaction="ignore"); w.writeheader(); w.writerows(shu)

CHONG = []  # can_shu 读到的「同一编号两张生效卡」，算账写进汇总、对账拦

def can_shu(*mulu):
    """读卡片开头「参数:」下的 键: 值，只认「状态: 生效」的卡；后面的目录覆盖前面的（决策库盖默认值）。返回 (参数, {键: 卡编号})"""
    out, laiyuan, bianhao = {}, {}, {}
    CHONG.clear()
    for m in mulu:
        if not m or not pathlib.Path(m).is_dir():
            continue
        for p in sorted(pathlib.Path(m).glob("[RD]-*.md")):
            s = p.read_text(encoding="utf-8")
            if not re.search(r"^状态: 生效", s, re.M):
                continue
            bh = (re.search(r"^编号: (\S+)", s, re.M) or [None, p.stem])[1]
            if bh in bianhao and bianhao[bh] != p:
                CHONG.append(f"{bh}：{bianhao[bh].name} 和 {p.name} 都是「生效」，旧的那张要改「已停用」")
            bianhao[bh] = p
            g = re.search(r"^参数:\n((?:  .*\n)*)", s, re.M)
            for line in (g.group(1).splitlines() if g else []):
                k, _, v = line.strip().partition(":")
                v = v.split("#")[0].strip()
                try:
                    v = float(v)
                except ValueError:
                    pass
                out[k.strip()] = v; laiyuan[k.strip()] = bh
    return out, laiyuan

def dianpu(ming=None):
    """主人的店铺文件夹：~/.yunjian/abacus/店铺/<店名>；只有一家时不用给店名。"""
    base = HOME / "店铺"
    if ming:
        return base / ming
    ds = [d for d in base.iterdir() if d.is_dir()] if base.is_dir() else []
    if len(ds) == 1:
        return ds[0]
    raise SystemExit("有几家店或还没建店铺文件夹，请用 --店铺 指定（abacus-getting-started 会建）")
