"""掌柜 · 推送：把出报.py／提醒.py 存下的卡片或文字发出去。
用法：python3 推送.py (--卡片 <卡片.json> | --文字 <报.md>) [--飞书群 oc_xxx] [--飞书机器人 <群机器人地址>] [--演练]
- --飞书群：本机装了 lark-cli、机器人在群里时用（自用）；
- --飞书机器人：主人自己在飞书群里加的「自定义机器人」地址（公开版；地址只存在主人的掌柜设置里，不进仓库）；
- 都不给：原样打印，由 Bot 在对话里发给主人。
发之前再打一遍码（手机号、微信号）。发失败退出码 1，不重发，写明原因。"""
import argparse, json, pathlib, subprocess, sys, urllib.request
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "keep-base")); import 底子


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("--卡片"); a.add_argument("--文字"); a.add_argument("--飞书群"); a.add_argument("--飞书机器人")
    a.add_argument("--演练", action="store_true")
    a = a.parse_args(argv)
    if not (a.卡片 or a.文字):
        raise SystemExit("要给 --卡片 或 --文字")
    if a.卡片:
        k = json.loads(底子.daima(pathlib.Path(a.卡片).read_text(encoding="utf-8")))
    t = 底子.daima(pathlib.Path(a.文字).read_text(encoding="utf-8")) if a.文字 else None
    if a.演练 or not (a.飞书群 or a.飞书机器人):
        print(t if t else json.dumps(k, ensure_ascii=False, indent=1)); return
    if a.飞书群:
        if a.卡片:
            tmp = pathlib.Path(a.卡片).with_suffix(".发.json"); tmp.write_text(json.dumps(k, ensure_ascii=False), encoding="utf-8")
            cmd = ["lark-cli", "im", "+messages-send", "--as", "bot", "--chat-id", a.飞书群, "--msg-type", "interactive", "--content", "@" + tmp.name]
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=tmp.parent)
        else:
            r = subprocess.run(["lark-cli", "im", "+messages-send", "--as", "bot", "--chat-id", a.飞书群, "--markdown", t], capture_output=True, text=True)
        ok = r.returncode == 0 and '"ok": true' in r.stdout
        print("已推到飞书群" if ok else "推送失败：" + (r.stdout + r.stderr)[-300:])
        raise SystemExit(0 if ok else 1)
    body = {"msg_type": "interactive", "card": k} if a.卡片 else {"msg_type": "text", "content": {"text": t}}
    req = urllib.request.Request(a.飞书机器人, data=json.dumps(body, ensure_ascii=False).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            ret = json.loads(resp.read().decode() or "{}")
    except Exception as e:  # noqa: BLE001
        print(f"推送失败：{e}"); raise SystemExit(1)
    ok = ret.get("code", ret.get("StatusCode", 0)) == 0
    print("已推到飞书群机器人" if ok else f"推送失败：{ret}")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
