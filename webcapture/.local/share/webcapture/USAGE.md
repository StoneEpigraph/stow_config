# webcapture 使用说明

**Linux 与 Windows 同一份代码，只换入口脚本。** 这份文档是操作手册：装、配、跑、看、排障。
设计细节与踩坑记录见 `README.md`（Linux）和 `README-windows.md`（Windows 差异）。

---

## 1. 它做什么

每 15 分钟对一组固定网址做一次**整页截图**，图上打时间水印；同时比对上一轮的内容，
发现「失败」「恢复」「内容变更」就推到钉钉或企业微信群机器人。

| 能力 | 说明 |
|---|---|
| 整页截图 | Playwright + 系统 Chromium/Chrome，1440px 宽视口，全页高度 |
| 时间水印 | 左上时间戳 + 斜向平铺水印 + 右下角时间条 |
| 动效冻结 | 截图前把轮播、横向滚动、定时器全部复位，避免「假差异」 |
| 内容变更报警 | 文本 sha256（主）+ 整页图逐像素（辅），附新增/删除行 |
| 失败报警 | 首次立刻报，之后默认每小时续报一次，不刷屏 |
| 恢复通知 | 站点恢复时推一条「已恢复」，含中断时长 |
| 产物发布 | 写到一个可被 SMB/共享访问的目录，`_latest/` 只有每个站最新一张 |

原始图不落地：比完直接打水印出成品，磁盘占用可控。

---

## 2. 前置条件

| 项 | Linux | Windows |
|---|---|---|
| 系统 | 任意发行版（本项目按 Arch 验证） | Windows 10 / 11 |
| Python | 3.9+，且能 `python3 -m venv` | 3.9+（`winget install Python.Python.3.12`） |
| 浏览器 | chromium / chrome / edge / brave 任一 | Chrome / Edge（自带即可） |
| 调度 | systemd user 实例 | 任务计划程序（系统自带） |
| 网络 | 能直连目标站点 | 同左 |

**不需要**装 Playwright 自带的 Chromium —— 默认复用系统浏览器，省 150MB。
个别机器两者都没有时：Linux `sudo pacman -S chromium`，Windows `setup.ps1 -InstallBrowser`。

---

## 3. 安装

### 3.1 Linux

仓库方式（推荐，和两台机器同步配置的做法一致）：

```bash
cd ~/stow_config && git pull
stow --no-folding webcapture                      # 把包链到 $HOME
~/.local/share/webcapture/setup.sh                # 建 venv、装依赖、查浏览器、生成 notify.conf
systemctl --user daemon-reload
systemctl --user enable --now webcapture.timer
```

不想用 stow 也可以就地跑，脚本靠 `readlink -f $0` 定位，不依赖固定路径：

```bash
git clone git@github.com:StoneEpigraph/stow_config.git ~/stow_config
cd ~/stow_config/webcapture/.local/share/webcapture && ./setup.sh
```

`setup.sh` 做四件事，重复跑是安全的：

1. 建 `~/.local/share/webcapture-venv`，装 `playwright` + `pillow`
2. 检查 `chromium/chrome/brave`，一个都没有就报错退出（提示装哪个包）
3. 若 `~/webcapture/notify.conf` 不存在，从模板复制一份并 `chmod 600`
4. 打印试跑命令

### 3.2 Windows

Windows 上**就地运行在仓库目录**（等价于 Linux 的 stow 软链），`git pull` 后代码立刻生效，
依赖和缓存放 `%LOCALAPPDATA%`，状态放 `%USERPROFILE%`，都不脏仓库。

```powershell
git clone git@github.com:StoneEpigraph/stow_config.git $env:USERPROFILE\stow_config
cd $env:USERPROFILE\stow_config\webcapture\.local\share\webcapture

# 建 venv、装依赖、查浏览器、生成 notify.conf、注册计划任务（一条搞定）
powershell -ExecutionPolicy Bypass -File .\setup.ps1 -RegisterTask

# 机器上没有 Chrome/Edge 时加 -InstallBrowser（下载约 150MB）
powershell -ExecutionPolicy Bypass -File .\setup.ps1 -InstallBrowser -RegisterTask
```

