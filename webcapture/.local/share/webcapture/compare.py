#!/usr/bin/env python3
"""网页变更检测：文本哈希 + 整页图对比。

设计要点
- 文本：取 JS 执行后的 body.innerText，归一化后 sha256 —— 内容变更是主信号（抗轮播图/广告噪声）。
- 图片：对比**打水印前**的原始整页截图（水印每次都变，带水印比会每张都全页差异）。
  只保留上一张 raw 作基线，磁盘占用有界。
- 基线第一次写入时报 baseline=True，不报警。
"""

import os
import re
import json
import hashlib
from datetime import datetime

from PIL import Image, ImageChops, ImageDraw

STATE_DIR = os.path.expanduser("~/webcapture/state")
DIFF_DIR = os.path.expanduser("~/public/webcapture/_diffs")
CONF = os.path.expanduser("~/webcapture/compare.conf")

DEFAULT_CONF = {
    "ALERT_ON_TEXT_CHANGE": "1",
    "ALERT_ON_IMAGE_CHANGE": "0",
    "IMAGE_DIFF_THRESHOLD": "0.02",
    "IGNORE_REGEX": r"^\d+/\d+$|^\d{1,2}:\d{2}(:\d{2})?$",
    "STRIP_DATE_PREFIX": "1",
    "MAX_SNIPPET_LINES": "6",
}


