"""货郎 · 选品卡：五看写好的 JSON（＋算盘回执）→ 查规矩 → 选品卡（Markdown 给人看，存店铺/选品卡/）
用法：python3 选品卡.py <选品卡.json> [--回执 <算盘回执.json>] [--店铺 <店铺文件夹>] [--演练]
规矩：利润只照算盘回执写（没装算盘就写「没装算盘」＋料单，不心算）；结论以「建议」开头、拍板留给主人；
没过爆品线的不能写「建议做」（主人仍可拍板做）；自己设计的款写「建议做」要带参照款；五看每栏都要写出处（平台·页面·店铺·时间，杨先生 10-31）；输出是表格；格式照 选品卡.schema.json（有 jsonschema 就用它查，没有就查必填栏）。不过就退出码 1。"""
import argparse, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "hawk-base")); import 底子

SC = json.loads((pathlib.Path(__file__).resolve().parent / "选品卡.schema.json").read_text(encoding="utf-8"))


def cha(k, hz=None):
    cuo = []
    try:
        import jsonschema
        cuo += [e.message for e in jsonschema.Draft202012Validator(SC).iter_errors(k)]
    except ImportError:
        cuo += [f"缺「{n}」" for n in SC["required"] if n not in k]
        cuo += [f"五看缺「{n}」" for n in SC["properties"]["五看"]["required"] if n not in k.get("五看", {})]
        cuo += [f"五看「{n}」没写出处" for n, v in k.get("五看", {}).items() if not (isinstance(v, dict) and str(v.get("出处", "")).strip())]
        if not str(k.get("结论", "")).startswith("建议"):
            cuo.append("结论要以「建议」开头（拍板留给主人）")
    lr = k.get("利润", {})
    if hz:
        for n, m in [("保本价", "保本价"), ("佣金上限", "佣金上限")]:
            if lr.get(n) != hz.get(m):
                cuo.append(f"利润「{n}」{lr.get(n)} 和算盘回执 {hz.get(m)} 对不上（只照回执写）")
        if lr.get("出处") != "算盘回执":
            cuo.append("给了算盘回执，利润出处要写「算盘回执」")
    elif lr.get("出处") == "算盘回执":
        cuo.append("没有算盘回执，不能写出处「算盘回执」")
    elif any(lr.get(n) is not None for n in ("保本价", "预估到手利润", "佣金上限")):
        cuo.append("没装算盘不能写利润数（不心算），写「没装算盘」＋料单")
    elif lr.get("出处") == "没装算盘" and not lr.get("料单"):
        cuo.append("没装算盘要给料单（售价、成本、运费、退货率）")
    if k.get("爆品线") not in ("过线", "自己设计") and "建议做" in str(k.get("结论", "")):
        cuo.append(f"爆品线是「{k.get('爆品线')}」，结论不能写「建议做」")
    if k.get("爆品线") == "自己设计" and "建议做" in str(k.get("结论", "")) and not k.get("参照款"):
        cuo.append("自己设计的款写「建议做」要写参照款（照哪款做的、它的出处）")
    for n, v in k.get("五看", {}).items():
        if 底子.kexi(str(v)):
            cuo.append(f"五看「{n}」里有像写给 AI 的话：{底子.kexi(str(v))}")
    return cuo


def md(k):
    lr = k["利润"]; w = k["五看"]
    l = (f"保本价 {lr.get('保本价')} 元｜预估到手 {lr.get('预估到手利润')} 元｜佣金上限 {lr.get('佣金上限', 0):.0%}"
         if lr["出处"] == "算盘回执" else f"没装算盘，利润没算；算账要的料：{lr.get('料单')}")
    hang = "\n".join(f"| {n} | {w[n]['看到的']} | {w[n]['出处']} |" for n in ["热度", "爆在哪", "货源", "周期", "竞品价"])
    can = f"\n| 参照款 | {k['参照款']} | — |" if k.get("参照款") else ""
    return f"""# 选品卡 · {k['款号']} {k['品名']}
来源：{k['来源']}｜爆品线：**{k['爆品线']}**｜推荐渠道：**{k['推荐渠道']}**

| 看什么 | 看到的 | 出处（平台·页面·店铺·时间） |
|---|---|---|
{hang}{can}
| 利润 | {l} | {'算盘回执' if lr['出处'] == '算盘回执' else '—'} |

**结论：{k['结论']}**（拍板请您定）
"""


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("卡"); a.add_argument("--回执"); a.add_argument("--店铺"); a.add_argument("--演练", action="store_true")
    a = a.parse_args(argv)
    k = json.loads(pathlib.Path(a.卡).read_text(encoding="utf-8"))
    hz = json.loads(pathlib.Path(a.回执).read_text(encoding="utf-8")) if a.回执 else None
    cuo = cha(k, hz)
    if cuo:
        print("选品卡不过：\n" + "\n".join("- " + c for c in cuo)); raise SystemExit(1)
    t = md(k); print(t)
    if not a.演练:
        dp = pathlib.Path(a.店铺) if a.店铺 else 底子.dianpu()
        (dp / "选品卡").mkdir(parents=True, exist_ok=True)
        (dp / "选品卡" / f"{k['款号']}.md").write_text(t, encoding="utf-8")
        print("选品卡 OK，已存")


if __name__ == "__main__":
    main()