脚本被执行策略拦住时，每条命令都带 `-ExecutionPolicy Bypass`，或先 `Unblock-File .\*.ps1`。

---

## 4. 装完必须做的三件事

### 4.1 改网址

网址写在 `capture.py` 顶部的 `DEFAULT_URLS`（默认四个：juanzhuzhongxin、bjyouth、bjjdzx、bjydf）。

```python
DEFAULT_URLS = [
    "https://www.juanzhuzhongxin.cn/donationWeb/",
    "https://www.bjyouth.gov.cn/",
    "https://www.bjjdzx.com/",
    "https://www.bjydf.cn/",
]
```

这是**代码里的配置**，改完应该提交到仓库，另一台机器 `git pull` 后才一致。
只想临时看别的站点，不用改代码 —— 传参即可：

```bash
~/.local/share/webcapture/shot.sh https://example.com/          # Linux
```
```powershell
powershell -ExecutionPolicy Bypass -File .\shot.ps1 https://example.com/   # Windows
```

新增站点第一次跑只**建基线**，不报警（没有可比对象）。

### 4.2 填报警渠道

正式文件（含密钥，**不进仓库**）：

| 平台 | 路径 |
|---|---|
| Linux | `~/webcapture/notify.conf` |
| Windows | `%USERPROFILE%\webcapture\notify.conf` |

```bash
$EDITOR ~/webcapture/notify.conf
```
```powershell
notepad $env:USERPROFILE\webcapture\notify.conf
```

最少填一个 webhook（**注释只能独占一行，不要写在值后面** —— 解析器不剥行尾注释，
`DINGTALK_KEYWORD=告警  # 注释` 会把注释一起当关键词，钉钉直接报 `310000`）：

```ini
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxxx

# 安全设置选了「自定义关键词」才填，值必须与机器人里填的完全一致
DINGTALK_KEYWORD=告警

# 安全设置选了「加签」才填，SEC 开头那一串
DINGTALK_SECRET=SECxxxx

# 企业微信（与钉钉二选一）
WECOM_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxx
```

群机器人怎么建：

- **钉钉**：建一个只有自己的群 → 群设置 → 机器人 → 添加机器人 → **自定义（Webhook 接入）**；
  安全设置三选一（关键词最省事，填什么就写进 `DINGTALK_KEYWORD`，消息标题会自动带上）；复制 Webhook。
- **企业微信**：注册组织（个人也能注册）→ 拉个内部群 → 群右上角 `...` → 群机器人 → 添加；
  只有 URL 里的 key，没有加签。个人微信没有官方机器人接口。

验证（真发一条消息）：

```bash
~/.local/share/webcapture-venv/bin/python3 ~/.local/share/webcapture/notify.py --test
```
```powershell
& "$env:LOCALAPPDATA\webcapture\venv\Scripts\python.exe" .\notify.py --test
```

`--preview` 只打印文案、不发消息，用来确认「当前有哪些渠道已配置」。

### 4.3 手动跑一轮

```bash
systemctl --user start webcapture.service
tail -5 ~/webcapture/run.out
```
```powershell
Start-ScheduledTask -TaskName webcapture
Get-Content "$env:USERPROFILE\webcapture\run.out" -Tail 5 -Encoding UTF8
```

看到 `done ok=4 fail=0 changed=0 recovered=0`、并且成品目录出现当天的图，就算装好了。

**验收清单**（五条都过才算完）：

1. `run.out` 里有 `done ok=4 fail=0`
2. 成品目录有 `<域名>/<今天>/<时分秒>.png`，图上有时间水印
3. `_latest/` 里每站一张图 + `SUMMARY.txt` 在
4. `notify.py --test` 钉钉/企业微信收到消息
5. 定时器/计划任务的下次运行时间正确（见第 6 节）

---

## 5. 配置参考

### 5.1 目录与环境变量

