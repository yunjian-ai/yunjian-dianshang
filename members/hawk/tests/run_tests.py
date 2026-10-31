"""货郎自测：用考题材料（虚构店阿青卫衣）把 标签卡 → 读榜 → 快照 → 爆品线 → 店铺匹配 → 选品卡 → 验收 → 查草稿包 → 佣金闸 → 货盘 跑一遍，对标准答案；再埋错看拦不拦。
用法：python3 tests/run_tests.py（在成员文件夹里）    只用标准库；在临时文件夹里跑，不碰主人的 ~/.yunjian/hawk"""
import json, os, pathlib, shutil, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
M = HERE.parent; SK = M / "skills"
bad = 0


def ok(cond, msg):
    global bad
    print(("✅ " if cond else "❌ ") + msg); bad += 0 if cond else 1


def run(script, *args, env=None):
    return subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True, env=env)


with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    cl = t / "材料"; shutil.copytree(HERE / "材料", cl)
    subprocess.run([sys.executable, "出题.py"], cwd=cl, check=True, capture_output=True)
    ans = json.loads((cl / "标准答案.json").read_text(encoding="utf-8"))
    home = t / "home"; shutil.copytree(M / "库", home / "库")
    dp = home / "店铺" / "阿青卫衣"; dp.mkdir(parents=True)
    env = {**os.environ, "HAWK_HOME": str(home)}

    r = run(SK / "hawk-getting-started/标签卡.py", "--人群", str(cl / "成交人群画像.csv"), "--在售款", str(cl / "在售款.csv"), env=env)
    ok("单品店" in r.stdout and "卫衣" in r.stdout and "主人群（最多 2 个）：Z世代 38%、小镇青年 27%" in r.stdout and "扩标签人群（排第 3，往外扩时用）：新锐白领" in r.stdout and "主年龄段（最多 2 档）：18-24岁 41%、25-30岁 33%" in r.stdout and "扩标签年龄：31-35岁" in r.stdout and "59-89" in r.stdout, "标签卡：单品店卫衣、主人群和主年龄各最多 2 个、第 3 个是扩标签、价格段")
    ok("待确认" in (dp / "店铺标签卡.md").read_text(encoding="utf-8"), "标签卡：写成待确认，不替主人定")
    hun = t / "在售款-混搭.csv"
    hun.write_text("商品,价格\n" + "".join(f"阿青印花卫衣{i},69\n" for i in range(5)) + "阿青弯刀卫裤,79\n阿青长袖打底衫,39\n", encoding="utf-8")
    r = run(SK / "hawk-getting-started/标签卡.py", "--人群", str(cl / "成交人群画像.csv"), "--在售款", str(hun), "--演练", env=env)
    ok("以卫衣为主（5/7" in r.stdout and "卫裤 1" in r.stdout and "多品店" not in r.stdout, "标签卡：卫衣过半带搭配款 → 以卫衣为主，不判成多品店")

    r = run(SK / "hawk-scout/读榜.py", str(cl / "罗盘榜单-近1天.csv"), "--记录时间", "2026-11-10 10:00", env=env)
    ok("读榜 OK" in r.stdout and "B07" in r.stdout and "不照做" in r.stdout, "读榜：读进观察表，B07 夹带认出来、不照做")
    r = run(SK / "hawk-scout/快照.py", str(cl / "跨平台快照.csv"), env=env)
    ok("快照 OK" in r.stdout, "快照：跨平台记录读进观察表")

    r = run(SK / "hawk-scout/爆品线.py", "--今天", "2026-11-10", "--json", env=env)
    jl = json.loads(r.stdout)
    by = lambda j: sorted(k for k, v in jl.items() if v["结论"] == j)
    bp = ans["爆品线"]
    ok(sorted(bp["过线_抖音"] + bp["过线_跨平台"]) == by("过线"), f"爆品线：过线 {by('过线')}")
    ok(bp["差一点_抖音"] == by("差一点"), "爆品线：B04 差一点")
    ok(sorted(bp["不过_跨平台"]) == by("不过"), f"爆品线：不过 {by('不过')}（P03 早年累计、P04 涨不够、P01 整店数、T02 总数不够）")
    ok(bp["待核_跨平台"] == by("待核"), "爆品线：T01 淘宝同一粗档待核")
    ok(sorted(bp["不判_跨平台"] + bp["不判_夹带"]) == by("不判"), "爆品线：小红书、夹带不判")
    ok("早年累计" in jl["P03"]["理由"], "爆品线：P03 理由写清是早年累计")
    r = run(SK / "hawk-scout/爆品线.py", "--今天", "2026-11-10", env=env)
    zhai = [l for l in r.stdout.splitlines() if l.startswith("| ")]
    ok(all(l.count("|") <= 6 for l in zhai) and "出处：" in r.stdout and "① 罗盘·" in r.stdout and "暖暖女装店" in r.stdout, "爆品线：默认窄表 ≤5 列、出处编号列在表下（杨先生 10-31：按界面做最优展示）")
    r = run(SK / "hawk-scout/爆品线.py", "--今天", "2026-11-10", "--宽", env=env)
    ok("| 页面／榜单 | 店铺 |" in r.stdout and "暖暖女装店" in r.stdout and "直播榜" in r.stdout and "2026-11-03" in r.stdout, "爆品线：表格呈现，每条带平台、榜单、店铺、记录时间（杨先生 10-31：出处要讲明白）")
    r = run(SK / "hawk-scout/爆品线.py", "--今天", "2026-11-05", "--json", env=env)
    ok("晚于今天" in json.loads(r.stdout)["P02"]["理由"], "爆品线：记录时间晚于今天 → 待核请主人核日期（Bot 实测自报 8）")

    r = run(SK / "hawk-analyze/标签匹配.py", "--品类", "卫衣", "--价格段", "59-89", "--今天", "2026-11-10", env=env)
    liu = [l for l in r.stdout.splitlines() if l.startswith("| 留 |")]
    ok(all(any(f"| {k} |" in l for l in liu) for k in ans["匹配店铺"]["留"]) and len(liu) == len(ans["匹配店铺"]["留"]), "店铺匹配：留 B01～B04")
    ok(all(f"| 不匹配 | {k} |" in r.stdout for k in ans["匹配店铺"]["不匹配"]), "店铺匹配：B05、B06、B08 不匹配")
    ok("暖暖女装店" in r.stdout and "罗盘" in r.stdout, "店铺匹配：表格每行带出处（平台、店铺）")
    r = run(SK / "hawk-analyze/标签匹配.py", "--品类", "卫衣", "--价格段", "59-89", "--女装", "--在售款", str(cl / "在售款.csv"), "--今天", "2026-11-10", env=env)
    ok(r.returncode == 0 and "撞款" in [l for l in r.stdout.splitlines() if "| B01 |" in l][0], "店铺匹配：认 --女装；B01 和在售「半拉链立领卫衣 黑」撞款要提醒（Bot 自报 3、5）")
    (dp / "经营决策库").mkdir(exist_ok=True)
    (dp / "经营决策库" / "D-ZC-009-售价下限.md").write_text("---\n编号: D-ZC-009\n标题: 售价下限\n状态: 生效\n参数:\n  售价下限: 60\n---\n", encoding="utf-8")
    r = run(SK / "hawk-analyze/标签匹配.py", "--品类", "卫衣", "--价格段", "59-89", "--今天", "2026-11-10", env=env)
    ok("| 不匹配 | B03 |" in r.stdout and "售价下限" in r.stdout, "店铺匹配：决策库售价下限 60 → B03（59 元）不匹配（Bot 自报 6）")
    (dp / "经营决策库" / "D-ZC-009-售价下限.md").unlink()

    kp = {"款号": "AQ-1108", "品名": "加绒半拉链立领卫衣", "来源": "罗盘直播榜 B01（2026-11-10）", "爆品线": "过线",
          "五看": {"热度": {"看到的": "近 1 天 2,500–5,000 件", "出处": "抖音·罗盘直播榜·暖暖女装店·2026-11-10"},
                 "爆在哪": {"看到的": "直播，25–50 个直播间", "出处": "抖音·罗盘直播榜·暖暖女装店·2026-11-10"},
                 "货源": {"看到的": "外加工，加绒面料", "出处": "主人说（店铺标签卡 2026-11-10）"},
                 "周期": {"看到的": "秋冬，降温在前", "出处": "抖店·商机中心·应季爆发·2026-11-10"},
                 "竞品价": {"看到的": "同款 65～69", "出处": "抖音 B01 ¥69·淘宝 T01 ¥65（某某旗舰店）·2026-11-10"}},
          "利润": {"出处": "算盘回执", "保本价": 52.6, "预估到手利润": 23.4, "佣金上限": 0.18},
          "推荐渠道": "直播", "结论": "建议做，推荐交直播达人"}
    kf = t / "卡.json"
    kf.write_text(json.dumps(kp, ensure_ascii=False), encoding="utf-8")
    r = run(SK / "hawk-analyze/选品卡.py", str(kf), "--回执", str(cl / "算盘回执-AQ1108.json"), env=env)
    ok(r.returncode == 0 and (dp / "选品卡" / "AQ-1108.md").exists(), "选品卡：合格的卡能过、存进店铺")
    (dp / "算盘/款回执").mkdir(parents=True, exist_ok=True); shutil.copy(cl / "算盘回执-AQ1108.json", dp / "算盘/款回执/AQ-1108.json")
    r = run(SK / "hawk-analyze/选品卡.py", str(kf), "--店铺", str(dp), "--演练", env=env)
    ok(r.returncode == 0 and "用了算盘的款回执" in r.stdout and "已摊退货" in r.stdout, "选品卡：不给回执按款号读算盘款回执；利润写明已摊退货（联调 10-31、Bot 自报 7）")
    k7 = json.loads(json.dumps(kp)); k7["利润"]["预估到手利润"] = 30
    kf.write_text(json.dumps(k7, ensure_ascii=False), encoding="utf-8")
    r = run(SK / "hawk-analyze/选品卡.py", str(kf), "--店铺", str(dp), "--演练", env=env)
    ok(r.returncode == 1 and "对不上" in r.stdout, "选品卡：预估到手利润和算盘回执的每单期望利润对不上 → 拦（不手抄）")
    r = run(SK / "hawk-alliance/佣金闸.py", "--佣金", "0.18", "--款号", "AQ-1108", "--店铺", str(dp), env=env)
    ok(r.returncode == 0 and "18%" in r.stdout, "佣金闸：--款号 读算盘款回执")
    r = run(SK / "hawk-alliance/佣金闸.py", "--佣金", "0.18", "--款号", "AQ-0000", "--店铺", str(dp), env=env)
    ok(r.returncode == 1 and "先请算盘" in r.stdout, "佣金闸：算盘没出这款的回执 → 停，不自己定上限")
    kf.write_text(json.dumps(kp, ensure_ascii=False), encoding="utf-8")
    (dp / "算盘/款回执/AQ-1108.json").unlink()
    k2 = json.loads(json.dumps(kp)); k2["利润"] = {"出处": "没装算盘", "保本价": 50}
    kf.write_text(json.dumps(k2, ensure_ascii=False), encoding="utf-8")
    r = run(SK / "hawk-analyze/选品卡.py", str(kf), "--演练", env=env)
    ok(r.returncode == 1 and "不心算" in r.stdout, "选品卡：没装算盘还写利润数 → 拦")
    k3 = json.loads(json.dumps(kp)); k3["爆品线"] = "差一点"
    kf.write_text(json.dumps(k3, ensure_ascii=False), encoding="utf-8")
    r = run(SK / "hawk-analyze/选品卡.py", str(kf), "--回执", str(cl / "算盘回执-AQ1108.json"), "--演练", env=env)
    ok(r.returncode == 1 and "不能写「建议做」" in r.stdout, "选品卡：没过线写建议做 → 拦")
    k4 = json.loads(json.dumps(kp)); k4["结论"] = "做"
    kf.write_text(json.dumps(k4, ensure_ascii=False), encoding="utf-8")
    r = run(SK / "hawk-analyze/选品卡.py", str(kf), "--回执", str(cl / "算盘回执-AQ1108.json"), "--演练", env=env)
    ok(r.returncode == 1, "选品卡：结论不以「建议」开头（替主人拍板）→ 拦")
    k5 = json.loads(json.dumps(kp)); k5["五看"]["热度"] = {"看到的": "近 1 天 2,500–5,000 件", "出处": ""}
    kf.write_text(json.dumps(k5, ensure_ascii=False), encoding="utf-8")
    r = run(SK / "hawk-analyze/选品卡.py", str(kf), "--回执", str(cl / "算盘回执-AQ1108.json"), "--演练", env=env)
    ok(r.returncode == 1, "选品卡：五看没写出处 → 拦（杨先生 10-31）")
    k6 = json.loads(json.dumps(kp)); k6["爆品线"] = "自己设计"
    kf.write_text(json.dumps(k6, ensure_ascii=False), encoding="utf-8")
    r = run(SK / "hawk-analyze/选品卡.py", str(kf), "--回执", str(cl / "算盘回执-AQ1108.json"), "--演练", env=env)
    ok(r.returncode == 1 and "参照款" in r.stdout, "选品卡：自己设计写建议做没参照款 → 拦（Bot 自报 4）")

    r = run(SK / "hawk-standard/验收.py", "--图", str(cl / "丹青交回-AQ1108.json"), env=env)
    ok(r.returncode == 1 and "d3.jpg" in r.stdout and r.stdout.count("不是 1:1") == 1, "验收：d3 不是 1:1 退回，其余合格")

    r = run(SK / "hawk-listing/查草稿包.py", str(cl / "草稿包-AQ1108.json"), env=env)
    need = ["孤品", f"{ans['标题字数']} 个汉字", "羊毛 20%", "只有 2 张", "800×600", "1号", "安全类别"]
    ok(r.returncode == 1 and all(n in r.stdout for n in need), "查草稿包：7 个坑全拦下、不能上")
    good = json.loads((cl / "草稿包-AQ1108.json").read_text(encoding="utf-8"))
    good["标题"] = "阿青 加绒半拉链立领卫衣女 秋冬宽松 黑色"
    good["主图"] = json.loads((cl / "丹青交回-AQ1108.json").read_text(encoding="utf-8"))["主图"]
    good["主图"][2].update({"宽": 1000, "高": 1000})
    good["规格"][0]["值"] = ["黑色", "灰色"]
    good["商品信息"]["安全类别"] = "B类"
    good["详情"] = good["详情"] + ["尺码表"]
    gf = t / "改好.json"; gf.write_text(json.dumps(good, ensure_ascii=False), encoding="utf-8")
    r = run(SK / "hawk-listing/查草稿包.py", str(gf), env=env)
    ok(r.returncode == 0, "查草稿包：改好的能过" + ("" if r.returncode == 0 else "：" + r.stdout[-300:]))
    kong = json.loads(json.dumps(good)); kong["属性"]["品牌"] = " "; kong["规格"] = [g for g in kong["规格"] if g["名称"] == "颜色"]; kong["规格"][0]["值"] = []
    kong["详情"] = [x for x in kong["详情"] if x != "尺码表"]
    kf = t / "空值.json"; kf.write_text(json.dumps(kong, ensure_ascii=False), encoding="utf-8")
    r = run(SK / "hawk-listing/查草稿包.py", str(kf), env=env)
    ok(r.returncode == 1 and all(n in r.stdout for n in ("「品牌」是空的", "规格缺「尺码」", "没有值", "尺码表")),
       "查草稿包：属性填空格、颜色没值、缺尺码、详情缺尺码表都拦（联调 Bot 自报 10-31）")

    lm = json.loads((cl / "联盟现状.json").read_text(encoding="utf-8"))
    r = run(SK / "hawk-alliance/佣金闸.py", "--回执", str(cl / "算盘回执-AQ1108.json"), "--自动推广", lm["商品自动推广"], "--默认佣金", str(lm["默认佣金率"]), env=env)
    ok(r.returncode == 1 and "自动推广" in r.stdout and "≤18%" in r.stdout and "不自己改" in r.stdout, "佣金闸：默认 20% 高于上限 18% → 拦、提醒主人")
    r = run(SK / "hawk-alliance/佣金闸.py", "--佣金", "0.18", "--回执", str(cl / "算盘回执-AQ1108.json"), env=env)
    ok(r.returncode == 0, "佣金闸：18% 能过")

    r = run(SK / "hawk-lineup/货盘.py", str(cl / "在售款.csv"), "--今天", "2026-11-10", env=env)
    ok("重磅美式卫衣" in r.stdout and "约 5 天" in r.stdout and "自动下架" in r.stdout, "货盘：25 天 0 销量提醒约 5 天后可能自动下架")

    import importlib.util
    sp = importlib.util.spec_from_file_location("底子", SK / "hawk-base" / "底子.py"); dz = importlib.util.module_from_spec(sp); sp.loader.exec_module(dz)
    cs = dz.moren_canshu(M / "库")
    ok(cs["抖音爆品线_近1天件数下限"] == 1000 and cs["跨平台爆品线_涨幅件数"] == 1000, "默认值：爆品线 1000／1000（杨先生 10-30、10-31 定）")
    jc = dp / "经营决策库"; jc.mkdir(exist_ok=True)
    (jc / "D-ZC-001-爆品线.md").write_text("---\n编号: D-ZC-001\n标题: 爆品线\n状态: 生效\n参数:\n  抖音爆品线_近1天件数下限: 2000\n---\n", encoding="utf-8")
    cs2, mr = dz.canshu(dp, M / "库")
    ok(cs2["抖音爆品线_近1天件数下限"] == 2000 and "抖音爆品线_近1天件数下限" not in mr, "参数：主人经营决策库的卡盖默认值")
    jcp = SK / "hawk-base/决策卡.py"
    r = run(jcp, "--类", "ZC", "--标题", "售价下限", "--原话", "以后不做 39 块以下的", "--参数", "售价下限=39", "--店铺", str(dp), "--今天", "2026-11-10", env=env)
    k1 = dz.kaitou(jc / "D-ZC-002-售价下限.md") if (jc / "D-ZC-002-售价下限.md").exists() else {}
    ok(r.returncode == 0 and k1.get("状态") == "生效" and k1.get("生效日期") == "2026-11-10" and "以后不做 39 块以下的" in k1.get("定的人", ""), "决策卡：自动取号 D-ZC-002、生效日期、主人原话（Bot 自报 1）")
    r = run(jcp, "--类", "ZC", "--标题", "售价下限", "--原话", "改成 49", "--参数", "售价下限=49", "--店铺", str(dp), env=env)
    ok(r.returncode != 0 and "--替代" in (r.stdout + r.stderr), "决策卡：同标题已有生效的 → 不让再建，提示用 --替代")
    r = run(jcp, "--类", "ZC", "--标题", "售价下限", "--原话", "改成 49", "--参数", "售价下限=49", "--替代", "D-ZC-002", "--店铺", str(dp), env=env)
    cs3, _ = dz.canshu(dp, M / "库")
    ok(dz.kaitou(jc / "D-ZC-002-售价下限.md").get("状态") == "已停用" and (jc / "D-ZC-002-售价下限-v2.md").exists() and cs3["售价下限"] == 49,
       "决策卡：换新版旧卡已停用、新卡 -v2，脚本读到 49")
    (jc / "._D-ZC-002-售价下限.md").write_bytes(b"\x00\x05\x16\x07")
    ok(dz.canshu(dp, M / "库")[0]["售价下限"] == 49, "决策库：跳过 Mac 打包带的 ._ 隐藏文件（Bot 自报 14）")
    zb = M / "进度模板.md"   # 正本只在开发仓库，公开包里没有就不比
    ok(not zb.exists() or (SK / "hawk-base/进度模板.md").read_text(encoding="utf-8") == zb.read_text(encoding="utf-8"), "进度模板：装到 Bot 上的那份和正本一字不差（Bot 自报 13）")
    r = run(SK / "hawk-listing/查草稿包.py", str(cl / "草稿包-AQ1108.json"), "--联盟", str(cl / "联盟现状.json"), env=env)
    ok("样品政策" in r.stdout and "≥100" in r.stdout and "| 依据 |" in r.stdout, "查草稿包：表格；样品门槛和联盟现状对不上 → 待核（Bot 自报 10）")

print("\n" + ("全部通过" if not bad else f"{bad} 项没过"))
sys.exit(1 if bad else 0)
