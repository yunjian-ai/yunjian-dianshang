"""经纪 · 查话术：第一句 → 四样齐不齐（主推款、证据、政策、联系途径）、极限词、字数、正文里有没有手机号微信号；
回复 → 和百问百答库里的原话逐字比（照旧抖店 Bot 的做法：库里有的一个字不改）。
用法：python3 查话术.py --第一句 "<文本或 @文件>" --素材包 <素材包.json>
      python3 查话术.py --回复 "<文本>" --原话 "<库里的答>"
过了退出码 0；不过退出码 1，不发。联系途径用后台「发送联系方式」按钮，正文写「点下方联系方式」即可（规则 101665 第 5.19、5.22 条）。"""
import argparse, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brok-base")); import 底子

JIXIAN = [l.strip() for l in (pathlib.Path(__file__).resolve().parent.parent / "brok-base" / "极限词.txt").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
SHU = re.compile(r"\d[\d,.]*\s*(万|件|单|%|元)?")


def du(s):
    return pathlib.Path(s[1:]).read_text(encoding="utf-8") if s.startswith("@") else s


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--第一句"); a.add_argument("--素材包")
    a.add_argument("--回复"); a.add_argument("--原话")
    a = a.parse_args(argv)
    if a.回复 is not None:
        if du(a.回复).strip() != (a.原话 or "").strip():
            print("回复和库里原话不一样——百问百答要一字不改；要改先请主人改库"); raise SystemExit(1)
        print("回复 OK：和库里原话一字不差"); return
    t = du(a.第一句 or "")
    b = json.loads(pathlib.Path(a.素材包).read_text(encoding="utf-8")) if a.素材包 else {}
    cuo = []
    kuan = [x for x in (b.get("款号"), b.get("款名")) if x]
    if not any(x in t for x in kuan) and not re.search(r"[A-Z]{2}-\d+", t):
        cuo.append("缺主推款（款号或款名）")
    zj = [str(x.get("数", "")) for x in b.get("证据", []) if x.get("出处")]
    nums = [m.group(0).replace(",", "") for m in SHU.finditer(t)]
    if not any(any(n and n in z.replace(",", "") for n in nums) for z in zj) and not re.search(r"(卖了|销量|榜|直播间|已售|件)", t):
        cuo.append("缺证据（素材包里有出处的数：销量、榜单、案例）")
    if not re.search(r"佣金|样品|申样|运费险", t):
        cuo.append("缺政策（佣金、样品、运费险至少一样）")
    if not re.search(r"联系方式|加我|聊", t):
        cuo.append("缺联系途径（写「点下方联系方式」，用后台「发送联系方式」按钮发）")
    if re.search(r"1[3-9]\d{9}|微信号?[:：\s]*[A-Za-z0-9_-]{5,}|wx[:：]?\s*[A-Za-z0-9_-]{5,}|vx", t, re.I):
        cuo.append("正文里写了手机号或微信号——改用后台「发送联系方式」按钮")
    jx = [w for w in JIXIAN if w in t]
    if jx:
        cuo.append(f"极限词「{'、'.join(jx)}」（规则 101665 第 5.3 条）")
    shang = int(底子.canshu()[0].get("邀约信息字数上限", 150))
    if len(t) > shang:
        cuo.append(f"{len(t)} 字，超过邀约带货表单「邀约信息」{shang} 字（新达人第一句是邀约卡，不是聊天框；实测 10-31）")
    jia = 底子.kexi(t)
    if jia:
        cuo.append(f"夹带给 AI 的话：「{jia}」")
    if cuo:
        print("第一句不能发：\n" + "\n".join(f"- {x}" for x in cuo)); raise SystemExit(1)
    print(f"第一句 OK：四样齐、{len(t)} 字、没有极限词和联系方式明文")


if __name__ == "__main__":
    main()