| 内容 | Linux 默认 | Windows 默认 | 覆盖变量 |
|---|---|---|---|
| 代码 | `~/.local/share/webcapture` | `<仓库>\webcapture\.local\share\webcapture` | — |
| 状态/日志/基线/配置 | `~/webcapture` | `%USERPROFILE%\webcapture` | `WEBCAPTURE_HOME` |
| 成品截图 | `~/public/webcapture` | `%USERPROFILE%\public\webcapture` | `WEBCAPTURE_IMG_ROOT` |
| 依赖 venv | `~/.local/share/webcapture-venv` | `%LOCALAPPDATA%\webcapture\venv` | `WEBCAPTURE_VENV` |
| 浏览器 profile | `~/.cache/webcapture-profile` | `%LOCALAPPDATA%\webcapture\profile` | `WEBCAPTURE_PROFILE` |
| 临时目录 | `~/.cache/webcapture-tmp` | `%LOCALAPPDATA%\webcapture\tmp` | `WEBCAPTURE_TMP` |
| 缓存父目录 | `~/.cache` | `%LOCALAPPDATA%\webcapture` | `WEBCAPTURE_CACHE` |

其余可覆盖项：

| 变量 | 默认 | 作用 |
|---|---|---|
| `WEBCAPTURE_BROWSER` | 自动探测 | 指定浏览器可执行文件 |
| `WEBCAPTURE_FONT` | DejaVu / 微软雅黑 | 水印字体（水印里要显示中文就指向 CJK 字体） |
| `WEBCAPTURE_UA` | 按平台生成 | 覆盖 User-Agent |
| `WEBCAPTURE_PYTHON` | — | 指定解释器（仅 Windows `shot.ps1`） |
| `RETENTION_DAYS` | 0（不删） | 超过 N 天的 png 自动删除 |
| `WEB_FREEZE_MOTION` | 1 | 0 = 关闭动效冻结（对比不出差异时才考虑关） |
| `WEB_IMAGE_WAIT_MS` | 3000 | 等图片可上屏的上限 |
| `WEB_DATE_WAIT_MS` | 6000 | 等顶栏日期填充的上限 |

Linux 上持久化环境变量（systemd 不读 `~/.bashrc`）：

```bash
systemctl --user edit webcapture.service
```

在打开的编辑器里，在 `[Service]` 段下加一行 `Environment=RETENTION_DAYS=7`（`#` 开头的行是注释，
别把内容也注释掉了），保存后：

```bash
systemctl --user daemon-reload && systemctl --user restart webcapture.timer
```

Windows 用用户级变量（计划任务会继承，改完要重新登录或重启）：

```powershell
[Environment]::SetEnvironmentVariable('WEBCAPTURE_IMG_ROOT', 'D:\public\webcapture', 'User')
```

### 5.2 notify.conf —— 报警策略

| 键 | 默认 | 含义 |
|---|---|---|
| `DINGTALK_WEBHOOK` | 空 | 钉钉群机器人地址 |
| `DINGTALK_SECRET` | 空 | 加签密钥（`SEC` 开头） |
| `DINGTALK_KEYWORD` | 空 | 自定义关键词，消息标题里自动带上 |
| `WECOM_WEBHOOK` | 空 | 企业微信群机器人地址 |
| `FAIL_ALERT_INTERVAL` | 3600 | 同一站点连续失败时两条提醒的最小间隔（秒），0 = 每次都报 |
| `ALERT_ON_RECOVER` | 1 | 是否发恢复通知 |

一次真实故障的推送节奏：`09:15 失败` → 静默 → `10:15 续报` → 静默 → `11:00 恢复`，共 3 条。
状态存 `state/<host>.health.json`，`fail_count=0` 即正常。

### 5.3 compare.conf —— 变更检测

没有这个文件就全用默认值。

