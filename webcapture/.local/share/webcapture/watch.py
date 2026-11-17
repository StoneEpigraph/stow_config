#!/usr/bin/env python3
"""页面指定位置监控：用 CSS 选择器盯住页面上的某块内容（排队号这类场景）。

配置：~/webcapture/watch.conf（模板 watch.conf.example），INI 格式：

    [watch]                        全局开关
    alert_on_change = 1
    wait_ms = 3000

    [当前叫号]                     一个监控点；节名就是报警文案里的名字
    url = https://example.com/queue/
    selector = #current-number
    when = <=10                    可选，满足条件时额外提醒

    [整页监控]                     selector 省略 = 盯这一页的整页文本
    url = https://example.com/news/

    [忽略轮播]                     ignore 可与上面任意一种组合
    url = https://example.com/queue/
    ignore = .carousel, .visitor-count

为什么用 INI 而不是 YAML / TOML：
  - `configparser` 是标准库，Python 3.9+ 都有，不用在 venv 里加依赖；
  - YAML 里 `selector: #current-number` 的 `#` 会被当成注释，值直接变空——
    CSS 的 id 选择器正好全以 # 开头，等于在最关键的字段上埋雷；
  - TOML 的 `tomllib` 要 Python 3.11+，3.9/3.10 还得额外装 tomli。

状态：~/webcapture/state/<host>.watch.json
    按**节名**记最后一次的文本，以及 when 是否已命中
    （后者用来让「满足条件」只提醒一次，而不是每轮都响；用节名而不是选择器做键，
    是为了改了选择器还能接上历史）。
"""

import configparser
import json
import operator
import os
import re
import time
from datetime import datetime

import paths

CONF = os.path.join(paths.out_root(), "watch.conf")
STATE_DIR = paths.state_dir()

# 这两个节名放全局开关；其余节一律当成监控点
GLOBAL_SECTIONS = ("watch", "global")

DEFAULT_CONF = {
    "alert_on_change": "1",
    "alert_on_first": "0",
    "wait_ms": "3000",
    "skip_compare_alert": "1",
}

# 兼容旧配置里的名字（WATCH_WAIT_MS / WATCH_SKIP_COMPARE_ALERT），写大写也认
_CONF_ALIAS = {
    "watch_wait_ms": "wait_ms",
    "watch_skip_compare_alert": "skip_compare_alert",
}

# 选择器没匹配到任何内容时记成这个，保证「以前有、现在没有」也能触发一次变化
MISS = "(未匹配)"

# 整页规则要存一整页文本，给它一个上限，避免异常页面把状态文件撑大。
# 截断只会让超出部分的改动漏报，不会误报。
WHOLE_MAX = 20000

WATCH_JS = r"""
(sel) => {
  const nodes = Array.prototype.slice.call(document.querySelectorAll(sel));
  const texts = nodes.map(function (el) {
    const t = (el.innerText !== undefined && el.innerText !== null)
      ? el.innerText : (el.textContent || '');
    return String(t).replace(/\s+/g, ' ').trim();
  }).filter(function (t) { return t.length > 0; });
  return {texts: texts, count: nodes.length};
}
"""

# 只做一次同步判断；轮询由 Python 侧用 page.wait_for_timeout 驱动。
WAIT_JS = r"""
(sel) => {
  const e = document.querySelector(sel);
  if (!e) return false;
  const t = (e.innerText !== undefined && e.innerText !== null) ? e.innerText : (e.textContent || '');
  return String(t).trim().length > 0;
}
"""

# 取整页文本，但先把 ignore 选择器命中的元素藏起来。
# 用「一次性样式表 + 临时属性」而不是改内联 style：不改动页原有 style（试过
# removeAttribute('style')，碰过 el.style 后 Chromium 会留下一个空 style=""），
# 而且 !important 能盖过元素自己的内联 display。取完立即卸掉属性并移除样式表。
# 注意：本函数在截图之后调用，所以隐藏不会影响归档图。
TEXT_JS = r"""
(sels) => {
  if (!document.body) return '';
  if (!sels || !sels.length) return document.body.innerText;
  const hit = [];
  for (let i = 0; i < sels.length; i++) {
    let nodes;
    try { nodes = document.querySelectorAll(sels[i]); } catch (e) { continue; }
    for (let j = 0; j < nodes.length; j++) hit.push(nodes[j]);
  }
  if (!hit.length) return document.body.innerText;
  const tag = 'data-wc-ignore';
  const sheet = document.createElement('style');
  sheet.textContent = '[' + tag + ']{display:none !important;}';
  (document.head || document.documentElement).appendChild(sheet);
  try {
    for (let k = 0; k < hit.length; k++) hit[k].setAttribute(tag, '');
    return document.body.innerText;
  } finally {
    for (let k = 0; k < hit.length; k++) hit[k].removeAttribute(tag);
    sheet.remove();
  }
}
"""

