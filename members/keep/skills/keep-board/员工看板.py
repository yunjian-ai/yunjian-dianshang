"""掌柜 · 员工看板：三位 AI 员工今天干了什么——一位一行「做了 → 出了 → 卡在哪、等您定」；多店时一店一段。
用法：python3 员工看板.py [--店铺 …] [--今天 2026-11-10] [--宽]
数全来自各员工的回执（店铺/<店>/回执/<日期>/<员工>.json，格式见 库/回执格式.json）；没回执写「今天没跑」，格式不对写明，不猜。"""
import argparse, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "keep-base")); import 底子, 汇总


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--店铺", nargs="*"); a.add_argument("--今天"); a.add_argument("--宽", action="store_true")
    a = a.parse_args(argv)
    day = a.今天 or str(底子.jintian())
    dps = [底子.dianpu(x) for x in a.店铺] if a.店铺 else 底子.dianpus()
    if not dps:
        raise SystemExit("还没有店铺文件夹")
    for dp in dps:
        rows = 汇总.yuangong(汇总.du_huizhi(dp, day))
        pao = sum(1 for r in rows if not r[1].startswith(("今天没跑", "回执格式")))
        print(f"**{dp.name} · {day} · 三位员工 {pao} 位今天干了活**")
        print(底子.biao(["员工", "做了", "出了", "卡在／等您定"], rows, kuan=a.宽, zhu=None if a.宽 else 3, jian=0))
        print(f"出处：{dp.name}/回执/{day}/\n")


if __name__ == "__main__":
    main()
