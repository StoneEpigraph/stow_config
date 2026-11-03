# webcapture —— Windows 版

> 完整操作手册（Linux + Windows 并列）见 [USAGE.md](USAGE.md)；
> 本文件只讲 Windows 特有的前置、差异和排障。

Windows 与 Linux **共用同一份 Python 逻辑**（`capture.py` / `compare.py` / `health.py` / `notify.py`），
只把「入口」换掉：

| Linux | Windows |
|---|---|
| `setup.sh` | `setup.ps1` |
| `shot.sh` | `shot.ps1` |
| `systemd --user` 的 `webcapture.timer` | 计划任务（`install-task.ps1`） |
| `flock` 单实例 | 独占文件句柄（`FileShare.None`） |
| `nmcli` / `ip route` 等网络 | TCP 连接探测（`TcpClient`） |
| `/usr/bin/chromium` | Chrome → Edge → Chromium → Playwright 自带 Chromium |
| DejaVu 字体、Linux UA | 微软雅黑、Windows UA |

截图、水印、动效冻结、文本/图像变更检测、钉钉/企业微信报警、失败降频与恢复通知，行为与 Linux 版完全一致。

---

## 前置

- Windows 10 / 11，PowerShell 5.1（系统自带）
- Python 3.9+（Playwright 的最低要求）

  ```powershell
  winget install Python.Python.3.12
  ```

- 浏览器：已装 Chrome 或 Edge 最省事；都没有时用 `setup.ps1 -InstallBrowser` 让 Playwright 下一个 Chromium。

---

## 部署

脚本**就地运行在仓库目录里**（等价于 Linux 的 stow 软链）：`git pull` 之后代码立刻生效，
不需要重新部署；依赖、缓存放 `%LOCALAPPDATA%`，状态放 `%USERPROFILE%`，都不会脏了仓库。

```powershell
git clone git@github.com:StoneEpigraph/stow_config.git $env:USERPROFILE\stow_config

cd $env:USERPROFILE\stow_config\webcapture\.local\share\webcapture

# 建 venv、装 playwright/pillow、检查浏览器、生成 notify.conf
powershell -ExecutionPolicy Bypass -File .\setup.ps1

# 没有 Chrome/Edge 时加 -InstallBrowser（下载约 150MB）
powershell -ExecutionPolicy Bypass -File .\setup.ps1 -InstallBrowser

# 先手动跑一轮确认能出图
powershell -ExecutionPolicy Bypass -File .\shot.ps1
```

填报警渠道（`notify.conf` 含密钥，不随仓库分发）：

```powershell
notepad $env:USERPROFILE\webcapture\notify.conf
& "$env:LOCALAPPDATA\webcapture\venv\Scripts\python.exe" .\notify.py --test
```

注册每 15 分钟的计划任务：

```powershell
powershell -ExecutionPolicy Bypass -File .\install-task.ps1

# 想一步到位：setup.ps1 也能直接带上
powershell -ExecutionPolicy Bypass -File .\setup.ps1 -RegisterTask
```

计划任务管理：

```powershell
Start-ScheduledTask -TaskName webcapture                  # 立刻跑一轮
Get-ScheduledTask -TaskName webcapture                    # 看状态
Get-ScheduledTaskInfo -TaskName webcapture | Format-List  # 看上次结果
Disable-ScheduledTask -TaskName webcapture                # 暂停
powershell -ExecutionPolicy Bypass -File .\uninstall-task.ps1
```

---

## 目录映射

| 内容 | Windows 路径 | 对应 Linux |
|---|---|---|
| 代码 | `<仓库>\webcapture\.local\share\webcapture` | `~/.local/share/webcapture`（stow 软链） |
| 状态 / 日志 / 基线 | `%USERPROFILE%\webcapture` | `~/webcapture` |
| 成品截图 | `%USERPROFILE%\public\webcapture` | `~/public/webcapture` |
| venv | `%LOCALAPPDATA%\webcapture\venv` | `~/.local/share/webcapture-venv` |
| 浏览器 profile | `%LOCALAPPDATA%\webcapture\profile` | `~/.cache/webcapture-profile` |
| 临时目录 | `%LOCALAPPDATA%\webcapture\tmp` | `~/.cache/webcapture-tmp` |

产物结构与 Linux 相同：`_latest\<域名>.png`、`_latest\SUMMARY.txt`、`<域名>\<日期>\<时分秒>.png`、
`_diffs\<域名>\<时间>.png`，状态在 `%USERPROFILE%\webcapture\state`。

---

## 与 Linux 版的差异

| 场景 | Linux | Windows |
|---|---|---|
| 调度 | systemd user timer，可选 linger 开机即跑 | 计划任务，**登录后**才跑（没有 linger 的对应物） |
| 错过触发点 | `Persistent=true` 补跑一轮 | `StartWhenAvailable` 补跑一轮 |
| 单实例 | `flock -n` | 独占打开 `%USERPROFILE%\webcapture\.lock` |
| 网络等待 | `nmcli` / `ip route` | 连接 `www.baidu.com:443`，最多 60 秒 |
| 截图权限 | `--no-sandbox` 等参数照旧 | 同左（参数对 Windows 无副作用） |
| 水印字体 | DejaVu / 文泉驿 | 微软雅黑 Bold，中英文都清楚 |
| User-Agent | `(X11; Linux x86_64)` | `(Windows NT 10.0; Win64; x64)` |
| 保留清理 | `find -mtime` | `Get-ChildItem` 按 `LastWriteTime` |

