#!/usr/bin/env python3
"""站点健康状态：连续失败计数、失败降频、恢复判定。

状态文件：~/webcapture/state/<host>.health.json
  fail_count     连续失败次数（0 表示正常）
  first_fail_ts  本轮连续失败的起始时间戳
  last_alert_ts  上次发出失败报警的时间戳（用于降频）
  last_error     最后一次的错误摘要

设计要点：
- 失败第一次必定报警；之后按 interval 降频，避免一天刷 96 条。
- 恢复只发一次：从 fail_count>0 变回 0 的那一轮。
"""

import os
import json
import time
from datetime import datetime

OUT_ROOT = os.path.expanduser("~/webcapture")
STATE_DIR = os.path.join(OUT_ROOT, "state")
DEFAULT_INTERVAL = 3600  # 连续失败时的最小提醒间隔（秒）


def _path(host):
    return os.path.join(STATE_DIR, host + ".health.json")


def load(host):
    try:
        with open(_path(host), encoding="utf-8") as f:
            d = json.load(f)
            return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def save(host, h):
    os.makedirs(STATE_DIR, exist_ok=True)
    tmp = _path(host) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(h, f, ensure_ascii=False, indent=1)
    os.replace(tmp, _path(host))


def fmt_dur(sec):
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


def _stamp(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def on_fail(host, err, interval=DEFAULT_INTERVAL):
    """记录一次失败，返回 {'action': 'alert'|'silent', ...}。"""
    now = time.time()
    h = load(host)
    h["fail_count"] = int(h.get("fail_count", 0)) + 1
    if not h.get("first_fail_ts"):
        h["first_fail_ts"] = now
        h["first_fail_at"] = _stamp(now)
    h["last_fail_ts"] = now
    h["last_fail_at"] = _stamp(now)
    h["last_error"] = (err or "")[:300]

    last_alert = float(h.get("last_alert_ts") or 0)
    is_first = h["fail_count"] == 1
    due = interval <= 0 or (now - last_alert) >= interval
    send = is_first or due
    if send:
        h["last_alert_ts"] = now
        h["alerted"] = int(h.get("alerted", 0)) + 1
    save(host, h)

    return {
        "action": "alert" if send else "silent",
        "host": host,
        "fail_count": h["fail_count"],
        "seconds": now - float(h["first_fail_ts"]),
        "first_fail_at": h.get("first_fail_at", ""),
        "last_error": h["last_error"],
        "next_alert_in": max(0, int(interval - (now - last_alert))) if not send else 0,
    }


def on_ok(host):
    """记录一次成功。此前处于失败态则返回恢复信息，否则返回 None。"""
    h = load(host)
    n = int(h.get("fail_count", 0))
    if n <= 0:
        if h and (set(h) - {"fail_count"}):
            save(host, {"fail_count": 0})
        return None

    now = time.time()
    info = {
        "host": host,
        "fail_count": n,
        "seconds": now - float(h.get("first_fail_ts") or now),
        "first_fail_at": h.get("first_fail_at", ""),
        "last_error": h.get("last_error", ""),
        "alerted": int(h.get("alerted", 0)),
    }
    save(host, {"fail_count": 0, "cleared_at": _stamp(now)})
    return info


def snapshot(host):
    """当前健康快照（用于排障）。"""
    h = load(host)
    return {
        "host": host,
        "fail_count": int(h.get("fail_count", 0)),
        "first_fail_at": h.get("first_fail_at", ""),
        "last_error": h.get("last_error", ""),
        "alerted": int(h.get("alerted", 0)),
    }