_OPS = {
    "<=": operator.le, "<": operator.lt,
    ">=": operator.ge, ">": operator.gt,
    "==": operator.eq, "=": operator.eq, "!=": operator.ne,
}
_WHEN_RE = re.compile(r"^\s*(<=|>=|==|!=|=|<|>)\s*(.+?)\s*$")
# 取文本里第一个数字。前面紧跟字母/数字/小数点的不算负号——排队号常见「A-101」这种写法，
# 若把连字符当符号会读成 -101，和阈值比较就永远不对了。
_NUM_RE = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?")
_SECTION_RE = re.compile(r"^\s*\[[^\]]+\]\s*$")


def _flag(conf, key):
    return str(conf.get(key, DEFAULT_CONF.get(key, "1"))).strip().lower() not in (
        "0", "false", "no", "off", "")


def _norm_url(url):
    return str(url or "").strip().rstrip("/")


def _state_path(host):
    return os.path.join(STATE_DIR, host + ".watch.json")


def _put(conf, key, val):
    """写进全局配置：键名小写化 + 兼容旧别名。"""
    k = str(key).strip().lower()
    conf[_CONF_ALIAS.get(k, k)] = str(val).strip()


def _load_ini(text, conf):
    """新版配置：一个节就是一个监控点，节名即标签。

    selector 省略时该节监控整页（整页文本）。ignore 是修饰符，两种都能配。
    返回 (监控点列表, 忽略规则列表)。
    """
    cp = configparser.ConfigParser(
        # 选择器 / 条件里可能出现 %，别让 configparser 当插值语法处理
        interpolation=None,
        # 常见写法 `selector = #current-number` 里的 # 是值本身，不是行内注释
        inline_comment_prefixes=None,
    )
    cp.read_string(text)
    rules = []
    ignores = []
    for sec in cp.sections():
        name = sec.strip()
        if name.lower() in GLOBAL_SECTIONS:
            for k, v in cp.items(sec):
                _put(conf, k, v)
            continue
        url = (cp.get(sec, "url", fallback="") or "").strip()
        selector = (cp.get(sec, "selector", fallback="") or "").strip()
        ignore = (cp.get(sec, "ignore", fallback="") or "").strip()
        if not url:
            # 没有 url 的节什么都不成（监控点和忽略规则都得知道看哪个页）
            continue
        rules.append({
            "name": name,
            "url": url,
            "url_norm": _norm_url(url),
            # selector 为空 = 整页监控
            "selector": selector,
            "whole": not selector,
            "label": name,
            "when": (cp.get(sec, "when", fallback="") or "").strip(),
        })
        if ignore:
            # 故意不按逗号拆：整串就是合法的 CSS 选择器列表，
            # 拆开会把 :is(a, b) 这种括号内的逗号弄断。
            ignores.append({
                "name": name,
                "url": url,
                "url_norm": _norm_url(url),
                "selector": ignore,
            })
    return rules, ignores


def _load_legacy(text, conf):
    """旧版竖线写法：`<URL> | <选择器> | <标签> | <条件>`，保留兼容（无忽略规则）。"""
    rules = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 2 or not parts[0] or not parts[1]:
                continue
            url, selector = parts[0], parts[1]
            label = parts[2] if len(parts) > 2 and parts[2] else selector
            rules.append({
                "name": label,
                "url": url,
                "url_norm": _norm_url(url),
                "selector": selector,
                "whole": False,
                "label": label,
                "when": parts[3] if len(parts) > 3 else "",
            })
        elif "=" in line:
            k, v = line.split("=", 1)
            _put(conf, k, v.strip().strip('"').strip("'"))
    return rules, []


