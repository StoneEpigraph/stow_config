# webcapture —— 网页定时整页截图 + 时间水印 + 失败报警 + 恢复通知

每 15 分钟对固定几个网址整页截图，图上打时间水印；请求失败推送到钉钉/企业微信群机器人，
站点恢复正常时再推一条「已恢复」，形成闭环。另可用 CSS 选择器盯页面上某个位置（比如排队号），
值变化或满足条件时单独提醒。

> **先看操作手册**：[USAGE.md](USAGE.md) —— 安装、配置、运维、排障，Linux 与 Windows 并列。
> 本文件是 Linux 侧的设计细节与踩坑记录；Windows 差异补充见 [README-windows.md](README-windows.md)。

## 部署到新机器

```bash
cd ~/stow_config && git pull
stow --no-folding webcapture
~/.local/share/webcapture/setup.sh          # 建 venv，装 playwright/pillow，检查 chromium
systemctl --user daemon-reload
systemctl --user enable --now webcapture.timer
systemctl --user list-timers webcapture.timer
```

`notify.conf` 不在仓库里（含密钥），放在 `~/webcapture/notify.conf`，需要报警就按
`notify.conf.example` 填 webhook，然后 `python3 ~/.local/share/webcapture/notify.py --test`。

另外两份可选的配置：`watch.conf` 由 `setup.sh` 从同名 `.example` 复制（页面指定位置监控，见下文），
`compare.conf` 只在需要调阈值时手动复制 `compare.conf.example`。

## 报警怎么配

只用群机器人 Webhook，不依赖任何客户端在线。

**钉钉**（推荐，个人账号就能用）
1. 建一个群（比如只有自己的「监控告警」群）
2. 群设置 → 机器人 → 添加机器人 → **自定义**（通过 Webhook 接入）
3. 安全设置选一个：
   - **自定义关键词** → 填 `告警`，同时写进 `DINGTALK_KEYWORD=告警`（消息标题会自动带上）
   - **加签** → 复制 `SEC...` 那串，写进 `DINGTALK_SECRET=`
   - **IP 地址段** → 把这台机器的出口 IP 加白
4. 复制 Webhook：`https://oapi.dingtalk.com/robot/send?access_token=xxx` → `DINGTALK_WEBHOOK=`

**企业微信**
1. 注册一个组织（个人/团队也能注册），拉一个内部群
2. 群 → 右上角 `...` → 群机器人 → 添加 → 新创建一个
3. 复制 Webhook：`https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx` → `WECOM_WEBHOOK=`
4. 企业微信机器人没有加签，`WECOM_SECRET` 不存在，只靠 URL 里的 key

> 个人微信**没有**官方机器人接口，只能走企业微信这条线。

**验证**
```bash
python3 ~/.local/share/webcapture/notify.py --preview   # 看文案长什么样、当前是否已配置
python3 ~/.local/share/webcapture/notify.py --test      # 真发一条
```

企业微信 markdown 单条上限 4096 字节，`notify.py` 会自动截断并提示去看 `capture.log`。

## 报警策略（health.py）

状态存在 `~/webcapture/state/<host>.health.json`，只做三件事：

| 场景 | 行为 |
|---|---|
| 首次失败 | 立刻报警，标题「⚠️ 网页截图失败 n/4」 |
| 持续失败 | 默认每 **1 小时**续报一次，其余轮次静默（详情仍写日志） |
| 恢复正常 | 推一条「✅ 网页截图已恢复 n/4」，含连续失败次数与中断时长 |

**为什么要降频**：站点真挂了是每 15 分钟一轮，不降频一天就是 96 条同一句话。
现在一次故障长这样：`09:15 失败` → 静默 → `10:15 续报` → 静默 → `11:00 恢复`，共 3 条。

配置在 `~/webcapture/notify.conf`：

| 键 | 默认 | 含义 |
|---|---|---|
| `FAIL_ALERT_INTERVAL` | 3600 | 连续失败时两条提醒的最小间隔（秒），0 = 每次都报 |
| `ALERT_ON_RECOVER` | 1 | 是否发恢复通知 |

恢复判定是**按站点**的：只要该站点下一轮成功且此前 `fail_count>0`，就发一次并清零。
手动单跑某个 URL 也会参与这个状态（和定时轮完全一致，便于排障）。

## 开机 / 重启后的行为

`webcapture.timer` 是 **systemd user timer**，归属于你的用户会话，所以：

