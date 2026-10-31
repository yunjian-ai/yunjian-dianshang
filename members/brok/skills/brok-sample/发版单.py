"""经纪 · 发版单：谈定单（含收件信息）→ 给厂家的发版单（款、色、码、件数、收件人、电话、地址），写进店铺 发版单/ 文件夹
用法：python3 发版单.py --谈定单 <谈定单.json> --单号 H11 [--厂家 某厂] [--出 <文件>] [--今天 …] [--店铺 …]
收件信息是隐私：**只写进发版单文件**，屏幕上只说写到哪了（杨先生 10-31：厂家发版＝发样衣）。缺款色码件数地址就不出，退出码 1。"""
import argparse, datetime as dt, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brok-base")); import 底子, 回执


def shoujian(s):
    m = re.search(r"1[3-9]\d{9}", s or "")
    if not m:
        return None
    ren = re.sub(r"[：:，,\s]+$", "", s[:m.start()]).strip() or "（没写）"
    di = re.sub(r"^[，,\s]+", "", s[m.end():]).strip()
    return ren, m.group(0), di


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--谈定单", required=True); a.add_argument("--单号", required=True)
    a.add_argument("--厂家", default="（经纪设置卡里的厂家）"); a.add_argument("--出"); a.add_argument("--今天"); a.add_argument("--店铺")
    a = a.parse_args(argv)
    d = json.loads(pathlib.Path(a.谈定单).read_text(encoding="utf-8"))
    sj = shoujian(d.get("收件信息") or "")
    que = [k for k in ("款号", "颜色", "尺码", "件数") if not d.get(k)] + ([] if sj and sj[2] else ["收件人、电话、地址"])
    if que:
        print("发版单出不了，缺：" + "、".join(que) + " → 只问这几样"); raise SystemExit(1)
    ren, dh, di = sj
    jin = a.今天 or str(底子.jintian())
    t = f"""发版单 · {a.单号}（{jin}）
给：{a.厂家}
| 款号 | 颜色 | 尺码 | 件数 |
|---|---|---|---|
| {d['款号']} | {d['颜色']} | {d['尺码']} | {d['件数']} |
收件人：{ren}　电话：{dh}　地址：{di}
要求：48 小时内发出（R-LM-001），单号发回给主人（回填合作单 {a.单号}）。
"""
    p = pathlib.Path(a.出) if a.出 else 底子.dianpu(a.店铺) / "发版单" / f"{a.单号}-{jin}.md"
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(t, encoding="utf-8")
    if not a.出:
        回执.ji(底子.dianpu(a.店铺), "brok", zuole={"发版单": 1}, chule=[f"发版单 {a.单号}"], chuchu="经纪·发版单", jintian=jin)
    print(f"发版单已写到 {p}：{d['款号']} {d['颜色']} {d['尺码']} × {d['件数']}，给 {a.厂家}；收件信息只在这份发版单里。\n提醒：厂家 48 小时内发货、单号回填合作单 {a.单号}（合作单走到⑦）。")


if __name__ == "__main__":
    main()
