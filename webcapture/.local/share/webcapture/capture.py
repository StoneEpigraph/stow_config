#!/usr/bin/env python3
"""按 URL 列表整页截图，并打上时间水印。

用法:
    capture.py [url ...]          # 不传则用内置 DEFAULT_URLS
输出:
    ~/webcapture/<host>/<YYYY-MM-DD>/<HHMMSS>.png
日志:
    ~/webcapture/capture.log
"""

import sys
import os
import re
import time
import traceback
from datetime import datetime

from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw, ImageFont

DEFAULT_URLS = [
    "https://www.juanzhuzhongxin.cn/donationWeb/",
    "https://www.bjyouth.gov.cn/",
    "https://www.bjjdzx.com/",
    "https://www.bjydf.cn/",
]

OUT_ROOT = os.path.expanduser("~/webcapture")
LOG = os.path.join(OUT_ROOT, "capture.log")
BROWSER_CANDIDATES = ["/usr/bin/chromium", "/usr/bin/google-chrome-stable"]
VIEWPORT = {"width": 1440, "height": 900}

# 本轮「第一次失败但重试后成功」的 URL，用于报警文案
RETRIED = []


def log(msg):
    os.makedirs(OUT_ROOT, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")


def host_slug(url):
    h = re.sub(r"^https?://", "", url).split("/")[0]
    return re.sub(r"[^\w.\-]", "_", h) or "unknown"


def find_browser():
    for p in BROWSER_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def font(size):
    for p in (
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def add_watermark(path, url, ts_text):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    text = f"{ts_text}   {url}"
    diag_font = font(max(22, int(w / 60)))

    # 斜向平铺的半透明水印
    tile = Image.new("RGBA", (int(w * 0.9), int(diag_font.size * 6)), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    # 中灰 + 描边：白底显灰、深底显浅，两种背景都看得见
    td.text((10, 10), text, font=diag_font, fill=(130, 130, 130, 130),
            stroke_width=2, stroke_fill=(245, 245, 245, 90))
    tile = tile.rotate(30, expand=True)
    step_x, step_y = tile.width + 60, tile.height + 60
    y = -tile.height
    while y < h + tile.height:
        x = -tile.width
        while x < w + tile.width:
            overlay.alpha_composite(tile, (int(x), int(y)))
            x += step_x
        y += step_y

    # 右下角清晰时间条
    bar_font = font(max(26, int(w / 55)))
    label = f"{ts_text}  |  {url}"
    tw = d.textlength(label, font=bar_font)
    pad = 14
    bw, bh = int(tw) + pad * 2, bar_font.size + pad * 2
    bx, by = w - bw - 24, h - bh - 24
    d.rectangle([bx, by, bx + bw, by + bh], fill=(0, 0, 0, 175))
    d.text((bx + pad, by + pad), label, font=bar_font, fill=(255, 255, 255, 255))

    # 左上角小标
    head = font(max(18, int(w / 80)))
    d.rectangle([0, 0, int(d.textlength(ts_text, font=head)) + 20, head.size + 12], fill=(0, 0, 0, 140))
    d.text((10, 6), ts_text, font=head, fill=(255, 255, 255, 230))

    Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB").save(path, "PNG", optimize=False)
    return w, h


def shoot(browser, url):
    now = datetime.now()
    ts_text = f"{now:%Y-%m-%d %H:%M:%S}"
    outdir = os.path.join(OUT_ROOT, host_slug(url), f"{now:%Y-%m-%d}")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f"{now:%H%M%S}.png")

    ctx = browser.new_context(
        viewport=VIEWPORT,
        device_scale_factor=1,
        ignore_https_errors=True,
        user_agent=("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
        locale="zh-CN",
    )
    page = ctx.new_page()
    last_err = None
    try:
        # 慢站/握手不稳的站（如 bjyouth.gov.cn 的 TLS 曲线偏老）重试一次
        for attempt in range(2):
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                break
            except Exception as e:
                last_err = f"{type(e).__name__}: {str(e).splitlines()[0]}"
                log(f"RETRY {url} 第{attempt + 1}次失败: {last_err}")
                if attempt == 1:
                    return None, 0, 0, last_err
                RETRIED.append(url)
                try:
                    page.close()
                except Exception:
                    pass
                page = ctx.new_page()
                continue

        try:
            page.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            pass
        # 滚动触发懒加载
        try:
            page.evaluate("""async () => {
                const h = document.body.scrollHeight;
                for (let y = 0; y < h; y += 800) {
                    window.scrollTo(0, y);
                    await new Promise(r => setTimeout(r, 120));
                }
                window.scrollTo(0, 0);
                await new Promise(r => setTimeout(r, 400));
            }""")
        except Exception:
            pass
        page.wait_for_timeout(1200)
        page.screenshot(path=out, full_page=True, animations="disabled", caret="hide")
        w, hgt = add_watermark(out, url, ts_text)
        return out, w, hgt, None
    except Exception as e:
        return None, 0, 0, f"{type(e).__name__}: {e}"
    finally:
        try:
            ctx.close()
        except Exception:
            pass


def alert(fails, oks, retried):
    """本轮有请求失败时推送到钉钉/企业微信；没配置就只写日志。"""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import notify
    except Exception as e:
        log(f"NOTIFY 模块加载失败: {e}")
        return
    ts = f"{datetime.now():%Y-%m-%d %H:%M:%S}"
    title = f"⚠️ 网页截图失败 {len(fails)}/{len(fails) + len(oks)}"
    text = notify.build_fail_text(ts, fails, oks, retried)
    try:
        res = notify.send(title, text)
        print(f"alert -> {res}")
    except Exception as e:
        log(f"NOTIFY 发送异常: {e}")


def main():
    urls = sys.argv[1:] or DEFAULT_URLS
    del RETRIED[:]
    exe = find_browser()
    if not exe:
        log("ERROR 找不到 chromium/chrome")
        print("找不到浏览器", file=sys.stderr)
        alert([("(启动失败)", "找不到 chromium/chrome")], [], [])
        return 1
    ok, fail = 0, 0
    fails, oks = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=exe,
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars",
                  "--disable-gpu", "--lang=zh-CN"],
        )
        try:
            for url in urls:
                out, w, hgt, err = shoot(browser, url)
                if out:
                    ok += 1
                    oks.append(host_slug(url))
                    print(f"OK   {url}  ->  {out}  ({w}x{hgt})")
                    log(f"OK {url} -> {out} {w}x{hgt}")
                else:
                    fail += 1
                    fails.append((url, err or "未知错误"))
                    print(f"FAIL {url}  {err}")
                    log(f"FAIL {url} {err}")
        finally:
            browser.close()
    print(f"done ok={ok} fail={fail}")
    if fails:
        alert(fails, oks, RETRIED)
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
