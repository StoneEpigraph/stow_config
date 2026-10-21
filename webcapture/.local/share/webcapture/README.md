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
| `.local/share/webcapture/shot.sh` | 入口：找解释器、flock 防重叠、日志、清理 |
| `.local/share/webcapture/notify.py` | 钉钉/企业微信 webhook 报警 |
| `.local/share/webcapture/setup.sh` | 一次性环境准备 |
| `.config/systemd/user/webcapture.*` | 每 15 分钟的 user timer |

## 产物

```
~/webcapture/<域名>/<YYYY-MM-DD>/<HHMMSS>.png
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
