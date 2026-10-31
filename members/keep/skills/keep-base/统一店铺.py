"""掌柜 · 统一店铺：把算盘、货郎、经纪各自的店铺文件夹并进四位共用的 ~/.yunjian/店铺/<店名>/（一家店一个名字、一份经营决策库），只挪不删。
用法：python3 统一店铺.py [--改名 旧名=新名 …] [--只并 abacus,hawk,brok] [--演练]
  例：python3 统一店铺.py --改名 阿青卫衣=抖店-A 实测店=抖店-A --演练   先看计划，没问题去掉 --演练
做法：每位成员 <家目录>/店铺/<旧名>/ 里的东西挪进 店铺/<新名>/；同名文件内容一样就留一份，不一样的把挪进来的改名「原名-来自<成员>」；
经营决策库的卡编号撞了（不同内容同编号）→ 挪进来的那张改成同类下一个空号，卡里「编号」跟着改；每一步记进 经营决策库/变更记录.md。
挪完，旧文件夹剩下的（应该是空的）整个挪到 <家目录>/店铺-已并入-<日期>/ 留底。之后三位成员会自动用共用的根目录（底子 dianpu_gen）。"""
import argparse, datetime as dt, filecmp, pathlib, re, shutil, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import 底子

CHENG = {"abacus": "算盘", "hawk": "货郎", "brok": "经纪"}


def xia_hao(jc, lei):
    ns = [int(m.group(1)) for p in jc.glob(f"D-{lei}-*.md") if (m := re.match(rf"D-{lei}-(\d+)", p.name))]
    return max(ns, default=0) + 1


def bing_juece(src, dst, cheng, ji, yanlian):
    """挪经营决策卡：同一张卡的几个版本（同编号）一起走；只有和「别的成员先放进来的」同编号、内容又不同才改号，几个版本改成同一个新号。"""
    dst.mkdir(parents=True, exist_ok=True)
    yuan = {p.name for p in dst.glob("D-*.md")}
    zu = {}
    for p in sorted(src.glob("*")):
        if p.name.startswith("._"):
            continue
        if p.name == "变更记录.md":
            q = dst / p.name
            if q.exists():
                q.write_text(q.read_text(encoding="utf-8").rstrip("\n") + "\n" + "\n".join(
                    l for l in p.read_text(encoding="utf-8").splitlines() if l.startswith("| 20")) + "\n", encoding="utf-8")
                p.unlink()
            else:
                shutil.move(str(p), q)
            continue
        m = re.match(r"D-([A-Z]+)-(\d+)", p.name)
        zu.setdefault(m.group(0) if m else p.name, []).append(p)
    for bh, ps in zu.items():
        m = re.match(r"D-([A-Z]+)-(\d+)$", bh)
        zhuang = [y for y in yuan if m and y.startswith(bh + "-")]
        if zhuang and all(any((dst / y).exists() and filecmp.cmp(p, dst / y, shallow=False) for y in zhuang) for p in ps):
            ji.append(f"{cheng} {bh}：和已有的一样，留一份")
            for p in ps:
                p.unlink()
            continue
        xin = bh
        if zhuang:
            xin = f"D-{m.group(1)}-{xia_hao(dst, m.group(1)):03d}"
            ji.append(f"{cheng} {bh}（{ps[0].name[len(bh) + 1:-3]}）：编号和别的成员的撞了 → 改成 {xin}")
        else:
            ji.append(f"{cheng} {bh}：挪进来" + (f"（{len(ps)} 个版本）" if len(ps) > 1 else ""))
        for p in ps:
            q = dst / (xin + p.name[len(bh):])
            if xin != bh:
                q.write_text(p.read_text(encoding="utf-8").replace(f"编号: {bh}", f"编号: {xin}", 1), encoding="utf-8"); p.unlink()
            else:
                shutil.move(str(p), q)


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--改名", nargs="*", default=[]); a.add_argument("--只并", default="abacus,hawk,brok")
    a.add_argument("--演练", action="store_true")
    a = a.parse_args(argv)
    gai = dict(x.split("=", 1) for x in a.改名 if "=" in x)
    root = 底子.HOME.parent
    if a.演练:   # 演练：把要并的几个文件夹复制到临时目录，在那里真跑一遍，计划和真做一模一样，原处一点不动
        import tempfile
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="统一店铺演练-"))
        for c in a.只并.split(",") + ["店铺"]:
            src = root / c / "店铺" if c != "店铺" else root / "店铺"
            if src.is_dir():
                shutil.copytree(src, (tmp / c / "店铺") if c != "店铺" else tmp / "店铺")
        root = tmp
    gen = root / "店铺"
    ji, today = [], dt.date.today().isoformat()
    for cheng in a.只并.split(","):
        home = root / cheng
        old = home / "店铺"
        ds = sorted(x for x in old.iterdir() if x.is_dir() and not x.name.startswith(".")) if old.is_dir() else []
        if not ds:   # 没有店（文件夹不在或是空的）：不并、不留底（Bot 实测 10-31）
            continue
        for d in ds:
            xin = gai.get(d.name, d.name)
            dst = gen / xin
            ji.append(f"— {CHENG.get(cheng, cheng)}：{d} → {dst}")
            if True:
                dst.mkdir(parents=True, exist_ok=True)
            for p in sorted(d.iterdir()):
                if p.name.startswith("._"):
                    continue
                q = dst / p.name
                if p.name == "经营决策库" and p.is_dir():
                    bing_juece(p, q, CHENG.get(cheng, cheng), ji, False)
                    continue
                if not q.exists():
                    ji.append(f"{CHENG.get(cheng, cheng)} {p.name}：挪进来")
                    if True:
                        shutil.move(str(p), q)
                elif p.is_file() and q.is_file() and filecmp.cmp(p, q, shallow=False):
                    ji.append(f"{CHENG.get(cheng, cheng)} {p.name}：和已有的一样，留一份")
                    if True:
                        p.unlink()
                else:
                    alt = dst / f"{p.stem}-来自{CHENG.get(cheng, cheng)}{p.suffix}"
                    ji.append(f"{CHENG.get(cheng, cheng)} {p.name}：已有同名、内容不同 → 存成 {alt.name}")
                    if True:
                        shutil.move(str(p), alt)
        if True:
            bak = home / f"店铺-已并入-{today}"
            shutil.move(str(old), bak)
            ji.append(f"{CHENG.get(cheng, cheng)} 旧文件夹剩下的挪到 {bak}（留底，不删）")
    if not ji:
        print("没有要并的：三位的家目录里都没有店铺文件夹"); return
    print(("【演练：在临时目录里照做了一遍，原处什么都没动】\n" if a.演练 else "") + "\n".join(ji).replace(str(root), "~/.yunjian" if a.演练 else str(root)))
    if not a.演练:
        for dst in (gen.iterdir() if gen.is_dir() else []):
            jc = dst / "经营决策库"
            if jc.is_dir():
                b = jc / "变更记录.md"
                head = "" if b.exists() else "# 经营决策库 · 变更记录（只追加，不删）\n| 日期 | 卡 | 版本 | 改了什么 | 出处 | 谁定的 |\n|---|---|---|---|---|---|\n"
                b.write_text((b.read_text(encoding="utf-8") if b.exists() else head).rstrip("\n") + f"\n| {today} | 全部 | — | 掌柜统一店铺：三位的店铺文件夹并成这一份（撞号的改了号，见下） | 统一店铺.py | 主人点头 |\n"
                             + "".join(f"| {today} | — | — | {x} | 统一店铺.py | 主人点头 |\n" for x in ji if "改成" in x), encoding="utf-8")


if __name__ == "__main__":
    main()