| 情况 | 会不会跑 |
|---|---|
| 重启后登录了桌面（或 ssh 登录） | ✅ 自动恢复，无需任何操作 |
| 重启后停在登录界面没登录 | ❌ 不跑 |
| 开了 linger（`loginctl enable-linger`） | ✅ 开机即跑，无需登录 |
| 休眠 / 挂起期间 | ❌ 不跑；唤醒后 `Persistent=true` 会补跑一次 |

`webcapture.timer` 设了 `Persistent=true`，时间戳在
`~/.local/share/systemd/timers/stamp-webcapture.timer`；错过的触发点在会话起来后补跑一轮。

**想让它在不登录的情况下也跑，开 linger（需要 sudo，一次即可）：**

```bash
sudo loginctl enable-linger stone
loginctl show-user stone | grep Linger     # 应显示 Linger=yes
```

代价是用户级 systemd 常驻，多占二三十兆内存；图形登录后用的是同一个 manager，不冲突。

`shot.sh` 在开跑前会等网络就绪（`nmcli` 判断，最多 60 秒），因为 user 实例里的
`After=network-online.target` 是空实现——开机补跑的那一轮往往还没连上网，
不等就会四条一起超时误报。

## 文件

| 路径 | 作用 |
|---|---|
| `.local/share/webcapture/capture.py` | Playwright 整页截图 + Pillow 打水印 |
| `.local/share/webcapture/compare.py` | 变更检测：文本哈希 + 整页图差异 |
| `.local/share/webcapture/watch.py` | 页面监控：按 CSS 选择器盯一块内容，或盯整页并排掉指定区域 |
| `.local/share/webcapture/watch.conf.example` | 监控配置模板（`setup` 会复制成 `~/webcapture/watch.conf`） |
| `.local/share/webcapture/shot.sh` | 入口：找解释器、flock 防重叠、日志、清理 |
| `.local/share/webcapture/notify.py` | 钉钉/企业微信 webhook 报警 |
| `.local/share/webcapture/health.py` | 站点健康状态：连续失败计数、降频、恢复判定 |
| `.local/share/webcapture/paths.py` | 跨平台路径 / 浏览器 / 字体探测（Linux + Windows） |
| `.local/share/webcapture/setup.sh` | 一次性环境准备（顺带复制几份 `*.conf.example`） |
| `.local/share/webcapture/setup.ps1` / `shot.ps1` / `install-task.ps1` | Windows 版入口与计划任务 |
| `.config/systemd/user/webcapture.*` | 每 15 分钟的 user timer |

## 动效冻结（capture.py）

整页截图最大的假差异来源不是内容变了，而是**轮播图转到了第几张、横向滚动条滚到哪一像素**。
实测同一站点两轮之间：bjyouth 大图 14.59%、bjjdzx 横向滚动条 16.71%。冻结后降到 **0.02%–0.05%**。

截图前（懒加载滚动完、等图片就绪后）执行一次 `freeze_motion()`：

1. **滚动归零**：所有元素 `scrollLeft/scrollTop` 置 0，`window.scrollTo(0,0)`，同源 iframe 递归处理
2. **轮播停播**：Swiper（`slideTo(0)` + `autoplay.stop()`）、Slick、Owl、Bootstrap、Splide 各自 API
3. **轨道归位**：SuperSlide 这类用 inline `left: -Npx` 位移的把 `left` 归零**并关闭过渡**；
   Swiper/layui 用 `transform` 位移的把 transform 置 `none`
4. **圆点归一**：分页高亮移回第一个，避免「图是第 1 张、点还亮在第 3 个」
5. **冻住定时器**：从文档创建起挂钩 `setInterval/setTimeout`，收尾时清空已注册的定时器
   并封住新的 `set*/requestAnimationFrame` —— 这是 theScrollTank 这类「每 tick 推 1px」的唯一有效手段

⚠️ 两个踩过的坑：

- **复位要在冻结之后再做一次**。第一次复位后到冻住之间还有 120ms，还在跑的轮播会把走过
  的那几像素重新写回 inline left（实测 -2px / -3px 不稳定），两轮仍然差 1~3px。
- **`left` 复位必须同时 `transition: none`**。SuperSlide 用 CSS 过渡做动画，而
  `screenshot(animations="disabled")` 会把进行中的过渡**快进到终点**，
  刚复位的位置又被推回原来那张幻灯片（实测两轮差 6%）。

