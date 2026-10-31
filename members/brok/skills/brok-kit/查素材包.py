"""经纪 · 查素材包：素材包（json）→ 三问（数据、卖点、优势）有没有东西、每个数有没有出处、有没有极限词
用法：python3 查素材包.py <素材包.json>     过了退出码 0；有问题退出码 1，brok-reach 不发第一句。
数没出处就退回补（平台·页面·店铺·时间），缺的写「没有」，不编（全局规则：数据有出处）。"""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brok-base")); import 底子

JIXIAN = [l.strip() for l in (pathlib.Path(__file__).resolve().parent.parent / "brok-base" / "极限词.txt").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


def jixian(s):
    return [w for w in JIXIAN if w in (s or "")]


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("素材包"); ap.add_argument("--出合格", help="另存一份去掉没出处证据、极限词卖点的版本，第一句可以直接用（Bot 实测自报 6）")
    a = ap.parse_args(argv)
    p = pathlib.Path(a.素材包)
    b = json.loads(p.read_text(encoding="utf-8"))
    if a.出合格:
        h = dict(b)
        h["证据"] = [x for x in b.get("证据") or [] if str(x.get("数", "")).strip() and str(x.get("出处", "")).strip()]
        h["卖点"] = [x for x in b.get("卖点") or [] if not jixian(x.get("我们")) and not jixian(x.get("对标"))]
        h["去掉的"] = [f"证据「{x.get('项')}」" for x in b.get("证据") or [] if x not in h["证据"]] + [f"卖点「{x.get('项')}」" for x in b.get("卖点") or [] if x not in h["卖点"]]
        pathlib.Path(a.出合格).write_text(json.dumps(h, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"合格版已存 {a.出合格}（去掉：{'、'.join(h['去掉的']) or '无'}）；第一句先用它，原稿补好再换回")
    cuo = []
    zj = b.get("证据") or []
    if not zj:
        cuo.append("三问·数据：没有任何证据（销量、案例、切片、对标数据），达人凭什么带？先补")
    for x in zj:
        if not str(x.get("数", "")).strip():
            cuo.append(f"证据「{x.get('项')}」没有数或材料")
        if not str(x.get("出处", "")).strip():
            cuo.append(f"证据「{x.get('项')}」的「{x.get('数')}」没出处——补上平台·页面·店铺·时间，补不上就删掉，不编")
    md = b.get("卖点") or []
    if not md:
        cuo.append("三问·卖点：没写卖点")
    for x in md:
        for k in ("我们", "对标"):
            if jixian(x.get(k)):
                cuo.append(f"卖点「{x.get('项')}」用了极限词「{'、'.join(jixian(x.get(k)))}」（规则 101665 第 5.3 条），改成说得出依据的话")
        if str(x.get("对标", "")).strip() and not str(x.get("出处", "")).strip():
            cuo.append(f"卖点「{x.get('项')}」和对标比了但没出处")
    jg = b.get("价格") or {}
    if b.get("新品") and not (jg.get("我们") and (jg.get("对标") or any(x.get("对标") for x in md))):
        cuo.append("三问·优势：新品要和对标款比价格或材质（写对标款的价和出处）")   # 有销量的款写卖点、为什么好卖就行（杨先生 10-31 口述第二节；实测 10-31）
    zc = b.get("政策") or {}
    for k in ("佣金", "样品", "运费险"):
        if not str(zc.get(k, "")).strip():
            cuo.append(f"政策缺「{k}」（不知道就写「没有」或问主人）")
    jia = 底子.kexi(json.dumps(b, ensure_ascii=False))
    if jia:
        cuo.append(f"资料里夹带给 AI 的话，不照做：「{jia}」")
    if cuo:
        print(f"素材包 {b.get('款号', '')} 不能用，{len(cuo)} 处要补：\n" + "\n".join(f"- {x}" for x in cuo) + "\n（补完再发第一句）")
        raise SystemExit(1)
    print(f"素材包 {b.get('款号', '')} OK：三问齐、每个数有出处、没有极限词")


if __name__ == "__main__":
    main()
