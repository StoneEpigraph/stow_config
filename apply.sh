#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# apply.sh —— 把本仓库（stow 包集合）合并到当前系统
#
#   ~/stow_config/<pkg>/...  --stow-->  $HOME/...
#
# 用法：
#   ./apply.sh               # 预演（dry-run），只打印会做什么，不动文件
#   ./apply.sh --go          # 真正执行；冲突的实体文件先备份到 ~/.stow_backup-<时间戳>/
#   ./apply.sh --go --adopt  # 执行前，先把系统上更新的实体文件反向收进仓库
#   ./apply.sh --go --prune  # 顺带清理历史遗留的坏软链（pkg 已删除的旧链接）
#   ./apply.sh --go --restow # 用 stow -R 重新收拢目录链接（会重建已有链，谨慎）
#
# 设计要点：
#   1. stow 遇到「目标已是实体文件」时只报冲突并中止。本脚本先备份、再移除，
#      不会静默丢数据；备份目录会打印出来。
#   2. 默认只做「仓库 -> 系统」的链接；反向吸收必须显式 --adopt。
#   3. 幂等：已正确链接的项会被 stow 跳过，重复执行安全。
#   4. 不要用 -R 做日常应用：它会把 ~/.config/gitui 这类目录重新折叠，
#      顺手带走历史上手工放进去的 .bak/.old 文件。日常只需要 `--go`。
#
# 回滚：把备份目录里的文件拷回原位，再删掉对应软链即可。
# ---------------------------------------------------------------------------
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${HOME}"

PACKAGES=(
  agents cargo dunst emacs fastfetch fcitx5 ghostty gitui kanata
  mvnvm ncmpcpp ripgrep vim workbuddy zed zsh
)

# 目标若还是「实体文件」就需要先备份让位（相对 $HOME）
CONFLICT_TARGETS=(
  ".config/ghostty/config"
  ".config/gitui/key_bindings.ron"
  ".config/zed/settings.json"
  ".config/zed/keymap.json"
  ".config/zed/themes"
  ".workbuddy/IDENTITY.md"
  ".workbuddy/SOUL.md"
  ".workbuddy/USER.md"
)

# 历史遗留、指向本仓库但目标已不存在的坏软链（仅 --prune 时处理）
# 不写死具体路径：自动扫描，包删掉之后残留的链接都能被清掉。
PRUNE_SCAN_DEPTH=4

# --adopt 时「系统 -> 仓库」的映射表： 相对$HOME路径 : 相对仓库路径
ADOPT_MAP=(
  ".config/gitui/key_bindings.ron:gitui/.config/gitui/key_bindings.ron"
  ".config/zed/settings.json:zed/.config/zed/settings.json"
  ".config/zed/keymap.json:zed/.config/zed/keymap.json"
)

GO=0; ADOPT=0; PRUNE=0; RESTOW=0
for a in "$@"; do
  case "$a" in
    --go)     GO=1 ;;
    --adopt)  ADOPT=1 ;;
    --prune)  PRUNE=1 ;;
    --restow) RESTOW=1 ;;
    -h|--help) sed -n '2,21p' "$0"; exit 0 ;;
    *) echo "未知参数: $a" >&2; exit 2 ;;
  esac
done