图片加载另有两道保障：

- `wait_images()`：对所有 `<img>` 调 `decode()`，确保「可上屏」而不只是「已下载」
  （bjyouth 有张 1.2MB 图会出现 `complete=false` 但 `naturalWidth=1080` 的瞬态）
- **持久 profile**（`~/.cache/webcapture-profile`）复用 HTTP 磁盘缓存：bjjdzx 主页 96 张图，
  冷缓存一轮 60 多张来不及下载，截图里一片空白格；缓存命中后未就绪图片 67 → 1~3 张，
  单轮耗时也从 ~70s 降到 ~22s

| 环境变量 | 默认 | 含义 |
|---|---|---|
| `WEB_FREEZE_MOTION` | 1 | 设 0 关闭动效冻结 |
| `WEB_IMAGE_WAIT_MS` | 3000 | 等图片就绪的上限（毫秒） |
| `WEB_DATE_WAIT_MS` | 6000 | 等 `#currentDate` 填充的上限（毫秒） |

profile 目录可随时删（会重建，只是下一轮变慢）：`rm -rf ~/.cache/webcapture-profile`。

## 变更检测（compare.py）

两路信号：

1. **文本哈希（主信号）**：取 JS 执行后的 `body.innerText`，归一化（去零宽字符、折叠空白、
   按 `IGNORE_REGEX` 丢噪声行）后算 sha256。变了就报警，并附上新增/删除的行。
2. **整页图差异（辅助）**：跟上一轮**打水印前**的裸图逐像素比，输出变化像素占比，
   并在 `~/public/webcapture/_diffs/<host>/` 生成红框标出变化区域的图。

为什么不直接比最终截图：**水印每轮都变**，带水印比会导致每张都"全页变化"。所以裸图另存
在 `~/webcapture/state/<host>.prev.png`（每站只留一张，磁盘有界），比完再打水印出成品。

配置 `~/webcapture/compare.conf`（模板 `compare.conf.example`）：

| 键 | 默认 | 含义 |
|---|---|---|
| `ALERT_ON_TEXT_CHANGE` | 1 | 文本变化就报警 |
| `ALERT_ON_IMAGE_CHANGE` | 0 | 图像变化也报警（噪声大，默认关） |
| `IMAGE_DIFF_THRESHOLD` | 0.02 | 变化像素占比阈值（2%） |
| `IGNORE_REGEX` | `^\d+/\d+$\|^\d{1,2}:\d{2}(:\d{2})?$` | 丢噪声行；默认滤轮播页码和纯时间 |
| `STRIP_DATE_PREFIX` | 1 | 剥掉行首「YYYY年M月D日 星期X」前缀 |
| `MAX_SNIPPET_LINES` | 6 | 报警里每站最多列几行 diff |
| `IGNORE_REORDER` | 1 | 「只是换了顺序」不报警：删掉的行和新增的行内容完全相同、只是位置不同 |

**第一次运行只建基线，不报警**（没有可比对象）。想重建基线就删 `~/webcapture/state/<host>.json`。

已知噪声：轮播图（页码/图片本身）、访问量计数、`星期X`、日期、**列表顺序轮转**。
文本侧靠 `IGNORE_REGEX` 和 `IGNORE_REORDER` 消化；图像侧因为默认 `ALERT_ON_IMAGE_CHANGE=0`，只记录不报警。

`IGNORE_REORDER` 是给 bjjdzx.com 那种横向滚动列表兜底的：页面里有个 `.theScrollTank`
（轨道宽 10000px、`overflow:hidden`）装着一排条目（LSD、K粉、摇头丸…），每条滚过一个条目宽就把
第一个 `li` 挪到队尾 —— DOM 顺序换了一格，于是 `innerText` 报 `+LSD / -LSD`，
而截图 0.00% 差异、网页一个字没改。判定规则是「新增行集合 == 删除行集合（含重复计数）」，
命中就只写日志「顺序变化 N 行（内容相同，忽略）」，不进报警队列。

