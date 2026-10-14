# MEMORY.md — 长期约定

## 称呼（固定，不要搞反）
- 用户 = **茶**
- 我（助手）= **茶友**

## 用户环境
- 双机工作流，**两台都是 Arch Linux**：
  - 本机：台式，MSI MS-7D42 主板，KDE Plasma（Wayland），用户 `stone`，shell zsh
  - 笔记本：ThinkBook 16 G5+，KDE Plasma（与本机基本一致），偶尔用窗口管理器 dwm / niri
- 两台同源：pacman / AUR / `~/.config/` 路径习惯通用。

## 配置管理：stow + GitHub（重要）
- 所有配置文件由 **GNU stow 2.4.1** 管理。仓库根目录 `~/stow_config`（`git@github.com:StoneEpigraph/stow_config.git`），茶定期在台式机与 ThinkBook 之间同步。
- 约定：**包名 = 应用名**，包内按 `$HOME` 相对路径组织（例：`ghostty/.config/config.ghostty`）。
- 我的身份文件属于包 **`workbuddy`**：
  - 仓库内真实文件：`~/stow_config/workbuddy/.workbuddy/{SOUL,IDENTITY,USER,MEMORY}.md`
  - `~/.workbuddy/` 下同名文件是指向仓库的软链
- **改这些文件时直接改（软链会写回仓库），改完提醒茶提交。绝对不要用 `stow --adopt`——那会用本地内容覆盖仓库内容。**
- 新增一个包的流程：`mkdir -p ~/stow_config/<pkg>/<相对路径>` → 放文件 → `cd ~/stow_config && stow --no-folding <pkg>`
- 在另一台机器上启用：`cd ~/stow_config && git pull && stow <pkg>`（若目标位置已存在同名实体文件，先删掉或移走，否则 stow 会报冲突）

## 通知配置（两套，别混）
- **Plasma 会话**：plasmanotifyrc → `[Notifications] PopupTimeout = 15000`（毫秒，15 秒）。
- **niri / dwm 会话**：用 dunst，配置在 stow 包 `dunst`（`~/stow_config/dunst/.config/dunst/dunstrc`）。
  - 关键设置：`notification_limit = 5`、`pause_on_mouse_over = false`、
    urgency timeout 分别 5 / 15 / 30 秒，
    以及规则 `[force-timeout-on-never-expire]`（`match_dbus_timeout = 0` + `override_dbus_timeout = 15`），
    专门按死浏览器/Electron 传 `timeout=0` 导致永不消失的通知。
  - 配色对齐 ghostty 的 Tomorrow Night Eighties（bg `#282c34`）。
  - **注意**：`override_dbus_timeout` 是**规则级**属性，不能写进 `[global]`（已查 dunst 源码 settings_data.h 确认）。
  - Plasma 会话下**不要**启动 dunst，否则会和 plasmashell 抢 org.freedesktop.Notifications。
  - dunst 在 Arch 上：`sudo pacman -S dunst`；改配置后 `dunstctl reload`。

## 会话环境差异
- 有通知相关的改动，记得**两处都看**（plasmanotifyrc + dunstrc），别只改一处就以为完事。

## 工作偏好
- 用简体中文交流，不需要寒暄，直接给可执行结论。
- 改他的系统配置时：**先读现状 → 备份 → 再改 → 验证 → 告诉他回滚路径**。
- 给出方案时优先"改配置文件 + 附图形界面等价操作"，因为界面操作会覆盖手改的值。
