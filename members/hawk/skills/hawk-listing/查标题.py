"""货郎 · 查标题：标题 → 字数、禁用泛称、不同品类堆砌、拼音字母代替、材质词含量（R-SP-001、R-SP-006）
用法：python3 查标题.py "<标题>" [--成分 "棉75% 羊毛20% 聚酯纤维5%"]   不过退出码 1
也给 查草稿包.py 调用：import 查标题; 查标题.cha(标题, 成分)"""
import argparse, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "hawk-base")); import 底子

FAN = ["孤品", "链接", "秒杀", "福利款", "捡漏"]   # 直播间口令，标题里一律不许
FAN_ZHU = ["好物", "百货"]                           # 泛称：标题里没有商品主体（品类词）时才算违规，有主体只提醒
PINLEI = [["卫衣", "T恤", "衬衫", "毛衣", "针织衫", "开衫", "外套", "羽绒服", "大衣", "风衣", "马甲", "连衣裙"], ["裤", "半身裙"]]
CAI = {"羊绒": ("羊绒", 30), "羊毛": ("羊毛", 30), "羽绒": ("绒", 50), "蚕丝": ("蚕丝", 30)}


def han(s):
    """按汉字算：一个字母或数字算半个。"""
    return sum(1 if '一' <= c <= '鿿' else 0.5 for c in s if not c.isspace())


def hanliang(cf, ci):
    m = re.search(ci + r"\s*([\d.]+)\s*%", cf or "")
    return float(m.group(1)) if m else None


def cha(bt, cf=None, cs=None):
    cs = cs or 底子.moren_canshu()
    cuo = []
    n = han(bt)
    if n < cs["标题字数下限"] or n > cs["标题字数上限"]:
        cuo.append(f"标题 {n:g} 个汉字，要 {cs['标题字数下限']}～{cs['标题字数上限']}（R-SP-001）")
    shang = any(p in bt for p in PINLEI[0]); xia = any(p in bt for p in PINLEI[1])
    zhuti = shang or xia or any(p in bt for p in ["打底衫", "内搭", "T恤", "套装", "裙"])
    for f in FAN:
        if f in bt:
            cuo.append(f"标题有「{f}」，不许（R-SP-001）")
    for f in FAN_ZHU:
        if f in bt:
            cuo.append(f"提醒：标题有泛称「{f}」，建议去掉（有商品主体，不算违规；R-SP-001）" if zhuti else f"标题用「{f}」代替商品主体，不许（R-SP-001）")
    if shang and xia and "套装" not in bt:
        cuo.append("上装和下装堆在一个标题里（不同品类堆砌，R-SP-001）")
    if re.search(r"[一-鿿][A-Za-z]{1,3}[一-鿿]|[一-鿿]\d[一-鿿]", bt):
        cuo.append("疑似用字母或数字代替汉字（R-SP-001），核一下")
    for ci, (cfci, xian) in CAI.items():
        if ci in bt:
            v = hanliang(cf, cfci)
            if cf is None:
                cuo.append(f"待核：标题写了「{ci}」，没给面料成分，核一下{cfci}含量是否 ≥{xian}%（R-SP-006）")
            elif v is None:
                cuo.append(f"标题写了「{ci}」，成分里查不到{cfci}含量，不能写（R-SP-006）")
            elif v < xian:
                cuo.append(f"标题写了「{ci}」，实际 {cfci} {v:g}% < {xian}%，不能写（R-SP-006）")
    return cuo


if __name__ == "__main__":
    a = argparse.ArgumentParser(); a.add_argument("标题"); a.add_argument("--成分")
    a = a.parse_args()
    c = cha(a.标题, a.成分)
    lan = [x for x in c if not x.startswith(("提醒", "待核"))]
    print("标题 OK" if not c else ("标题不过：\n" if lan else "标题能用，有几处要看：\n") + "\n".join("- " + x for x in c))
    raise SystemExit(1 if lan else 0)
