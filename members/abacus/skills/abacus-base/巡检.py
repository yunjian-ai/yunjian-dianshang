"""算盘 · 巡检：底座三本账每周体检，查出要更新的地方，写变更单草稿（不自己改卡）
用法：python3 巡检.py [--店铺 <店铺文件夹>] [--正文 <取回的官方正文文件夹>]
  平台规则库：--正文 文件夹里放「<官方编号>-正文.txt」（浏览器打开卡上的官方链接，只取文章正文那一块存下来，第一行写「页面更新日期：xxxx」）
              → 比页面更新日期和正文指纹；不一样的写变更单草稿。官方编号不是学习中心文章的（比如税务公告），只提醒看有没有新公告替代
  自动化地图：最后走通超过 14 天的列出来（要空走一遍只读步骤）；连续失败 ≥1 的列出来（要自愈）
  经营决策库：生效日期超过 90 天没动的列出来（问主人还算不算数）
输出：打印清单；有要改的在 店铺/变更单/ 写「B-草稿-日期-编号.md」，等主人或干活时确认
"""
import argparse, datetime as dt, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import 指纹
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "abacus-fetch")); import 底账

def tou(s, k):
    m = re.search(rf"^{k}: (.*)$", s, re.M)
    return m.group(1).strip() if m else ""

def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--店铺"); a.add_argument("--正文")
    a = a.parse_args(argv)
    dp = pathlib.Path(a.店铺) if a.店铺 else 底账.dianpu()
    jin = dt.date.today()
    caogao = []
    print("## 平台规则库")
    for p in sorted((底账.KU / "平台规则库").glob("R-*.md")):
        s = p.read_text(encoding="utf-8")
        if tou(s, "状态") == "待核":
            print(f"待核 {tou(s, '编号')} {tou(s, '标题')}：核实前不参与算账，下次取数时顺手核")
            continue
        if tou(s, "状态") != "生效":
            continue
        bh, oid = tou(s, "编号"), tou(s, "官方编号")
        zw = pathlib.Path(a.正文) / f"{oid}-正文.txt" if a.正文 else None
        if not zw or not zw.exists():
            print(f"没取到 {bh} {tou(s, '标题')}（官方编号 {oid}）" + ("：不是学习中心文章，看有没有新公告替代" if not re.match(r"^[0-9A-Za-z]+$", oid) else ""))
            continue
        t = zw.read_text(encoding="utf-8")
        gx = (re.search(r"页面更新日期[:：][ \t]*([0-9][0-9-]*)", t) or [None, ""])[1]
        zw_fp = 指纹.zhiwen(t)
        jiu_gx, jiu_fp = tou(s, "页面更新日期"), tou(s, "正文指纹")
        if zw_fp == jiu_fp and (not gx or gx in jiu_gx):
            print(f"一致 {bh}")
            continue
        why = []
        if gx and gx not in jiu_gx: why.append(f"页面更新日期 {jiu_gx} → {gx}")
        if zw_fp != jiu_fp: why.append(f"正文指纹 {jiu_fp} → {zw_fp}")
        print(f"变了 {bh} {tou(s, '标题')}：{'；'.join(why)}（先隔一会儿重取一次，两次都变才算真改）")
        caogao.append((bh, f"""# 变更单草稿（巡检 {jin}）
- 本子：平台规则库
- 怎么发现的：每周巡检
- 涉及的卡：{bh} {tou(s, '标题')}
- 变化：{'；'.join(why)}
- 官方链接：{tou(s, '官方链接')}
- 要做：读新正文，写清旧的怎么写、新的怎么写；改参数的话写清哪些公式受影响、旧订单按旧规则不重算
- 确认：附官方原文那一段请主人看一眼，点头再改卡（版本 +1，旧版标「已停用」不删）
"""))
    print("## 自动化地图")
    for p in sorted((底账.KU / "自动化地图").glob("M-*.md")):
        s = p.read_text(encoding="utf-8")
        zt = tou(s, "最后走通")
        try:
            tian = (jin - dt.date.fromisoformat(zt)).days
        except ValueError:
            tian = 999
        sb = int(tou(s, "连续失败") or 0)
        if sb:
            print(f"要自愈 {tou(s, '编号')} {tou(s, '标题')}：连续失败 {sb} 次")
        elif tian > 14:
            print(f"要空走 {tou(s, '编号')} {tou(s, '标题')}：{tian} 天没走过（只走只读步骤，不点提交）")
        else:
            print(f"可用 {tou(s, '编号')}（{tian} 天前走通）")
    print("## 经营决策库")
    for p in sorted((dp / "经营决策库").glob("D-*.md")) if (dp / "经营决策库").is_dir() else []:
        s = p.read_text(encoding="utf-8")
        try:
            tian = (jin - dt.date.fromisoformat(tou(s, "生效日期"))).days
        except ValueError:
            continue
        if tou(s, "状态").startswith("生效") and tian > 90:
            print(f"问主人 {tou(s, '编号')} {tou(s, '标题')}：{tian} 天没动，还算数吗")
    if caogao:
        d = dp / "变更单"; d.mkdir(parents=True, exist_ok=True)
        for bh, t in caogao:
            (d / f"B-草稿-{jin}-{bh}.md").write_text(t, encoding="utf-8")
        print(f"写了 {len(caogao)} 张变更单草稿到 {d}")
    print("巡检 完")

if __name__ == "__main__":
    main()
