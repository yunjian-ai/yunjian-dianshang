"""经纪 · 回读核对：谈定单 ↔ 设完以后在后台读回来的（指定达人列、佣金率、渠道品绑定）→ 一致／不一致
用法：python3 回读核对.py --谈定单 <谈定单.json> --回读 <回读.json>
回读.json 照后台抄：{"UID": "...", "佣金": 0.16, "款号": "AQ-1108", "渠道品绑定UID": "...", "渠道类型": "专属达人带货"}（普通链接没有后两项）。
不一致退出码 1：合作单不往下走，告诉主人哪一项对不上。"""
import argparse, json, pathlib


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--谈定单", required=True); a.add_argument("--回读", required=True)
    a = a.parse_args(argv)
    d = json.loads(pathlib.Path(a.谈定单).read_text(encoding="utf-8")); r = json.loads(pathlib.Path(a.回读).read_text(encoding="utf-8"))
    cuo = []
    for k in ("UID", "款号"):
        if d.get(k) and str(d[k]) != str(r.get(k)):
            cuo.append(f"{k}：谈定 {d[k]}，后台 {r.get(k)}")
    if d.get("佣金") is not None and abs(float(d["佣金"]) - float(r.get("佣金", -1))) > 1e-6:
        cuo.append(f"佣金：谈定 {d['佣金']:.0%}，后台 {float(r.get('佣金', 0)):.0%}" + ("（降佣次日 0 点才生效，明天再回读一次）" if d.get("降佣") else ""))
    if d.get("链接类型") == "渠道品":
        if str(r.get("渠道品绑定UID")) != str(d.get("UID")):
            cuo.append(f"渠道品绑定：应绑 {d.get('UID')}，后台 {r.get('渠道品绑定UID')}")
        if r.get("渠道类型") != "专属达人带货":
            cuo.append(f"渠道类型：应是「专属达人带货」，后台「{r.get('渠道类型')}」")
    if cuo:
        print("回读对不上：\n" + "\n".join("- " + x for x in cuo) + "\n（合作单停在⑥，告诉主人）"); raise SystemExit(1)
    print("回读一致：" + "、".join(k for k in ("UID", "款号", "佣金") if d.get(k) is not None) + ("、渠道品绑定" if d.get("链接类型") == "渠道品" else ""))


if __name__ == "__main__":
    main()