def _parse():
    """解析配置，返回 (全局配置, 监控点列表, 忽略规则列表)。"""
    conf = dict(DEFAULT_CONF)
    try:
        with open(CONF, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        return conf, [], []
    # 有 [节] 就按 INI 解析；一个节都没有则按旧的竖线格式，老配置文件继续能用
    if any(_SECTION_RE.match(ln) for ln in text.splitlines()):
        rules, ignores = _load_ini(text, conf)
    else:
        rules, ignores = _load_legacy(text, conf)
    return conf, rules, ignores


def load():
    """返回 (全局配置, 监控点列表)。文件不存在时列表为空。

    解析出错就往上抛：宁可让 capture.log 里出现一条 WATCH 异常，
    也不要静默变成「一个监控点都没有」——那种故障没有任何提示，很难发现。
    调用方（capture.py）本来就包在 try 里、会写日志。
    """
    conf, rules, _ = _parse()
    return conf, rules


def rules_for(url):
    _, rules = load()
    key = _norm_url(url)
    return [r for r in rules if r["url_norm"] == key]


def has_rules(url):
    return bool(rules_for(url))


def urls_not_in(urls):
    """watch.conf 里出现、但不在本轮截图列表中的 URL（追加进列表，页面才有人去开）。

    监控点和忽略规则都算：只写了 ignore 的页也需要被打开。
    """
    _, rules, ignores = _parse()
    have = {_norm_url(u) for u in urls}
    extra = []
    for r in list(rules) + list(ignores):
        if r["url_norm"] in have:
            continue
        have.add(r["url_norm"])
        extra.append(r["url"])
    return extra


def ignore_selectors(url):
    """该 URL 在整页对比时要忽略的 CSS 选择器（每项已是一个可直接用的查询串）。"""
    _, _, ignores = _parse()
    key = _norm_url(url)
    return [ig["selector"] for ig in ignores if ig["url_norm"] == key]


def body_text(page, selectors):
    """取 body.innerText；给了 selectors 就先把那些位置临时隐藏再取。

    用 CSS 选择器排除噪声区域比 compare.conf 的 IGNORE_REGEX 逐行匹配可靠：
    轮播 / 广告位的文案一换，正则就得跟着改，而选择器不用。
    """
    return page.evaluate(TEXT_JS, list(selectors or [])) or ""


def should_suppress_compare(url):
    """有监控点的 URL 默认不再按整页文本报警：排队号每轮都在变，否则每轮都刷一条。"""
    try:
        conf, _ = load()
    except Exception:
        return False
    return _flag(conf, "skip_compare_alert") and has_rules(url)


def load_state(host):
    try:
        with open(_state_path(host), encoding="utf-8") as f:
            d = json.load(f)
            return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def save_state(host, st):
    os.makedirs(STATE_DIR, exist_ok=True)
    p = _state_path(host)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)


def _num(text):
    m = _NUM_RE.search(str(text).replace(",", "").replace("，", ""))
    return float(m.group()) if m else None


def when_ok(text, expr):
    """when 条件判定：对文本里第一个数字比较；== / != 的右边不是数字时按文本比。"""
    m = _WHEN_RE.match(str(expr or ""))
    if not m:
        return False
    op, rhs = m.group(1), m.group(2).strip()
    fn = _OPS[op]
    try:
        target = float(rhs)
    except ValueError:
        if op in ("==", "=", "!="):
            return fn(str(text).strip(), rhs)
        return False
    n = _num(text)
    if n is None:
        return False
    return fn(n, target)


def _fit(text, limit=200):
    text = str(text)
    return text if len(text) <= limit else text[:limit] + "…"


def _extract(page, selector, wait_ms):
    """取选择器匹配到的文本（多命中就拼起来）。空结果返回 MISS。"""
    try:
        if wait_ms > 0:
            deadline = time.time() + wait_ms / 1000.0
            while True:
                ready = False
                try:
                    ready = bool(page.evaluate(WAIT_JS, selector))
                except Exception:
                    pass
                if ready or time.time() >= deadline:
                    break
                page.wait_for_timeout(120)
        res = page.evaluate(WATCH_JS, selector) or {}
    except Exception as e:
        return {"text": MISS, "count": 0, "error": f"{type(e).__name__}: {e}"}
    texts = [t for t in (res.get("texts") or []) if t]
    if not texts:
        return {"text": MISS, "count": int(res.get("count") or 0)}
    joined = " / ".join(texts[:3])
    if len(texts) > 3:
        joined += f" …(+{len(texts) - 3})"
    return {"text": _fit(joined), "count": int(res.get("count") or len(texts))}


def _whole_text(page, ignore_sels):
    """整页规则的取值。

    先把 ignore 命中的区域藏掉，再用 compare.py 的归一化（去零宽、折空白、
    剥行首日期、按 IGNORE_REGEX 丢时钟/轮播页码这类行）。必须跟现有整页报警
    用同一套口径：直接用原始 innerText 的话，一个时钟就够让整页规则每轮都响。
    """
    import compare
    return compare.norm_text(body_text(page, ignore_sels))[:WHOLE_MAX]