def load_conf():
    conf = dict(DEFAULT_CONF)
    if os.path.exists(CONF):
        with open(CONF, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                conf[k.strip()] = v.strip().strip('"').strip("'")
    return conf


# 行首的「YYYY年M月D日 星期X」：属于站点顶栏的当日日期，不是内容。
# 有的站点这条时有时无（见 capture.py 里 window.onload 的说明），必须剥掉否则每轮误报。
# 注意两点，否则会把正常内容吃掉：
#   1. 必须后面还有实际内容（\s+(?=\S)）—— 有站点的正文里就有「整行只有一个日期」的条目
#      （如 bjjdzx 的 1844年10月24日 / 1928年10月24日），整行只有一个日期不能被剥空；
#   2. 剥完只剩「星期六」这种残片也要丢掉。
DATE_PREFIX_RE = re.compile(
    r"^\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日"
    r"(\s*星期[一二三四五六日天])?\s+(?=\S)"
)
WEEKDAY_ONLY_RE = re.compile(r"^星期[一二三四五六日天]$")


def norm_text(raw):
    """归一化：去零宽字符、行尾空白、连续空白、行首日期前缀、可选忽略行。"""
    conf = load_conf()
    ignore = conf.get("IGNORE_REGEX", "")
    pat = re.compile(ignore) if ignore else None
    strip_date = conf.get("STRIP_DATE_PREFIX", "1") not in ("0", "false", "no", "")
    lines = []
    for ln in (raw or "").splitlines():
        ln = ln.replace("\u200b", "").replace("\xa0", " ")
        ln = re.sub(r"[ \t]+", " ", ln).strip()
        if not ln:
            continue
        if strip_date:
            ln = DATE_PREFIX_RE.sub("", ln).strip()
            if not ln or WEEKDAY_ONLY_RE.match(ln):
                continue
        if pat and pat.search(ln):
            continue
        lines.append(ln)
    return "\n".join(lines)


def text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _paths(host):
    os.makedirs(STATE_DIR, exist_ok=True)
    return {
        "meta": os.path.join(STATE_DIR, f"{host}.json"),
        "text": os.path.join(STATE_DIR, f"{host}.txt"),
        "prev_raw": os.path.join(STATE_DIR, f"{host}.prev.png"),
    }


def load_state(host):
    p = _paths(host)
    if not os.path.exists(p["meta"]):
        return None
    try:
        with open(p["meta"], encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_state(host, meta):
    p = _paths(host)
    with open(p["meta"], "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def text_diff(old_text, new_text, max_lines=6):
    """返回 (added, removed) 行列表，超出截断。"""
    import difflib
    old_l = old_text.splitlines()
    new_l = new_text.splitlines()
    added, removed = [], []
    for line in difflib.unified_diff(old_l, new_l, lineterm="", n=0):
        if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
            continue
        if line.startswith("+"):
            added.append(line[1:].strip())
        elif line.startswith("-"):
            removed.append(line[1:].strip())
    return added[:max_lines], removed[:max_lines], len(added), len(removed)


def image_diff(prev_path, cur_path, out_path=None, threshold_pixel=25, save_min_ratio=0.003):
    """对齐到相同宽度与较小高度做逐像素比较。返回变化像素占比。"""
    if not (os.path.exists(prev_path) and os.path.exists(cur_path)):
        return None
    a = Image.open(prev_path).convert("RGB")
    b = Image.open(cur_path).convert("RGB")
    w = max(a.width, b.width)
    if a.width != w:
        a = a.resize((w, int(a.height * w / a.width)), Image.LANCZOS)
    if b.width != w:
        b = b.resize((w, int(b.height * w / b.width)), Image.LANCZOS)
    h = min(a.height, b.height)
    a = a.crop((0, 0, w, h))
    b = b.crop((0, 0, w, h))

    diff = ImageChops.difference(a, b).convert("L")
    mask = diff.point(lambda p: 255 if p > threshold_pixel else 0)
    total = w * h
    changed = mask.histogram()[255]
    ratio = changed / total if total else 0.0

    if out_path and ratio >= save_min_ratio:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        # 按 40px 横带定位变化块，红框标出，比整页染红看得清
        marked = b.copy()
        d = ImageDraw.Draw(marked, "RGBA")
        band, boxes = 40, 0
        for y in range(0, h, band):
            y2 = min(y + band, h)
            bbox = mask.crop((0, y, w, y2)).getbbox()
            if not bbox:
                continue
            x1, _, x2, _ = bbox
            d.rectangle([max(0, x1 - 4), max(0, y - 2), min(w - 1, x2 + 4), min(h - 1, y2 + 2)],
                        fill=(255, 0, 0, 45), outline=(220, 0, 0, 220), width=2)
            boxes += 1
            if boxes >= 300:
                break
        marked.save(out_path, "PNG")
    return ratio


def check(host, raw_png, page_text, url):
    """对比本轮与基线。返回 info dict；首次运行只建基线。"""
    conf = load_conf()
    text = norm_text(page_text)
    th = text_hash(text)
    p = _paths(host)
    prev = load_state(host)

    info = {
        "host": host, "url": url, "baseline": False,
        "text_changed": False, "added": [], "removed": [],
        "added_n": 0, "removed_n": 0,
        "img_ratio": None, "img_diff_path": None,
    }

    # ---- 图片对比（用裸图，跟水印无关）----
    if os.path.exists(p["prev_raw"]):
        try:
            out = os.path.join(DIFF_DIR, host, f"{datetime.now():%Y%m%d-%H%M%S}.png")
            ratio = image_diff(p["prev_raw"], raw_png, out)
            info["img_ratio"] = ratio
            thr = float(conf.get("IMAGE_DIFF_THRESHOLD", "0.02"))
            if ratio is not None and ratio > thr:
                info["img_diff_path"] = out
        except Exception as e:
            info["img_error"] = str(e)
    else:
        info["first_image"] = True

    # ---- 文本对比 ----
    if prev is None or "text_hash" not in prev:
        info["baseline"] = True
    elif prev["text_hash"] != th:
        info["text_changed"] = True
        old_text = ""
        if os.path.exists(p["text"]):
            try:
                old_text = open(p["text"], encoding="utf-8").read()
            except Exception:
                pass
        a, r, an, rn = text_diff(old_text, text, int(conf.get("MAX_SNIPPET_LINES", "6")))
        info.update(added=a, removed=r, added_n=an, removed_n=rn)

    # ---- 写回状态 ----
    with open(p["text"], "w", encoding="utf-8") as f:
        f.write(text)
    try:
        os.replace(raw_png, p["prev_raw"])
    except Exception:
        pass
    save_state(host, {
        "url": url,
        "text_hash": th,
        "text_len": len(text),
        "img_ratio": info["img_ratio"],
        "checked_at": f"{datetime.now():%Y-%m-%d %H:%M:%S}",
    })
    return info


def should_alert(info):
    conf = load_conf()
    if info.get("baseline"):
        return False
    if info["text_changed"] and conf.get("ALERT_ON_TEXT_CHANGE", "1") == "1":
        return True
    if info["img_ratio"] is not None and conf.get("ALERT_ON_IMAGE_CHANGE", "0") == "1":
        try:
            thr = float(conf.get("IMAGE_DIFF_THRESHOLD", "0.02"))
        except Exception:
            thr = 0.02
        if info["img_ratio"] > thr:
            return True
    return False
