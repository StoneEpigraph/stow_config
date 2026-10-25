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

# ── 动效冻结 ────────────────────────────────────────────────────────────────
# 目的：轮播图、横向滚动条（theScrollTank）、数字滚动等「JS 定时器驱动」的东西
# 每轮截图位置都不同，会让两次截图的图像差异动辄 5%~15%，把真正的内容变化淹掉。
# 做法是「回到初始位置 + 停掉驱动」：
#   1) 所有容器 scrollLeft/scrollTop 归零（含同源 iframe）
#   2) 已知轮播库调各自 API 停播并 slideTo(0)
#   3) SuperSlide 这类用 inline `left: -Npx` 位移的，把 left 归零
#   4) Swiper/layui 这类用 transform 位移的，把 track 的 transform 置 none
#   5) 分页圆点状态归一（否则图是第 1 张、点还亮在第 3 个）
#   6) 冻住定时器：清掉页面注册过的 setInterval、封住新的 set*/rAF
# 注意：CSS 动画/过渡不归这里管 —— page.screenshot(animations="disabled")
# 已经会让有限动画快进到终态、无限动画回到初始态，比手工 pause 更稳。
MOTION_INIT_JS = r"""
(() => {
  if (window.__wcMotionHooked) return;
  window.__wcMotionHooked = true;
  const origSetInterval = window.setInterval.bind(window);
  const origClearInterval = window.clearInterval.bind(window);
  const origSetTimeout = window.setTimeout.bind(window);
  const origClearTimeout = window.clearTimeout.bind(window);
  const ivs = new Set();
  const tms = new Set();
  window.__wcOrigTimeout = origSetTimeout;
  window.setInterval = function (fn, ms) {
    const id = origSetInterval(fn, ms);
    ivs.add(id);
    return id;
  };
  window.clearInterval = function (id) { ivs.delete(id); return origClearInterval(id); };
  window.setTimeout = function (fn, ms) {
    if (typeof fn !== 'function') return origSetTimeout(fn, ms);
    let id;
    id = origSetTimeout(function () { tms.delete(id); return fn.apply(this, arguments); }, ms);
    tms.add(id);
    return id;
  };
  window.clearTimeout = function (id) { tms.delete(id); return origClearTimeout(id); };
  window.__wcTimerCount = function () { return ivs.size + tms.size; };
  // clearPending=true 时连已挂起的 setTimeout 一起清（递归 setTimeout 的轮播
  // 否则还会再往前走一格）
  window.__wcFreezeTimers = function (clearPending) {
    ivs.forEach(function (id) { origClearInterval(id); });
    ivs.clear();
    if (clearPending) {
      tms.forEach(function (id) { origClearTimeout(id); });
      tms.clear();
    }
    window.setInterval = function () { return 0; };
    window.setTimeout = function () { return 0; };
    window.requestAnimationFrame = function () { return 0; };
  };
})();
"""

