"""货郎 · 查草稿包：链接草稿包 → 两道自检（官方上架规范＋店铺链接标准）→ 能不能上
用法：python3 查草稿包.py <草稿包.json> [--店铺 <店铺文件夹>] [--联盟 <联盟现状.json>]   不过退出码 1，hawk-listing 不进上架
查：格式（草稿包.schema.json）、标题（查标题.py）、主图张数尺寸比例和第 1 张、规格写法、详情 4 样、商品信息 7 项。
也给验收用：import 查草稿包; 查草稿包.cha_tu(主图列表, 参数)"""
import argparse, json, pathlib, re, sys
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "hawk-base")); import 底子
sys.path.insert(0, str(HERE)); import 查标题

SC = json.loads((HERE / "草稿包.schema.json").read_text(encoding="utf-8"))
XQ = ["模特展示", "细节展示", "吊牌展示"]
XX = ["品牌", "品名", "号型规格", "成分含量", "执行标准", "洗涤护理", "安全类别"]
YAN = re.compile(r"(色|白|黑|灰|红|蓝|绿|黄|紫|粉|棕|咖|杏|米|卡其|藏青)")


def cha_tu(zt, cs, zhuang=None):
    cuo = []
    zhuang = zhuang or cs["主图张数"]
    if len(zt) < 3:
        cuo.append(f"主图只有 {len(zt)} 张，官方至少 3 张（R-SP-002）")
    elif len(zt) < zhuang:
        cuo.append(f"主图 {len(zt)} 张，店铺链接标准要 {zhuang} 张")
    for i, t in enumerate(zt, 1):
        if t["宽"] != t["高"]:
            cuo.append(f"第 {i} 张 {t['文件']} {t['宽']}×{t['高']} 不是 1:1（R-SP-002）")
        if min(t["宽"], t["高"]) < 600:
            cuo.append(f"第 {i} 张 {t['文件']} 小于 600×600（R-SP-002）")
        elif min(t["宽"], t["高"]) < cs["主图最小边"]:
            cuo.append(f"第 {i} 张 {t['文件']} 小于店铺标准 {cs['主图最小边']}")
    if zt and not re.search(r"正面.*实物|实物.*正面", zt[0].get("内容", "")):
        cuo.append("第 1 张要是正面全貌实物（R-SP-002）")
    return cuo


def cha(c, cs):
    cuo = []
    try:
        import jsonschema
        cuo += ["格式：" + e.message for e in jsonschema.Draft202012Validator(SC).iter_errors(c)]
    except ImportError:
        cuo += [f"格式：缺「{n}」" for n in SC["required"] if n not in c]
    cuo += 查标题.cha(c.get("标题", ""), c.get("属性", {}).get("面料成分"), cs)
    cuo += cha_tu(c.get("主图", []), cs)
    for g in c.get("规格", []):
        if g.get("名称") not in ("颜色", "尺寸", "尺码"):
            cuo.append(f"规格名「{g.get('名称')}」不规范，只用颜色、尺寸（R-SP-004）")
        if g.get("名称") == "颜色":
            bad = [v for v in g.get("值", []) if not YAN.search(v)]
            if bad and not g.get("规格图"):
                cuo.append(f"颜色值 {'、'.join(bad)} 不是颜色词、又没有规格图（R-SP-004）")
        if g.get("名称") in ("尺寸", "尺码"):
            if any(re.fullmatch(r"[A-Za-z]+|\d+", v) for v in g.get("值", [])) and not (g.get("规格图") or g.get("尺码表")):
                cuo.append("尺寸是字母或纯数字，要带尺码表或规格图（R-SP-004）")
    for x in XQ:
        if x not in c.get("详情", []):
            cuo.append(f"详情缺「{x}」（R-SP-003）")
    for x in XX:
        if not c.get("商品信息", {}).get(x):
            cuo.append(f"商品信息缺「{x}」（R-SP-003）" + ("；照吊牌填，成人贴身衣物一般是 B 类" if x == "安全类别" else ""))
    return cuo


def cha_lm(c, lm):
    """草稿包的样品政策和联盟现状的买样返款门槛对不对得上（Bot 实测自报 10）。"""
    yp = re.findall(r"≥\s*(\d+)", str(c.get("样品政策", ""))); lmm = re.findall(r"≥\s*(\d+)", str(lm.get("买样返款门槛", "")))
    if yp and lmm and yp[0] != lmm[0]:
        return [f"待核：样品政策写「{c.get('样品政策')}」，联盟现在是「{lm.get('买样返款门槛')}」，两处对不上，请主人定一个（R-LM-001）"]
    return []


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("草稿包"); a.add_argument("--店铺"); a.add_argument("--联盟")
    a = a.parse_args(argv)
    c = json.loads(pathlib.Path(a.草稿包).read_text(encoding="utf-8"))
    dp = pathlib.Path(a.店铺) if a.店铺 else None
    cs, _ = 底子.canshu(dp)
    cuo = cha(c, cs)
    if a.联盟:
        cuo += cha_lm(c, json.loads(pathlib.Path(a.联盟).read_text(encoding="utf-8")))
    gui = lambda x: (re.findall(r"R-[A-Z]+-\d+", x) or ["店铺链接标准"])[0]
    lan = [x for x in cuo if not x.startswith(("提醒", "待核"))]
    print(f"草稿包 {c.get('款号')}：" + (f"**不能上**（{len(lan)} 处要改）" if lan else "能上（停在提交前请主人点发布）") + "\n")
    if cuo:
        print("| # | 要看的 | 问题和改法 | 依据 |\n|---|---|---|---|")
        for i, x in enumerate(lan + [x for x in cuo if x not in lan], 1):
            wen = re.sub(r"（R-[A-Z]+-\d+）", "", x)
            print(f"| {i} | {'要改' if x in lan else x[:2]} | {wen} | {gui(x)} |")
    if lan:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