`STRIP_DATE_PREFIX` 是给 bjyouth.gov.cn 这类站兜底的：它的顶栏日期由
`window.onload` 里的 JS 填进 `#currentDate`，而 `window.onload` 要等百度统计、
党政机关标识等第三方资源加载完才触发 —— 实测快时 2s、慢时 20s+、偶尔整轮都不填。
于是同一页面的 `innerText` 在「有日期」「无日期」之间随机跳变，每跳一次就报一次变更。
`capture.py` 会先等它填上（`WEB_DATE_WAIT_MS`，默认 6s），等不到也照常截图；
`compare.py` 再剥掉行首日期前缀，两边都不依赖对方。注意规则只剥「日期后面还有内容」的行，
正文里「整行只有一个日期」的条目（如 bjjdzx 的 `1844年10月24日`）会原样保留。

## 排队页监控（watch.py）

整页对比适合「网站发新公告」这种粗粒度变更，但排队页上会变的只有那个号码：编号每轮都在变，
整页报警就变成「每 15 分钟响一次」，而真正关心的「前面还有几个人」藏在 DOM 里看不出来。
所以另有一条按 **CSS 选择器盯指定位置** 的路子，也可以反过来用：**盯整页、把噪声区域排掉**。

配置 `~/webcapture/watch.conf`（模板 `watch.conf.example`，不建就完全不监控）。
用的是 INI 格式（`configparser` 是标准库，不引入任何第三方依赖）：

```ini
[watch]
alert_on_change = 1
wait_ms = 3000

# 一个节 = 一个监控点；节名就是报警文案里显示的名字，也是状态文件里的键
[当前叫号]
url = https://example.com/queue/
selector = #current-number

[前面等待]
url = https://example.com/queue/
selector = .waiting-count
when = <=10

# selector 不写 = 监控整页（可以顺手排掉噪声区域）
[整页]
url = https://example.com/news/

[忽略轮播和访问量]
url = https://example.com/queue/
ignore = .carousel, .visitor-count

# 行内不要写 # 注释：`url = https://a.com/  # 备注` 会把 # 后面也当成 URL 的一部分
```

- `url` 必填，`selector` **可省**（省了就是监控整页文本），`when` 也可省（省了就只看变化）；
  字段名大小写不敏感。
- `ignore` 可选：读**整页文本**之前先把这些区域藏掉（多个用逗号写，也可以直接用 `:is()`）。
  它只影响整页文本（整页节自己的取值、以及 `compare.py` 对该页的整页对比），
  **不影响**同一个节里 `selector` 的取值——那个仍按选择器原样取。
- **一个节就是一个监控点**，有没有 `selector` 都一样；只是 `selector` 把范围缩到一块，
  没有就是整页。所以「整页 + 忽略轮播」写成 `url` + `ignore` 两行就够，不用再写 `selector`。
- **节名就是标签**，也是状态文件里的键 —— 改选择器不会丢历史，改节名则算新监控点（重建基线）。
- 同一个 URL 写多个节就是盯多个位置；选择器命中多个元素时，取前 3 个用 ` / ` 拼起来。
- 这个 URL **不用**再改 `capture.py` 的 `DEFAULT_URLS`：`main()` 会把它并进本轮截图列表，
  只写 ignore 的页也一样，否则没人打开那个页面就取不到内容。
- 旧的竖线写法（`URL | 选择器 | 标签 | 条件`）仍能读，方便老配置，但不建议新写。

**为什么不选 YAML / TOML**：YAML 里 `selector: #current-number` 的 `#` 是注释符，值会变空，
而 CSS 的 id 选择器全以 `#` 开头 —— 最关键的字段正好踩雷；TOML 的 `tomllib` 要 Python 3.11+，
而这个项目在 Windows 上仍支持 3.9/3.10。INI 两样都不会：值里的 `#`、`|`、`%` 都是字面量。

`when` 支持 `<= < >= > == != =`，取文本里**第一个数字**比较（`A-101` 的连字符不当负号）；
`==` / `!=` 右边不是数字时按文本比较。条件只在「不满足 → 满足」时提醒**一次**，
之后一直满足不会刷屏——这正是「排到我之前提醒我一下」的语义。

`[watch]` 段的全局开关：

| 键 | 默认 | 含义 |
|---|---|---|
| `alert_on_change` | 1 | 文本变了就报 |
| `alert_on_first` | 0 | 第一次取值（建基线）是否也报 |
| `wait_ms` | 3000 | 等元素出现的上限（毫秒），0 = 不等直接取 |
| `skip_compare_alert` | 1 | 该 URL 有监控点时跳过整页变更报警（只写日志）；含图像报警，要保留就把这个设 0 |

几个实现上的约定：

