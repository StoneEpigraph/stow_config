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
import shutil
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
# 成品截图对外发布目录（~/public 已由 Samba 共享，内网可直接看）
IMG_ROOT = os.path.expanduser("~/public/webcapture")
RAW_DIR = os.path.expanduser("~/webcapture/state/.raw")
LOG = os.path.join(OUT_ROOT, "capture.log")
BROWSER_CANDIDATES = ["/usr/bin/chromium", "/usr/bin/google-chrome-stable"]
VIEWPORT = {"width": 1440, "height": 900}

# 本轮「第一次失败但重试后成功」的 URL，用于报警文案
RETRIED = []

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import health  # noqa: E402  站点健康状态（连续失败计数 / 恢复判定）

DEFAULT_FAIL_INTERVAL = 3600  # 连续失败时最小提醒间隔（秒），可被 notify.conf 覆盖


def notify_conf():
    """读取 notify.conf（缺失时返回空 dict）。"""
    try:
        import notify
        return notify.load_conf()
    except Exception:
        return {}


def _conf_int(conf, key, default):
    try:
        v = conf.get(key)
        return default if v in (None, "") else int(float(v))
    except Exception:
        return default


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


def add_watermark(src, dst, url, ts_text):
    img = Image.open(src).convert("RGB")
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

    Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB").save(dst, "PNG", optimize=False)
    return w, h


def shoot(browser, url):
    now = datetime.now()
    ts_text = f"{now:%Y-%m-%d %H:%M:%S}"
    outdir = os.path.join(IMG_ROOT, host_slug(url), f"{now:%Y-%m-%d}")
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
                    return None, 0, 0, last_err, None
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
        # 先存裸图（差异对比用裸图，水印每轮都变会污染 diff）
        raw = os.path.join(RAW_DIR, f".tmp-{host_slug(url)}.png")
        os.makedirs(RAW_DIR, exist_ok=True)
        page.screenshot(path=raw, full_page=True, animations="disabled", caret="hide")
        try:
            page_text = page.evaluate("document.body.innerText") or ""
        except Exception:
            page_text = ""

        w, hgt = add_watermark(raw, out, url, ts_text)

        info = None
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import compare
            info = compare.check(host_slug(url), raw, page_text, url)
        except Exception as e:
            log(f"COMPARE 跳过 {url}: {e}")
        return out, w, hgt, None, info
    except Exception as e:
        return None, 0, 0, f"{type(e).__name__}: {e}", None
    finally:
        try:
            ctx.close()
        except Exception:
            pass


def update_latest(url, out):
    """给每站最新成品图建一个固定文件名的硬链接，供内网直接查看。

    用硬链接而不是软链：Samba 对符号链接的处理依客户端和 unix extensions 而定，
    Windows 资源管理器常见打不开；硬链接在 SMB 里就是普通文件，也不额外占空间。
    """
    d = os.path.join(IMG_ROOT, "_latest")
    os.makedirs(d, exist_ok=True)
    dest = os.path.join(d, host_slug(url) + ".png")
    try:
        if os.path.lexists(dest):
            os.remove(dest)
        os.link(out, dest)
    except OSError:
        try:
            shutil.copy2(out, dest)  # 跨文件系统等情况下退化为复制
        except Exception as e:
            log(f"LATEST 更新失败 {url}: {e}")


