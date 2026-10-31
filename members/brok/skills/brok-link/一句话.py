"""经纪 · 主人一句话 → 谈定单：UID、佣金、链接类型、款号、颜色、尺码、件数、收件信息；缺什么只问什么；写出要走的路线
用法：python3 一句话.py "UID 71234567890，16%，渠道品，AQ-1108 黑 L 两件，地址……" [--出 <谈定单.json>]
链接类型：普通（主品「指定达人·固定佣金」M-BY-006）／渠道品（M-BY-006 设佣金＋M-DD-103 建专属达人渠道品，渠道品继承主品佣金不能单独设，R-LM-005）／全店（M-BY-007 按 UID）。
「从 16 降到 12」认成降佣：次日 0 点生效（R-LM-004）。收件信息只进谈定单和发版单，不打印到汇总里。"""
import argparse, json, pathlib, re

YANSE = "黑白灰红粉蓝绿黄紫咖棕杏米卡其藏青酒红"
SHU = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}


def jie(t):
    d, que = {}, []
    m = re.search(r"UID[:：\s]*(\d{6,20})", t, re.I) or re.search(r"(?<!\d)(?!1[3-9]\d{9}(?!\d))(\d{9,20})(?!\d)", t.split("地址")[0])
    d["UID"] = m.group(1) if m else None
    m = re.search(r"从\s*(\d+(?:\.\d+)?)\s*%?\s*降到\s*(\d+(?:\.\d+)?)\s*%?", t)
    if m:
        d["佣金"], d["原佣金"], d["降佣"] = float(m.group(2)) / 100, float(m.group(1)) / 100, True
    else:
        m = re.search(r"(\d+(?:\.\d+)?)\s*%", t)
        d["佣金"] = float(m.group(1)) / 100 if m else None
    d["链接类型"] = "渠道品" if re.search(r"渠道品|专属链接|专属", t) else "全店" if "全店" in t else "普通" if re.search(r"普通|单链接|单品", t) else None
    m = re.search(r"([A-Z]{1,3}-?\d{2,6})", t)
    d["款号"] = m.group(1) if m else None
    if not d["款号"]:   # 真店的款多是中文名（实测 10-31「弯刀卫裤」）：找带品类字的那一段
        for seg in re.split(r"[，,；;。\s]+", t.split("地址")[0]):
            if re.search(r"(卫衣|卫裤|裤|衫|外套|开衫|裙|马甲|毛衣|羽绒服|T恤)$", seg) and not re.search(r"\d|%|UID|渠道品|普通|全店", seg, re.I):
                d["款号"] = seg; break
    m = re.search(rf"([{YANSE}]{{1,3}})色?\s*(XXXL|XXL|XL|[2-4]XL|L|M|S)", t)
    d["颜色"], d["尺码"] = (m.group(1), m.group(2)) if m else (None, None)
    m = re.search(r"(\d+|[一两二三四五六七八九十])\s*件", t)
    d["件数"] = (int(m.group(1)) if m.group(1).isdigit() else SHU[m.group(1)]) if m else None
    m = re.search(r"(?:地址|寄到|收件)[:：\s]*(.+)$", t)
    d["收件信息"] = m.group(1).strip() if m else None
    for k, why in [("UID", "达人 UID"), ("佣金", "佣金比例")] + ([] if d.get("降佣") else [("链接类型", "普通链接还是渠道品")]):
        if d.get(k) is None:
            que.append(why)
    if not d.get("降佣") and not d.get("款号"):
        que.append("哪一款")
    d["发版单还缺"] = [] if d.get("降佣") else [why for k, why in [("颜色", "颜色尺码"), ("件数", "几件"), ("收件信息", "地址（收件人、电话、地址）")] if d.get(k) is None]
    return d, que


def lu(d):
    if d.get("降佣"):
        return ["M-BY-006：找到这个 UID 的指定达人策略改佣金（降佣次日 0 点生效，R-LM-004）", "回读：佣金推广管理「佣金率范围」"]
    if d.get("链接类型") == "全店":
        return ["M-BY-007：全店定向合作 → 按 UID 绑定 → 固定佣金率（只对设了全部达人佣金的商品生效，优先级低于指定达人）", "回读：全店定向合作列表"]
    xs = ["M-BY-006：新增推广策略 → 选这款 → 指定达人佣金 → 加 UID → 固定佣金率"]
    if d.get("链接类型") == "渠道品":
        xs.append("M-DD-103：新建渠道品 → 专属达人带货 → 绑同一个 UID（渠道品继承主品佣金，不能在渠道品里设，R-LM-005）")
    return xs + ["回读：佣金推广管理「指定达人」列" + ("、渠道品列表按 UID 筛" if d.get("链接类型") == "渠道品" else "")]


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("话"); a.add_argument("--出")
    a = a.parse_args(argv)
    d, que = jie(a.话)
    d["路线"] = lu(d); d["缺"] = que
    show = {k: v for k, v in d.items() if k not in ("收件信息", "路线", "缺", "降佣", "发版单还缺") and v is not None}
    if not d.get("降佣"):
        show["收件信息"] = "已收（只进发版单）" if d.get("收件信息") else "没有"
    print("谈定单：" + "，".join(f"{k} {v:.0%}" if k in ("佣金", "原佣金") and v is not None else f"{k} {v}" for k, v in show.items()))
    print("要走：\n" + "\n".join(f"{i}. {x}" for i, x in enumerate(d["路线"], 1)))
    if d.get("降佣"):
        print(f"注意：佣金从 {d['原佣金']:.0%} 降到 {d['佣金']:.0%}，**次日 0 点才生效**（提高才是实时，R-LM-004）")
    if que:
        print("还缺：" + "、".join(que) + " → 只问这几样，问到再设")
    elif d.get("发版单还缺"):
        print("设链接的料齐了；寄样要的「" + "、".join(d["发版单还缺"]) + "」出发版单前再问（设链接不等它）")
    if a.出:
        pathlib.Path(a.出).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    raise SystemExit(3 if que else 0)


if __name__ == "__main__":
    main()
