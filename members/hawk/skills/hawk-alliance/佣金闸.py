"""货郎 · 佣金闸：要设的佣金（或联盟自动推广的默认佣金）↔ 算盘给的佣金上限 → 超了就拦
用法：python3 佣金闸.py --佣金 0.20 （--回执 <算盘回执.json> 或 --款号 AQ-1108）[--自动推广 已开启 --默认佣金 0.20] [--店铺 <店铺文件夹>]
--款号：读算盘写的 店铺/<店>/算盘/款回执/<款号>.json（联调 10-31）。
上限取「主人定的封顶」（经营决策库 佣金封顶_主人定）和算盘上限里低的那个（杨先生 10-31）。
官方普通计划佣金 1%～50%；超上限退出码 1（只拦、不改，改佣金请主人点）。"""
import argparse, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "hawk-base")); import 底子


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--佣金", type=float); a.add_argument("--回执"); a.add_argument("--款号")
    a.add_argument("--自动推广", default=""); a.add_argument("--默认佣金", type=float); a.add_argument("--店铺")
    a = a.parse_args(argv)
    if not a.回执:
        if not a.款号:
            raise SystemExit("给 --回执 或 --款号（读算盘的款回执）")
        q = 底子.dianpu(a.店铺) / "算盘" / "款回执" / (a.款号.replace("/", "_") + ".json")
        if not q.exists():
            print(f"算盘还没给 {a.款号} 出款回执（{q}）→ 先请算盘试算这款，不自己定上限"); raise SystemExit(1)
        a.回执 = str(q)
    hz = json.loads(pathlib.Path(a.回执).read_text(encoding="utf-8"))
    sx = float(hz["佣金上限"]); cuo = []; ly = f"算盘给 {hz.get('款号', '')} 的上限"
    try:
        feng = float(底子.canshu(a.店铺)[0].get("佣金封顶_主人定") or 0)
    except SystemExit:
        feng = 0.0
    if feng and feng < sx:   # 主人定的封顶为准，算盘只能往下压（杨先生 10-31：正常 20、打得好 22，22 就是顶）
        sx, ly = feng, "主人定的封顶"   # 说清是谁定的，别把主人封顶说成算盘的（联调 Bot 自报 10-31）
    yong = a.佣金 if a.佣金 is not None else a.默认佣金
    if yong is not None and not (0.01 <= yong <= 0.5):
        cuo.append(f"佣金 {yong:.0%} 不在官方普通计划 1%～50% 里")
    if yong is not None and yong > sx:
        cuo.append(f"佣金 {yong:.0%} 高于{ly} {sx:.0%}")
    if a.自动推广 == "已开启" and a.默认佣金 is not None and a.默认佣金 > sx:
        cuo.append(f"联盟开着商品自动推广、默认 {a.默认佣金:.0%}，这款发布后会被按 {a.默认佣金:.0%} 自动放进联盟 → 发布前请主人定：这款调到 ≤{sx:.0%}，或这款不走自动推广")
    if cuo:
        print("佣金闸拦下：\n" + "\n".join("- " + x for x in dict.fromkeys(cuo)) + "\n（只提醒，不自己改；改佣金请主人点头）"); raise SystemExit(1)
    print(f"佣金 OK：{yong:.0%} ≤ {ly} {sx:.0%}")


if __name__ == "__main__":
    main()
