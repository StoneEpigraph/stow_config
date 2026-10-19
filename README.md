# stow_config

Arch Linux 双机 dotfiles：台式机（MSI MS-7D42 / KDE Plasma）+ ThinkBook 16 G5+。
用 GNU stow 管理，**包名 = 应用名**，包内按 `$HOME` 的相对路径组织。

```
~/stow_config/<pkg>/.config/<app>/xxx   --stow-->   ~/.config/<app>/xxx
```

两台机器路径习惯一致（用户都是 `stone`），所以同一份包可以直接搬。

---

## 快速开始

### 新机器一次装齐

```bash
git clone git@github.com:StoneEpigraph/stow_config.git ~/stow_config
cd ~/stow_config
./apply.sh          # 预演，只打印会做什么，不动文件
./apply.sh --go     # 真正执行
```

`apply.sh` 会先把挡路的实体文件备份到 `~/.stow_backup-<时间戳>/`，再让位给软链，不会静默丢数据。

### 只装 / 卸某一个包

```bash
cd ~/stow_config
stow --no-folding -t ~ zsh     # 装
stow -D -t ~ zsh               # 卸（只删软链，仓库文件不动）
```

`--no-folding` 保持包的目录结构，避免 stow 把整个目录折叠成一条软链——折叠之后单文件增删会很别扭。

### apply.sh 的开关

| 参数 | 作用 | 什么时候用 |
|---|---|---|
| 无 | 预演（`stow -n`） | 每次都先跑一遍 |
| `--go` | 执行 | 日常唯一需要的 |
| `--adopt` | 先把系统上的实体文件反向收进仓库 | 在新机器上接管已有配置 |
| `--prune` | 清理指向本仓库的孤儿软链（断链、手工 `ln -s` 的重复链） | 换机、删包之后 |
| `--restow` | `stow -R`，重建所有目录链 | 少用，见下 |

> `--restow` 会把 `~/.config/gitui` 这类目录重新折叠，顺手带走手工放进去的 `.bak`/`.old`。日常只要 `--go`。

---

## 约定

- **包名 = 应用名**，一个包只管一个程序。
- 新增包：`mkdir -p <pkg>/<相对路径>` → 放文件 → 把包名加进 `apply.sh` 的 `PACKAGES` → `stow --no-folding -t ~ <pkg>`。
- 仓库里的文件就是系统上生效的文件（软链），**改完记得 commit**，否则换机就丢。
- **不要用 `stow --adopt`**：它会用系统上的版本覆盖仓库内容。要反向吸收，用 `apply.sh --go --adopt`（只针对脚本里 `ADOPT_MAP` 列出的那几个文件）。
- 目标位置已有实体文件时 stow 会报冲突中止，先手动移走或跑 `./apply.sh --go` 让它备份让位。

---

## 包一览

| 包 | 接管的路径 | 说明 |
|---|---|---|
| `agents` | `~/.agents/` | 21 个 agent 技能包（pdf、docx、pptx、xlsx、mcp-builder、skill-creator 等）+ 版本锁 |
| `cargo` | `~/.cargo/` | crates 国内镜像、统一 target 目录、git 走命令行 |
| `dunst` | `~/.config/dunst/dunstrc` | niri / dwm 会话的通知守护，重点防通知无限堆积 |
| `emacs` | `~/.emacs.d/` | `init.el` + `config/` 分模块（ui、org、lsp、eaf、hugo、md、kbd…） |
| `fastfetch` | `~/.config/fastfetch/` | 系统信息展示，含 detailed / standard / minial 三套 preset |
| `fcitx5` | `~/.pam_environment`、`~/.config/environment.d/im.conf` | 输入法环境变量 |
| `ghostty` | `~/.config/ghostty/config` | 终端。**目前是 stow 生成的空模板，没有任何实际选项** |
| `gitui` | `~/.config/gitui/{theme,key_bindings}.ron` | git TUI 的主题与键位 |
| `kanata` | `~/kanata.kbd` | 键盘重映射（Lisp 风格配置，`defsrc` 全键位 + 分层） |
| `mvnvm` | `~/.mvnvm.properties` | Maven 3.5.4，下载源换阿里云 |
| `ncmpcpp` | `~/.ncmpcpp/config` | MPD 客户端（目前只写了一行 music dir） |
| `qbittorrent-history` | `~/.local/bin/qbhist*`、`~/.config/systemd/user/` | qBittorrent 下载历史库，重复下载时给提示 |
| `ripgrep` | `~/.config/.ripgreprc` | 默认 `--hidden`、限制超长行、自定义 `web` 类型 |
| `vim` | `~/.vimrc`、`~/.vim/` | vim-plug + 11 个插件（nerdtree、airline、ctrlp、emmet…） |
| `workbuddy` | `~/.workbuddy/*.md` | AI 助手的身份与记忆文件（SOUL / IDENTITY / USER / MEMORY） |
| `zed` | `~/.config/zed/{settings,keymap}.json` | 编辑器，含 `openai_compatible` 模型接入配置 |
| `zsh` | `~/.zshrc`、`~/.zshenv`、`~/.zsh/` | oh-my-zsh + `ys` 主题 + autosuggestions，别名与各语言 PATH |

体积参考：`cargo` 1.6G、`emacs` 236M、`agents` 14M、`vim` 11M，其余都在几十 KB。

---

## 各包要点

### zsh
`ZSH_THEME="ys"`，`plugins=(git)`，`.zsh/` 下带 `zsh-autosuggestions`。
`.zshenv` 负责非交互也要生效的东西：cargo 环境、`FZF_DEFAULT_COMMAND`、`RIPGREP_CONFIG_PATH`、`.local/bin` 进 PATH。
`.zshrc` 里还挂了 thefuck、zoxide、atuin、sdkman、rustup 镜像。