FREEZE_JS = r"""
async () => {
  const rep = {scrolls: 0, lefts: 0, tf: 0, dots: 0, libs: [], marquee: 0, timers: 0};
  const origTimeout = window.__wcOrigTimeout || window.setTimeout.bind(window);
  const sleep = (ms) => new Promise(function (r) { origTimeout(r, ms); });
  const CAROUSEL = /(carousel|slider|slide|swiper|banner|focus|marquee|scrolltank|slidebox|轮播)/i;
  const ACTIVE = ['on', 'active', 'cur', 'current', 'selected',
                  'swiper-pagination-bullet-active', 'layui-this'];

  const docs = [document];
  (function walkFrames(doc) {
    doc.querySelectorAll('iframe, frame').forEach(function (f) {
      try {
        const d = f.contentDocument;
        if (d && docs.indexOf(d) < 0) { docs.push(d); walkFrames(d); }
      } catch (e) {}
    });
  })(document);

  const clsOf = (el) => (el.className && typeof el.className === 'string') ? el.className : '';
  const isCarousel = (el) => !!el && CAROUSEL.test(clsOf(el) + ' ' + (el.id || ''));

  function resetScroll() {
    docs.forEach(function (doc) {
      try { (doc.defaultView || window).scrollTo(0, 0); } catch (e) {}
      doc.querySelectorAll('*').forEach(function (el) {
        if (el.scrollLeft > 0) { el.scrollLeft = 0; rep.scrolls++; }
        if (el.scrollTop > 0) { el.scrollTop = 0; }
      });
    });
  }

  function stopLibs() {
    docs.forEach(function (doc) {
      const w = doc.defaultView || window;
      doc.querySelectorAll('.swiper, .swiper-container').forEach(function (el) {
        const s = el.swiper;
        if (!s) return;
        try { if (s.autoplay && s.autoplay.running) s.autoplay.stop(); } catch (e) {}
        try { s.slideTo(0, 0, false); } catch (e) {}
        rep.libs.push('swiper');
      });
      doc.querySelectorAll('.splide').forEach(function (el) {
        const s = el.splide;
        if (!s) return;
        try { s.pause(); } catch (e) {}
        try { s.go(0); } catch (e) {}
        rep.libs.push('splide');
      });
      try {
        const bs = w.bootstrap;
        if (bs && bs.Carousel) {
          doc.querySelectorAll('.carousel').forEach(function (el) {
            const inst = bs.Carousel.getInstance(el);
            if (!inst) return;
            try { inst.pause(); } catch (e) {}
            try { inst.to(0); } catch (e) {}
            rep.libs.push('bootstrap');
          });
        }
      } catch (e) {}
      const $ = w.jQuery;
      if ($ && $.fn) {
        try {
          $('.slick-slider').each(function () {
            try { $(this).slick('slickPause'); $(this).slick('slickGoTo', 0, true); rep.libs.push('slick'); } catch (e) {}
          });
        } catch (e) {}
        try {
          $('.owl-carousel').each(function () {
            try {
              $(this).trigger('stop.owl.autoplay');
              $(this).trigger('to.owl.carousel', [0, 0]);
              rep.libs.push('owl');
            } catch (e) {}
          });
        } catch (e) {}
        // 仍排在队列里的 jQuery 动画一律停掉（theScrollTank 这类会自己往回推）
        try { $(':animated').stop(true, false); } catch (e) {}
        try { $('[class*=slideBox] ul').stop(true, false); } catch (e) {}
      }
    });
  }

  function resetTracks() {
    docs.forEach(function (doc) {
      const w = doc.defaultView || window;
      doc.querySelectorAll('*').forEach(function (root) {
        if (!isCarousel(root)) return;
        const nodes = [root].concat(Array.prototype.slice.call(root.querySelectorAll('*'), 0, 150));
        nodes.forEach(function (n) {
          const st = n.getAttribute && n.getAttribute('style');
          if (st && /left\s*:\s*-/.test(st)) {
            n.style.left = '0px';
            // 必须同时关掉过渡：SuperSlide 这类是 `transition: left .3s` 做动画，
            // 截图时 Playwright 的 animations="disabled" 会把进行中的过渡**快进到终点**，
            // 于是刚复位的位置又被推回原来那张幻灯片（实测同一站两轮差 6%）。
            n.style.transition = 'none';
            rep.lefts++;
          }
          const tf = w.getComputedStyle(n).transform;
          if (tf && tf !== 'none' && tf !== 'matrix(1, 0, 0, 1, 0, 0)') {
            // 只动「像一条轨道」的元素（多个子节点或本身内容超宽），避免误伤装饰性 transform
            if (n.children.length > 1 || n.scrollWidth - n.clientWidth > 8) {
              n.style.transform = 'none';
              n.style.transition = 'none';
              rep.tf++;
            }
          }
        });
      });
    });
  }

  function resetDots() {
    const BOX = /(hd|dots?|pagination|indicator|nav|thumb)/i;
    docs.forEach(function (doc) {
      doc.querySelectorAll('*').forEach(function (box) {
        if (!BOX.test(clsOf(box))) return;
        const par = box.parentElement;
        if (!isCarousel(par) && !(par && isCarousel(par.parentElement))) return;
        const items = Array.prototype.filter.call(
          box.querySelectorAll('li, span, a, i'),
          function (n) { return n.children.length === 0 && !n.textContent.trim(); }
        );
        if (items.length < 2) return;
        const act = [];
        items.forEach(function (n) {
          ACTIVE.forEach(function (k) { if (n.classList.contains(k)) act.push(k); });
        });
        if (!act.length) return;
        items.forEach(function (n, i) { act.forEach(function (k) { n.classList.toggle(k, i === 0); }); });
        rep.dots++;
      });
    });
  }

  function stopMarquee() {
    docs.forEach(function (doc) {
      doc.querySelectorAll('marquee').forEach(function (m) {
        try { m.stop(); } catch (e) {}
        try { m.scrollLeft = 0; } catch (e) {}
        rep.marquee++;
      });
    });
  }

  resetScroll();
  stopLibs();
  resetTracks();
  resetDots();
  stopMarquee();
  await sleep(120);
  resetScroll();
  if (window.__wcFreezeTimers) {
    rep.timers = window.__wcTimerCount ? window.__wcTimerCount() : 0;
    window.__wcFreezeTimers(true);
  }
  // 关键：定时器冻住后再复位一次。第一次复位之后、冻住之前，还在跑的轮播
  // 会把这 120ms 里走过的那几像素重新写回 inline left（实测 -2px / -3px 不稳定），
  // 于是两轮截图仍然差 1~3px。冻住之后的这次复位才是最终落点。
  rep.scrolls = 0;
  rep.lefts = 0;
  rep.tf = 0;
  resetScroll();
  resetTracks();
  await sleep(80);
  resetScroll();
  rep.libs = Array.from(new Set(rep.libs));
  return rep;
}
"""

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