def _diff(old_text, new_text):
    """整页文本的行级差异；「只是换了顺序」也会被识别出来（reordered）。"""
    import compare
    return compare.diff_change(old_text or "", new_text, 3)


def check(host, url, page):
    """抓取该 URL 的所有监控点并与上一轮比较。返回结果 dict，无规则时返回 None。

    结果结构：
        {"host", "url", "baseline": [...], "changes": [...], "missing": [...]}
    changes 里每项含 label / selector / old / new / when / when_fire。
    """
    conf, all_rules, ignores = _parse()
    key = _norm_url(url)
    rules = [r for r in all_rules if r["url_norm"] == key]
    if not rules:
        return None
    ignore_sels = [ig["selector"] for ig in ignores if ig["url_norm"] == key]

    try:
        wait_ms = int(float(conf.get("wait_ms", "3000") or 0))
    except Exception:
        wait_ms = 3000
    alert_on_change = _flag(conf, "alert_on_change")
    alert_on_first = _flag(conf, "alert_on_first")

    st = load_state(host)
    out = {"host": host, "url": url, "baseline": [], "changes": [], "missing": []}
    # 整页文本只取一次（可能多个整页规则共用同一页）
    whole_cache = {}

    for r in rules:
        name, selector, label = r["name"], r["selector"], r["label"]
        whole = bool(r.get("whole"))
        if whole:
            if "v" not in whole_cache:
                whole_cache["v"] = _whole_text(page, ignore_sels)
            got = {"text": whole_cache["v"], "count": 0}
        else:
            got = _extract(page, selector, wait_ms)
        text = got["text"]
        prev = st.get(name) or {}
        prev_text = prev.get("text")

        hit = when_ok(text, r["when"]) if r["when"] else False
        entry = {
            "label": label,
            "selector": selector,
            "whole": whole,
            "old": prev_text,
            "new": text,
            "when": r["when"],
            "when_hit": hit,
        }

        if prev_text is None:
            out["baseline"].append(entry)
            if alert_on_first:
                out["changes"].append(entry)
        else:
            changed = text != prev_text
            if changed and whole:
                d = _diff(prev_text, text)
                if d.get("reordered"):
                    # 和 compare.py 一致：删掉的行和新增的行内容相同、只是换了顺序，不打断
                    changed = False
                else:
                    entry.update(added=d.get("added"), removed=d.get("removed"),
                                 added_n=d.get("added_n", 0),
                                 removed_n=d.get("removed_n", 0))
            # 条件从「不满足」跳到「满足」才报一次；一直满足不重复打扰
            when_fire = bool(r["when"]) and hit and not bool(prev.get("when_hit"))
            if (changed and alert_on_change) or when_fire:
                entry["changed"] = changed
                entry["when_fire"] = when_fire
                out["changes"].append(entry)

        if text == MISS:
            out["missing"].append({"label": label, "selector": selector,
                                   "error": got.get("error", "")})

        st[name] = {
            "label": label,
            "selector": selector,
            "text": text,
            "when": r["when"],
            "when_hit": hit,
            "count": got.get("count", 0),
            "updated_at": f"{datetime.now():%Y-%m-%d %H:%M:%S}",
        }

    save_state(host, st)
    return out


def format_message(ts, results):
    """拼报警文案（钉钉/企业微信 markdown：每个逻辑行单独成段）。"""
    n = sum(len(r.get("changes") or []) for r in results)
    blocks = [f"**时间**：{ts}", f"**监控点变化**：{n} 处"]
    for r in results:
        changes = r.get("changes") or []
        if not changes:
            continue
        blocks.append(f"**【{r['host']}】**")
        for c in changes:
            if c.get("whole"):
                # 整页规则不能把整页文本塞进消息里，只列行级差异
                blocks.append(f"{c['label']}（整页）")
                blocks.append(f"文本 +{c.get('added_n', 0)}/-{c.get('removed_n', 0)} 行")
                for s in c.get("added") or []:
                    blocks.append(f"+{s[:80]}")
                for s in c.get("removed") or []:
                    blocks.append(f"-{s[:80]}")
            else:
                blocks.append(f"{c['label']}（{c['selector']}）")
                if c.get("old") is None:
                    blocks.append(f"首次取值：{c['new']}")
                else:
                    blocks.append(f"旧值：{c.get('old')}")
                    blocks.append(f"新值：{c['new']}")
            if c.get("when_fire"):
                blocks.append(f"命中条件：{c['when']}")
            blocks.append(f"页面：{r['url']}")
    return f"🔔 监控点变化 {n} 处", "\n\n".join(blocks)