`_latest\` 仍优先用硬链接（NTFS 支持），跨卷或失败时自动退化成复制，和 Linux 版一致。

---

## 环境变量

| 变量 | 默认 | 作用 |
|---|---|---|
| `WEBCAPTURE_HOME` | `%USERPROFILE%\webcapture` | 状态 / 日志 / 基线 |
| `WEBCAPTURE_IMG_ROOT` | `%USERPROFILE%\public\webcapture` | 成品截图（想放共享盘就指到 D 盘） |
| `WEBCAPTURE_CACHE` | `%LOCALAPPDATA%\webcapture` | venv 之外的缓存父目录 |
| `WEBCAPTURE_PROFILE` | `<CACHE>\profile` | 浏览器 profile（HTTP 磁盘缓存） |
| `WEBCAPTURE_TMP` | `<CACHE>\tmp` | 临时目录 |
| `WEBCAPTURE_BROWSER` | 自动探测 | 指定浏览器 exe |
| `WEBCAPTURE_FONT` | 微软雅黑 | 指定水印字体 |
| `WEBCAPTURE_UA` | 按平台生成 | 指定 User-Agent |
| `WEBCAPTURE_VENV` | `%LOCALAPPDATA%\webcapture\venv` | 指定 venv 目录（`shot.ps1` 用） |
| `WEBCAPTURE_PYTHON` | — | 指定解释器（`shot.ps1` 优先试它） |
| `RETENTION_DAYS` | 0（不删） | 超过天数的截图自动清理 |
| `WEB_FREEZE_MOTION` / `WEB_IMAGE_WAIT_MS` / `WEB_DATE_WAIT_MS` | 1 / 3000 / 6000 | 与 Linux 版相同 |

设置成**用户级**持久变量（计划任务会继承）：

```powershell
[Environment]::SetEnvironmentVariable('WEBCAPTURE_IMG_ROOT', 'D:\public\webcapture', 'User')
```

> 改完要重新登录（或重启），计划任务才会拿到新环境变量；
> 手动跑 `shot.ps1` 时新开的 PowerShell 窗口即可生效。

报警降频和变更检测的开关仍在两个配置文件里，键名和 Linux 版完全一样：

- `%USERPROFILE%\webcapture\notify.conf`：`FAIL_ALERT_INTERVAL`、`ALERT_ON_RECOVER`
- `%USERPROFILE%\webcapture\compare.conf`：`ALERT_ON_TEXT_CHANGE`、`IGNORE_REGEX` 等

---

## 让局域网看截图

默认目录是 `%USERPROFILE%\public\webcapture`，直接开个只读共享即可：

```powershell
New-SmbShare -Name webcapture `
             -Path "$env:USERPROFILE\public\webcapture" `
             -ReadAccess Everyone

# 取消共享
Remove-SmbShare -Name webcapture
```

如果已经有一块共享盘（或 NAS 挂载），更推荐把成品直接写过去：

```powershell
[Environment]::SetEnvironmentVariable('WEBCAPTURE_IMG_ROOT', '\\nas\public\webcapture', 'User')
```

> 注意：`_latest` 的硬链接只在同一卷内可用，写到网络共享会自动退化成复制（功能不受影响）。

局域网访问：`\\<主机名>\webcapture\_latest`，和 Linux 版一样先看 `SUMMARY.txt` 的最后成功时间。

---

## 排障

| 现象 | 处理 |
|---|---|
| 日志里 `ERROR 未找到 Chrome / Edge ...` | 装 Chrome/Edge，或跑 `setup.ps1 -InstallBrowser`，或用 `WEBCAPTURE_BROWSER` 指定 |
| 计划任务上次运行结果 `0x2` | 有站点截图失败（脚本用退出码 2 表示），看 `run.out` / `capture.log` |
| 上次运行结果 `0x1` | 找不到浏览器，或 Playwright 启动失败（看 `run.out` 里的 traceback） |
| 上次运行结果 `0x3` | 缺 playwright/pillow，重跑 `setup.ps1` |
| 任务不跑 | 该任务只在**当前用户登录后**运行；`Get-ScheduledTaskInfo` 看 `LastRunTime` |
| 中文变乱码 | 脚本已强制 UTF-8；手动看日志用 `Get-Content "$env:USERPROFILE\webcapture\run.out" -Encoding UTF8` |
| `PROFILE 复用失败 ... 清锁重试` | 上一轮被强杀留下的锁；脚本会自动清，仍失败就删 `%LOCALAPPDATA%\webcapture\profile` |
| 首次跑截图里大量空白格 | 持久 profile 首次是冷缓存，跑两轮后稳定（与 Linux 版同因） |
| 脚本被策略拦住 | 命令里加 `-ExecutionPolicy Bypass`，或 `Unblock-File .\*.ps1` |
| 想看详细日志 | `Get-Content "$env:USERPROFILE\webcapture\capture.log" -Tail 50 -Encoding UTF8` |

调试单站点：

```powershell
powershell -ExecutionPolicy Bypass -File .\shot.ps1 https://www.bjyouth.gov.cn/
```

---

## 卸载

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall-task.ps1

Remove-Item -Recurse -Force "$env:USERPROFILE\webcapture"
Remove-Item -Recurse -Force "$env:USERPROFILE\public\webcapture"
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\webcapture"
```
