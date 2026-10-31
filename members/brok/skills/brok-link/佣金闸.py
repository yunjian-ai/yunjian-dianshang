"""经纪 · 佣金闸：要设的佣金 ↔ 算盘给这款的上限、平台下限（普通类目 5%，R-LM-008）→ 超了、低了都拦
用法：python3 佣金闸.py --佣金 0.16 [--回执 <算盘回执.json> 或 --款号 AQ-1108] [--店铺 <店铺文件夹>]
      --款号：读算盘写的 店铺/<店>/算盘/款回执/<款号>.json（联调 10-31）；算盘没出这款的回执就只看主人封顶，并说一句
      按主人的规矩算能给多少：python3 佣金闸.py --层级 核心 [--回执 …]（读决策库「核心达人佣金」，别的层读「默认佣金」，再和封顶取低）
封顶以主人定的为准（经营决策库「佣金封顶_主人定」；杨先生 10-31：正常 20%、打得好 22%，22% 就是顶，除非特别交代）；算盘的上限只能往下压，成本是模拟值时不用。
      没装算盘：python3 佣金闸.py --佣金 0.16 --上限 0.2（主人在经纪设置卡里给的数）
借货郎 hawk-alliance/佣金闸.py 的口径（同一张算盘回执），加平台下限。拦下退出码 1，只拦不改，请主人定。"""
import argparse, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brok-base")); import 底子


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--佣金", type=float); a.add_argument("--回执"); a.add_argument("--款号")
    a.add_argument("--上限", type=float); a.add_argument("--店铺"); a.add_argument("--层级", choices=["核心", "成长", "新", "沉睡"])
    a = a.parse_args(argv)
    cs, _ = 底子.canshu(a.店铺)
    xia = float(cs["佣金下限"])
    feng = float(cs.get("佣金封顶_主人定") or 0) or (a.上限 or 0)   # 主人定的封顶为准（杨先生 10-31：正常 20、打得好 22，22 就是顶）
    sx, ly = (feng, "主人定的封顶") if feng else (None, "")
    if not a.回执 and a.款号:
        q = 底子.dianpu(a.店铺) / "算盘" / "款回执" / (a.款号.replace("/", "_") + ".json")
        if q.exists():
            a.回执 = str(q)
        else:
            print(f"算盘还没给 {a.款号} 出款回执，这次只看主人定的封顶；要更准请算盘先试算这款")
    if a.回执:
        hz = json.loads(pathlib.Path(a.回执).read_text(encoding="utf-8")); ss = float(hz["佣金上限"])
        if "模拟" in str(hz.get("成本来源", "")):
            print(f"⚠️ 算盘这款的成本是模拟值，算出的 {ss:.0%} 不作数，只看主人定的封顶")
        elif sx is None or ss < sx:   # 算盘只能往下压，不能往上抬
            sx, ly = ss, f"算盘给 {hz.get('款号', '')} 的上限（比主人封顶低，按低的）" if feng else f"算盘给 {hz.get('款号', '')} 的上限"
    if sx is None:
        print("没有佣金封顶：主人没定、算盘也没有能用的数 → 先问主人最多给多少，不自己定"); raise SystemExit(1)
    if a.佣金 is None:   # 按层级读主人的规矩，和封顶取低（Bot 回归 10-31：核心 25% 只能手填）
        if not a.层级:
            raise SystemExit("给 --佣金，或给 --层级 让脚本按主人的规矩算")
        gz, mc = (float(cs.get("核心达人佣金") or 0), "核心达人佣金") if a.层级 == "核心" else (0.0, "")
        if not gz:
            gz, mc = float(cs.get("默认佣金") or 0), "默认佣金"
        if not gz:
            print(f"主人还没定{a.层级}达人给多少（默认佣金也没定）→ 先问主人，不自己定"); raise SystemExit(1)
        gei = min(gz, sx)
        print(f"{a.层级}达人能给 {gei:.0%}：主人的规矩「{mc}」{gz:.0%}" + (f"，高于{ly} {sx:.0%}，按低的给" if gz > sx else f"，不超{ly} {sx:.0%}"))
        a.佣金 = gei
    cuo = []
    if a.佣金 > sx:
        cuo.append(f"佣金 {a.佣金:.0%} 高于{ly} {sx:.0%} → 请主人定（照上限给，或主人改上限）")
    if a.佣金 < xia:
        cuo.append(f"佣金 {a.佣金:.0%} 低于平台最低佣金 {xia:.0%}（普通类目，R-LM-008）→ 设了达人也生成不了推广链接")
    if a.佣金 > 0.5:
        cuo.append("佣金超过 50%，不合常理，先跟主人核对")
    if abs(a.佣金 * 100 - round(a.佣金 * 100)) > 1e-6:
        cuo.append(f"佣金 {a.佣金 * 100:g}% 不是整数——指定达人「固定佣金率」只能填 5-80 之间的整数（后台实看 10-31），请主人定取整")
    if cuo:
        print("佣金闸拦下：\n" + "\n".join("- " + x for x in cuo) + "\n（只拦不改，请主人定）"); raise SystemExit(1)
    print(f"佣金 OK：{xia:.0%} ≤ {a.佣金:.0%} ≤ {ly} {sx:.0%}")


if __name__ == "__main__":
    main()
