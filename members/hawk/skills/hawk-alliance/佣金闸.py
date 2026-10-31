"""货郎 · 佣金闸：要设的佣金（或联盟自动推广的默认佣金）↔ 算盘给的佣金上限 → 超了就拦
用法：python3 佣金闸.py --佣金 0.20 --回执 <算盘回执.json> [--自动推广 已开启 --默认佣金 0.20]
官方普通计划佣金 1%～50%；超上限退出码 1（只拦、不改，改佣金请主人点）。"""
import argparse, json, pathlib


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--佣金", type=float); a.add_argument("--回执", required=True)
    a.add_argument("--自动推广", default=""); a.add_argument("--默认佣金", type=float)
    a = a.parse_args(argv)
    hz = json.loads(pathlib.Path(a.回执).read_text(encoding="utf-8"))
    sx = float(hz["佣金上限"]); cuo = []
    yong = a.佣金 if a.佣金 is not None else a.默认佣金
    if yong is not None and not (0.01 <= yong <= 0.5):
        cuo.append(f"佣金 {yong:.0%} 不在官方普通计划 1%～50% 里")
    if yong is not None and yong > sx:
        cuo.append(f"佣金 {yong:.0%} 高于算盘给的上限 {sx:.0%}（{hz.get('款号', '')}）")
    if a.自动推广 == "已开启" and a.默认佣金 is not None and a.默认佣金 > sx:
        cuo.append(f"联盟开着商品自动推广、默认 {a.默认佣金:.0%}，这款发布后会被按 {a.默认佣金:.0%} 自动放进联盟 → 发布前请主人定：这款调到 ≤{sx:.0%}，或这款不走自动推广")
    if cuo:
        print("佣金闸拦下：\n" + "\n".join("- " + x for x in dict.fromkeys(cuo)) + "\n（只提醒，不自己改；改佣金请主人点头）"); raise SystemExit(1)
    print(f"佣金 OK：{yong:.0%} ≤ 上限 {sx:.0%}")


if __name__ == "__main__":
    main()
