"""货郎 · 决策卡：主人定的事 → 经营决策库里一张合格式的卡（自动取号、套模板、查重、换新版）
用法：python3 决策卡.py --类 ZC|HP|DR --标题 售价下限 --原话 "以后不做 39 块以下的" [--参数 售价下限=39 ...]
       [--内容 "…"] [--状态 生效|待确认] [--替代 D-ZC-003] [--今天 2026-10-31] [--店铺 <店铺文件夹>] [--演练]
规矩（库/模板/决策卡.md）：编号 D-<类>-<三位号>，按库里已有的最大号 +1；同标题已有一张「生效」的，要用 --替代 换新版
（同编号、版本 +1、文件名加 -v<版本>，旧卡改「已停用」不删）；参数名要和 库/默认值/选品上架-服装店.md 同名，脚本才用得上。
Bot 实测自报 1（10-31）：之前只写「照模板」，手写的卡缺编号、状态、版本、参数。"""
import argparse, datetime as dt, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import 底子


def main(argv=None):
    a = argparse.ArgumentParser()
    a.add_argument("--类", required=True, choices=["ZC", "HP", "DR"]); a.add_argument("--标题", required=True)
    a.add_argument("--原话", required=True); a.add_argument("--参数", nargs="*", default=[]); a.add_argument("--内容", default="")
    a.add_argument("--状态", default="生效", choices=["生效", "待确认"]); a.add_argument("--替代"); a.add_argument("--影响", default="")
    a.add_argument("--今天"); a.add_argument("--店铺"); a.add_argument("--演练", action="store_true")
    a = a.parse_args(argv)
    dp = pathlib.Path(a.店铺) if a.店铺 else 底子.dianpu()
    jc = dp / "经营决策库"
    jin = a.今天 or str(dt.date.today())
    ka = {p: 底子.kaitou(p) for p in sorted(jc.glob("D-*.md")) if not p.name.startswith("._")} if jc.exists() else {}
    cs = 底子.moren_canshu()
    can = dict(x.split("=", 1) for x in a.参数 if "=" in x)
    ti = [f"参数「{n}」默认值里没有这个名字，脚本用不上；要用请改成默认值里的名字" for n in can if n not in cs]
    if a.替代:
        jiu = [(p, k) for p, k in ka.items() if k.get("编号") == a.替代 and k.get("状态") == "生效"]
        if not jiu:
            raise SystemExit(f"找不到生效的 {a.替代}，换不了新版")
        bh, bb = a.替代, max(int(k.get("版本") or 1) for _, k in jiu) + 1
        ming = f"{bh}-{a.标题}-v{bb}.md"; tidai = f"{bh} 版本 {bb - 1}"
    else:
        tong = [k["编号"] for k in ka.values() if k.get("标题") == a.标题 and k.get("状态") == "生效"]
        if tong:
            raise SystemExit(f"已经有一张生效的「{a.标题}」（{tong[0]}）；改它就加 --替代 {tong[0]}，旧卡会改成已停用")
        hao = [int(m.group(1)) for k in ka.values() if (m := re.match(rf"D-{a.类}-(\d+)", k.get("编号", "")))]
        bh, bb = f"D-{a.类}-{max(hao, default=0) + 1:03d}", 1
        ming = f"{bh}-{a.标题}.md"; tidai = "无"
    canshu = "".join(f"\n  {n}: {v}" for n, v in can.items())
    t = f"""---
编号: {bh}
标题: {a.标题}
状态: {a.状态}
版本: {bb}
生效日期: {jin}
定的人: 主人原话「{a.原话}」
替代: {tidai}
影响: [{a.影响}]
参数:{canshu}
---

# {a.标题}
{a.内容 or a.原话}
"""
    print(t)
    for x in ti:
        print("⚠️ " + x)
    if a.演练:
        return
    jc.mkdir(parents=True, exist_ok=True)
    if a.替代:
        for p, _ in jiu:
            p.write_text(re.sub(r"^状态: 生效", "状态: 已停用", p.read_text(encoding="utf-8"), count=1, flags=re.M), encoding="utf-8")
    (jc / ming).write_text(t, encoding="utf-8")
    print(f"已写 {jc / ming}" + (f"；{a.替代} 旧版改成已停用" if a.替代 else ""))


if __name__ == "__main__":
    main()
