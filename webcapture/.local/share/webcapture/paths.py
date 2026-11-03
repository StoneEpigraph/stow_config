#!/usr/bin/env python3
"""跨平台路径与外部依赖探测（Linux / Windows 共用）。

所有目录都可以用环境变量覆盖，默认值与 Linux 版完全一致（老机器行为不变）：

  WEBCAPTURE_HOME       状态 / 日志 / 基线        Linux ~/webcapture
  WEBCAPTURE_IMG_ROOT   成品截图                  Linux ~/public/webcapture
  WEBCAPTURE_CACHE      临时目录与 profile 的父目录
                                                  Linux ~/.cache
                                                  Windows %LOCALAPPDATA%\\webcapture
  WEBCAPTURE_PROFILE    浏览器 profile（持久缓存） Linux ~/.cache/webcapture-profile
  WEBCAPTURE_TMP        临时目录                  Linux ~/.cache/webcapture-tmp
  WEBCAPTURE_BROWSER    指定浏览器可执行文件
  WEBCAPTURE_FONT       指定水印字体
  WEBCAPTURE_UA         指定 User-Agent
"""

import os
import shutil

IS_WINDOWS = os.name == "nt"


def _expand(path):
    return os.path.expanduser(os.path.expandvars(path))


def home():
    return os.path.expanduser("~")


def out_root():
    """状态 / 日志 / 基线。"""
    return _expand(os.environ.get("WEBCAPTURE_HOME")
                   or os.path.join(home(), "webcapture"))


def state_dir():
    return os.path.join(out_root(), "state")


def log_path():
    return os.path.join(out_root(), "capture.log")


def img_root():
    """成品截图发布目录。Windows 上默认 %USERPROFILE%\\public\\webcapture，
    想让它落到 D 盘共享目录就设 WEBCAPTURE_IMG_ROOT。"""
    return _expand(os.environ.get("WEBCAPTURE_IMG_ROOT")
                   or os.path.join(home(), "public", "webcapture"))


def cache_root():
    p = os.environ.get("WEBCAPTURE_CACHE")
    if p:
        return _expand(p)
    if IS_WINDOWS:
        base = os.environ.get("LOCALAPPDATA") or os.path.join(home(), "AppData", "Local")
        return os.path.join(base, "webcapture")
    return os.path.join(home(), ".cache")


def profile_dir():
    """持久 profile。复用 HTTP 磁盘缓存，冷缓存一轮会有大量空白格。"""
    p = os.environ.get("WEBCAPTURE_PROFILE")
    if p:
        return _expand(p)
    return os.path.join(cache_root(), "profile" if IS_WINDOWS else "webcapture-profile")


def tmp_dir():
    p = os.environ.get("WEBCAPTURE_TMP")
    if p:
        return _expand(p)
    return os.path.join(cache_root(), "tmp" if IS_WINDOWS else "webcapture-tmp")


def browser_candidates():
    """系统浏览器候选路径（按顺序探测）。"""
    if IS_WINDOWS:
        roots = []
        for key in ("PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432", "LOCALAPPDATA"):
            v = os.environ.get(key)
            if v and v not in roots:
                roots.append(v)
        rels = (
            r"Google\Chrome\Application\chrome.exe",
            r"Microsoft\Edge\Application\msedge.exe",
            r"Chromium\Application\chrome.exe",
            r"BraveSoftware\Brave-Browser\Application\brave.exe",
        )
        return [os.path.join(r, rel) for r in roots for rel in rels]
    return [
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/google-chrome",
        "/usr/bin/microsoft-edge",
        "/usr/bin/microsoft-edge-stable",
        "/usr/bin/brave",
        "/snap/bin/chromium",
    ]


def _browser_names():
    if IS_WINDOWS:
        return ("chrome", "chrome.exe", "msedge", "msedge.exe",
                "chromium", "chromium.exe", "brave", "brave.exe")
    return ("chromium", "chromium-browser", "google-chrome-stable",
            "google-chrome", "microsoft-edge", "microsoft-edge-stable", "brave")


def find_browser():
    """返回浏览器可执行文件路径；找不到返回 None。

    顺序：WEBCAPTURE_BROWSER → 常见安装路径 → PATH。
    Playwright 自带的 Chromium 由 capture.py 另外兜底。
    """
    forced = os.environ.get("WEBCAPTURE_BROWSER")
    if forced:
        forced = _expand(forced)
        return forced if os.path.isfile(forced) else None
    for p in browser_candidates():
        if p and os.path.isfile(p):
            return p
    for name in _browser_names():
        w = shutil.which(name)
        if w:
            return w
    return None


def browser_hint():
    if IS_WINDOWS:
        return ("未找到 Chrome / Edge / Chromium。装一个 Chrome 或 Edge，"
                "或运行 setup.ps1 -InstallBrowser 下载 Playwright 自带 Chromium。")
    return "未找到 chromium/chrome。Arch 上装一个： sudo pacman -S chromium"


def font_candidates():
    """水印字体候选（越靠前越优先）。Windows 用微软雅黑，中英文都好看。"""
    forced = os.environ.get("WEBCAPTURE_FONT")
    cands = [_expand(forced)] if forced else []
    if IS_WINDOWS:
        windir = os.environ.get("WINDIR") or r"C:\Windows"
        fonts = os.path.join(windir, "Fonts")
        cands += [os.path.join(fonts, n) for n in (
            "msyhbd.ttc",   # 微软雅黑 Bold
            "msyh.ttc",     # 微软雅黑
            "arialbd.ttf",
            "segoeuib.ttf",
            "simhei.ttf",   # 黑体
        )]
        return cands
    cands += [
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        # 带 CJK 的兜底（水印里有中文站点名时不会变成方块）
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ]
    return cands


def user_agent():
    """按平台给一个自然的 UA；站点按 UA 下发不同资源时截图才不会「看起来不对」。"""
    forced = os.environ.get("WEBCAPTURE_UA")
    if forced:
        return forced
    if IS_WINDOWS:
        return ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
    return ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