WAIT_IMG_JS = r"""
async (ms) => {
  const imgs = Array.from(document.images).filter(function (i) { return i.currentSrc || i.src; });
  const timeout = new Promise(function (r) { setTimeout(function () { r('timeout'); }, ms); });
  const one = function (i) {
    if (i.complete && i.naturalWidth > 0) return Promise.resolve(true);
    const dec = (i.decode ? i.decode() : Promise.resolve());
    return dec.then(function () { return true; }).catch(function () { return false; });
  };
  // decode() 卡住时不能让整页僵死，用 race 兜住
  const res = await Promise.race([
    Promise.all(imgs.map(one)),
    timeout.then(function () { return null; }),
  ]);
  const bad = res ? imgs.filter(function (i, k) { return !res[k]; })
      : imgs.filter(function (i) { return !(i.complete && i.naturalWidth > 0); });
  return bad.map(function (i) { return (i.currentSrc || i.src).split('/').pop().slice(0, 40); });
}
"""


def wait_images(page, url):
    """等所有图片真正可上屏（decode 完成），避免归档里出现空白格。

    只等 `complete` 不够 —— 实测 bjyouth 的缩略图会出现
    `complete=false` 但 `naturalWidth=1080`（已解码）的瞬时状态，
    以及偶尔整块空白。上限 WEB_IMAGE_WAIT_MS（默认 3000ms），超时不阻塞。
    """
    limit = int(os.environ.get("WEB_IMAGE_WAIT_MS", "3000"))
    deadline = time.time() + limit / 1000.0
    while True:
        remain = max(300, int((deadline - time.time()) * 1000))
        try:
            bad = page.evaluate(WAIT_IMG_JS, remain)
        except Exception:
            return
        if not bad:
            return
        if time.time() >= deadline:
            log(f"IMGWAIT {url} 仍有 {len(bad)} 张未就绪: " + ", ".join(bad[:3]))
            return
        page.wait_for_timeout(200)


def freeze_motion(page, url):
    """把轮播/横向滚动拉回初始位置并冻住定时器，返回统计（失败不影响截图）。"""
    if os.environ.get("WEB_FREEZE_MOTION", "1").lower() in ("0", "false", "no", "off"):
        return None
    try:
        rep = page.evaluate(FREEZE_JS)
    except Exception as e:
        log(f"FREEZE 跳过 {url}: {type(e).__name__}: {str(e).splitlines()[0]}")
        return None
    bits = []
    if rep.get("libs"):
        bits.append("轮播库 " + "/".join(rep["libs"]))
    if rep.get("scrolls"):
        bits.append(f"归零滚动 {rep['scrolls']} 处")
    if rep.get("lefts"):
        bits.append(f"left 归零 {rep['lefts']}")
    if rep.get("tf"):
        bits.append(f"transform 复位 {rep['tf']}")
    if rep.get("dots"):
        bits.append(f"圆点归一 {rep['dots']}")
    if rep.get("marquee"):
        bits.append(f"marquee {rep['marquee']}")
    if rep.get("timers"):
        bits.append(f"清定时器 {rep['timers']}")
    if bits:
        log(f"FREEZE {url} " + " | ".join(bits))
    return rep