启用：`stow --no-folding -t ~ zsh`，然后 `exec zsh` 或重开终端。
依赖（不在仓库里，需要自己装）：`oh-my-zsh`、`thefuck`、`zoxide`、`atuin`、`sdkman`、`yazi`、`fd`。

### ripgrep
`~/.config/.ripgreprc` 提供 `--hidden`、`--max-columns=240`、`web` 类型等默认项。
**ripgrep 只认 `RIPGREP_CONFIG_PATH`，不会自动去找这个文件**，所以 `.zshenv` 里那行 export 是前提，删了配置就静默失效。

### dunst
给 niri / dwm 这类没有 plasmashell 的会话用。三条防线：`notification_limit = 5`、三个 urgency 的 timeout（5/15/30 秒）、`match_dbus_timeout` 规则把应用传来的"永不超时"按成 15 秒。
**Plasma 会话不要启动 dunst**，否则会和 plasmashell 抢 `org.freedesktop.Notifications`。
改完 `dunstctl reload`。

### kanata
`~/kanata.kbd` 只是配置，程序本身要另外装：

```bash
sudo pacman -S kanata
kanata --cfg ~/kanata.kbd        # 先手动跑，确认键位没问题
```

要开机自启得自己写 systemd 服务或用桌面自启（`Exec=kanata --cfg /home/<user>/kanata.kbd`）。
kanata 走 `uinput`，用户需要在 `input` 组里，否则会报权限错误。
当前这台机器**没有安装 kanata**，这个包只是把配置留档。

### fcitx5
`environment.d/im.conf` 管 Wayland 会话，`.pam_environment` 管登录时；`~/.zshrc` 里还有一份 `XMODIFIERS` 等变量。
改完要重新登录（`environment.d` 在会话启动时读一次）。

### emacs
`init.el` 是入口，`config/` 下按主题拆分：`init-package`（包管理）、`init-ui`、`init-org`、`init-lsp`、`init-eaf`、`init-hugo`、`init-md`、`init-kbd` 等。
`elpa/` 是 73 个已安装包，`eln-cache/` 是原生编译产物——**换机时这两块可以不要**，让 emacs 自己重装，能省 200M+。

### cargo
`config.toml` 里 crates.io 换成清华 TUNA，另备了 USTC / rsproxy；`target-dir` 统一到 `~/.target`；`git-fetch-with-cli = true` 避免内网拉取卡住。
`registry/`、`git/`、`advisory-dbs/` 都是缓存，**新机器建议只拷 `config.toml`**，别把 1.6G 拉一遍。

### vim
vim-plug 管理，`~/.vim/plugged` 已有 11 个插件。新机器首次启动需要 `:PlugInstall`。
`plugin/` 下是分文件的插件配置（`apperance.vim` 文件名确实是这么拼的）。

### ghostty
仓库里只有一份空模板（`Ghostty` 首次运行自动生成的那种），没有任何实际选项，配色走默认。
如果要改，直接编辑 `~/.config/ghostty/config`（它已经是软链或实体文件，取决于有没有 stow 过）。

### agents
`~/.agents/skills/` 下 21 个技能，`.skill-lock.json` 记录版本。纯数据，不涉及启动。

### workbuddy
`SOUL.md`（人格底色）、`IDENTITY.md`（身份）、`USER.md`（用户画像）、`MEMORY.md`（长期约定）。
这些文件是 AI 助手跨会话的记忆，**改动要慎重，且不要用 `--adopt` 反吸**。

### qbittorrent-history
读 `~/.local/share/qBittorrent/BT_backup/` 里的 `.torrent` + `.fastresume`（不依赖 WebUI），
只收录**下载完成**的任务，正在下载的不入库。重复下载时提示"已经下载过，是否重新下载"。

```bash
stow --no-folding -t ~ qbittorrent-history
qbhist stats              # 看库状态
qbhist check <磁力/种子>   # 查是否下过
qbhist enable-magnet      # 接管磁力链接，添加前弹确认
qbhist hook               # 让 qBittorrent 每下完一个就即时入库（需 qBittorrent 退出时写入）
qbhist stop               # 停掉后台同步（systemd 会再拉起，要长期停用 systemctl --user disable）
```

**开机自动同步**靠 systemd 用户服务，不再用 XDG autostart：

```bash
systemctl --user enable --now qbhist-sync.service   # 启用（本来就已 enable 可跳过）
systemctl --user status qbhist-sync.service         # 看状态
journalctl --user -u qbhist-sync.service -f         # 看日志
loginctl enable-linger $USER                        # 关键：不登录桌面也运行
```

`enable-linger` 必须开，否则用户服务只在图形登录后启动、注销即停。
服务是 `Restart=always`，进程被杀了 15 秒后自动拉起，不依赖登录会话。
单实例互斥用 `flock`（`~/.local/share/qb-history/watch.lock`），不靠 PID 文件——
重启后 PID 会复用，靠 pid 判断会误以为已有实例在跑而静默退出。

数据在 `~/.local/share/qb-history/history.db`（不进 git）。换机后重新 `daemon-reload`
再 enable 即可；unit 里用 `%h` 展开家目录，不写死用户名。

---

## 换机流程

```bash
# 新机器
git clone git@github.com:StoneEpigraph/stow_config.git ~/stow_config
cd ~/stow_config && ./apply.sh          # 看清楚要动哪些文件
./apply.sh --go

# 日常同步（两台都改了之后）
cd ~/stow_config && git pull            # 或 push
stow --no-folding -t ~ <改动的包>
```

`git pull` 之后如果仓库新增了文件，需要重新 `stow` 一次对应包才会建链；已有的软链不用管。
