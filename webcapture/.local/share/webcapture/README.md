# webcapture —— 网页定时整页截图 + 时间水印 + 失败报警

每 15 分钟对固定几个网址整页截图，图上打时间水印；任一请求最终失败就推送到钉钉/企业微信群机器人。

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

## 文件

| 路径 | 作用 |
|---|---|
| `.local/share/webcapture/capture.py` | Playwright 整页截图 + Pillow 打水印 |
| `.local/share/webcapture/compare.py` | 变更检测：文本哈希 + 整页图差异 |
| `.local/share/webcapture/shot.sh` | 入口：找解释器、flock 防重叠、日志、清理 |
| `.local/share/webcapture/notify.py` | 钉钉/企业微信 webhook 报警 |
| `.local/share/webcapture/setup.sh` | 一次性环境准备 |
| `.config/systemd/user/webcapture.*` | 每 15 分钟的 user timer |

## 变更检测（compare.py）

两路信号：

1. **文本哈希（主信号）**：取 JS 执行后的 `body.innerText`，归一化（去零宽字符、折叠空白、
   按 `IGNORE_REGEX` 丢噪声行）后算 sha256。变了就报警，并附上新增/删除的行。
2. **整页图差异（辅助）**：跟上一轮**打水印前**的裸图逐像素比，输出变化像素占比，
   并在 `~/webcapture/diffs/<host>/` 生成红框标出变化区域的图。

为什么不直接比最终截图：**水印每轮都变**，带水印比会导致每张都"全页变化"。所以裸图另存
在 `~/webcapture/state/<host>.prev.png`（每站只留一张，磁盘有界），比完再打水印出成品。

配置 `~/webcapture/compare.conf`（模板 `compare.conf.example`）：

| 键 | 默认 | 含义 |
|---|---|---|
| `ALERT_ON_TEXT_CHANGE` | 1 | 文本变化就报警 |
| `ALERT_ON_IMAGE_CHANGE` | 0 | 图像变化也报警（噪声大，默认关） |
| `IMAGE_DIFF_THRESHOLD` | 0.02 | 变化像素占比阈值（2%） |
| `IGNORE_REGEX` | `^\d+/\d+$\|^\d{1,2}:\d{2}(:\d{2})?$` | 丢噪声行；默认滤轮播页码和纯时间 |
| `MAX_SNIPPET_LINES` | 6 | 报警里每站最多列几行 diff |

**第一次运行只建基线，不报警**（没有可比对象）。想重建基线就删 `~/webcapture/state/<host>.json`。

已知噪声：轮播图（页码/图片本身）、访问量计数、`星期X`、日期。文本侧靠 `IGNORE_REGEX` 消化；
图像侧因为默认 `ALERT_ON_IMAGE_CHANGE=0`，只记录不报警。


## 产物

```
~/webcapture/<域名>/<YYYY-MM-DD>/<HHMMSS>.png     # 成品（带水印）
~/webcapture/state/<域名>.{json,txt,prev.png}      # 基线：哈希 / 上轮文本 / 上轮裸图
~/webcapture/diffs/<域名>/<时间>.png               # 红框标出变化的差异图
~/webcapture/capture.log     # 每条结果即时写，排障先看这个
~/webcapture/run.out         # 每轮汇总
```

## 改网址

改 `capture.py` 顶部的 `DEFAULT_URLS`。

## 注意

- `/tmp` 若是小容量 tmpfs，pip 会报「设备上没有空间」；`shot.sh`/`setup.sh` 已把 `TMPDIR`
  指到 `~/.cache/webcapture-tmp`，Chromium 也带 `--disable-dev-shm-usage`。
- 不给 Playwright 下载自带 Chromium，直接用系统 `chromium`/`google-chrome-stable`。
- 水印用中灰+浅描边，纯白字在白底页面会看不见。
- 磁盘占用约 300–500MB/天；要自动清理就在 `shot.sh` 里把 `RETENTION_DAYS` 改成 7。