PROFILE_DIR = os.path.expanduser("~/.cache/webcapture-profile")


def launch_ctx(p, exe):
    """带持久 profile 的浏览器上下文。

    用持久 profile 不是为了留 cookie，而是为了复用 **HTTP 磁盘缓存**：
    bjjdzx 主页有 96 张图（不少 1MB+），冷缓存一轮下来 60 多张来不及下载，
    截图里就是一片空白格 —— 而「这一轮哪几张空白」每轮都不同，图像差异能到 13%。
    缓存命中后未就绪图片稳定在个位数（实测 67 → 1~3）。
    """
    os.makedirs(PROFILE_DIR, exist_ok=True)
    kw = dict(
        executable_path=exe,
        headless=True,
        viewport=VIEWPORT,
        device_scale_factor=1,
        ignore_https_errors=True,
        user_agent=("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
        locale="zh-CN",
        args=["--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars",
              "--disable-gpu", "--lang=zh-CN"],
    )
    ctx = None
    for attempt in range(2):
        try:
            ctx = p.chromium.launch_persistent_context(PROFILE_DIR, **kw)
            break
        except Exception as e:
            if attempt:
                raise
            # 上一轮被 kill 掉时 profile 会留下锁文件，清掉再试一次
            log(f"PROFILE 复用失败（{type(e).__name__}: {str(e).splitlines()[0]}），清锁重试")
            for name in ("SingletonLock", "SingletonSocket", "SingletonCookie"):
                try:
                    os.remove(os.path.join(PROFILE_DIR, name))
                except OSError:
                    pass
    # 从文档创建起就挂钩定时器，才能在收尾时把它们一次清掉
    try:
        ctx.add_init_script(MOTION_INIT_JS)
    except Exception as e:
        log(f"FREEZE 挂钩失败: {type(e).__name__}: {e}")
    return ctx


def shoot(ctx, url):
    now = datetime.now()
    ts_text = f"{now:%Y-%m-%d %H:%M:%S}"
    outdir = os.path.join(IMG_ROOT, host_slug(url), f"{now:%Y-%m-%d}")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f"{now:%H%M%S}.png")

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
        # 有些站点（如 bjyouth.gov.cn）的日期/星期是在 window.onload 里填进
        # #currentDate / #currentDayOfWeek 的，而 window.onload 要等所有第三方资源
        # （百度统计、党政机关标识 dcs.conac.cn 等）加载完才触发 —— 实测快时 2s、
        # 慢时 20s+、偶尔整轮都不填，于是同一页面的 innerText 在
        # 「有日期」「无日期」两种状态间随机跳变 → 文本哈希误报。
        # 这里先等它填上（让归档截图尽量一致），等不到不阻塞；
        # 真正的兜底是 compare.py 里剥掉行首日期前缀。
        try:
            if page.evaluate("() => !!document.getElementById('currentDate')"):
                page.wait_for_function(
                    "() => { const e = document.getElementById('currentDate');"
                    " return e && e.textContent.trim().length > 0; }",
                    timeout=int(os.environ.get("WEB_DATE_WAIT_MS", "6000")),
                )
        except Exception:
            log(f"DATE {url} 未在等待期内填充（不影响截图）")
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
        # 懒加载图片可能还在下载：不等它落地，同一站点两轮截图的差异会来自
        # 「这一轮某张图还是空白」
        wait_images(page, url)
        # 懒加载都触发完了，现在把轮播/横向滚动拉回初始位置并冻住定时器，
        # 否则两次截图的差异全来自「这一轮恰好滚到哪儿」
        freeze_motion(page, url)
        page.wait_for_timeout(150)
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
            page.close()
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
        ctx = launch_ctx(p, exe)
        try:
            for url in urls:
                slug = host_slug(url)
                out, w, hgt, err, info = shoot(ctx, url)
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
            ctx.close()
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
