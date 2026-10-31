"""云间成员回执：每次干完活往 店铺/<店>/回执/<日期>/<成员>.json 记一笔，掌柜读它出报（四位同一个写法，格式正本在掌柜 keep-base/回执格式.json）。
脚本里：import 回执; 回执.ji(店铺文件夹, "brok", zuole={"第一句": 1}, chule=["发版单 H11"], kazai=[...], deng=[...], shu={"分层": {...}}, chuchu="精选联盟·合作消息")
命令行：python3 回执.py --店铺 <文件夹> --成员 brok [--做了 第一句=1 …] [--出了 …] [--卡在 …] [--等主人定 …] [--今天 2026-11-10]
做了：同名累加；出了／卡在／等主人定：去重追加；数：同名整块换新。只记数和结论，不记联系方式、收件信息。"""
import argparse, datetime as dt, json, os, pathlib


def ji(dp, chengyuan, zuole=None, chule=(), kazai=(), deng=(), shu=None, chuchu="", jintian=None):
    if not dp:
        return None
    day = str(jintian or os.environ.get("YUNJIAN_TODAY") or dt.date.today())[:10]
    p = pathlib.Path(dp) / "回执" / day / f"{chengyuan}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {"成员": chengyuan, "店铺": pathlib.Path(dp).name, "日期": day, "做了": {}, "出了": [], "卡在": [], "等主人定": [], "数": {}, "出处": []}
    for k, v in (zuole or {}).items():
        d["做了"][k] = d["做了"].get(k, 0) + v
    for key, xs in (("出了", chule), ("卡在", kazai), ("等主人定", deng)):
        for x in xs:
            if x and x not in d[key]:
                d[key].append(x)
    d["数"].update(shu or {})
    if chuchu and chuchu not in d["出处"]:
        d["出处"].append(chuchu)
    d["记录时间"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)
    return p


def main(argv=None):
    a = argparse.ArgumentParser()
    a.add_argument("--店铺", required=True); a.add_argument("--成员", required=True); a.add_argument("--做了", nargs="*", default=[])
    a.add_argument("--出了", nargs="*", default=[]); a.add_argument("--卡在", nargs="*", default=[]); a.add_argument("--等主人定", nargs="*", default=[])
    a.add_argument("--出处", default=""); a.add_argument("--今天")
    a = a.parse_args(argv)
    zuole = {k: float(v) if "." in v else int(v) for k, v in (x.split("=", 1) for x in a.做了 if "=" in x)}
    print("回执已记", ji(a.店铺, a.成员, zuole, a.出了, a.卡在, a.等主人定, None, a.出处, a.今天))


if __name__ == "__main__":
    main()
