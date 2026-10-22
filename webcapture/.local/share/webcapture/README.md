# webcapture —— 网页定时整页截图 + 时间水印 + 失败报警 + 恢复通知

每 15 分钟对固定几个网址整页截图，图上打时间水印；请求失败推送到钉钉/企业微信群机器人，
站点恢复正常时再推一条「已恢复」，形成闭环。

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

## 文件

| 路径 | 作用 |
|---|---|
| `.local/share/webcapture/capture.py` | Playwright 整页截图 + Pillow 打水印 |
| `.local/share/webcapture/compare.py` | 变更检测：文本哈希 + 整页图差异 |
| `.local/share/webcapture/shot.sh` | 入口：找解释器、flock 防重叠、日志、清理 |
| `.local/share/webcapture/notify.py` | 钉钉/企业微信 webhook 报警 |
| `.local/share/webcapture/health.py` | 站点健康状态：连续失败计数、降频、恢复判定 |
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
~/webcapture/state/<域名>.health.json              # 连续失败计数（fail_count=0 即正常）
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
