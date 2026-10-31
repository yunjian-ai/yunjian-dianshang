"""货郎 · 验收：丹青／执笔交回来的东西 → 照店铺链接标准的合格线逐条打勾，不过的写明哪条、退回
用法：python3 验收.py --图 <交回.json> [--标题 "<执笔给的标题>" --成分 "<面料成分>"] [--店铺 <店铺文件夹>]
交回.json：{"主图": [{"文件","宽","高","内容"}, ...]}   不过退出码 1"""
import argparse, json, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "hawk-base")); import 底子
sys.path.insert(0, str(HERE.parent / "hawk-listing")); import 查草稿包, 查标题


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--图"); a.add_argument("--标题"); a.add_argument("--成分"); a.add_argument("--店铺")
    a = a.parse_args(argv)
    cs, _ = 底子.canshu(a.店铺)
    cuo = []
    if a.图:
        zt = json.loads(pathlib.Path(a.图).read_text(encoding="utf-8")).get("主图", [])
        cuo += 查草稿包.cha_tu(zt, cs)
        print(f"主图 {len(zt)} 张：" + ("全部合格" if not cuo else "有不合格"))
    if a.标题:
        cuo += 查标题.cha(a.标题, a.成分, cs)
    if cuo:
        print("退回，照链接标准改：\n" + "\n".join("- " + x for x in cuo)); raise SystemExit(1)
    print("验收 OK")


if __name__ == "__main__":
    main()