| 键 | 默认 | 含义 |
|---|---|---|
| `ALERT_ON_TEXT_CHANGE` | 1 | 文本变化就报警（主信号） |
| `ALERT_ON_IMAGE_CHANGE` | 0 | 图像变化也报警（噪声大，默认只记录） |
| `IMAGE_DIFF_THRESHOLD` | 0.02 | 变化像素占比阈值（2%） |
| `IGNORE_REGEX` | `^\d+/\d+$\|^\d{1,2}:\d{2}(:\d{2})?$` | 丢弃匹配的整行，默认滤轮播页码和纯时间 |
| `STRIP_DATE_PREFIX` | 1 | 剥掉行首「YYYY年M月D日 星期X」前缀 |
| `MAX_SNIPPET_LINES` | 6 | 报警里每站最多列几行 diff |
| `IGNORE_REORDER` | 1 | 只是换了顺序（增删行内容相同）不报警 |

模板在 `compare.conf.example`，复制到 `$WEBCAPTURE_HOME/compare.conf` 再改。
默认值已经能压住轮播、日期、列表轮转三类噪声，**没遇到新噪声就别动它**。

### 5.4 改轮询间隔

**Linux** —— 改 `~/.config/systemd/user/webcapture.timer` 的 `OnCalendar`
（**注释必须独占一行**，systemd 不认行尾 `#`，写在值后面会让 timer 解析失败）：

```ini
# 每 15 分钟；每 30 分钟改 0/30，每小时改 hourly
OnCalendar=*:0/15
```

```bash
systemctl --user daemon-reload && systemctl --user restart webcapture.timer
systemctl --user list-timers webcapture.timer     # 确认 NEXT 时间
```

**Windows** —— 重注册，参数直接给：

```powershell
powershell -ExecutionPolicy Bypass -File .\install-task.ps1 -IntervalMinutes 30
```

自定义任务名可以并存多套（`-TaskName webcapture-test`），调试时不影响正式任务。

---

## 6. 日常操作

| 操作 | Linux | Windows |
|---|---|---|
| 立即跑一轮 | `systemctl --user start webcapture.service` | `Start-ScheduledTask -TaskName webcapture` |
| 暂停定时 | `systemctl --user stop webcapture.timer` | `Disable-ScheduledTask -TaskName webcapture` |
| 恢复定时 | `systemctl --user start webcapture.timer` | `Enable-ScheduledTask -TaskName webcapture` |
| 看下次运行 | `systemctl --user list-timers webcapture.timer` | `Get-ScheduledTaskInfo -TaskName webcapture` |
| 看每轮汇总 | `tail -30 ~/webcapture/run.out` | `Get-Content "$env:USERPROFILE\webcapture\run.out" -Tail 30 -Encoding UTF8` |
| 看逐条结果 | `tail -50 ~/webcapture/capture.log` | `Get-Content "$env:USERPROFILE\webcapture\capture.log" -Tail 50 -Encoding UTF8` |
| 看服务日志 | `journalctl --user -u webcapture.service -n 50` | `Get-ScheduledTaskInfo -TaskName webcapture \| Format-List`（历史记录默认关闭，排障以 `run.out` 为准） |
| 开机自启 | `enable` 后已生效；免登录需 linger（见下） | 任务自带「登录时」触发器 |
| 卸载定时 | `systemctl --user disable --now webcapture.timer` | `.\uninstall-task.ps1` |

**Linux 免登录运行**（重启后停在登录界面也照跑）：

```bash
sudo loginctl enable-linger stone
loginctl show-user stone | grep Linger      # Linger=yes 即生效
```

代价是用户级 systemd 常驻，多占二三十兆内存。**Windows 没有对应物**：计划任务是
`LogonType Interactive`，必须当前用户登录后才跑；注销即停、锁屏无影响。

睡眠/休眠期间两边都不跑，醒来后补跑一轮（Linux `Persistent=true`，Windows `StartWhenAvailable`）。

`capture.log` 里每行开头就是结论，排障只认这几个词：

```
BROWSER /usr/bin/chromium
OK      https://www.bjyouth.gov.cn/  1557x3085  22.4s
CHANGE https://www.bjjdzx.com/ 文本 +1/-1 行，图像 0.00%
BASELINE https://example.com/ 已建立基线
FAIL   https://www.bjydf.cn/  Timeout ... | 连续第 1 次 | 已报警
```

---

## 7. 产物与内网共享