- **抓取时机**：在页面稳定、动效冻结之后、打水印之前取，所以拿到的是归档截图里那块内容。
- 等元素用的是 Python 侧轮询，不是 `page.wait_for_function`：截图前 `freeze_motion()` 已把页面
  的 `setTimeout` / `rAF` 换成空实现，页面侧轮询永远等不到。
- 选择器没匹配到内容记成 `(未匹配)`，**当作一次变化**参与对比，日志里出 `WATCH-WARN`。
  内容后来出现时就会有一条「(未匹配) → 真实值」的报警。
- 每轮的取值存在 `~/webcapture/state/<域名>.watch.json`，删掉即重建基线。
- 一个 URL 既有公告又有排队号时，可用 `skip_compare_alert = 0` 让两条报警都发。

**整页监控（`selector` 省略）的额外约定**：

- 整页文本先过 `ignore` 隐藏，再过 `compare.norm_text()`（丢零宽、折空白、剥行首日期、
  按 `IGNORE_REGEX` 丢时钟/轮播页码）。**必须跟已有整页报警同一套口径**：直接用原始
  `innerText`，一个时钟就够让整页规则每轮都响。
- 行级差异也复用 `compare.diff_change()`，所以 bjjdzx 那种横向滚动列表「只是换了顺序」不报警。
- 报警文案只能是**行级摘要**（`文本 +N/-M 行` 加前几行新增/删除），不会把整页原文塞进消息。
- 有整页规则时同样会用 `skip_compare_alert` **抑制 `compare.py` 的整页报警**，否则一轮两条。
  副作用：`ALERT_ON_IMAGE_CHANGE = 1` 时图像报警会被一并抑制；需要就设 `skip_compare_alert = 0`。
- `alert_on_change` / `alert_on_first` / `when` 对整页规则一样生效；整页取值上限
  `WHOLE_MAX = 20000` 字符，超出部分截断（只会漏报尾部改动，不会误报）。

> 只在本轮截图时采样一次（默认 15 分钟一轮，受 `webcapture.timer` 限制），**不是常驻轮询**。
> 要「每分钟看一次」得把这个 timer 频率调高，或另做常驻 watcher。

**安静模式**：排队号每轮都变时，把 `alert_on_change` 设 0，只留每个节的 `when`，
就只在「人数 ≤10」「状态变可预约」这种关键时刻响一下。

### 忽略指定区域（`ignore`）

绝大多数场景要的不是「只盯一小块」，而是「**整页都盯着，但轮播/广告位/访问量别来烦我**」。
这类噪声原来只能在 `compare.conf` 里用 `IGNORE_REGEX` 逐行匹配，文案一改就得跟着改正则；
`ignore` 直接用 CSS 选择器圈区域，页面改版只需改一行选择器：

```ini
[忽略轮播和访问量]
url = https://example.com/queue/
ignore = .carousel, .visitor-count
```

这个节没有 `selector`，所以它就是**整页监控**：除了这两块，页面上其它任何文字变化都会报。
想同时盯整页又盯某一块，就写两个节（一个省掉 `selector`，一个写）：

```ini
[整页]
url = https://example.com/news/

[叫号]
url = https://example.com/news/
selector = #current-number
```

实现上的几个选择：

- 取文本前用一张**一次性样式表**（`[data-wc-ignore]{display:none !important}`）把命中的元素藏掉，
  读完 `innerText` 立即删属性、移除样式表。不改元素原有内联 `style`：早先试过
  `removeAttribute('style')`，碰过 `el.style` 后 Chromium 会留下一个空的 `style=""`。
- `!important` 能盖过元素自带的 `display:block`，否则藏不住。
- 在**截图之后**才隐藏，所以归档图和 `_diffs/` 里看到的还是完整页面。
- 只影响**文本**对比：整页图差异还是按像素比（图像没法这么简单地「抠掉一块」）。
- 选择器写错（语法非法）不会炸，只是那一条不生效；日志里有 `IGNORE ... 忽略 N 条选择器` 可对数。
- `ignore` 的值**整串**交给 `querySelectorAll`，不按逗号拆——`:is(.a, .b)` 里的逗号
  拆开会把选择器拆断。逗号组合、后代/子/相邻组合器（`.list > li+li`）、伪类、属性选择器都能用。
- 续行要缩进（`configparser` 会把缩进行拼到上一行，用 `\n` 连起来，在 CSS 里等于空格）：