log()  { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
item() { printf '      %s\n' "$*"; }

# 目标是否已被本仓库的软链接管（含通过目录软链间接接管的情况）
managed_by_repo() {
  local resolved
  resolved="$(readlink -f "$1" 2>/dev/null || true)"
  case "$resolved" in "$REPO"/*) return 0 ;; *) return 1 ;; esac
}

command -v stow >/dev/null || { echo "未安装 GNU stow，请先: sudo pacman -S stow" >&2; exit 1; }

log "仓库: $REPO   目标: $TARGET"
for p in "${PACKAGES[@]}"; do
  [ -d "$REPO/$p" ] || { echo "缺少包目录: $p" >&2; exit 1; }
done

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="$HOME/.stow_backup-$STAMP"

# --- 1) 找出需要让位的实体文件 --------------------------------------------
need_backup=()
for t in "${CONFLICT_TARGETS[@]}"; do
  p="$TARGET/$t"
  managed_by_repo "$p" && continue
  if [ -e "$p" ] && [ ! -L "$p" ]; then need_backup+=("$t"); fi
done

if [ ${#need_backup[@]} -gt 0 ]; then
  log "以下目标当前是实体文件，需要先备份再让位给软链："
  for t in "${need_backup[@]}"; do item "$TARGET/$t"; done
  if [ "$GO" = 1 ]; then
    for t in "${need_backup[@]}"; do
      mkdir -p "$BACKUP/$(dirname "$t")"
      cp -a "$TARGET/$t" "$BACKUP/$t"
    done
    log "已备份 -> $BACKUP"
  else
    item "（预演模式，未实际备份 / 删除）"
  fi
fi

# --- 2) 可选：反向吸收系统上更新的实体文件 --------------------------------
if [ "$ADOPT" = 1 ]; then
  log "--adopt：把系统上的实体文件先收进仓库"
  for m in "${ADOPT_MAP[@]}"; do
    src="$TARGET/${m%%:*}"; dst="$REPO/${m##*:}"
    managed_by_repo "$src" && continue
    if [ -f "$src" ] && [ ! -L "$src" ]; then
      mkdir -p "$(dirname "$dst")"
      if [ "$GO" = 1 ]; then cp -a "$src" "$dst"; fi
      item "$([ "$GO" = 1 ] && echo 已吸收 || echo '(预演) ') $src -> $dst"
    fi
  done
fi

# --- 3) 让位：移除将被软链替换的实体文件 ----------------------------------
if [ "$GO" = 1 ] && [ ${#need_backup[@]} -gt 0 ]; then
  log "移除已备份的实体文件，让位给软链"
  for t in "${need_backup[@]}"; do
    p="$TARGET/$t"
    if [ -d "$p" ] && [ ! -L "$p" ]; then rmdir "$p" 2>/dev/null || rm -rf "$p"
    else rm -f "$p"; fi
    item "已让位: $p"
  done
fi

# --- 4) stow --------------------------------------------------------------
if [ "$GO" = 1 ]; then
  log "执行 stow$([ "$RESTOW" = 1 ] && echo ' -R')"
  stow -v ${RESTOW:+-R} -t "$TARGET" "${PACKAGES[@]}"
else
  log "预演 stow（模拟，未改文件系统）"
  stow -n -v ${RESTOW:+-R} -t "$TARGET" "${PACKAGES[@]}"
  echo
  log "确认无误后执行:  ./apply.sh --go"
fi

# --- 5) 可选：清理历史遗留坏链 --------------------------------------------
# 「包目录删了、但 $HOME 下的软链还在」会留下断链。
# 扫描 $HOME 下有限深度内、指向本仓库却已断掉的软链，逐个清掉。
if [ "$PRUNE" = 1 ]; then
  log "--prune：清理目标已不存在的仓库软链"
  REPO_BASE="$(basename "$REPO")"
  scan="$(mktemp)"
  find "$TARGET" -maxdepth "$PRUNE_SCAN_DEPTH" -xtype l 2>/dev/null > "$scan" || true
  found=0
  while IFS= read -r link; do
    tgt="$(readlink "$link" 2>/dev/null || true)"
    case "$tgt" in
      *"$REPO_BASE"/*) ;;        # 指向本仓库的断链，需要处理
      *) continue ;;
    esac
    found=1
    if [ "$GO" = 1 ]; then rm -f "$link"; item "已删除: ${link#$TARGET/}"; else item "(预演) 将删除: ${link#$TARGET/}"; fi
  done < "$scan"
  rm -f "$scan"
  [ "$found" = 0 ] && item "没有发现坏链"
fi

log "完成。回滚方式：把 $BACKUP 里的文件拷回原位并删除对应软链。"