```
<IMG_ROOT>/_latest/<域名>.png               每站最新一张（硬链接，名字固定）
<IMG_ROOT>/_latest/SUMMARY.txt              每站最后成功时间 + 本轮结果
<IMG_ROOT>/<域名>/<YYYY-MM-DD>/<HHMMSS>.png 成品（带水印）
<IMG_ROOT>/_diffs/<域名>/<时间>.png          红框标出变化区域的差异图
<WEBCAPTURE_HOME>/state/<域名>.{json,txt,prev.png}   基线
<WEBCAPTURE_HOME>/state/<域名>.health.json           连续失败计数
<WEBCAPTURE_HOME>/capture.log / run.out              日志
```

**站点失败时旧图留在 `_latest/` 不动** —— 判断当前状态要先看 `SUMMARY.txt` 的「最后成功」时间，
不能只看图。

### Linux（Samba）

`~/public` 已由 `[public]` 共享，直接访问：

```
Windows   \\<本机IP>\public\webcapture\_latest
macOS     smb://<本机IP>/public/webcapture
Linux     smbclient //<本机IP>/public -N
```

IP 由 DHCP 分配（示例机器是 `10.168.1.152`），换网络会变；想固定就给路由器配静态租约。
现有 `[public]` 是 `read only = no`，内网任何人都能删东西 —— 想只读就单开一段：

```ini
[webcapture]
   path = /home/stone/public/webcapture
   public = yes
   read only = yes
   browseable = yes
```

### Windows（SMB）

```powershell
New-SmbShare -Name webcapture -Path "$env:USERPROFILE\public\webcapture" -ReadAccess Everyone
Remove-SmbShare -Name webcapture        # 取消
```

已经有共享盘或 NAS 时，直接把成品写过去更省事：

```powershell
[Environment]::SetEnvironmentVariable('WEBCAPTURE_IMG_ROOT', '\\nas\public\webcapture', 'User')
```

`_latest` 的硬链接只在同一卷内有效，跨卷/网络共享会自动退化成复制，功能不受影响。

---

## 8. 运维操作

**重建基线**（内容改版后不想报一次大 diff，或基线被残缺快照污染）：

```bash
rm ~/webcapture/state/www.example.com.json        # 下一轮重新建基线，不报警
```

要连文本和裸图一起重置，把 `.txt`、`.prev.png` 也删掉。

**单站调试**（只跑一个站点，其他状态不受影响）：

```bash
~/.local/share/webcapture/shot.sh https://www.bjydf.cn/
~/.local/share/webcapture-venv/bin/python3 ~/.local/share/webcapture/capture.py https://www.bjydf.cn/
```
```powershell
powershell -ExecutionPolicy Bypass -File .\shot.ps1 https://www.bjydf.cn/
```

单跑同样参与健康状态，所以用来验证「恢复通知」也有效。
推荐走 `shot.sh` / `shot.ps1`：它们带单实例锁、网络等待、日志重定向和保留清理，与定时轮完全同一条路径；
直接调 `capture.py` 的区别只是输出打到前台，调完即走。

**清理磁盘**：默认每天约 300–500MB。开保留策略（推荐 7–14 天）：

```bash
# Linux：同样写进 systemctl --user edit webcapture.service 的 [Service] 段
Environment=RETENTION_DAYS=7
```
```powershell
# Windows：用户级变量，计划任务会继承（改完重新登录）
[Environment]::SetEnvironmentVariable('RETENTION_DAYS', '7', 'User')
```

清理由入口脚本在每轮结束时做，按文件 mtime 删 `*.png`，不影响 `state/` 里的基线。

**清空浏览器缓存**（截图里大量空白格、或 profile 损坏时）：

```bash
rm -rf ~/.cache/webcapture-profile
```
```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\webcapture\profile"
```

删掉会重建，代价只是下一轮变慢（冷缓存要重新下载图片）。

**升级**：代码是同一份，`git pull` 即可；依赖有变化时重跑一次 `setup.sh` / `setup.ps1`。

```bash
cd ~/stow_config && git pull          # Linux
```
```powershell
cd $env:USERPROFILE\stow_config; git pull    # Windows
```