```ini
[忽略]
url = https://example.com/queue/
ignore = .carousel,
         .visitor-count,
         ul.list > li:nth-child(2)
```

## 产物

成品截图直接落在 `~/public/webcapture/`（`~/public` 已由 Samba 共享，内网可直接看），
状态与日志留在 `~/webcapture/`（不对外）。

```
~/public/webcapture/_latest/<域名>.png                 # 每站最新一张（硬链接，名字固定）
~/public/webcapture/_latest/SUMMARY.txt                # 每站最后成功时间 + 本轮结果
~/public/webcapture/<域名>/<YYYY-MM-DD>/<HHMMSS>.png   # 成品（带水印）
~/public/webcapture/_diffs/<域名>/<时间>.png            # 红框标出变化的差异图
~/webcapture/state/<域名>.{json,txt,prev.png}          # 基线：哈希 / 上轮文本 / 上轮裸图
~/webcapture/state/<域名>.health.json                  # 连续失败计数（fail_count=0 即正常）
~/webcapture/state/<域名>.watch.json                   # 监控点上轮的文本与条件命中状态
~/webcapture/capture.log     # 每条结果即时写，排障先看这个
~/webcapture/run.out         # 每轮汇总
~/webcapture/notify.conf     # webhook（含密钥，只在仓库外）
~/webcapture/compare.conf    # 变更检测阈值
~/webcapture/watch.conf      # 页面指定位置监控
```

`_latest/` 用**硬链接**而不是软链：Samba 对符号链接的处理依客户端和 `unix extensions` 而定，
Windows 资源管理器常打不开；硬链接在 SMB 里就是普通文件，且不额外占空间（同一 inode）。

站点失败时**旧图会留在 `_latest/` 不动**，靠 `SUMMARY.txt` 里的「最后成功」时间区分——
所以看最新状态是先扫一眼 SUMMARY，而不是只看图。

### 内网访问（SMB）

`/etc/samba/smb.conf` 里已有 `[public]` 段指向 `/home/stone/public`，匿名只读浏览即可：

```
Windows      \\10.168.1.152\public\webcapture
             \\10.168.1.152\public\webcapture\_latest     ← 只看当前状态用这个
macOS        smb://10.168.1.152/public/webcapture
Linux        smbclient //10.168.1.152/public -N
```

IP 现在由 dhcpcd 从路由器获取，**换网络会变**；想固定就用主机名（需 nmbd + WINS）或给路由器配静态租约。

如果想给截图单独开一个**只读**共享（避免匿名写满/误删），在 `smb.conf` 追加：

```ini
[webcapture]
   path = /home/stone/public/webcapture
   public = yes
   read only = yes
   browseable = yes
```

然后 `sudo systemctl restart smb`。注意现有 `[public]` 是 `read only = no`，内网任何人都能删东西。

## 改网址

改 `capture.py` 顶部的 `DEFAULT_URLS`。

## 注意

- 路径、浏览器、字体、UA 的探测集中在 `paths.py`，Linux 与 Windows 共用；
  两个平台上目录默认值不同（Windows 用 `%LOCALAPPDATA%` 存 venv/profile），
  全部可用 `WEBCAPTURE_*` 环境变量覆盖，见 README-windows.md。
- `/tmp` 若是小容量 tmpfs，pip 会报「设备上没有空间」；`shot.sh`/`setup.sh` 已把 `TMPDIR`
  指到 `~/.cache/webcapture-tmp`，Chromium 也带 `--disable-dev-shm-usage`。
- 默认不下载 Playwright 自带 Chromium，直接用系统浏览器（`paths.py` 按平台探测 Chrome / Edge /
  chromium）；Windows 上两个都没有时用 `setup.ps1 -InstallBrowser` 补一个。
- 水印用中灰+浅描边，纯白字在白底页面会看不见。
- 磁盘占用约 300–500MB/天；要自动清理就把环境变量 `RETENTION_DAYS=7` 传进去（默认 0 = 不删）。
  用 systemd 的话在 `webcapture.service` 里加 `Environment=RETENTION_DAYS=7`。
- 依赖装在 `~/.local/share/webcapture-venv`（`setup.sh` 建的独立 venv），**不要依赖
  `~/.workbuddy/binaries/python/...`** —— 那是 WorkBuddy 自己的运行时，升级时可能被清掉。
  `shot.sh` 的探测顺序：独立 venv → WorkBuddy venv → `/usr/bin/python3`，逐个验证能否 import。