def write_latest_summary(entries):
    """_latest/SUMMARY.txt：每站最后一次成功时间 + 本轮结果。

    这个文件是为了避免「_latest 里那张图是几小时前的，但我不知道」——
    站点失败时旧图会留在原处，靠这里的时间戳和状态区分。
    """
    d = os.path.join(IMG_ROOT, "_latest")
    os.makedirs(d, exist_ok=True)
    lines = [f"生成时间: {datetime.now():%Y-%m-%d %H:%M:%S}",
             "说明: 图片名固定为 <域名>.png，每次成功截图后替换；时间是该站最后一次成功的时间。",
             ""]
    for e in entries:
        host = e["host"]
        p = os.path.join(d, host + ".png")
        if os.path.exists(p):
            last = f"{datetime.fromtimestamp(os.path.getmtime(p)):%Y-%m-%d %H:%M:%S}"
        else:
            last = "（尚无成功截图）"
        state = "本轮正常" if e["ok"] else f"本轮失败：{e['err']}"
        lines.append(f"{host:<26} 最后成功 {last:<20} {state}")
    try:
        with open(os.path.join(d, "SUMMARY.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except Exception as e:
        log(f"LATEST 写 SUMMARY 失败: {e}")


def alert(fails, oks, retried):
    """本轮有请求失败时推送到钉钉/企业微信；没配置就只写日志。

    fails 项为 (url, err, state)，state 里带连续失败次数与是否降频静默。
    """
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


def alert_recovered(recovered, total):
    """站点从失败态恢复时推一条，形成闭环。"""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import notify
    except Exception as e:
        log(f"NOTIFY 模块加载失败: {e}")
        return
    ts = f"{datetime.now():%Y-%m-%d %H:%M:%S}"
    title = f"✅ 网页截图已恢复 {len(recovered)}/{total}"
    text = notify.build_recover_text(ts, recovered, total)
    try:
        res = notify.send(title, text)
        print(f"recover alert -> {res}")
    except Exception as e:
        log(f"NOTIFY 发送异常: {e}")


def alert_changes(changed, total):
    """页面内容/外观有变化时推送。"""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import notify
    except Exception as e:
        log(f"NOTIFY 模块加载失败: {e}")
        return
    ts = f"{datetime.now():%Y-%m-%d %H:%M:%S}"
    lines = [f"**时间**：{ts}", f"**变更站点**：{len(changed)} / {total}", ""]
    for info in changed:
        lines.append(f"**【{info['host']}】**")
        if info.get("text_changed"):
            an, rn = info.get("added_n", 0), info.get("removed_n", 0)
            lines.append(f"文本变更：+{an} 行 / -{rn} 行")
            for s in info.get("added", []):
                lines.append(f"> + {s[:120]}")
            for s in info.get("removed", []):
                lines.append(f"> - {s[:120]}")
        if info.get("img_ratio") is not None:
            lines.append(f"图像变化：{info['img_ratio'] * 100:.2f}%")
        if info.get("img_diff_path"):
            lines.append(f"差异图：{info['img_diff_path']}")
        lines.append("")
    title = f"🔔 网页内容变更 {len(changed)}/{total}"
    try:
        res = notify.send(title, "\n".join(lines))
        print(f"change alert -> {res}")
    except Exception as e:
        log(f"NOTIFY 发送异常: {e}")


def main():
    urls = sys.argv[1:] or DEFAULT_URLS
    del RETRIED[:]
    conf = notify_conf()
    fail_interval = _conf_int(conf, "FAIL_ALERT_INTERVAL", DEFAULT_FAIL_INTERVAL)
    recover_on = _conf_int(conf, "ALERT_ON_RECOVER", 1)

    exe = find_browser()
    if not exe:
        log("ERROR 找不到 chromium/chrome")
        print("找不到浏览器", file=sys.stderr)
        try:
            st = health.on_fail("__browser__", "找不到 chromium/chrome", fail_interval)
        except Exception:
            st = {"action": "alert", "fail_count": 1}
        if st.get("action") == "alert":
            alert([("(启动失败)", "找不到 chromium/chrome", st)], [], [])
        return 1
    try:
        if health.load("__browser__").get("fail_count"):
            health.save("__browser__", {"fail_count": 0})
    except Exception:
        pass

    ok, fail = 0, 0
    fails, oks = [], []
    changed, recovered = [], []
    summary = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=exe,
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars",
                  "--disable-gpu", "--lang=zh-CN"],
        )
        try:
            for url in urls:
                slug = host_slug(url)
                out, w, hgt, err, info = shoot(browser, url)
                if out:
                    ok += 1
                    oks.append(slug)
                    print(f"OK   {url}  ->  {out}  ({w}x{hgt})")
                    log(f"OK {url} -> {out} {w}x{hgt}")
                    update_latest(url, out)
                    summary.append({"host": slug, "ok": True, "err": ""})
                    try:
                        rec = health.on_ok(slug)
                    except Exception as e:
                        rec = None
                        log(f"HEALTH 写状态失败 {slug}: {e}")
                    if rec:
                        rec["url"] = url
                        recovered.append(rec)
                        log(f"RECOVER {url} 连续失败 {rec['fail_count']} 次后恢复，"
                            f"中断 {health.fmt_dur(rec['seconds'])}")
                    if info:
                        _report_change(url, info, changed)
                else:
                    fail += 1
                    try:
                        st = health.on_fail(slug, err or "未知错误", fail_interval)
                    except Exception as e:
                        st = {"action": "alert", "fail_count": 1, "seconds": 0}
                        log(f"HEALTH 写状态失败 {slug}: {e}")
                    st["url"] = url
                    fails.append((url, err or "未知错误", st))
                    summary.append({"host": slug, "ok": False,
                                    "err": (err or "未知错误").splitlines()[0][:90]})
                    state_txt = ("已报警" if st.get("action") == "alert" else "降频静默")
                    print(f"FAIL {url}  {err}  [连续第 {st.get('fail_count', 1)} 次 / {state_txt}]")
                    log(f"FAIL {url} {err} | 连续第 {st.get('fail_count', 1)} 次 | {state_txt}")
        finally:
            browser.close()
    print(f"done ok={ok} fail={fail} changed={len(changed)} recovered={len(recovered)}")
    write_latest_summary(summary)

    if any(len(f) >= 3 and f[2].get("action") == "alert" for f in fails):
        alert(fails, oks, RETRIED)
    if changed:
        alert_changes(changed, len(urls))
    if recovered:
        if recover_on:
            alert_recovered(recovered, len(urls))
        else:
            log(f"RECOVER 共 {len(recovered)} 站恢复，但 ALERT_ON_RECOVER=0，不发送")
    return 0 if fail == 0 else 2


def _report_change(url, info, bucket):
    """把变化写进日志并按配置决定是否进报警队列。"""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import compare
    except Exception:
        return
    if info.get("baseline"):
        log(f"BASELINE {url} 已建立基线")
        return
    bits = []
    if info.get("text_changed"):
        bits.append(f"文本 +{info.get('added_n', 0)}/-{info.get('removed_n', 0)} 行")
        for s in info.get("added", [])[:3]:
            bits.append(f"+{s[:80]}")
        for s in info.get("removed", [])[:3]:
            bits.append(f"-{s[:80]}")
    if info.get("img_ratio"):  # 0.0 不算变化，别刷日志
        bits.append(f"图像 {info['img_ratio'] * 100:.2f}%")
    if bits:
        log(f"CHANGE {url} " + "，".join(bits))
        print(f"CHG  {url}  " + "，".join(bits))
    if compare.should_alert(info):
        bucket.append(info)


if __name__ == "__main__":
    sys.exit(main())