**卸载**：

```bash
systemctl --user disable --now webcapture.timer
rm -rf ~/.local/share/webcapture-venv ~/.cache/webcapture-profile ~/.cache/webcapture-tmp
rm -rf ~/webcapture ~/public/webcapture
cd ~/stow_config && stow -D webcapture
```
```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall-task.ps1
Remove-Item -Recurse -Force "$env:USERPROFILE\webcapture", "$env:USERPROFILE\public\webcapture", "$env:LOCALAPPDATA\webcapture"
```

---

## 9. 排障

### 9.1 退出码（两边一致）

| 码 | 含义 | 处理 |
|---|---|---|
| 0 | 全部成功 | — |
| 1 | 找不到浏览器 / Playwright 启动失败 | 装浏览器，或 `WEBCAPTURE_BROWSER` 指定；看 `run.out` 里的 traceback |
| 2 | 至少一个站点截图失败 | 看 `capture.log` 的 `FAIL` 行；网络/证书/站点改版都可能 |
| 3 | 缺 playwright / pillow | 重跑 `setup.sh` / `setup.ps1` |

Linux 上对应 `systemctl --user status webcapture.service` 里的 `Result: exit-code` / `status=2`。
Windows 上对应「上次运行结果」`0x2` / `0x1` / `0x3`。

### 9.2 常见现象

| 现象 | 原因与处理 |
|---|---|
| 一张图都没出，日志 `缺 playwright/pillow` | venv 没建好：重跑 `setup.sh` / `setup.ps1` |
| `未找到 chromium/chrome` | 装浏览器；Linux 别装 snap 版（沙箱受限），Windows 用 Chrome/Edge |
| 定时任务到点不跑 | Linux：`list-timers` 看 NEXT、`loginctl` 看 linger；Windows：任务必须用户已登录 |
| 截图大量空白格（首轮） | 冷缓存，跑两轮就稳定；仍空则查网络/代理 |
| 每轮都报同一个站点的变更 | 先看 `capture.log` 的 `CHANGE` 行确认是否真变；确属噪声再加 `IGNORE_REGEX` / 开 `STRIP_DATE_PREFIX` / 开 `IGNORE_REORDER` |
| 报警频繁但网页没变 | 看 `_diffs/` 红框图；多半是轮播/滚动，确认 `WEB_FREEZE_MOTION=1` |
| 钉钉返回 `310000 关键词不匹配` | `DINGTALK_KEYWORD` 与机器人安全设置不一致 |
| 钉钉消息挤成一行 / 符号变圆点 | 钉钉 markdown 只支持有限语法，本项目的分段格式已适配；不要自行删掉空行 |
| Windows 中文乱码 | 脚本已强制 UTF-8；手动看日志加 `-Encoding UTF8` |
| Windows `PROFILE 复用失败` | 上轮被强杀留下锁，脚本会清锁重试；仍失败删 profile 目录 |
| `设备上没有空间` | `/tmp` 是小 tmpfs；入口脚本已把临时目录指到磁盘，别绕过 `shot.sh` / `shot.ps1` 直接 `pip install` |

---

## 10. 设计取舍（改之前先读）

- **文本为主信号，图像为辅**。图像比对噪声大（字体渲染、广告位），默认只记录不报警。
- **水印不打在比对的图上**。裸图单独存 `state/<host>.prev.png`，否则每轮「全页变化」。
- **顺序变化不报警**。横向滚动列表会把第一个条目轮转到末尾，导致 `+X/-X` 的假报警；
  代价是「新闻重排」也不报。要恢复就 `IGNORE_REORDER=0`。
- **失败降频**。不降频的话站点挂一天就是 96 条同样的消息。
- **动效冻结**是必要的，不是可选优化：同一站点两轮之间，轮播能让整页差异到 14%+，
  冻结后稳定在 0.02%–0.05%。
- **用系统浏览器**而不是 Playwright 自带 Chromium：省 150MB，且和用户实际看到的渲染一致。

---

*最后更新：2026-11-03*
