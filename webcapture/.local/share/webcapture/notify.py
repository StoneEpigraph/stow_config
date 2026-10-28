#!/usr/bin/env python3
"""截图失败报警：钉钉群机器人 / 企业微信群机器人 Webhook。

配置：~/webcapture/notify.conf（KEY=VALUE）
测试：notify.py --test
"""

import os
import sys
import json
import time
import hmac
import base64
import hashlib
import urllib.parse
import urllib.request

CONF = os.path.expanduser("~/webcapture/notify.conf")
LOG = os.path.expanduser("~/webcapture/capture.log")


def log(msg):
    from datetime import datetime
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] NOTIFY {msg}\n")
    except Exception:
        pass


def load_conf():
    conf = {}
    if not os.path.exists(CONF):
        return conf
    with open(CONF, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            conf[k.strip()] = v.strip().strip('"').strip("'")
    return conf


def post_json(url, payload, timeout=12):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", "replace")
    try:
        j = json.loads(body)
    except Exception:
        return True, body[:200]
    code = j.get("errcode", j.get("code", 0))
    return (code == 0), body[:300]


def _clamp(text, limit_bytes):
    """按字节截断（企业微信 markdown 单条上限 4096 字节）。

    注意：截断提示本身也要占预算。若剩余预算装不下提示，就直接硬截断 ——
    否则会出现「只剩截断提示、正文和标题关键词全被吃掉」的情况（钉钉关键词
    校验会因此报 310000 关键词不匹配，整条报警发不出去）。
    """
    b = text.encode("utf-8")
    if len(b) <= limit_bytes:
        return text
    tail = "\n\n…（内容过长已截断，完整信息见 ~/webcapture/capture.log）"
    keep = limit_bytes - len(tail.encode())
    if keep < 32:
        return b[:max(0, limit_bytes)].decode("utf-8", "ignore")
    return b[:keep].decode("utf-8", "ignore") + tail


def send_dingtalk(conf, title, text):
    hook = conf.get("DINGTALK_WEBHOOK", "")
    if not hook:
        return None
    secret = conf.get("DINGTALK_SECRET", "")
    if secret:
        ts = str(round(time.time() * 1000))
        sign = base64.b64encode(
            hmac.new(secret.encode(), f"{ts}\n{secret}".encode(), hashlib.sha256).digest()
        )
        hook += f"&timestamp={ts}&sign={urllib.parse.quote_plus(sign)}"
    kw = conf.get("DINGTALK_KEYWORD", "")
    if kw and kw not in title and kw not in text:
        title = f"{kw} {title}"
    return post_json(hook, {"msgtype": "markdown",
                            "markdown": {"title": _clamp(title, 200),
                                         "text": _clamp(text, 18000)}})


def send_wecom(conf, title, text):
    hook = conf.get("WECOM_WEBHOOK", "")
    if not hook:
        return None
    return post_json(hook, {"msgtype": "markdown",
                            "markdown": {"content": _clamp(f"**{title}**\n{text}", 3800)}})


def send(title, text):
    """向所有已配置渠道发送；返回 {渠道: (是否成功, 响应)}"""
    conf = load_conf()
    results = {}
    for name, fn in (("dingtalk", send_dingtalk), ("wecom", send_wecom)):
        try:
            r = fn(conf, title, text)
        except Exception as e:
            r = (False, f"{type(e).__name__}: {e}")
        if r is None:
            continue
        results[name] = r
        log(f"{name} {'OK' if r[0] else 'FAIL'} {r[1]}")
    if not results:
        log("未配置任何 webhook，跳过报警")
    return results


def _fmt_dur(sec):
    sec = int(max(0, sec))
    d, rem = divmod(sec, 86400)
    hh, rem = divmod(rem, 3600)
    mm, ss = divmod(rem, 60)
    if d:
        return f"{d}天{hh}小时{mm}分"
    if hh:
        return f"{hh}小时{mm}分"
    if mm:
        return f"{mm}分{ss}秒"
    return f"{ss}秒"


def _unpack(item):
    """失败项支持 (url, err) 与 (url, err, state) 两种形式。"""
    if len(item) >= 3:
        return item[0], item[1], item[2] or {}
    return item[0], item[1], {}


def build_fail_text(ts, fails, oks, retried):
    n_silent = sum(1 for f in fails if _unpack(f)[2].get("action") == "silent")
    only_one = n_silent == 0 and len(fails) == 1

    lines = [f"**时间**：{ts}",
             "",
             f"**结果**：失败 {len(fails)} / 共 {len(fails) + len(oks)}",
             ""]
    for item in fails:
        url, err, st = _unpack(item)
        lines.append(f"- ❌ {url}")
        lines.append(f"  {err}")
        n = int(st.get("fail_count", 0) or 0)
        if n > 1:
            dur = _fmt_dur(st.get("seconds", 0))
            since = st.get("first_fail_at", "")
            lines.append(f"  连续失败第 {n} 次，已持续 {dur}"
                         + (f"（首次 {since}）" if since else ""))
        elif n == 1:
            lines.append("  首次失败")
        if st.get("action") == "silent":
            nxt = _fmt_dur(st.get("next_alert_in", 0))
            lines.append(f"  （本条为降频静默，约 {nxt} 后再提醒）")
    if oks:
        lines.append("")
        lines.append("**已成功**：" + "、".join(oks))
    if retried:
        lines.append("")
        lines.append("**重试后成功**：" + "、".join(retried))
    if n_silent:
        lines.append("")
        lines.append(f"**降频中**：{n_silent} 个站点本轮未重复提醒，持续失败会按间隔再报。")
    if only_one and not oks:
        lines.append("")
        lines.append("> 全部站点均失败，可能是网络或浏览器问题，建议先看 capture.log。")
    return "\n".join(lines)


def build_recover_text(ts, recovered, total):
    lines = [f"**时间**：{ts}", "",
             f"**已恢复**：{len(recovered)} / {total}", ""]
    for info in recovered:
        url = info.get("url") or info.get("host", "")
        lines.append(f"- ✅ {url}")
        n = int(info.get("fail_count", 0) or 0)
        dur = _fmt_dur(info.get("seconds", 0))
        lines.append(f"  连续失败 {n} 次后恢复，中断 {dur}")
        err = (info.get("last_error") or "").strip()
        if err:
            lines.append(f"  最后错误：{err[:160]}")
    lines.append("")
    lines.append("截图已恢复正常，后续按 15 分钟继续。")
    return "\n".join(lines)


def main():
    if "--preview" in sys.argv:
        print("=== 失败报警（示例：首次失败 + 一个降频静默）===")
        print(build_fail_text(
            "2026-10-22 10:15:03",
            [("https://www.bjyouth.gov.cn/",
              "TimeoutError: Page.goto: Timeout 60000ms exceeded.",
              {"action": "alert", "fail_count": 1, "seconds": 0}),
             ("https://www.bjydf.cn/",
              "TimeoutError: Page.goto: Timeout 60000ms exceeded.",
              {"action": "silent", "fail_count": 5, "seconds": 4020,
               "first_fail_at": "2026-10-22 09:08:11", "next_alert_in": 2880})],
            ["www.bjjdzx.com"], ["www.juanzhuzhongxin.cn"]))
        print()
        print("=== 续报（示例：连续失败第 3 次）===")
        print(build_fail_text(
            "2026-10-22 11:15:03",
            [("https://www.bjyouth.gov.cn/",
              "TimeoutError: Page.goto: Timeout 60000ms exceeded.",
              {"action": "alert", "fail_count": 3, "seconds": 3600,
               "first_fail_at": "2026-10-22 10:15:01"})],
            ["www.bjjdzx.com", "www.bjydf.cn", "www.juanzhuzhongxin.cn"], []))
        print()
        print("=== 恢复报警（示例）===")
        print(build_recover_text("2026-10-22 11:30:05", [{
            "url": "https://www.bjyouth.gov.cn/", "host": "www.bjyouth.gov.cn",
            "fail_count": 3, "seconds": 4500,
            "last_error": "TimeoutError: Page.goto: Timeout 60000ms exceeded.",
        }], 4))
        print()
        print("=== 变更报警（示例）===")
        print("**时间**：2026-10-22 10:15:03\n\n**变更站点**：1 / 4\n\n"
              "**【www.bjjdzx.com】**\n\n文本变更：+1 行 / -1 行\n\n"
              "＋ 关于2026年度申报工作的通知\n\n－ 关于2025年度申报工作的通知\n\n"
              "图像变化：3.29%\n\n差异图：~/public/webcapture/_diffs/www.bjjdzx.com/20261022-101503.png")
        conf = load_conf()
        print(f"\n=== 当前渠道 ===\n钉钉：{'已配置' if conf.get('DINGTALK_WEBHOOK') else '未配置'}"
              f"（加签{'有' if conf.get('DINGTALK_SECRET') else '无'}，"
              f"关键词 {conf.get('DINGTALK_KEYWORD') or '无'}）\n"
              f"企业微信：{'已配置' if conf.get('WECOM_WEBHOOK') else '未配置'}\n"
              f"失败降频：连续失败时每 {conf.get('FAIL_ALERT_INTERVAL') or '3600'} 秒最多一条\n"
              f"恢复通知：{'开' if (conf.get('ALERT_ON_RECOVER') or '1') != '0' else '关'}\n"
              f"配置文件：{CONF}")
        return 0
    if "--test" in sys.argv:
        from datetime import datetime
        ts = f"{datetime.now():%Y-%m-%d %H:%M:%S}"
        r = send("✅ 截图报警通道测试", build_fail_text(
            ts, [("https://示例.com/", "TimeoutError: 这是一条测试消息")], ["ok.example.com"], []))
        if not r:
            print(f"没有可用渠道：请编辑 {CONF} 填入 webhook")
            return 1
        for k, (ok, resp) in r.items():
            print(f"{k}: {'成功' if ok else '失败'}  {resp}")
        return 0 if all(v[0] for v in r.values()) else 2
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
